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
        # Проверяем присутствие в рабочем чате
        try:
            work_member = await callback.bot.get_chat_member(config.work_chat_id, user_id)
            in_work = work_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
        except Exception as e:
            # Пользователь не найден в чате (никогда не был или давно вышел)
            print(f"Ошибка при проверке рабочего чата для {user_id}: {e}")
            in_work = False
        
        # Проверяем присутствие в обучающей группе
        try:
            study_member = await callback.bot.get_chat_member(config.study_group_id, user_id)
            in_study = study_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
        except Exception as e:
            # Пользователь не найден в чате (никогда не был или давно вышел)
            print(f"Ошибка при проверке обучающей группы для {user_id}: {e}")
            in_study = False
        
        # Обновляем реальный статус присутствия в базе
        db.update_presence(user_id, in_work, in_study)
        
        removed_from = []
        
        # Удаляем из рабочего чата, если пользователь там есть
        if in_work:
            try:
                await callback.bot.ban_chat_member(config.work_chat_id, user_id)
                await callback.bot.unban_chat_member(config.work_chat_id, user_id)
                removed_from.append("рабочего чата")
            except Exception as e:
                print(f"Не удалось удалить из рабочего чата: {e}")
        
        # Удаляем из обучающей группы, если пользователь там есть
        if in_study:
            try:
                await callback.bot.ban_chat_member(config.study_group_id, user_id)
                await callback.bot.unban_chat_member(config.study_group_id, user_id)
                removed_from.append("обучающей группы")
            except Exception as e:
                print(f"Не удалось удалить из обучающей группы: {e}")
        
        # Удаляем из базы данных
        db.remove_user(user_id)
        
        # Формируем сообщение о результате
        if removed_from:
            status_text = f"\n\nПользователь удален из: {', '.join(removed_from)}"
        else:
            status_text = "\n\nПользователь удален из базы данных (уже не был в чатах)"
        
        await callback.message.edit_text(
            f"{callback.message.text}{status_text}"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"{callback.message.text}\n\nОшибка: {str(e)}"
        )
    
    await callback.answer()
