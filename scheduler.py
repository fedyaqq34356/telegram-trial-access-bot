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
    return str(host.get("BanStatus", "2")).strip() == "2"


async def _check_one_agency(agency, bot: Bot, db: Database, group_chat_id: int):
    """Проверяет одно агентство и сразу отправляет уведомление. Запускается параллельно."""
    from handlers.check_handlers import get_grade, check_risk, active_sessions
    from parser import HaloLiveParser

    agency_name = agency["name"]
    parser = active_sessions.get(agency_name)

    if parser:
        try:
            all_hosts = await asyncio.to_thread(_fetch_all_hosts, parser)
        except Exception as e:
            logger.error(f"Risk check fetch error for {agency_name}: {e}")
            active_sessions.pop(agency_name, None)
            return
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
            return
        elif result is not True:
            logger.error(f"Login failed for {agency_name} during risk check")
            return
        active_sessions[agency_name] = parser
        try:
            all_hosts = await asyncio.to_thread(_fetch_all_hosts, parser)
        except Exception as e:
            logger.error(f"Risk check fetch error for {agency_name}: {e}")
            return

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

            nickname = host.get("NickName") or host.get("AnchorName") or "—"
            at_risk.append({
                "anchor_id": anchor_id,
                "nickname": nickname,
            })
            db.mark_risk_notified(anchor_id, host.get("Agent", agency_name))

        except Exception as e:
            logger.error(f"Error processing host {host.get('DisplayAccountId')}: {e}")
            continue

    if not at_risk:
        return

    # Каждая девушка на отдельной строке
    header = (
        f"⚠️ Агентство: <b>{agency_name}</b>\n\n"
        f"Следующие аккаунты находятся в зоне риска:\n\n"
    )
    footer = (
        f"\n\nПроверьте свой коэффициент в @Toshelp_bot и примите меры для его снижения.\n\n"
        f"⛔ Возможна блокировка аккаунта при нарушении лимитов"
    )

    id_lines = "\n".join(
        f"🔸 ID: {h['anchor_id']} (Ник: {h['nickname']})"
        for h in at_risk
    )
    full_text = header + id_lines + footer

    if len(full_text) <= 4096:
        try:
            await bot.send_message(group_chat_id, full_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send risk notification for {agency_name}: {e}")
    else:
        # Разбиваем на части если очень много девушек
        current_lines = []
        current_len = len(header) + len(footer)
        part = 1

        for h in at_risk:
            line = f"🔸 ID: {h['anchor_id']} (Ник: {h['nickname']})\n"
            if current_len + len(line) > 3800:
                chunk_header = header if part == 1 else f"⚠️ Агентство: <b>{agency_name}</b> (продолжение {part})\n\n"
                try:
                    await bot.send_message(group_chat_id, (chunk_header + "".join(current_lines) + footer).strip(), parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to send risk part {part} for {agency_name}: {e}")
                part += 1
                current_lines = [line]
                current_len = len(footer) + len(line)
            else:
                current_lines.append(line)
                current_len += len(line)

        if current_lines:
            chunk_header = header if part == 1 else f"⚠️ Агентство: <b>{agency_name}</b> (продолжение {part})\n\n"
            try:
                await bot.send_message(group_chat_id, (chunk_header + "".join(current_lines) + footer).strip(), parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send final risk part for {agency_name}: {e}")


async def check_all_agencies_for_risk(bot: Bot, db: Database, admin_ids: list):
    if db.get_setting("notifications_enabled", "1") != "1":
        return

    group_chat_id_str = db.get_setting("notifications_group_id")
    if not group_chat_id_str:
        logger.warning("notifications_group_id not set, skipping risk check")
        return

    group_chat_id = int(group_chat_id_str)
    agencies = db.get_all_agencies()

    # Все агентства проверяются и отправляют сообщения ОДНОВРЕМЕННО
    await asyncio.gather(
        *[_check_one_agency(agency, bot, db, group_chat_id) for agency in agencies],
        return_exceptions=True
    )


def setup_scheduler(bot: Bot, db: Database, admin_ids: list) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(check_expired_trials, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_expiring_soon, 'interval', hours=1, args=[bot, db, admin_ids])
    scheduler.add_job(check_all_agencies_for_risk, 'interval', minutes=2, args=[bot, db, admin_ids])

    return scheduler
