import asyncio
import re
import time
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from parser import HaloLiveParser, SESSION_EXPIRED
from keyboards import get_cancel_kb
from state import user_modes, admin_check_mode

router = Router()
logger = logging.getLogger(__name__)

pending_tfa: dict = {}      # admin_tg_id -> {anchor_id, user_tg_id, user_username, agency_name}
pending_parsers: dict = {}  # agency_name -> HaloLiveParser instance (awaiting 2FA)
active_sessions: dict = {}  # agency_name -> logged-in HaloLiveParser instance
user_last_check: dict = {}  # user_id -> timestamp of last check

CHECK_COOLDOWN = 15  # seconds between checks for non-admin users

GRADE_LIMITS = {"S": None, "A": 0.25, "B": 0.18, "C": 0.18, "D": 0.12}
PUNISHMENTS = {
    "S": None,
    "A": "⛔ Бан на 1 день",
    "B": "⛔ Бан на 3 дня",
    "C": "⛔ Бан на 7 дней",
    "D": "⛔ Перманентный бан",
}


def is_valid_anchor_id(text: str) -> bool:
    return bool(re.match(r'^\d{7,15}$', text.strip()))


def get_grade(monthly_income: int) -> str:
    monthly_income = int(monthly_income)
    if monthly_income >= 45000:
        return "S"
    elif monthly_income >= 20000:
        return "A"
    elif monthly_income >= 7000:
        return "B"
    elif monthly_income >= 2000:
        return "C"
    else:
        return "D"


def check_risk(grade: str, down_rate: float, real_down_rate: float) -> list:
    risks = []
    if float(down_rate) >= 0.18:
        risks.append("— коэффициент в профиле выше 0.18")
    limit = GRADE_LIMITS.get(grade)
    if limit is not None and float(real_down_rate) >= limit:
        risks.append(f"— коэффициент за 30 дней выше лимита для уровня {grade}")
    return risks


def format_check_result(host: dict) -> str:
    grade = get_grade(host["MonthlyIncome"])
    down_rate = float(host["DownRate"])
    real_down_rate = float(host["RealDownRate"])
    monthly_income = int(host["MonthlyIncome"])
    risks = check_risk(grade, down_rate, real_down_rate)

    text = (
        f"Ваш ID: {host['DisplayAccountId']}\n"
        f"Агентство: {host['Agent']}\n\n"
        f"Коэффициент в профиле: {down_rate}\n"
        f"Коэффициент за последние 30 дней: {real_down_rate}\n\n"
        f"Месячный заработок: {monthly_income:,} coins\n"
        f"Уровень: {grade}\n"
    )

    if not risks:
        text += "\n✅ Всё в норме"
    else:
        punishment = PUNISHMENTS.get(grade)
        text += "\n⚠️ Внимание, вы в зоне риска\n\nПричина:\n"
        text += "\n".join(risks)
        if punishment:
            text += f"\n\nВозможное наказание:\n{punishment}"

    return text


@router.callback_query(F.data == "cancel_2fa")
async def cancel_2fa_callback(callback: CallbackQuery, bot: Bot, db: Database):
    admin_id = callback.from_user.id
    pending = pending_tfa.get(admin_id)

    if not pending:
        await callback.message.edit_text("❌ Нет активной проверки.")
        await callback.answer()
        return

    user_tg_id = pending["user_tg_id"]
    agency_name = pending["agency_name"]

    for aid in db.get_all_admins():
        pending_tfa.pop(aid, None)
    pending_parsers.pop(agency_name, None)

    try:
        await bot.send_message(
            user_tg_id,
            "⚠️ Проверка отменена. Попробуйте отправить ID ещё раз позже."
        )
    except Exception as e:
        logger.error(f"Cannot notify user {user_tg_id} about cancellation: {e}")

    await callback.message.edit_text("❌ Проверка отменена. Пользователь уведомлён.")
    await callback.answer()


