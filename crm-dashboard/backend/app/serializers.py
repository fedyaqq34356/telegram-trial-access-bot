"""Преобразование ORM-объектов в словари для API с вычисленными полями."""
from sqlalchemy.orm import Session

from .models import Agency, Host, User
from .services import app_settings
from .services.levels import enrich_host


def host_to_dict(host: Host, agency_name: str) -> dict:
    return {
        "id": host.id,
        "agency_id": host.agency_id,
        "agency_name": agency_name,
        "display_account_id": host.display_account_id,
        "nickname": host.nickname,
        "avatar_url": host.avatar_url,
        "agent_name": host.agent_name or agency_name,
        "email": host.email,
        "ratio": host.ratio,
        "ratio_percent": round(host.ratio / 100, 2),
        "down_rate": host.down_rate,
        "real_down_rate": host.real_down_rate,
        "receive_rate": host.receive_rate,
        "monthly_income": host.monthly_income,
        "weekly_income": host.weekly_income,
        "last_day_income": host.last_day_income,
        "monthly_online": host.monthly_online,
        "weekly_online": host.weekly_online,
        "last_day_online": host.last_day_online,
        "balance_coins": host.balance_coins,
        "split_diamond": host.split_diamond,
        "monthly_income_ranking": host.monthly_income_ranking,
        "ban_status": host.ban_status,
        "fake": host.fake,
        "approval_date": host.approval_date,
        "updated_at": host.updated_at.isoformat() if host.updated_at else None,
    }


def enrich_hosts(db: Session, hosts: list[Host], agency_names: dict[int, str]) -> list[dict]:
    grade_config = app_settings.get_grade_config(db)
    coins_per_usd = app_settings.get_coins_per_usd(db)
    warn = float(app_settings.get_setting(db, "warning_threshold"))
    out = []
    for h in hosts:
        base = host_to_dict(h, agency_names.get(h.agency_id, ""))
        out.append(enrich_host(base, grade_config, coins_per_usd, warn))
    return out


def show_blocked_enabled(db: Session) -> bool:
    return app_settings.get_setting(db, "show_blocked").strip().lower() in ("1", "true", "yes", "on")


def filter_blocked(db: Session, items: list[dict]) -> list[dict]:
    """Убирает заблокированных, если в настройках не включён их показ."""
    if show_blocked_enabled(db):
        return items
    return [h for h in items if not h.get("is_blocked")]


def agency_names_map(db: Session) -> dict[int, str]:
    return {a.id: a.name for a in db.query(Agency).all()}
