from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Пользователи")],
        [KeyboardButton(text="На пробном периоде")],
        [KeyboardButton(text="Проверка")],
        [KeyboardButton(text="Удалить участника")],
        [KeyboardButton(text="Добавить администратора")],
        [KeyboardButton(text="Убрать администратора")],
        [KeyboardButton(text="Список администраторов")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_trial_decision(telegram_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Оставить", callback_data=f"approve_{telegram_id}"),
            InlineKeyboardButton(text="Кикнуть", callback_data=f"kick_{telegram_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)