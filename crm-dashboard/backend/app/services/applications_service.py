"""Общие помощники для заявок: статусы, сериализация, текст уведомления."""
import json

from ..models import Application, ApplicationStatusEvent

STATUS_LABELS = {
    "new": "Новая",
    "in_progress": "В работе",
    "contacted": "Связались",
    "approved": "Одобрена",
    "rejected": "Отклонена",
    "registered": "Зарегистрирована",
    "office_activated": "Активирована офисом",
    "training": "На обучении",
    "working": "Начала работу",
}

def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)

def photos(app: Application) -> list[str]:
    try:
        v = json.loads(app.photos_json or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []

def contact_display(app: Application) -> str:
    parts = []
    if app.contact_telegram:
        parts.append(app.contact_telegram)
    if app.contact_whatsapp:
        parts.append(app.contact_whatsapp)
    return " / ".join(parts) or "—"

def serialize_event(ev: ApplicationStatusEvent) -> dict:
    return {
        "id": ev.id,
        "old_status": ev.old_status,
        "old_status_label": status_label(ev.old_status) if ev.old_status else "",
        "new_status": ev.new_status,
        "new_status_label": status_label(ev.new_status),
        "actor": ev.actor,
        "note": ev.note,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }

def serialize_application(app: Application, with_events: bool = False) -> dict:
    data = {
        "id": app.id,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "age": app.age,
        "country": app.country,
        "contact_telegram": app.contact_telegram,
        "contact_whatsapp": app.contact_whatsapp,
        "contact_display": contact_display(app),
        "email": app.email,
        "experience": app.experience,
        "experience_apps": app.experience_apps,
        "time_commitment": app.time_commitment,
        "photos_count": len(photos(app)),
        "status": app.status,
        "status_label": status_label(app.status),
        "manager_comment": app.manager_comment,
        "source": app.source,
    }
    if with_events:
        data["events"] = [serialize_event(e) for e in app.events]
    return data

def build_notification_text(app: Application) -> str:
    """Формат уведомления о новой заявке (ТЗ §12)."""
    date = app.created_at.strftime("%d.%m.%Y") if app.created_at else ""
    exp = "Да" if app.experience else "Нет"
    if app.experience and app.experience_apps:
        exp = f"Да ({app.experience_apps})"
    lines = [
        "<b>Новая заявка</b>",
        "",
        f"Возраст: {app.age}",
        f"Страна: {app.country}",
        f"Telegram/whatsapp: {contact_display(app)}",
        f"Email: {app.email or '—'}",
        f"Опыт: {exp}",
        f"Готова работать: {app.time_commitment or '—'}",
        f"Фото: {len(photos(app))} шт.",
        f"Дата: {date}",
        f"ID заявки: #{app.id}",
    ]
    return "\n".join(lines)
