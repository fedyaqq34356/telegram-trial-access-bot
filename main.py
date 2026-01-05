import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command

from config import Config
from database import Database
from handlers import router
from scheduler import setup_scheduler
from keyboards import get_main_menu

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def start_command(message, db: Database):
    user_id = message.from_user.id
    
    if db.is_admin(user_id):
        await message.answer(
            "Админ-панель бота управления участниками",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            f"Ваш ID: `{user_id}`",
            parse_mode="Markdown"
        )

async def main():
    config = Config.from_env()
    db = Database()
    
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    
    dp.message.register(start_command, Command("start"))
    dp.include_router(router)
    
    dp['db'] = db
    dp['config'] = config
    
    admin_ids = db.get_all_admins()
    if not admin_ids:
        logging.warning("Нет администраторов в базе данных")
        logging.warning("Добавьте администратора вручную в таблицу admins")
    else:
        logging.info(f"Загружено {len(admin_ids)} администратор(ов)")
    
    scheduler = setup_scheduler(bot, db, admin_ids)
    scheduler.start()
    logging.info("Планировщик запущен")
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"Бот запущен и готов к работе\n\n"
                f"Пробный период: 8 дней"
            )
        except:
            pass
    
    logging.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")