@router.message(F.text == "Проверить ID")
async def prompt_admin_check(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.add(message.from_user.id)
    await message.answer("Введите ID для проверки:", reply_markup=get_cancel_kb())


@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot, db: Database):
    user_id = message.from_user.id

    if db.is_admin(user_id):
        if user_id in pending_tfa:
            await _handle_tfa_response(message, bot, db)
        elif user_id in admin_check_mode:
            admin_check_mode.discard(user_id)
            await _handle_id_check(message, bot, db)
        return

    await _handle_id_check(message, bot, db)


async def _handle_tfa_response(message: Message, bot: Bot, db: Database):
    user_id = message.from_user.id
    code = (message.text or "").strip()

    if not re.match(r'^\d{6}$', code):
        await message.answer("Код должен состоять из 6 цифр. Попробуйте ещё раз.")
        return

    pending = pending_tfa[user_id]
    anchor_id = pending["anchor_id"]
    user_tg_id = pending["user_tg_id"]
    user_username = pending["user_username"]
    agency_name = pending["agency_name"]

    parser = pending_parsers.get(agency_name)
    if not parser:
        await message.answer("⚠️ Ошибка при получении данных. Попробуйте позже.")
        pending_tfa.pop(user_id, None)
        return

    login_result = await asyncio.to_thread(parser.login, code)

    if login_result is True:
        active_sessions[agency_name] = parser
        host = await asyncio.to_thread(parser.find_by_id, anchor_id)

        admin_ids = db.get_all_admins()
        for admin_id in admin_ids:
            pending_tfa.pop(admin_id, None)
        pending_parsers.pop(agency_name, None)

        if host and host is not SESSION_EXPIRED:
            result_text = format_check_result(host)
            grade = get_grade(host["MonthlyIncome"])
            risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
            db.save_check(
                tg_id=user_tg_id,
                username=user_username,
                anchor_id=anchor_id,
                agency=host.get("Agent", agency_name),
                down_rate=host["DownRate"],
                real_down_rate=host["RealDownRate"],
                monthly_income=host["MonthlyIncome"],
                grade=grade,
                has_risk=len(risks) > 0,
                found=True
            )
            try:
                await bot.send_message(user_tg_id, result_text)
            except Exception as e:
                logger.error(f"Cannot send result to user {user_tg_id}: {e}")
            await message.answer("✅ Готово. Ответ отправлен пользователю.")
        else:
            db.save_check(
                tg_id=user_tg_id,
                username=user_username,
                anchor_id=anchor_id,
                agency=agency_name,
                down_rate="",
                real_down_rate="",
                monthly_income="",
                grade="",
                has_risk=False,
                found=False
            )
            try:
                await bot.send_message(
                    user_tg_id,
                    "ID не найден. Проверьте правильность ID и попробуйте ещё раз."
                )
            except Exception as e:
                logger.error(f"Cannot send not-found message to user {user_tg_id}: {e}")
            await message.answer("✅ Проверка завершена. ID не найден ни в одном агентстве.")

    else:
        await message.answer("❌ Неверный код 2FA. Попробуйте ввести код ещё раз:")


