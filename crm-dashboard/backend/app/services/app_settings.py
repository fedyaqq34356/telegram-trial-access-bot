"""Key/value настройки приложения (курс, лимиты уровней, интервал и т.д.)."""
import json

from sqlalchemy.orm import Session

from ..models import Setting

DEFAULT_GRADE_CONFIG = {
    "S": {"min": 45000, "limit": 0.25, "punishment": "Бан на 1 день"},
    "A": {"min": 20000, "limit": 0.25, "punishment": "Бан на 1 день"},
    "B": {"min": 7000, "limit": 0.18, "punishment": "Бан на 3 дня"},
    "C": {"min": 2000, "limit": 0.18, "punishment": "Бан на 7 дней"},
    "D": {"min": 0, "limit": 0.12, "punishment": "Перманентный бан"},
}

DEFAULTS = {
    "coins_per_usd": "20",
    "max_ratio_percent": "20",
    "sync_interval_minutes": "15",
    "split_min_balance": "100",
    "split_skip_receive_rate": "0.4",
    "warning_threshold": "0.9",  # доля лимита, после которой статус "предупреждение"
    "show_blocked": "false",     # показывать заблокированных пользователей (по умолчанию выкл.)
    "grade_config": json.dumps(DEFAULT_GRADE_CONFIG),
    # ── публичный сайт tos-site (раздел CRM «Мой сайт») ──
    "training_password": "",            # один пароль на всех для страницы «Обучение»
    "training_lessons_json": "[]",      # полное обучение: [{type:video|text|checklist, title, body|url, items}]
    "training_lessons_quick_json": "[]",  # быстрый старт (5–10 мин)
    "apply_example_video_json": "{}",     # видео-пример для заявки: {ru,en,ua} → пути videos/<uuid>

    "notify_email": "",                 # email для уведомлений о заявках (опционально)
    "owner_telegram_id": "",            # кому слать уведомления о заявках (приоритетнее config)
    "social_telegram": "",              # ссылка/username Telegram агентства
    "social_instagram": "",
    "social_tiktok": "",
    "social_whatsapp": "",              # номер телефона или ссылка WhatsApp
    "faq_json": "[]",                   # [{q, a}] — переопределение/дополнение FAQ
    "site_text_overrides_json": "{}",   # точечные переопределения текстов сайта по ключам
}


def get_setting(db: Session, key: str, default: str | None = None) -> str:
    row = db.get(Setting, key)
    if row is not None:
        return row.value
    if default is not None:
        return default
    return DEFAULTS.get(key, "")


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()


def get_all_settings(db: Session) -> dict:
    result = dict(DEFAULTS)
    for row in db.query(Setting).all():
        result[row.key] = row.value
    return result


def get_grade_config(db: Session) -> dict:
    raw = get_setting(db, "grade_config")
    try:
        cfg = json.loads(raw)
        if isinstance(cfg, dict) and cfg:
            return cfg
    except Exception:
        pass
    return DEFAULT_GRADE_CONFIG


def get_coins_per_usd(db: Session) -> float:
    try:
        return float(get_setting(db, "coins_per_usd")) or 20.0
    except Exception:
        return 20.0


def ensure_defaults(db: Session) -> None:
    for key, value in DEFAULTS.items():
        if db.get(Setting, key) is None:
            db.add(Setting(key=key, value=value))
    db.commit()
