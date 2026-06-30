"""Обработка кнопок заявок с сайта (Одобрить / Написать / Отклонить).

Кнопки приходят под уведомлением о новой заявке (его шлёт CRM-backend).
callback_data: appapprove_{id} | appreject_{id} | appwrite_{id}
Статус меняется через internal-API CRM (PATCH /internal/applications/{id}/status, X-Internal-Token).
"""
import asyncio
import logging
import re

import requests
from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import Config

logger = logging.getLogger(__name__)
router = Router()

def _set_status(config: Config, app_id: int, status: str) -> dict | None:
    try:
        r = requests.patch(
            f"{config.crm_api_base}/internal/applications/{app_id}/status",
            json={"status": status, "actor": "бот"},
            headers={"X-Internal-Token": config.internal_api_token},
            timeout=15,
        )
        if r.ok:
            return r.json()
        logger.warning(f"set_status {app_id}->{status} failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        logger.error(f"set_status error: {e}")
    return None

def _get_application(config: Config, app_id: int) -> dict | None:
    try:
        r = requests.get(
            f"{config.crm_api_base}/internal/applications/{app_id}",
            headers={"X-Internal-Token": config.internal_api_token},
            timeout=15,
        )
        if r.ok:
            return r.json()
    except Exception as e:
        logger.error(f"get_application error: {e}")
    return None

def _contact_link(telegram: str, whatsapp: str) -> tuple[str | None, str]:
    """Возвращает (ссылка, отображение) для связи с девушкой."""
    tg = (telegram or "").strip()
    if tg and not tg.replace("+", "").isdigit():
        m = re.search(r"(?:t\.me/|@)?([A-Za-z0-9_]{4,})", tg)
        if m:
            return f"https://t.me/{m.group(1)}", f"Telegram: @{m.group(1)}"
    wa = (whatsapp or telegram or "").strip()
    digits = re.sub(r"\D", "", wa)
    if len(digits) >= 8:
        return f"https://wa.me/{digits}", f"WhatsApp: +{digits}"
    return None, (tg or wa or "контакт не указан")

@router.callback_query(F.data.startswith("appapprove_"))
async def app_approve(callback: CallbackQuery, config: Config):
    app_id = int(callback.data.split("_")[1])
    res = await asyncio.to_thread(_set_status, config, app_id, "approved")
    if res:
        await callback.message.edit_text(f"{callback.message.text}\n\n✅ Заявка #{app_id} одобрена")
        await callback.answer("Одобрено")
    else:
        await callback.answer("Не удалось обновить статус (CRM недоступна)", show_alert=True)

@router.callback_query(F.data.startswith("appreject_"))
async def app_reject(callback: CallbackQuery, config: Config):
    app_id = int(callback.data.split("_")[1])
    res = await asyncio.to_thread(_set_status, config, app_id, "rejected")
    if res:
        await callback.message.edit_text(f"{callback.message.text}\n\n❌ Заявка #{app_id} отклонена")
        await callback.answer("Отклонено")
    else:
        await callback.answer("Не удалось обновить статус (CRM недоступна)", show_alert=True)

@router.callback_query(F.data.startswith("appwrite_"))
async def app_write(callback: CallbackQuery, config: Config):
    """Запасной путь (если в кнопке не было прямой ссылки): показываем контакт девушки."""
    app_id = int(callback.data.split("_")[1])
    data = await asyncio.to_thread(_get_application, config, app_id)
    if not data:
        await callback.answer("Не удалось получить контакт", show_alert=True)
        return
    link, display = _contact_link(data.get("contact_telegram", ""), data.get("contact_whatsapp", ""))
    text = f"Связь по заявке #{app_id}\n{display}"
    if link:
        text += f"\n{link}"
    await callback.message.answer(text)
    await callback.answer()