async def _handle_id_check(message: Message, bot: Bot, db: Database):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if not is_valid_anchor_id(text):
        await message.answer("Пожалуйста, отправьте корректный ID (только цифры).")
        return

    if not db.is_admin(user_id):
        now = time.time()
        last = user_last_check.get(user_id, 0)
        if now - last < CHECK_COOLDOWN:
            remaining = int(CHECK_COOLDOWN - (now - last))
            await message.answer(f"⏳ Подождите {remaining} сек. перед следующей проверкой.")
            return
        user_last_check[user_id] = now

    anchor_id = text
    user_username = message.from_user.username

    await message.answer("🔍 Ищу вашу информацию...")

    admin_ids = db.get_all_admins()
    agencies = db.get_all_agencies()

    if not agencies:
        await message.answer("⚠️ Нет подключённых агентств. Обратитесь к администратору.")
        return

    had_timeout = False
    had_network_error = False

    for agency in agencies:
        agency_name = agency["name"]

        # Try reusing an existing session first
        existing = active_sessions.get(agency_name)
        if existing:
            try:
                host = await asyncio.to_thread(existing.find_by_id, anchor_id)
            except Exception as e:
                logger.error(f"find_by_id exception (cached session) for agency {agency_name}: {e}")
                host = None

            if host is SESSION_EXPIRED:
                logger.info(f"Session expired for agency {agency_name}, will re-login")
                active_sessions.pop(agency_name, None)
                # Fall through to fresh login below
            elif host is not None:
                result_text = format_check_result(host)
                grade = get_grade(host["MonthlyIncome"])
                risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
                db.save_check(
                    tg_id=user_id,
                    username=user_username,
                    anchor_id=anchor_id,
                    agency=host.get("Agent", agency_name),
                    down_rate=host["DownRate"],
                    real_down_rate=host["RealDownRate"],
                    monthly_income=host["MonthlyIncome"],
                    grade=grade,
                    has_risk=len(risks) > 0,
                    found=True
                )
                await message.answer(result_text)
                return
            else:
                # host is None — ID not found in this agency, try next
                continue

        # No valid cached session — create a new one and log in
        parser = HaloLiveParser(
            url=agency["url"],
            account=agency["account"],
            password=agency["password"],
            aemail=agency["aemail"],
            apassword=agency["apassword"]
        )

        try:
            login_result = await asyncio.to_thread(parser.login, None)
        except Exception as e:
            logger.error(f"Login exception for agency {agency_name}: {e}")
            continue

        if login_result is True:
            active_sessions[agency_name] = parser
            try:
                host = await asyncio.to_thread(parser.find_by_id, anchor_id)
            except Exception as e:
                logger.error(f"find_by_id exception for agency {agency_name}: {e}")
                continue

            if host and host is not SESSION_EXPIRED:
                result_text = format_check_result(host)
                grade = get_grade(host["MonthlyIncome"])
                risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
                db.save_check(
                    tg_id=user_id,
                    username=user_username,
                    anchor_id=anchor_id,
                    agency=host.get("Agent", agency_name),
                    down_rate=host["DownRate"],
                    real_down_rate=host["RealDownRate"],
                    monthly_income=host["MonthlyIncome"],
                    grade=grade,
                    has_risk=len(risks) > 0,
                    found=True
                )
                await message.answer(result_text)
                return

        elif login_result == "need_tfa":
            pending_parsers[agency_name] = parser
            for admin_id in admin_ids:
                pending_tfa[admin_id] = {
                    "anchor_id": anchor_id,
                    "user_tg_id": user_id,
                    "user_username": user_username,
                    "agency_name": agency_name
                }
                tfa_kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="❌ Отменить проверку", callback_data="cancel_2fa")
                ]])
                try:
                    await bot.send_message(
                        admin_id,
                        f"🔐 Требуется код 2FA для агентства {agency_name}\n"
                        f"Введите 6-значный код из Google Authenticator:",
                        reply_markup=tfa_kb
                    )
                except Exception as e:
                    logger.error(f"Cannot send 2FA request to admin {admin_id}: {e}")

            await message.answer("⏳ Требуется дополнительная проверка. Ожидайте ответа...")
            return

        elif login_result == "timeout":
            had_timeout = True
            logger.error(f"Login timeout for agency {agency_name}")
            continue

        elif login_result == "network":
            had_network_error = True
            logger.error(f"Login network error for agency {agency_name}")
            continue

        else:
            logger.error(f"Login failed for agency {agency_name}")
            continue

    db.save_check(
        tg_id=user_id,
        username=user_username,
        anchor_id=anchor_id,
        agency="",
        down_rate="",
        real_down_rate="",
        monthly_income="",
        grade="",
        has_risk=False,
        found=False
    )

    if had_timeout:
        await message.answer("⚠️ Время ожидания истекло. Попробуйте позже.")
    elif had_network_error:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
    else:
        await message.answer("ID не найден. Проверьте правильность ID и попробуйте ещё раз.")
