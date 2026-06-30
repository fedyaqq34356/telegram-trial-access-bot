import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..audit import log_action
from ..database import get_db
from ..deps import can_perform, get_current_user, resolve_scope
from ..models import Agency, SplitOperation, User
from ..schemas import SplitRequest
from ..services import app_settings
from ..services.split_service import start_split_async

router = APIRouter(prefix="/split", tags=["split"])

def _serialize(op: SplitOperation, coins_per_usd: float) -> dict:
    details = {}
    try:
        details = json.loads(op.details) if op.details else {}
    except Exception:
        details = {}
    return {
        "id": op.id,
        "scope_label": op.scope_label,
        "agency_id": op.agency_id,
        "processed": op.processed,
        "skipped": op.skipped,
        "errors": op.errors,
        "total_amount_coins": op.total_amount_coins,
        "total_amount_usd": round(op.total_amount_coins / coins_per_usd, 2),
        "agency_amount_coins": op.agency_amount_coins,
        "agency_amount_usd": round(op.agency_amount_coins / coins_per_usd, 2),
        "host_amount_coins": op.total_amount_coins - op.agency_amount_coins,
        "host_amount_usd": round((op.total_amount_coins - op.agency_amount_coins) / coins_per_usd, 2),
        "status": op.status,
        "details": details,
        "started_at": op.started_at.isoformat() if op.started_at else None,
        "finished_at": op.finished_at.isoformat() if op.finished_at else None,
        "duration_seconds": op.duration_seconds,
    }

@router.post("/run")
def run(payload: SplitRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scope = resolve_scope(db, user, payload.agency_id)
    allowed = [aid for aid in scope if can_perform(db, user, aid, "can_split")]
    if not allowed:
        raise HTTPException(status_code=403, detail="Нет прав на запуск Split по выбранным агентствам")

    agencies = db.query(Agency).filter(Agency.id.in_(allowed)).order_by(Agency.name).all()
    scope_label = agencies[0].name if len(agencies) == 1 else "Все агентства"

    op_id = start_split_async(user.id, allowed, scope_label)
    log_action(db, user, "split", agency_name=scope_label, status="running",
               message=f"Запущен Split по области «{scope_label}»")

    op = db.get(SplitOperation, op_id)
    return _serialize(op, app_settings.get_coins_per_usd(db))

@router.get("/history")
def history(
    agency_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scope = resolve_scope(db, user, agency_id)
    coins_per_usd = app_settings.get_coins_per_usd(db)
    q = db.query(SplitOperation)
    if agency_id is not None:
        q = q.filter(SplitOperation.agency_id == agency_id)
    else:
        q = q.filter((SplitOperation.agency_id.is_(None)) | (SplitOperation.agency_id.in_(scope)))
    total = q.count()
    ops = q.order_by(SplitOperation.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [_serialize(o, coins_per_usd) for o in ops],
        "total": total,
        "page": page,
        "limit": limit,
    }
