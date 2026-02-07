from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ChatMemberStatus

from database import Database
from config import Config

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, db: Database):
    user_id = int(callback.data.split("_")[1])
    db.update_status(user_id, "approved")
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\nПользователь оставлен"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("kick_"))
async def kick_user(callback: CallbackQuery, db: Database, config: Config):
    user_id = int(callback.data.split("_")[1])
    
    try:
        try:
            work_member = await callback.bot.get_chat_member(config.work_chat_id, user_id)
            in_work = work_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
        except:
            in_work = False
        
        try:
            study_member = await callback.bot.get_chat_member(config.study_group_id, user_id)
            in_study = study_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
        except:
            in_study = False
        
        if in_work:
            try:
                await callback.bot.ban_chat_member(config.work_chat_id, user_id)
                await callback.bot.unban_chat_member(config.work_chat_id, user_id)
            except:
                pass
        
        if in_study:
            try:
                await callback.bot.ban_chat_member(config.study_group_id, user_id)
                await callback.bot.unban_chat_member(config.study_group_id, user_id)
            except:
                pass
        
        db.remove_user(user_id)
        
        await callback.message.edit_text(
            f"{callback.message.text}\n\nПользователь удален"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"{callback.message.text}\n\nОшибка: {str(e)}"
        )
    
    await callback.answer()
