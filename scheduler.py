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
            except:
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
            except:
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

BLOCKED_STATUSES = {
    "banned", "blocked", "disabled", "frozen",
    "ban", "block", "disable", "freeze",
    "заблокирован", "бан",
}

def _is_account_active(host: dict) -> bool:
    status = host.get("AccountStatus", "")
    if status is None:
        return True
    status_str = str(status).strip().lower()
    if not status_str or status_str in ("", "0", "normal", "active", "ok", "enabled"):
        return True
    if status_str in BLOCKED_STATUSES:
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

        for host in all_hosts:
            try:
                anchor_id = str(host.get("DisplayAccountId", ""))

                if not _is_account_active(host):
                    logger.debug(f"Skipping blocked account {anchor_id} (AccountStatus={host.get('AccountStatus')})")
                    db.clear_risk(anchor_id)
                    continue

                grade = get_grade(host["MonthlyIncome"])
                risks = check_risk(grade, host["DownRate"], host["RealDownRate"])

                if not risks:
                    db.clear_risk(anchor_id)
                    continue

                if not db.should_notify(anchor_id):
                    continue

                msg = (
                    f"⚠️ Внимание! Аккаунт в зоне риска\n\n"
                    f"ID: {anchor_id}\n"
                    f"Nickname: {host.get('AnchorName', '—')}\n"
                    f"Агентство: {host.get('Agent', agency_name)}\n\n"
                    f"Причина:\n" + "\n".join(risks) + "\n\n"
                    f"Срочно проверь свой коэффициент в боте и начни исправлять показатели.\n\n"
                    f"Если не обратить внимание на ситуацию, аккаунт могут заблокировать ⛔"
                )

                await bot.send_message(group_chat_id, msg)
                db.mark_risk_notified(anchor_id, host.get("Agent", agency_name))

            except Exception as e:
                logger.error(f"Error processing host {host.get('DisplayAccountId')}: {e}")
                continue


def setup_scheduler(bot: Bot, db: Database, admin_ids: list) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(check_expired_trials, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_expiring_soon, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_all_agencies_for_risk, 'interval', hours=6, args=[bot, db, admin_ids])

    return scheduler
