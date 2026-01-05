from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database import Database
from keyboards import get_trial_decision
from utils import format_user_info

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

def setup_scheduler(bot: Bot, db: Database, admin_ids: list) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        check_expired_trials,
        'interval',
        hours=1,
        args=[bot, db, admin_ids]
    )
    
    scheduler.add_job(
        check_expiring_soon,
        'interval',
        hours=1,
        args=[bot, db, admin_ids]
    )
    
    return scheduler