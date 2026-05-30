import asyncio
import re
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from parser import HaloLiveParser, SESSION_EXPIRED
from keyboards import get_cancel_kb
from state import user_modes, admin_check_mode, pending_tfa, tfa_waitlist

router = Router()
logger = logging.getLogger(__name__)

pending_parsers: dict = {}
active_sessions: dict = {}

GRADE_LIMITS = {"S": None, "A": 0.25, "B": 0.18, "C": 0.18, "D": 0.12}
PUNISHMENTS = {
    "S": None,
    "A": "Бан на 1 день",
    "B": "Бан на 3 дня",
    "C": "Бан на 7 дней",
    "D": "Перманентный бан аккаунта",
}
GRADE_DESCRIPTIONS = {
    "S": "заработок от 45 000 coins и выше",
    "A": "заработок от 20 000 до 44 999 coins",
    "B": "заработок от 7 000 до 19 999 coins",
    "C": "заработок от 2 000 до 6 999 coins",
    "D": "заработок менее 2 000 coins за последние 30 дней",
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
        risks.append("profile_rate")
    limit = GRADE_LIMITS.get(grade)
    if limit is not None and float(real_down_rate) >= limit:
        risks.append(f"monthly_rate:{limit}")
    return risks


def format_check_result(host: dict) -> str:
    grade = get_grade(host["MonthlyIncome"])
    down_rate = float(host["DownRate"])
    real_down_rate = float(host["RealDownRate"])
    monthly_income = int(host["MonthlyIncome"])
    raw_risks = check_risk(grade, down_rate, real_down_rate)

    monthly_rank = host.get("MonthlyIncomeRanking")
    limit = GRADE_LIMITS.get(grade)

    profile_icon = "✅" if down_rate < 0.18 else "❌"
    monthly_ok = (limit is None) or (real_down_rate < limit)
    monthly_icon = "✅" if monthly_ok else "❌"

    lines = []
    lines.append(f"🆔 Ваш ID: {host['DisplayAccountId']}")
    if monthly_rank is not None:
        lines.append(f"🏆 Место в рейтинге приложения: {monthly_rank} место")
    lines.append(f"🏢 Агентство: {host['Agent']}")
    lines.append("")
    lines.append(f"Ваш уровень: <b>{grade}</b> — {GRADE_DESCRIPTIONS[grade]}")
    lines.append(f"Заработок за последние 30 дней: <b>{monthly_income:,} coins</b>")
    lines.append(f"Коэффициент в профиле: <b>{down_rate}</b> {profile_icon}")
    lines.append(f"Коэффициент за последние 30 дней: <b>{real_down_rate}</b> {monthly_icon}")

    if not raw_risks:
        lines.append("")
        lines.append("✅ Всё в норме! Так держать 🌟")
    else:
        lines.append("")
        lines.append("⚠️ <b>Внимание! Вы находитесь в зоне риска</b>")
        lines.append("")
        lines.append("Причина:")
        for risk in raw_risks:
            if risk == "profile_rate":
                lines.append("")
                lines.append("🔸 Коэффициент в профиле превышает допустимый лимит.")
                lines.append(f"Допустимый лимит: до <b>0.18</b>")
                lines.append(f"Ваш коэффициент: <b>{down_rate}</b>")
            elif risk.startswith("monthly_rate:"):
                lim_val = risk.split(":")[1]
                lines.append("")
                lines.append(f"🔸 Коэффициент за последние 30 дней превышает допустимый лимит для уровня <b>{grade}</b>.")
                lines.append(f"Допустимый лимит: до <b>{lim_val}</b>")
                lines.append(f"Ваш коэффициент за 30 дней: <b>{real_down_rate}</b>")
        punishment = PUNISHMENTS.get(grade)
        if punishment:
            lines.append("")
            lines.append(f"⛔ Возможное наказание:")
            lines.append(f"{punishment}")
        lines.append("")
        lines.append("📌 Рекомендуется как можно быстрее улучшить показатели, чтобы снизить риск блокировки.")

    return "\n".join(lines)


def _save_session(db: Database, agency_name: str, parser: HaloLiveParser):
    try:
        cookies = parser.get_cookies()
        phpsessid = cookies.get("PHPSESSID", "")
        acuid = cookies.get("acuid", "")
        if phpsessid or acuid:
            db.save_agency_session(agency_name, phpsessid, acuid)
            logger.info(f"Session saved for {agency_name}")
    except Exception as e:
        logger.error(f"Failed to save session for {agency_name}: {e}")


def restore_sessions(db: Database, agencies: list):
    for agency in agencies:
        agency_name = agency["name"]
        saved = db.get_agency_session(agency_name)
        if not saved:
            continue
        phpsessid = saved["phpsessid"]
        acuid = saved["acuid"]
        if not phpsessid and not acuid:
            continue
        parser = HaloLiveParser(
            url=agency["url"],
            account=agency["account"],
            password=agency["password"],
            aemail=agency["aemail"],
            apassword=agency["apassword"]
        )
        ok = parser.restore_from_cookies(phpsessid, acuid)
        if ok:
            active_sessions[agency_name] = parser
            logger.info(f"Restored session for {agency_name} from DB")
        else:
            db.delete_agency_session(agency_name)
            logger.warning(f"Saved session for {agency_name} is expired, deleted")


async def _process_and_send(bot: Bot, db: Database, parser, anchor_id: str,
                            user_tg_id: int, user_username, agency_name: str):
    try:
        host = await asyncio.to_thread(parser.find_by_id, anchor_id)
    except Exception as e:
        logger.error(f"find_by_id error for {anchor_id}: {e}")
        host = None

    if host and host is not SESSION_EXPIRED:
        result_text = format_check_result(host)
        grade = get_grade(host["MonthlyIncome"])
        raw_risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
        db.save_check(
            tg_id=user_tg_id, username=user_username, anchor_id=anchor_id,
            agency=host.get("Agent", agency_name),
            down_rate=host["DownRate"], real_down_rate=host["RealDownRate"],
            monthly_income=host["MonthlyIncome"], grade=grade,
            has_risk=len(raw_risks) > 0, found=True
        )
        try:
            await bot.send_message(user_tg_id, result_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Cannot send result to user {user_tg_id}: {e}")
    else:
        db.save_check(
            tg_id=user_tg_id, username=user_username, anchor_id=anchor_id,
            agency=agency_name, down_rate="", real_down_rate="",
            monthly_income="", grade="", has_risk=False, found=False
        )
        try:
            await bot.send_message(user_tg_id, "ID не найден. Проверьте правильность ID и попробуйте ещё раз.")
        except Exception as e:
            logger.error(f"Cannot send not-found to user {user_tg_id}: {e}")


async def _search_in_agency(agency_name: str, parser, anchor_id: str) -> dict | None:
    """Ищет девушку в одном агентстве. Возвращает host dict или None."""
    try:
        host = await asyncio.to_thread(parser.find_by_id, anchor_id)
        if host is SESSION_EXPIRED:
            return SESSION_EXPIRED
        return host
    except Exception as e:
        logger.error(f"find_by_id error in {agency_name}: {e}")
        return None


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
        await bot.send_message(user_tg_id, "⚠️ Проверка отменена. Попробуйте отправить ID ещё раз позже.")
    except Exception as e:
        logger.error(f"Cannot notify user {user_tg_id}: {e}")

    waitlist = tfa_waitlist.pop(agency_name, [])
    for waiter in waitlist:
        try:
            await bot.send_message(waiter["user_tg_id"], "⚠️ Проверка отменена. Попробуйте отправить ID ещё раз позже.")
        except Exception as e:
            logger.error(f"Cannot notify waiter {waiter['user_tg_id']}: {e}")

    await callback.message.edit_text(f"❌ Проверка отменена. Уведомлено пользователей: {1 + len(waitlist)}.")
    await callback.answer()


@router.message(F.text == "Проверить ID")
async def prompt_admin_check(message: Message, db: Database):
    if message.chat.type != "private":
        return
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.add(message.from_user.id)
    await message.answer("Введите ID для проверки:", reply_markup=get_cancel_kb())


@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot, db: Database):
    if message.chat.type != "private":
        return
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
        if is_valid_anchor_id(code):
            await message.answer("⏳ Сейчас ожидается код из Google Authenticator.\nВведите 6-значный код или нажмите «❌ Отменить проверку».")
        else:
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
        _save_session(db, agency_name, parser)

        for admin_id in db.get_all_admins():
            pending_tfa.pop(admin_id, None)
        pending_parsers.pop(agency_name, None)

        await _process_and_send(bot, db, parser, anchor_id, user_tg_id, user_username, agency_name)

        waitlist = tfa_waitlist.pop(agency_name, [])
        for waiter in waitlist:
            await _process_and_send(bot, db, parser, waiter["anchor_id"], waiter["user_tg_id"], waiter["user_username"], agency_name)

        await message.answer(f"✅ Готово. Обработано запросов: {1 + len(waitlist)}. Ответы отправлены пользователям.")
    else:
        await message.answer("❌ Неверный код 2FA. Попробуйте ввести код ещё раз:")


async def _handle_id_check(message: Message, bot: Bot, db: Database):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if not is_valid_anchor_id(text):
        await message.answer("Пожалуйста, отправьте корректный ID (только цифры).")
        return

    anchor_id = text
    user_username = message.from_user.username

    await message.answer("🔍 Ищу вашу информацию...")

    admin_ids = db.get_all_admins()
    agencies = db.get_all_agencies()

    if not agencies:
        await message.answer("⚠️ Нет подключённых агентств. Обратитесь к администратору.")
        return

    # ── Шаг 1: параллельный поиск во всех агентствах с активными сессиями ──
    agencies_with_session = [a for a in agencies if a["name"] in active_sessions]
    agencies_without_session = [a for a in agencies if a["name"] not in active_sessions]

    if agencies_with_session:
        tasks = [
            _search_in_agency(a["name"], active_sessions[a["name"]], anchor_id)
            for a in agencies_with_session
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for agency, result in zip(agencies_with_session, results):
            agency_name = agency["name"]
            if isinstance(result, Exception):
                continue
            if result is SESSION_EXPIRED:
                active_sessions.pop(agency_name, None)
                db.delete_agency_session(agency_name)
                agencies_without_session.append(agency)
                continue
            if result is not None:
                # Нашли девушку!
                host = result
                result_text = format_check_result(host)
                grade = get_grade(host["MonthlyIncome"])
                raw_risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
                db.save_check(
                    tg_id=user_id, username=user_username, anchor_id=anchor_id,
                    agency=host.get("Agent", agency_name),
                    down_rate=host["DownRate"], real_down_rate=host["RealDownRate"],
                    monthly_income=host["MonthlyIncome"], grade=grade,
                    has_risk=len(raw_risks) > 0, found=True
                )
                await message.answer(result_text, parse_mode="HTML")
                return

    # ── Шаг 2: агентства без сессии — логинимся (2FA или обычный) ──
    had_timeout = False
    had_network_error = False
    tfa_requested = False

    for agency in agencies_without_session:
        agency_name = agency["name"]

        # Уже ждём 2FA для этого агентства
        if agency_name in pending_parsers:
            if agency_name not in tfa_waitlist:
                tfa_waitlist[agency_name] = []
            tfa_waitlist[agency_name].append({
                "anchor_id": anchor_id,
                "user_tg_id": user_id,
                "user_username": user_username,
            })
            await message.answer("⏳ Требуется дополнительная проверка. Ожидайте ответа...")
            return

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
            logger.error(f"Login exception for {agency_name}: {e}")
            continue

        if login_result is True:
            active_sessions[agency_name] = parser
            _save_session(db, agency_name, parser)
            try:
                host = await asyncio.to_thread(parser.find_by_id, anchor_id)
            except Exception as e:
                logger.error(f"find_by_id exception for {agency_name}: {e}")
                continue

            if host and host is not SESSION_EXPIRED:
                result_text = format_check_result(host)
                grade = get_grade(host["MonthlyIncome"])
                raw_risks = check_risk(grade, float(host["DownRate"]), float(host["RealDownRate"]))
                db.save_check(
                    tg_id=user_id, username=user_username, anchor_id=anchor_id,
                    agency=host.get("Agent", agency_name),
                    down_rate=host["DownRate"], real_down_rate=host["RealDownRate"],
                    monthly_income=host["MonthlyIncome"], grade=grade,
                    has_risk=len(raw_risks) > 0, found=True
                )
                await message.answer(result_text, parse_mode="HTML")
                return

        elif login_result == "need_tfa":
            if tfa_requested:
                continue
            tfa_requested = True
            pending_parsers[agency_name] = parser
            pending_entry = {
                "anchor_id": anchor_id,
                "user_tg_id": user_id,
                "user_username": user_username,
                "agency_name": agency_name
            }
            for admin_id in admin_ids:
                pending_tfa[admin_id] = pending_entry
            tfa_kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="❌ Отменить проверку", callback_data="cancel_2fa")
            ]])
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🔐 Требуется код 2FA для агентства {agency_name}\nВведите 6-значный код из Google Authenticator:",
                        reply_markup=tfa_kb
                    )
                except Exception as e:
                    logger.error(f"Cannot send 2FA request to admin {admin_id}: {e}")
            await message.answer("⏳ Требуется дополнительная проверка. Ожидайте ответа...")
            return

        elif login_result == "timeout":
            had_timeout = True
        elif login_result == "network":
            had_network_error = True

    # ── Нигде не нашли ──
    db.save_check(
        tg_id=user_id, username=user_username, anchor_id=anchor_id,
        agency="", down_rate="", real_down_rate="",
        monthly_income="", grade="", has_risk=False, found=False
    )

    if had_timeout:
        await message.answer("⚠️ Время ожидания истекло. Попробуйте позже.")
    elif had_network_error:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
    else:
        await message.answer("ID не найден. Проверьте правильность ID и попробуйте ещё раз.")
