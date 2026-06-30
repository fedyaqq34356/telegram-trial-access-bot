from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

from database import Database
from config import Config
from utils import format_user_info, format_username, format_user_list_item

router = Router()

MAX_MESSAGE_LENGTH = 4000

@router.message(F.text == "Пользователи")
async def show_users(message: Message, db: Database):
    users = db.get_all_users()
    
    if not users:
        await message.answer("Нет пользователей")
        return
    
    users_text = ""
    for user in users:
        users_text += f"{format_user_list_item(user)}\n"
        users_text += "-" * 50 + "\n"
    
    file = BufferedInputFile(
        users_text.encode("utf-8"),
        filename="users.txt"
    )
    
    await message.answer_document(
        document=file,
        caption="Все пользователи"
    )

@router.message(F.text == "На пробном периоде")
async def show_trial_users(message: Message, db: Database):
    users = db.get_trial_users()
    
    if not users:
        await message.answer("Нет пользователей на пробном периоде")
        return
    
    user_texts = [format_user_info(user, show_time=True) for user in users]
    
    current_message = "На пробном периоде:\n\n"
    message_count = 1
    
    for user_text in user_texts:
        test_message = current_message + user_text + "\n\n"
        
        if len(test_message) > MAX_MESSAGE_LENGTH:
            await message.answer(current_message.strip())
            message_count += 1
            current_message = f"На пробном периоде (часть {message_count}):\n\n{user_text}\n\n"
        else:
            current_message = test_message
    
    if current_message.strip():
        await message.answer(current_message.strip())

@router.message(F.text == "Проверка")
async def check_presence(message: Message, db: Database, config: Config):
    from keyboards import get_trial_decision
    
    users = db.get_all_users()
    found_issues = False
    
    await message.answer("Начинаю проверку...")
    
    for user in users:
        try:
            work_member = await message.bot.get_chat_member(
                config.work_chat_id, user["telegram_id"]
            )
            in_work = work_member.status not in (
                ChatMemberStatus.LEFT,
                ChatMemberStatus.KICKED,
            )
        except Exception as e:
            print(f"Ошибка при проверке пользователя {user['telegram_id']} в рабочем чате: {e}")
            in_work = False
        
        try:
            study_member = await message.bot.get_chat_member(
                config.study_group_id, user["telegram_id"]
            )
            in_study = study_member.status not in (
                ChatMemberStatus.LEFT,
                ChatMemberStatus.KICKED,
            )
        except Exception as e:
            print(f"Ошибка при проверке пользователя {user['telegram_id']} в обучающей группе: {e}")
            in_study = False
        
        db.update_presence(user["telegram_id"], in_work, in_study)
        
        if in_study and not in_work:
            try:
                await message.bot.ban_chat_member(
                    config.study_group_id, user["telegram_id"]
                )
                await message.bot.unban_chat_member(
                    config.study_group_id, user["telegram_id"]
                )
                
                text = (
                    "Пользователь удален из обучающей группы (нет в рабочем чате)\n\n"
                    f"{user['name']}\n"
                    f"ID: {user['telegram_id']}\n"
                    f"{format_username(user['username'])}"
                )
                
                await message.answer(text)
                db.remove_user(user["telegram_id"])
                found_issues = True
            except Exception as e:
                await message.answer(
                    f"Ошибка при удалении {user['telegram_id']}: {e}"
                )
        
        elif not in_work or not in_study:
            left_from = []
            if not in_work:
                left_from.append("рабочего чата")
            if not in_study:
                left_from.append("обучающей группы")
            
            text = (
                f"Пользователь вышел из: {', '.join(left_from)}\n\n"
                f"{user['name']}\n"
                f"ID: {user['telegram_id']}\n"
                f"{format_username(user['username'])}"
            )
            
            keyboard = get_trial_decision(user["telegram_id"])
            await message.answer(text, reply_markup=keyboard)
            found_issues = True
    
    if not found_issues:
        await message.answer("Проверка завершена. Все пользователи на месте.")
    else:
        await message.answer("Проверка завершена")

@router.message(F.text == "История проверок")
async def show_check_history(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    records = db.get_history(limit=20)
    if not records:
        await message.answer("История проверок пуста.")
        return
    text = "📋 Последние 20 проверок:\n\n"
    for r in records:
        username_str = f"@{r['username']}" if r['username'] else "без username"
        found_str = f"🏢 {r['agency']} | Уровень: {r['grade']}" if r['found'] else "❌ Не найден"
        status_str = "⚠️ Риск" if r['has_risk'] else "✅ Норма"
        text += f"👤 {username_str} (TG ID: {r['tg_id']}) | Halo ID: {r['anchor_id']}\n"
        text += f"📅 {r['created_at']}\n"
        text += f"{found_str}\n"
        if r['found']:
            text += f"📊 Профиль: {r['down_rate']} | 30 дней: {r['real_down_rate']}\n"
            text += f"💰 Заработок: {r['monthly_income']} coins\n"
            text += f"{status_str}\n"
        text += "—" * 20 + "\n"
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)

@router.message(F.text == "Уведомления")
async def notifications_menu(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return

    enabled = db.get_setting("notifications_enabled", "1") == "1"
    group_id = db.get_setting("notifications_group_id", "не установлен")
    status_str = "✅ Включены" if enabled else "❌ Выключены"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Выключить" if enabled else "✅ Включить",
            callback_data="toggle_notifications"
        )],
        [InlineKeyboardButton(text="Установить группу", callback_data="set_notif_group")],
        [InlineKeyboardButton(text="История уведомлений", callback_data="notif_history")],
    ])

    await message.answer(
        f"🔔 Уведомления в группу\n\n"
        f"Статус: {status_str}\n"
        f"Группа: {group_id}\n\n"
        f"Бот проверяет коэффициенты каждые 6 часов и отправляет предупреждение "
        f"девушкам в группу если обнаружен риск. Повторное уведомление по одному "
        f"аккаунту — не чаще раза в 24 часа.",
        reply_markup=kb
    )

@router.message(F.text == "Агентства")
async def show_agencies(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    agencies = db.get_all_agencies()
    if not agencies:
        await message.answer("Нет подключённых агентств.\n\nНажмите «Добавить агентство» чтобы добавить первое.")
        return
    text = f"🏢 Подключённых агентств: {len(agencies)}\n\n"
    for ag in agencies:
        tfa_str = "✅ Есть" if ag["tfa_required"] else "❌ Нет"
        text += f"ID {ag['id']}. {ag['name']}\n   URL: {ag['url']}\n   2FA: {tfa_str}\n\n"
    text += "Чтобы удалить — нажмите «Удалить агентство»."
    await message.answer(text)
