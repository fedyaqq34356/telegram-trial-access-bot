from aiogram import Router
from aiogram.types import ChatMemberUpdated, ChatJoinRequest
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER, LEFT

from database import Database
from config import Config
from utils import format_username

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

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_joined(event: ChatMemberUpdated, db: Database, config: Config):
    user = event.new_chat_member.user
    chat_id = event.chat.id
    
    if not db.get_user(user.id):
        db.add_user(
            telegram_id=user.id,
            name=user.full_name,
            username=user.username,
            trial_minutes=config.trial_minutes
        )

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
        
        admins = db.get_all_admins()
        text = (f"Пользователь вышел из {left_from}\n\n"
                f"{user_data['name']}\n"
                f"ID: {user_data['telegram_id']}\n"
                f"{format_username(user_data['username'])}")
        
        for admin_id in admins:
            try:
                await event.bot.send_message(admin_id, text)
            except:
                continue
        
        if chat_id == config.study_group_id:
            try:
                await event.bot.ban_chat_member(config.work_chat_id, user_id)
                await event.bot.unban_chat_member(config.work_chat_id, user_id)
            except:
                pass
            try:
                await event.bot.ban_chat_member(config.study_group_id, user_id)
                await event.bot.unban_chat_member(config.study_group_id, user_id)
            except:
                pass
            db.remove_user(user_id)