from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ChatMemberStatus

from database import Database
from config import Config
from utils import format_user_info, format_username, format_user_list_item

router = Router()

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
        users_text.encode('utf-8'),
        filename='users.txt'
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
    
    text = "На пробном периоде:\n\n"
    for user in users:
        text += f"{format_user_info(user, show_time=True)}\n\n"
    
    await message.answer(text)

@router.message(F.text == "Проверка")
async def check_presence(message: Message, db: Database, config: Config):
    from keyboards import get_trial_decision
    
    users = db.get_all_users()
    found_issues = False
    
    for user in users:
        try:
            work_member = await message.bot.get_chat_member(config.work_chat_id, user['telegram_id'])
            study_member = await message.bot.get_chat_member(config.study_group_id, user['telegram_id'])
            
            in_work = work_member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            in_study = study_member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            
            db.update_presence(user['telegram_id'], in_work, in_study)
            
            if in_study and not in_work:
                try:
                    await message.bot.ban_chat_member(config.study_group_id, user['telegram_id'])
                    await message.bot.unban_chat_member(config.study_group_id, user['telegram_id'])
                    
                    text = (f"Пользователь удален из обучающей группы (нет в рабочем чате)\n\n"
                            f"{user['name']}\n"
                            f"ID: {user['telegram_id']}\n"
                            f"{format_username(user['username'])}")
                    
                    await message.answer(text)
                    db.remove_user(user['telegram_id'])
                    found_issues = True
                except:
                    continue
            elif not in_work or not in_study:
                left_from = []
                if not in_work:
                    left_from.append("рабочего чата")
                if not in_study:
                    left_from.append("обучающей группы")
                
                text = (f"Пользователь вышел из: {', '.join(left_from)}\n\n"
                        f"{user['name']}\n"
                        f"ID: {user['telegram_id']}\n"
                        f"{format_username(user['username'])}")
                
                keyboard = get_trial_decision(user['telegram_id'])
                await message.answer(text, reply_markup=keyboard)
                found_issues = True
        except:
            continue
    
    if not found_issues:
        await message.answer("Проверка завершена. Все пользователи на месте.")
    else:
        await message.answer("Проверка завершена")