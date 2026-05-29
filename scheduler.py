import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database import Database
from keyboards import get_trial_decision
from utils import format_user_info

logger = logging.getLogger(__name__)


async def check_expired_trials(bot: Bot, db: Database, admin_ids: list):
    expired = db.get_expired_trials()
    for user in expired:
        text = f"Пробный период завершен\n\n{format_user_info(user)}"
        keyboard = get_trial_decision(user['telegram_id'])
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, text, reply_markup=keyboard)
            except Exception:
                continue


async def check_expiring_soon(bot: Bot, db: Database, admin_ids: list):
    expiring = db.get_users_expiring_soon(hours=24)
    for user in expiring:
        text = (f"Пробный период скоро истечет\n\n"
                f"{format_user_info(user, show_time=True)}\n\n"
                f"Остался 1 день")
        keyboard = get_trial_decision(user['telegram_id'])
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, text, reply_markup=keyboard)
            except Exception:
                continue
        db.mark_notified(user['telegram_id'])


def _fetch_all_hosts(parser):
    r = parser.session.get(
        f"{parser.url}/anchor/anchorManage/loadExtAnchorInfoList",
        params={"page": 1, "limit": 9999},
        headers={**parser.headers, "Referer": f"{parser.url}/anchor/anchorManage/waibu_anchorInfo?in_iframe=1"},
        timeout=30
    )
    return r.json().get("data", [])


def _is_account_active(host: dict) -> bool:
    status = host.get("AccountStatus", "")
    if status is None:
        return True
    status_str = str(status).strip().lower()
    if not status_str or status_str in ("", "0", "normal", "active", "ok", "enabled"):
        return True
    blocked = {"banned", "blocked", "disabled", "frozen", "ban", "block", "disable", "freeze"}
    if status_str in blocked:
        return False
    try:
        if int(status_str) != 0:
            return False
    except (ValueError, TypeError):
        pass
    return True


async def check_all_agencies_for_risk(bot: Bot, db: Database, admin_ids: list):
    from handlers.check_handlers import get_grade, check_risk, active_sessions
    from parser import HaloLiveParser

    if db.get_setting("notifications_enabled", "1") != "1":
        return

    group_chat_id_str = db.get_setting("notifications_group_id")
    if not group_chat_id_str:
        logger.warning("notifications_group_id not set, skipping risk check")
        return

    group_chat_id = int(group_chat_id_str)
    agencies = db.get_all_agencies()

    for agency in agencies:
        agency_name = agency["name"]
        parser = active_sessions.get(agency_name)

        if parser:
            try:
                all_hosts = await asyncio.to_thread(_fetch_all_hosts, parser)
            except Exception as e:
                logger.error(f"Risk check fetch error for {agency_name}: {e}")
                active_sessions.pop(agency_name, None)
                continue
        else:
            parser = HaloLiveParser(
                url=agency["url"],
                account=agency["account"],
                password=agency["password"],
                aemail=agency["aemail"],
                apassword=agency["apassword"]
            )
            result = await asyncio.to_thread(parser.login, None)
            if result == "need_tfa":
                logger.info(f"Skipping risk check for {agency_name}: 2FA required")
                continue
            elif result is not True:
                logger.error(f"Login failed for {agency_name} during risk check")
                continue
            active_sessions[agency_name] = parser
            try:
                all_hosts = await asyncio.to_thread(_fetch_all_hosts, parser)
            except Exception as e:
                logger.error(f"Risk check fetch error for {agency_name}: {e}")
                continue

        # Собираем риски только по текущему агентству
        at_risk = []

        for host in all_hosts:
            try:
                anchor_id = str(host.get("DisplayAccountId", ""))

                if not _is_account_active(host):
                    db.clear_risk(anchor_id)
                    continue

                down_rate = host.get("DownRate")
                real_down_rate = host.get("RealDownRate")
                monthly_income = host.get("MonthlyIncome")

                if down_rate is None or real_down_rate is None or monthly_income is None:
                    continue

                grade = get_grade(monthly_income)
                risks = check_risk(grade, float(down_rate), float(real_down_rate))

                if not risks:
                    db.clear_risk(anchor_id)
                    continue

                if not db.should_notify(anchor_id):
                    continue

                at_risk.append({
                    "anchor_id": anchor_id,
                    "nickname": host.get("NickName") or host.get("AnchorName", "—"),
                    "agency": host.get("Agent", agency_name),
                    "grade": grade,
                    "down_rate": float(down_rate),
                    "real_down_rate": float(real_down_rate),
                    "risks": risks,
                })
                db.mark_risk_notified(anchor_id, host.get("Agent", agency_name))

            except Exception as e:
                logger.error(f"Error processing host {host.get('DisplayAccountId')}: {e}")
                continue

        if not at_risk:
            continue

        # Формируем одно сообщение на агентство, разбиваем если > 4000 символов
        header = f"⚠️ <b>Агентство: {agency_name}</b>\nАккаунты в зоне риска\n\n"
        SEP = "━━━━━━━━━━━━━━"

        GRADE_LIMITS = {"S": None, "A": 0.25, "B": 0.18, "C": 0.18, "D": 0.12}
        PUNISHMENTS = {
            "S": None,
            "A": "⛔ Бан на 1 день",
            "B": "⛔ Бан на 3 дня",
            "C": "⛔ Бан на 7 дней",
            "D": "⛔ Перманентный бан аккаунта",
        }

        blocks = []
        for h in at_risk:
            limit = GRADE_LIMITS.get(h["grade"])
            punishment = PUNISHMENTS.get(h["grade"])
            risk_lines = []
            for risk in h["risks"]:
                if risk == "profile_rate":
                    risk_lines.append(f"🔸 Коэффициент в профиле: <b>{h['down_rate']}</b> (лимит: до <b>0.18</b>)")
                elif risk.startswith("monthly_rate:"):
                    lim_val = risk.split(":")[1]
                    risk_lines.append(f"🔸 Коэффициент за 30 дней: <b>{h['real_down_rate']}</b> (лимит: до <b>{lim_val}</b>)")

            block = (
                f"👤 <b>{h['nickname']}</b> | 🆔 {h['anchor_id']}\n"
                f"🎖 Уровень: <b>{h['grade']}</b>\n"
                + "\n".join(risk_lines)
            )
            if punishment:
                block += f"\n{punishment}"
            block += f"\n{SEP}"
            blocks.append(block)

        footer = "\n📌 Срочно проверьте коэффициент и начните исправлять показатели.\nЕсли не обратить внимание — аккаунт могут заблокировать ⛔"

        # Отправляем, разбивая на части при необходимости
        current = header
        part = 2
        for i, block in enumerate(blocks):
            addition = block + "\n"
            # Последний блок — добавляем футер
            is_last = (i == len(blocks) - 1)
            tail = footer if is_last else ""

            if len(current) + len(addition) + len(tail) > 4000:
                try:
                    await bot.send_message(group_chat_id, current.strip(), parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to send risk message for {agency_name}: {e}")
                current = f"⚠️ <b>Агентство: {agency_name}</b> (часть {part})\n\n" + addition
                part += 1
            else:
                current += addition

        current += footer
        try:
            await bot.send_message(group_chat_id, current.strip(), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send risk summary for {agency_name}: {e}")


def setup_scheduler(bot: Bot, db: Database, admin_ids: list) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(check_expired_trials, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_expiring_soon, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_all_agencies_for_risk, 'interval', seconds=30, args=[bot, db, admin_ids])

    return scheduler
