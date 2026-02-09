from aiogram import Router
from aiogram.types import ChatMemberUpdated, ChatJoinRequest
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER, LEFT

from database import Database
from config import Config
from utils import format_username
from keyboards import get_trial_decision

router = Router()

@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest, db: Database, config: Config):
    user = event.from_user
    chat_id = event.chat.id
    
    await event.approve()
    
    if chat_id == config.work_chat_id:
        if not db.get_user(user.id):
            db.add_user(
                telegram_id=user.id,
                name=user.full_name,
                username=user.username,
                trial_minutes=config.trial_minutes
            )
            # ВАЖНО: При добавлении пользователь только в рабочем чате, не в обучающей группе
            db.update_presence(user.id, in_work=True, in_study=False)

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_joined(event: ChatMemberUpdated, db: Database, config: Config):
    user = event.new_chat_member.user
    chat_id = event.chat.id
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        # Создаем нового пользователя
        db.add_user(
            telegram_id=user.id,
            name=user.full_name,
            username=user.username,
            trial_minutes=config.trial_minutes
        )
        # Устанавливаем флаг присутствия только для того чата, в который вступил
        if chat_id == config.work_chat_id:
            db.update_presence(user.id, in_work=True, in_study=False)
        elif chat_id == config.study_group_id:
            db.update_presence(user.id, in_work=False, in_study=True)
    else:
        # Обновляем флаг присутствия для существующего пользователя
        if chat_id == config.work_chat_id:
            db.update_presence(user.id, in_work=True, in_study=user_data['in_study_group'])
        elif chat_id == config.study_group_id:
            db.update_presence(user.id, in_work=user_data['in_work_chat'], in_study=True)

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED | LEFT))
async def user_left(event: ChatMemberUpdated, db: Database, config: Config):
    user_id = event.from_user.id
    user_data = db.get_user(user_id)
    
    if user_data:
        chat_id = event.chat.id
        
        if chat_id == config.work_chat_id:
            db.update_presence(user_id, False, user_data['in_study_group'])
            left_from = "рабочего чата"
        elif chat_id == config.study_group_id:
            db.update_presence(user_id, user_data['in_work_chat'], False)
            left_from = "обучающей группы"
        else:
            return
        
        # Отправляем уведомление администраторам с кнопками действий
        admins = db.get_all_admins()
        text = (f"Пользователь вышел из {left_from}\n\n"
                f"{user_data['name']}\n"
                f"ID: {user_data['telegram_id']}\n"
                f"{format_username(user_data['username'])}")
        
        keyboard = get_trial_decision(user_data['telegram_id'])
        
        for admin_id in admins:
            try:
                await event.bot.send_message(admin_id, text, reply_markup=keyboard)
            except:
                continue
        
        # ВАЖНОЕ ПРАВИЛО: Если пользователь покинул обучающую группу, 
        # удаляем его из рабочего чата и из базы данных
        if chat_id == config.study_group_id:
            try:
                # Удаляем из рабочего чата
                await event.bot.ban_chat_member(config.work_chat_id, user_id)
                await event.bot.unban_chat_member(config.work_chat_id, user_id)
            except Exception as e:
                print(f"Ошибка при удалении из рабочего чата: {e}")
            
            # Удаляем из базы данных
            db.remove_user(user_id)
