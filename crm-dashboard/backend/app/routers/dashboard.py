import json
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, resolve_scope
from ..models import ActionLog, Agency, Host, SplitOperation, User
from ..serializers import agency_names_map, enrich_hosts, filter_blocked
from ..services import app_settings
from ..services.levels import GRADE_ORDER, income_range_label

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def parse_online_minutes(s: str) -> int:
    if not s:
        return 0
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    total = 0
    if h:
        total += int(h.group(1)) * 60
    if m:
        total += int(m.group(1))
    if not h and not m:
        digits = re.findall(r"\d+", s)
        if digits:
            total = int(digits[0])
    return total


def fmt_online(total_minutes: int) -> dict:
    return {"hours": total_minutes // 60, "minutes": total_minutes % 60, "total_minutes": total_minutes}


def _aggregate(items: list[dict], coins_per_usd: float) -> dict:
    y_income = sum(h["last_day_income"] for h in items)
    m_income = sum(h["monthly_income"] for h in items)
    y_agency = sum(h.get("last_day_income_agency", 0) for h in items)
    m_agency = sum(h.get("month_income_agency", 0) for h in items)
    y_online = sum(parse_online_minutes(h["last_day_online"]) for h in items)
    m_online = sum(parse_online_minutes(h["monthly_online"]) for h in items)
    at_risk = sum(1 for h in items if h["risk_status"] == "danger")
    warnings = sum(1 for h in items if h["risk_status"] == "warning")
    total = len(items)
    return {
        "users": total,
        "yesterday_income_coins": y_income,
        "yesterday_income_usd": round(y_income / coins_per_usd, 2),
        "month_income_coins": m_income,
        "month_income_usd": round(m_income / coins_per_usd, 2),
        "yesterday_agency_income_coins": y_agency,
        "yesterday_agency_income_usd": round(y_agency / coins_per_usd, 2),
        "month_agency_income_coins": m_agency,
        "month_agency_income_usd": round(m_agency / coins_per_usd, 2),
        "yesterday_online": fmt_online(y_online),
        "month_online": fmt_online(m_online),
        "at_risk_count": at_risk,
        "warnings_count": warnings,
        "at_risk_percent": round((at_risk + warnings) / total * 100, 1) if total else 0,
    }


@router.get("/stats")
def dashboard_stats(
    agency_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scope = resolve_scope(db, user, agency_id)
    coins_per_usd = app_settings.get_coins_per_usd(db)
    grade_config = app_settings.get_grade_config(db)
    names = agency_names_map(db)

    hosts = db.query(Host).filter(Host.agency_id.in_(scope)).all() if scope else []
    items = filter_blocked(db, enrich_hosts(db, hosts, names))

    cards = _aggregate(items, coins_per_usd)

    # по агентствам
    per_agency = []
    agencies = db.query(Agency).filter(Agency.id.in_(scope)).order_by(Agency.name).all() if scope else []
    by_agency: dict[int, list] = {a.id: [] for a in agencies}
    for h in items:
        by_agency.setdefault(h["agency_id"], []).append(h)

    # последние операции (вкл. «Все агентства» с agency_id=None) — чтобы найти последний сплит каждого
    recent_ops = db.query(SplitOperation).order_by(SplitOperation.id.desc()).limit(50).all()

    def last_split_for(agency_id: int, agency_name: str):
        """Последний сплит агентства, учитывая и запуски «Все агентства»."""
        for op in recent_ops:  # от новых к старым
            if op.agency_id == agency_id:
                return op.started_at, op.total_amount_coins
            if op.agency_id is None:  # многоагентский запуск — берём долю из деталей
                try:
                    det = json.loads(op.details or "{}")
                except Exception:
                    det = {}
                for row in det.get("agencies", []):
                    if row.get("agency") == agency_name and row.get("status") == "ok":
                        return op.started_at, row.get("amount", 0)
        return None, 0

    for a in agencies:
        agg = _aggregate(by_agency.get(a.id, []), coins_per_usd)
        ls_date, ls_amount = last_split_for(a.id, a.name)
        agg.update({
            "agency_id": a.id,
            "agency_name": a.name,
            "withdrawable_coins": a.withdrawable_coins,
            "withdrawable_usd": round(a.withdrawable_coins / coins_per_usd, 2),
            "last_synced_at": a.last_synced_at.isoformat() if a.last_synced_at else None,
            "last_split_amount": ls_amount,
            "last_split_date": ls_date.isoformat() if ls_date else None,
        })
        per_agency.append(agg)

    # распределение уровней
    total = len(items)
    dist = []
    for grade in GRADE_ORDER:
        cnt = sum(1 for h in items if h["grade"] == grade)
        dist.append({
            "grade": grade,
            "range": income_range_label(grade, grade_config),
            "count": cnt,
            "percent": round(cnt / total * 100, 1) if total else 0,
        })

    # последний split в области видимости
    last_q = db.query(SplitOperation)
    if agency_id is not None:
        last_q = last_q.filter(SplitOperation.agency_id == agency_id)
    last_split = last_q.order_by(SplitOperation.id.desc()).first()
    last_split_out = None
    if last_split:
        last_split_out = {
            "id": last_split.id,
            "scope_label": last_split.scope_label,
            "processed": last_split.processed,
            "skipped": last_split.skipped,
            "errors": last_split.errors,
            "total_amount_coins": last_split.total_amount_coins,
            "total_amount_usd": round(last_split.total_amount_coins / coins_per_usd, 2),
            "status": last_split.status,
            "date": last_split.started_at.isoformat() if last_split.started_at else None,
        }

    recent_actions = [
        {
            "id": a.id, "username": a.username, "action_type": a.action_type,
            "agency_name": a.agency_name, "anchor_id": a.anchor_id, "target": a.target,
            "old_value": a.old_value, "new_value": a.new_value, "status": a.status,
            "message": a.message, "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in db.query(ActionLog).order_by(ActionLog.id.desc()).limit(6).all()
    ]

    recent_splits = []
    for s in db.query(SplitOperation).order_by(SplitOperation.id.desc()).limit(5).all():
        recent_splits.append({
            "id": s.id, "scope_label": s.scope_label, "processed": s.processed,
            "skipped": s.skipped, "errors": s.errors, "status": s.status,
            "total_amount_coins": s.total_amount_coins,
            "total_amount_usd": round(s.total_amount_coins / coins_per_usd, 2),
            "date": s.started_at.isoformat() if s.started_at else None,
        })

    last_synced = max((a.last_synced_at for a in agencies if a.last_synced_at), default=None)

    return {
        "cards": {**cards, "last_split": last_split_out},
        "per_agency": per_agency,
        "level_distribution": dist,
        "last_split": last_split_out,
        "recent_actions": recent_actions,
        "recent_splits": recent_splits,
        "coins_per_usd": coins_per_usd,
        "updated_at": last_synced.isoformat() if last_synced else None,
    }
