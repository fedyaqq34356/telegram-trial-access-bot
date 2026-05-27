import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Filter

from database import Database
from keyboards import get_cancel_kb
from state import user_modes, admin_check_mode, pending_tfa

router = Router()
logger = logging.getLogger(__name__)

# admin_id -> {"step": str, "data": dict}
agency_setup: dict = {}

DEFAULT_URL = "https://admin.livegirl.me"

STEPS = ["name", "account", "password", "aemail", "apassword"]
STEP_PROMPTS = {
    "name":     "Введите название агентства (например: TosAgency):",
    "account":  "Введите логин 1-го шага (account):",
    "password": "Введите пароль 1-го шага (password):",
    "aemail":   "Введите логин 2-го шага (aemail — название агентства в панели):",
    "apassword": "Введите пароль 2-го шага (apassword):",
}

MENU_TEXTS = {
    "Пользователи", "На пробном периоде", "Проверка", "Удалить участника",
    "Skip пробный период", "Добавить администратора", "Убрать администратора",
    "Список администраторов", "История проверок", "Агентства",
    "Добавить агентство", "Редактировать агентство", "Удалить агентство",
    "Проверить ID",
}

EDIT_FIELDS = {
    "name":        "Название",
    "account":     "Логин (account)",
    "password":    "Пароль 1",
    "aemail":      "Email/логин 2 (aemail)",
    "apassword":   "Пароль 2",
    "tfa_required": "2FA",
}


class InAgencySetup(Filter):
    """Matches only when this admin has an active agency setup session."""
    async def __call__(self, message: Message) -> bool:
        admin_id = message.from_user.id
        # 2FA ожидает код — не перехватывать сообщение
        if admin_id in pending_tfa:
            return False
        if message.text in MENU_TEXTS:
            agency_setup.pop(admin_id, None)
            user_modes.pop(admin_id, None)
            admin_check_mode.discard(admin_id)
            return False
        return admin_id in agency_setup


@router.message(F.text == "Добавить агентство")
async def add_agency_start(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    agency_setup[message.from_user.id] = {"step": "name", "data": {}}
    await message.answer(
        "Добавление нового агентства.\n\n" + STEP_PROMPTS["name"],
        reply_markup=get_cancel_kb()
    )


@router.message(F.text == "Редактировать агентство")
async def edit_agency_start(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    agencies = db.get_all_agencies()
    if not agencies:
        await message.answer("Нет подключённых агентств.")
        return
    text = "Введите номер (ID) агентства для редактирования:\n\n"
    for ag in agencies:
        tfa = "2FA ✅" if ag["tfa_required"] else "2FA ❌"
        text += f"{ag['id']}. {ag['name']} — {tfa}\n"
    agency_setup[message.from_user.id] = {"step": "edit_id", "data": {}}
    await message.answer(text, reply_markup=get_cancel_kb())


@router.message(F.text == "Удалить агентство")
async def delete_agency_start(message: Message, db: Database):
    if not db.is_admin(message.from_user.id):
        return
    user_modes.pop(message.from_user.id, None)
    admin_check_mode.discard(message.from_user.id)
    agencies = db.get_all_agencies()
    if not agencies:
        await message.answer("Нет подключённых агентств.")
        return
    text = "Введите номер (ID) агентства для удаления:\n\n"
    for ag in agencies:
        tfa = "2FA ✅" if ag["tfa_required"] else "2FA ❌"
        text += f"{ag['id']}. {ag['name']} — {tfa}\n"
    agency_setup[message.from_user.id] = {"step": "delete", "data": {}}
    await message.answer(text, reply_markup=get_cancel_kb())



@router.message(InAgencySetup())
async def agency_setup_handler(message: Message, db: Database):
    admin_id = message.from_user.id
    if not db.is_admin(admin_id):
        return

    state = agency_setup.get(admin_id)
    if not state:
        return

    step = state["step"]
    text = (message.text or "").strip()

    if step == "delete":
        if not text.isdigit():
            await message.answer("Введите числовой ID из списка агентств.")
            return
        agency = db.get_agency(int(text))
        if not agency:
            await message.answer("Агентство с таким ID не найдено. Попробуйте ещё раз.")
            return
        db.remove_agency(agency["id"])
        del agency_setup[admin_id]
        await message.answer(f"✅ Агентство «{agency['name']}» удалено.")
        return

    if step == "edit_id":
        if not text.isdigit():
            await message.answer("Введите числовой ID из списка агентств.")
            return
        agency = db.get_agency(int(text))
        if not agency:
            await message.answer("Агентство с таким ID не найдено. Попробуйте ещё раз.")
            return
        state["data"]["agency_id"] = agency["id"]
        state["data"]["agency_name"] = agency["name"]
        state["step"] = "edit_field"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Название", callback_data="ag_ef_name")],
            [
                InlineKeyboardButton(text="Логин (account)", callback_data="ag_ef_account"),
                InlineKeyboardButton(text="Пароль 1", callback_data="ag_ef_password"),
            ],
            [
                InlineKeyboardButton(text="Email (aemail)", callback_data="ag_ef_aemail"),
                InlineKeyboardButton(text="Пароль 2", callback_data="ag_ef_apassword"),
            ],
            [InlineKeyboardButton(text="2FA (вкл/выкл)", callback_data="ag_ef_tfa")],
        ])
        await message.answer(
            f"Агентство: {agency['name']}\n\nКакое поле редактировать?",
            reply_markup=kb
        )
        return

    if step == "edit_field":
        await message.answer("Выберите поле из кнопок выше.")
        return

    if step == "edit_tfa":
        await message.answer("Нажмите кнопку «Да» или «Нет».")
        return

    if step == "edit_value":
        field = state["data"]["edit_field"]
        agency_id = state["data"]["agency_id"]
        agency_name = state["data"]["agency_name"]
        db.update_agency(agency_id, field, text)
        del agency_setup[admin_id]
        label = EDIT_FIELDS.get(field, field)
        await message.answer(f"✅ Агентство «{agency_name}»: поле «{label}» обновлено.")
        return

    # Collect field value
    state["data"][step] = text

    idx = STEPS.index(step)
    if idx + 1 < len(STEPS):
        next_step = STEPS[idx + 1]
        state["step"] = next_step
        await message.answer(STEP_PROMPTS[next_step], reply_markup=get_cancel_kb())
    else:
        # All fields collected — ask about 2FA
        state["step"] = "tfa"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Да", callback_data="ag_tfa_yes"),
            InlineKeyboardButton(text="Нет", callback_data="ag_tfa_no"),
        ]])
        await message.answer("Требуется 2FA (Google Authenticator)?", reply_markup=kb)


