"""Отправка уведомлений о новых заявках в Telegram (через Bot API напрямую).

Получатель — владелец (`owner_telegram_id` из настроек CRM, иначе config.owner_telegram_id).
Уведомления НЕ рассылаются всем админам — только владельцу.
"""
import json
import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/{method}"


def build_contact_url(telegram: str, whatsapp: str) -> str | None:
    """Ссылка для кнопки «Написать»: t.me/<username> или wa.me/<phone>."""
    tg = (telegram or "").strip()
    if tg:
        m = re.search(r"(?:t\.me/|@)?([A-Za-z0-9_]{4,})", tg)
        if m and not tg.replace("+", "").isdigit():
            return f"https://t.me/{m.group(1)}"
    wa = (whatsapp or telegram or "").strip()
    digits = re.sub(r"\D", "", wa)
    if len(digits) >= 8:
        return f"https://wa.me/{digits}"
    return None


def _keyboard(app_id: int, telegram: str, whatsapp: str) -> dict:
    write_url = build_contact_url(telegram, whatsapp)
    write_btn = (
        {"text": "✍️ Написать", "url": write_url}
        if write_url else
        {"text": "✍️ Написать", "callback_data": f"appwrite_{app_id}"}
    )
    return {"inline_keyboard": [[
        {"text": "✅ Одобрить", "callback_data": f"appapprove_{app_id}"},
        write_btn,
        {"text": "❌ Отклонить", "callback_data": f"appreject_{app_id}"},
    ]]}


def notify_new_application(
    *, token: str, owner_id: str | int, text: str, photo_paths: list[str],
    app_id: int, telegram: str, whatsapp: str,
) -> None:
    """Шлёт владельцу медиагруппу фото (подпись = text) + сообщение с кнопками действий.

    Безопасно для вызова из BackgroundTasks — все ошибки логируются, не пробрасываются.
    """
    try:
        owner = str(owner_id or "").strip()
        if not token or not owner:
            logger.warning("telegram_notify: не задан bot_token или owner_telegram_id — пропуск")
            return

        photos = [Path(p) for p in photo_paths if Path(p).exists()]
        if photos:
            media = []
            files = {}
            for i, p in enumerate(photos[:3]):
                key = f"photo{i}"
                files[key] = (p.name, p.read_bytes())
                item = {"type": "photo", "media": f"attach://{key}"}
                if i == 0:
                    item["caption"] = text
                    item["parse_mode"] = "HTML"
                media.append(item)
            r = requests.post(
                API.format(token=token, method="sendMediaGroup"),
                data={"chat_id": owner, "media": json.dumps(media)},
                files=files, timeout=30,
            )
            if not r.ok:
                logger.warning(f"sendMediaGroup failed: {r.text[:300]}")
                # запасной путь — просто текст
                requests.post(API.format(token=token, method="sendMessage"),
                              data={"chat_id": owner, "text": text, "parse_mode": "HTML"}, timeout=20)
        else:
            requests.post(API.format(token=token, method="sendMessage"),
                          data={"chat_id": owner, "text": text, "parse_mode": "HTML"}, timeout=20)

        # отдельное сообщение с кнопками (у медиагруппы клавиатуры быть не может)
        requests.post(
            API.format(token=token, method="sendMessage"),
            data={
                "chat_id": owner,
                "text": f"Действия по заявке #{app_id}:",
                "reply_markup": json.dumps(_keyboard(app_id, telegram, whatsapp)),
            }, timeout=20,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"notify_new_application failed: {e}")
