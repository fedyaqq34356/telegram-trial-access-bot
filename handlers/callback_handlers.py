from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ChatMemberStatus

from database import Database
from config import Config
from state import user_modes

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
        except Exception as e:
            print(f"Ошибка при проверке рабочего чата для {user_id}: {e}")
            in_work = False
        
        try:
            study_member = await callback.bot.get_chat_member(config.study_group_id, user_id)
            in_study = study_member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
        except Exception as e:
            print(f"Ошибка при проверке обучающей группы для {user_id}: {e}")
            in_study = False
        
        db.update_presence(user_id, in_work, in_study)
        
        removed_from = []
        
        if in_work:
            try:
                await callback.bot.ban_chat_member(config.work_chat_id, user_id)
                await callback.bot.unban_chat_member(config.work_chat_id, user_id)
                removed_from.append("рабочего чата")
            except Exception as e:
                print(f"Не удалось удалить из рабочего чата: {e}")
        
        if in_study:
            try:
                await callback.bot.ban_chat_member(config.study_group_id, user_id)
                await callback.bot.unban_chat_member(config.study_group_id, user_id)
                removed_from.append("обучающей группы")
            except Exception as e:
                print(f"Не удалось удалить из обучающей группы: {e}")
        
        db.remove_user(user_id)
        
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

@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, db: Database):
    if not db.is_admin(callback.from_user.id):
        await callback.answer()
        return
    current = db.get_setting("notifications_enabled", "1")
    new_val = "0" if current == "1" else "1"
    db.set_setting("notifications_enabled", new_val)
    status = "включены ✅" if new_val == "1" else "выключены ❌"
    await callback.message.edit_text(f"Уведомления {status}.\n\nВернитесь в меню «Уведомления» чтобы изменить настройки.")
    await callback.answer()

@router.callback_query(F.data == "set_notif_group")
async def set_notif_group_prompt(callback: CallbackQuery, db: Database):
    if not db.is_admin(callback.from_user.id):
        await callback.answer()
        return
    user_modes[callback.from_user.id] = "set_notif_group"
    await callback.message.edit_text(
        "Введите ID группы куда отправлять уведомления.\n\n"
        "Чтобы узнать ID: добавьте @userinfobot в группу и перешлите ему любое сообщение.\n"
        "ID выглядит так: -1001234567890"
    )
    await callback.answer()

@router.callback_query(F.data == "notif_history")
async def notif_history(callback: CallbackQuery, db: Database):
    if not db.is_admin(callback.from_user.id):
        await callback.answer()
        return
    records = db.get_notification_history(20)
    if not records:
        await callback.message.edit_text("История уведомлений пуста.")
        await callback.answer()
        return
    text = "📋 Последние уведомления:\n\n"
    for r in records:
        cleared = "✅ риск прошёл" if r["risk_cleared"] else "⚠️ активен"
        text += f"ID: {r['anchor_id']} | {r['agency']}\n📅 {r['last_notified_at']} | {cleared}\n{'—' * 20}\n"
    await callback.message.edit_text(text[:4000])
    await callback.answer()