_EDIT_FIELD_MAP = {
    "ag_ef_name":      "name",
    "ag_ef_account":   "account",
    "ag_ef_password":  "password",
    "ag_ef_aemail":    "aemail",
    "ag_ef_apassword": "apassword",
}


@router.callback_query(F.data.in_(set(_EDIT_FIELD_MAP.keys())))
async def agency_edit_field_callback(callback: CallbackQuery, db: Database):
    admin_id = callback.from_user.id
    if not db.is_admin(admin_id):
        await callback.answer()
        return

    state = agency_setup.get(admin_id)
    if not state or state.get("step") != "edit_field":
        await callback.answer("Сессия устарела. Начните заново.")
        return

    field = _EDIT_FIELD_MAP[callback.data]
    state["data"]["edit_field"] = field
    state["step"] = "edit_value"
    label = EDIT_FIELDS[field]
    await callback.message.edit_text(f"Введите новое значение для «{label}»:")
    await callback.answer()


@router.callback_query(F.data == "ag_ef_tfa")
async def agency_edit_tfa_field_callback(callback: CallbackQuery, db: Database):
    admin_id = callback.from_user.id
    if not db.is_admin(admin_id):
        await callback.answer()
        return

    state = agency_setup.get(admin_id)
    if not state or state.get("step") != "edit_field":
        await callback.answer("Сессия устарела. Начните заново.")
        return

    state["step"] = "edit_tfa"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Да", callback_data="ag_edit_tfa_yes"),
        InlineKeyboardButton(text="Нет", callback_data="ag_edit_tfa_no"),
    ]])
    await callback.message.edit_text("2FA требуется?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.in_({"ag_edit_tfa_yes", "ag_edit_tfa_no"}))
async def agency_edit_tfa_value_callback(callback: CallbackQuery, db: Database):
    admin_id = callback.from_user.id
    if not db.is_admin(admin_id):
        await callback.answer()
        return

    state = agency_setup.get(admin_id)
    if not state or state.get("step") != "edit_tfa":
        await callback.answer("Сессия устарела. Начните заново.")
        return

    tfa_required = callback.data == "ag_edit_tfa_yes"
    agency_id = state["data"]["agency_id"]
    agency_name = state["data"]["agency_name"]
    db.update_agency(agency_id, "tfa_required", int(tfa_required))
    del agency_setup[admin_id]
    tfa_str = "включена ✅" if tfa_required else "не требуется ❌"
    await callback.message.edit_text(f"✅ Агентство «{agency_name}»: 2FA {tfa_str}.")
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def cancel_callback(callback: CallbackQuery):
    admin_id = callback.from_user.id
    agency_setup.pop(admin_id, None)
    user_modes.pop(admin_id, None)
    admin_check_mode.discard(admin_id)
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.callback_query(F.data.in_({"ag_tfa_yes", "ag_tfa_no"}))
async def agency_tfa_callback(callback: CallbackQuery, db: Database):
    admin_id = callback.from_user.id
    if not db.is_admin(admin_id):
        await callback.answer()
        return

    state = agency_setup.get(admin_id)
    if not state or state.get("step") != "tfa":
        await callback.answer("Сессия устарела. Начните заново.")
        return

    tfa_required = callback.data == "ag_tfa_yes"
    data = state["data"]

    db.add_agency(
        name=data["name"],
        url=DEFAULT_URL,
        account=data["account"],
        password=data["password"],
        aemail=data["aemail"],
        apassword=data["apassword"],
        tfa_required=tfa_required,
    )

    del agency_setup[admin_id]

    tfa_str = "включена ✅" if tfa_required else "не требуется ❌"
    await callback.message.edit_text(
        f"✅ Агентство «{data['name']}» добавлено.\n"
        f"2FA: {tfa_str}"
    )
    await callback.answer()
