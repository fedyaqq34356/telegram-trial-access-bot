from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Filter

from database import Database
from config import Config
from keyboards import get_cancel_kb, get_main_menu, get_trial_period_menu, get_coefficient_menu
from state import user_modes, admin_check_mode

router = Router()

@router.message(F.text == "Тестовый период")
async def open_trial_section(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    await message.answer("Раздел: Тестовый период", reply_markup=get_trial_period_menu())

@router.message(F.text == "Коэффициент неприязни")
async def open_coefficient_section(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    await message.answer("Раздел: Коэффициент неприязни", reply_markup=get_coefficient_menu())

@router.message(F.text == "⬅️ Назад")
async def go_back_to_main(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    await message.answer("Главное меню", reply_markup=get_main_menu())

ALL_MENU_TEXTS = {
    "Пользователи", "На пробном периоде", "Проверка", "Удалить участника",
    "Skip пробный период", "Добавить администратора", "Убрать администратора",
    "Список администраторов", "История проверок", "Агентства",
    "Добавить агентство", "Редактировать агентство", "Удалить агентство",
    "Проверить ID", "Тестовый период", "Коэффициент неприязни", "Уведомления", "⬅️ Назад",
}

class HasActiveMode(Filter):
    async def __call__(self, message: Message) -> bool:
        admin_id = message.from_user.id
        if message.text in ALL_MENU_TEXTS:
            user_modes.pop(admin_id, None)
            return False
        return bool(user_modes.get(admin_id))

@router.message(F.text == "Удалить участника")
async def delete_user_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    admin_check_mode.discard(message.from_user.id)
    user_modes[message.from_user.id] = "delete_user"
    await message.answer(
        "Введите Telegram ID пользователя для удаления:",
        reply_markup=get_cancel_kb()
    )

@router.message(F.text == "Skip пробный период")
async def skip_trial_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    admin_check_mode.discard(message.from_user.id)
    user_modes[message.from_user.id] = "skip_trial"
    await message.answer(
        "Введите Telegram ID пользователя для перехода в 'Оставлен':",
        reply_markup=get_cancel_kb()
    )

@router.message(F.text == "Добавить администратора")
async def add_admin_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    admin_check_mode.discard(message.from_user.id)
    user_modes[message.from_user.id] = "add_admin"
    await message.answer(
        "Введите Telegram ID пользователя для добавления в администраторы:",
        reply_markup=get_cancel_kb()
    )

@router.message(F.text == "Убрать администратора")
async def remove_admin_prompt(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    admin_check_mode.discard(message.from_user.id)
    user_modes[message.from_user.id] = "remove_admin"
    await message.answer(
        "Введите Telegram ID администратора для удаления:",
        reply_markup=get_cancel_kb()
    )

@router.message(F.text == "Список администраторов")
async def show_admins(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    admins = db.get_all_admins()
    if not admins:
        await message.answer("Нет администраторов")
        return
    text = "Администраторы:\n\n"
    for admin_id in admins:
        text += f"ID: {admin_id}\n"
    await message.answer(text)

@router.message(F.text.regexp(r'^\d+$'), HasActiveMode())
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

@router.message(F.text.regexp(r'^-\d+$'), HasActiveMode())
async def handle_negative_input(message: Message, db: Database):
    user_id = message.from_user.id
    mode = user_modes.get(user_id)

    if mode == "set_notif_group":
        try:
            group_id = int(message.text.strip())
            db.set_setting("notifications_group_id", str(group_id))
            await message.answer(f"✅ Группа установлена: {group_id}")
        except ValueError:
            await message.answer("Неверный формат. Введите числовой ID группы.")
        user_modes[user_id] = None
