"""CRM-раздел «Статистика сайта»: агрегированная статистика посещений публичного сайта.

Доступ только у пользователей с правом can_view_traffic (или суперадмина) —
проверяется на backend через require_view_traffic, недостаточно скрыть в UI.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_view_traffic
from ..models import Application, PageVisit, User

router = APIRouter(prefix="/traffic", tags=["traffic"])

def _day_expr():
    return func.date(PageVisit.created_at)

@router.get("/stats")
def traffic_stats(
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(require_view_traffic),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    base = db.query(PageVisit).filter(PageVisit.created_at >= since)

    total_visits = base.count()
    unique_visitors = (
        db.query(func.count(func.distinct(PageVisit.visitor_id)))
        .filter(PageVisit.created_at >= since, PageVisit.visitor_id != "")
        .scalar()
    ) or 0

    prev_visits = db.query(func.count(PageVisit.id)).filter(
        PageVisit.created_at >= prev_since, PageVisit.created_at < since
    ).scalar() or 0

    day_col = _day_expr()
    rows = (
        db.query(day_col.label("d"), func.count(PageVisit.id))
        .filter(PageVisit.created_at >= since)
        .group_by("d").all()
    )
    by_day = {str(d): int(c) for d, c in rows}

    uniq_rows = (
        db.query(day_col.label("d"), func.count(func.distinct(PageVisit.visitor_id)))
        .filter(PageVisit.created_at >= since, PageVisit.visitor_id != "")
        .group_by("d").all()
    )
    uniq_by_day = {str(d): int(c) for d, c in uniq_rows}

    daily = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).date().isoformat()
        daily.append({"date": day, "visits": by_day.get(day, 0), "uniques": uniq_by_day.get(day, 0)})

    def _top(column, limit=12, coalesce_host=False):
        q = db.query(column, func.count(PageVisit.id)).filter(PageVisit.created_at >= since)
        q = q.group_by(column).order_by(func.count(PageVisit.id).desc()).limit(limit)
        out = []
        for val, cnt in q.all():
            out.append({"key": val or "", "count": int(cnt)})
        return out

    # Источник = utm_source, иначе referrer_host, иначе "Прямые заходы"
    src_rows = (
        db.query(PageVisit.utm_source, PageVisit.referrer_host, func.count(PageVisit.id))
        .filter(PageVisit.created_at >= since)
        .group_by(PageVisit.utm_source, PageVisit.referrer_host).all()
    )
    src_agg: dict[str, int] = {}
    for utm, host, cnt in src_rows:
        key = utm or host or "Прямые заходы"
        src_agg[key] = src_agg.get(key, 0) + int(cnt)
    sources = sorted(
        [{"key": k, "count": v} for k, v in src_agg.items()],
        key=lambda x: x["count"], reverse=True,
    )[:12]

    campaigns = [r for r in _top(PageVisit.utm_campaign) if r["key"]]
    top_pages = _top(PageVisit.path)

    dev_rows = (
        db.query(PageVisit.device, func.count(PageVisit.id))
        .filter(PageVisit.created_at >= since)
        .group_by(PageVisit.device).all()
    )
    devices = [{"key": d or "unknown", "count": int(c)} for d, c in dev_rows]

    # Конверсия: заявки за период + разбивка по источникам
    total_apps = db.query(func.count(Application.id)).filter(Application.created_at >= since).scalar() or 0
    app_src_rows = (
        db.query(Application.utm_source, func.count(Application.id))
        .filter(Application.created_at >= since)
        .group_by(Application.utm_source).all()
    )
    apps_by_source = {(s or "Прямые заходы"): int(c) for s, c in app_src_rows}

    conversion_by_source = []
    for s in sources:
        visits = s["count"]
        apps = apps_by_source.get(s["key"], 0)
        conversion_by_source.append({
            "source": s["key"],
            "visits": visits,
            "applications": apps,
            "rate": round(apps / visits * 100, 2) if visits else 0.0,
        })

    return {
        "range_days": days,
        "totals": {
            "visits": total_visits,
            "uniques": int(unique_visitors),
            "applications": int(total_apps),
            "conversion_rate": round(int(total_apps) / total_visits * 100, 2) if total_visits else 0.0,
            "visits_prev": int(prev_visits),
            "visits_delta_percent": round((total_visits - prev_visits) / prev_visits * 100, 1) if prev_visits else None,
        },
        "daily": daily,
        "sources": sources,
        "campaigns": campaigns,
        "top_pages": top_pages,
        "devices": devices,
        "conversion_by_source": conversion_by_source,
    }
