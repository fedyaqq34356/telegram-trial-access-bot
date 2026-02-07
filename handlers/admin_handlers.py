from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus

from database import Database
from config import Config

router = Router()

user_modes = {}

@router.message(F.text == "Удалить участника")
async def delete_user_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    user_modes[message.from_user.id] = "delete_user"
    await message.answer("Введите Telegram ID пользователя для удаления:")

@router.message(F.text == "Skip пробный период")
async def skip_trial_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    user_modes[message.from_user.id] = "skip_trial"
    await message.answer("Введите Telegram ID пользователя для перехода в 'Оставлен':")

@router.message(F.text == "Добавить администратора")
async def add_admin_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    user_modes[message.from_user.id] = "add_admin"
    await message.answer("Введите Telegram ID пользователя для добавления в администраторы:")

@router.message(F.text == "Убрать администратора")
async def remove_admin_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    user_modes[message.from_user.id] = "remove_admin"
    await message.answer("Введите Telegram ID администратора для удаления:")

@router.message(F.text == "Список администраторов")
async def show_admins(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return
    
    admins = db.get_all_admins()
    
    if not admins:
        await message.answer("Нет администраторов")
        return
    
    text = "Администраторы:\n\n"
    for admin_id in admins:
        text += f"ID: {admin_id}\n"
    
    await message.answer(text)

@router.message(F.text.regexp(r'^\d+$'))
async def handle_user_input(message: Message, db: Database, config: Config):
    user_id = message.from_user.id
    mode = user_modes.get(user_id)
    
    if not mode:
        return
    
    target_id = int(message.text)
    
    if mode == "delete_user":
        user = db.get_user(target_id)
        
        if not user:
            await message.answer("Пользователь не найден")
        else:
            try:
                try:
                    work_member = await message.bot.get_chat_member(config.work_chat_id, target_id)
                    in_work = work_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
                except:
                    in_work = False
                
                try:
                    study_member = await message.bot.get_chat_member(config.study_group_id, target_id)
                    in_study = study_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
                except:
                    in_study = False
                
                if in_work:
                    try:
                        await message.bot.ban_chat_member(config.work_chat_id, target_id)
                        await message.bot.unban_chat_member(config.work_chat_id, target_id)
                    except:
                        pass
                
                if in_study:
                    try:
                        await message.bot.ban_chat_member(config.study_group_id, target_id)
                        await message.bot.unban_chat_member(config.study_group_id, target_id)
                    except:
                        pass
                
                db.remove_user(target_id)
                await message.answer(f"Пользователь {user['name']} удален")
            except Exception as e:
                await message.answer(f"Ошибка: {str(e)}")
    
    elif mode == "skip_trial":
        user = db.get_user(target_id)
        
        if not user:
            await message.answer("Пользователь не найден")
        else:
            db.update_status(target_id, "approved")
            await message.answer(f"Пользователь {user['name']} переведен в 'Оставлен'")
    
    elif mode == "add_admin":
        db.add_admin(target_id)
        await message.answer(f"Пользователь с ID {target_id} теперь администратор")
    
    elif mode == "remove_admin":
        db.remove_admin(target_id)
        await message.answer(f"Пользователь с ID {target_id} больше не администратор")
    
    user_modes[user_id] = None
