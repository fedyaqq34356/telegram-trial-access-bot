from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, resolve_scope
from ..models import Host, User
from ..serializers import agency_names_map, enrich_hosts, filter_blocked

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("")
def list_risk(
    agency_id: int | None = None,
    status: str = "all",
    level: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scope = resolve_scope(db, user, agency_id)
    if not scope:
        return {"items": [], "total": 0, "page": page, "limit": limit}

    hosts = db.query(Host).filter(Host.agency_id.in_(scope)).all()
    names = agency_names_map(db)
    items = filter_blocked(db, enrich_hosts(db, hosts, names))

    items = [h for h in items if h["risk_status"] in ("warning", "danger")]

    if status in ("warning", "danger"):
        items = [h for h in items if h["risk_status"] == status]
    if level:
        levels = {x.strip().upper() for x in level.split(",") if x.strip()}
        items = [h for h in items if h["grade"] in levels]
    if search:
        q = search.strip().lower()
        items = [h for h in items if q in str(h["display_account_id"]).lower() or q in h["nickname"].lower()]

    items.sort(key=lambda h: (0 if h["risk_status"] == "danger" else 1, -(h["risk_excess"] or -99)))

    total = len(items)
    start = (page - 1) * limit
    return {"items": items[start:start + limit], "total": total, "page": page, "limit": limit}
