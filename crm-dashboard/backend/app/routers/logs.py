from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_superadmin
from ..models import ActionLog, SecurityLog, User

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/actions")
def action_logs(
    action_type: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ActionLog)
    if action_type:
        q = q.filter(ActionLog.action_type == action_type)
    total = q.count()
    rows = q.order_by(ActionLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id, "username": r.username, "action_type": r.action_type,
                "agency_name": r.agency_name, "anchor_id": r.anchor_id, "target": r.target,
                "old_value": r.old_value, "new_value": r.new_value, "status": r.status,
                "message": r.message, "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total, "page": page, "limit": limit,
    }

@router.delete("/actions")
def clear_action_logs(
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    """Очистка журнала изменений. Доступно только главному админу."""
    deleted = db.query(ActionLog).delete()
    db.commit()
    return {"deleted": deleted}

@router.get("/security")
def security_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    q = db.query(SecurityLog)
    total = q.count()
    rows = q.order_by(SecurityLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id, "username": r.username, "action": r.action,
                "ip_address": r.ip_address, "user_agent": r.user_agent,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": total, "page": page, "limit": limit,
    }
