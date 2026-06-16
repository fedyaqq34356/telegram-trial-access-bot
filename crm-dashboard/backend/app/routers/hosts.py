from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..audit import log_action
from ..database import get_db
from ..deps import accessible_agency_ids, can_perform, get_current_user, resolve_scope
from ..models import Agency, Host, User
from ..schemas import RatioUpdate
from ..serializers import agency_names_map, enrich_hosts, filter_blocked
from ..services import app_settings
from ..services.sessions import sessions
from ..services.sync_service import ensure_session

router = APIRouter(prefix="/hosts", tags=["hosts"])

SORT_FIELDS = {
    "last_day_income", "monthly_income", "weekly_income",
    "last_day_online", "monthly_online", "real_down_rate",
    "down_rate", "grade", "risk_status", "ratio", "nickname",
    "approval_date",
}
GRADE_RANK = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
RISK_RANK = {"danger": 0, "warning": 1, "safe": 2}


@router.get("")
def list_hosts(
    agency_id: int | None = None,
    search: str | None = None,
    level: str | None = None,
    risk_status: str | None = None,
    min_ratio: float | None = None,
    max_ratio: float | None = None,
    sort: str = "monthly_income",
    order: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scope = resolve_scope(db, user, agency_id)
    if not scope:
        return {"items": [], "total": 0, "page": page, "limit": limit}

    hosts = db.query(Host).filter(Host.agency_id.in_(scope)).all()
    names = agency_names_map(db)
    items = filter_blocked(db, enrich_hosts(db, hosts, names))

    if search:
        q = search.strip().lower()
        items = [h for h in items if q in str(h["display_account_id"]).lower() or q in h["nickname"].lower()]
    if level:
        levels = {x.strip().upper() for x in level.split(",") if x.strip()}
        items = [h for h in items if h["grade"] in levels]
    if risk_status:
        statuses = {x.strip().lower() for x in risk_status.split(",") if x.strip()}
        items = [h for h in items if h["risk_status"] in statuses]
    if min_ratio is not None:
        items = [h for h in items if h["ratio_percent"] >= min_ratio]
    if max_ratio is not None:
        items = [h for h in items if h["ratio_percent"] <= max_ratio]

    reverse = order.lower() == "desc"
    sort = sort if sort in SORT_FIELDS else "monthly_income"

    def sort_key(h):
        if sort == "grade":
            return GRADE_RANK.get(h["grade"], 9)
        if sort == "risk_status":
            return RISK_RANK.get(h["risk_status"], 9)
        val = h.get(sort)
        return (val is None, val if val is not None else 0)

    items.sort(key=sort_key, reverse=reverse)

    total = len(items)
    start = (page - 1) * limit
    return {
        "items": items[start:start + limit],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{host_id}")
def get_host(host_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    host = db.get(Host, host_id)
    if host is None or host.agency_id not in accessible_agency_ids(db, user):
        raise HTTPException(status_code=404, detail="Девушка не найдена")
    names = agency_names_map(db)
    return enrich_hosts(db, [host], names)[0]


@router.post("/{host_id}/ratio")
def change_ratio(
    host_id: int,
    payload: RatioUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    host = db.get(Host, host_id)
    if host is None or host.agency_id not in accessible_agency_ids(db, user):
        raise HTTPException(status_code=404, detail="Девушка не найдена")
    if not can_perform(db, user, host.agency_id, "can_change_ratio"):
        raise HTTPException(status_code=403, detail="Нет прав на изменение процента")

    max_ratio = float(app_settings.get_setting(db, "max_ratio_percent"))
    if payload.ratio_percent > max_ratio:
        raise HTTPException(status_code=400, detail=f"Максимальный процент — {max_ratio}%")

    agency = db.get(Agency, host.agency_id)
    status_session = ensure_session(db, agency)
    if status_session != "ok":
        log_action(db, user, "ratio_change", agency_name=agency.name, anchor_id=host.display_account_id,
                   old_value=host.ratio / 100, new_value=payload.ratio_percent, status="error",
                   message=f"Сессия: {status_session}")
        raise HTTPException(status_code=400, detail=f"Нет активной сессии Halo: {status_session}")

    parser = sessions.get_active(agency.id)
    ratio_value = int(round(payload.ratio_percent * 100))
    old_percent = host.ratio / 100
    # Halo ждёт внутренний AccountId (id=26776921), а не DisplayAccountId — подтверждено перехватом
    result = parser.set_ratio(host.account_id or host.display_account_id, ratio_value, host.agent_name or agency.name)

    if result["ok"]:
        host.ratio = ratio_value
        db.commit()
        log_action(db, user, "ratio_change", agency_name=agency.name, anchor_id=host.display_account_id,
                   target=host.nickname, old_value=old_percent, new_value=payload.ratio_percent,
                   status="done", message="Процент изменён")
        return {"status": "done", "ratio_percent": payload.ratio_percent}

    log_action(db, user, "ratio_change", agency_name=agency.name, anchor_id=host.display_account_id,
               target=host.nickname, old_value=old_percent, new_value=payload.ratio_percent,
               status="error", message=result.get("msg", ""))
    raise HTTPException(status_code=400, detail=f"Ошибка панели: {result.get('msg')}")
