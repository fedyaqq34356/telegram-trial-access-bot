"""CRM-раздел «Заявки» (авторизованный) + internal-эндпоинт для Telegram-бота."""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import APPLICATION_STATUSES, Application, ApplicationStatusEvent, User
from ..services import storage
from ..services.applications_service import (
    photos as app_photos,
    serialize_application,
    status_label,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])
internal_router = APIRouter(prefix="/internal", tags=["internal"])


def _apply_status_change(db: Session, app: Application, new_status: str, actor: str, note: str = "") -> None:
    if new_status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=400, detail="Недопустимый статус")
    if new_status == app.status:
        return
    db.add(ApplicationStatusEvent(
        application_id=app.id, old_status=app.status, new_status=new_status, actor=actor, note=note,
    ))
    app.status = new_status


@router.get("")
def list_applications(
    status: str | None = None,
    country: str | None = None,
    experience: bool | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Application)
    if status and status != "all":
        query = query.filter(Application.status == status)
    if country:
        query = query.filter(Application.country.ilike(f"%{country}%"))
    if experience is not None:
        query = query.filter(Application.experience == experience)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Application.contact_telegram.ilike(like),
            Application.contact_whatsapp.ilike(like),
            Application.email.ilike(like),
        ))
    if date_from:
        query = query.filter(Application.created_at >= date_from)
    if date_to:
        query = query.filter(Application.created_at <= date_to)

    total = query.count()
    rows = (
        query.order_by(Application.id.desc())
        .offset((page - 1) * limit).limit(limit).all()
    )
    return {
        "items": [serialize_application(a) for a in rows],
        "total": total,
        "page": page,
        "limit": limit,
        "statuses": [{"value": s, "label": status_label(s)} for s in APPLICATION_STATUSES],
    }


@router.get("/new-count")
def new_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(func.count(Application.id)).filter(Application.status == "new").scalar()
    return {"count": int(n or 0)}


@router.get("/{app_id}")
def get_application(app_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return serialize_application(app, with_events=True)


@router.patch("/{app_id}")
def update_application(
    app_id: int,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    actor = user.name or user.username
    if "status" in payload and payload["status"]:
        _apply_status_change(db, app, str(payload["status"]), actor)
    if "manager_comment" in payload:
        app.manager_comment = str(payload["manager_comment"])
    db.commit()
    db.refresh(app)
    return serialize_application(app, with_events=True)


@router.get("/{app_id}/photo/{idx}")
def application_photo(
    app_id: int, idx: int,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    paths = app_photos(app)
    if idx < 0 or idx >= len(paths):
        raise HTTPException(status_code=404, detail="Фото не найдено")
    try:
        path = storage.abs_path(paths[idx])
    except storage.UploadError:
        raise HTTPException(status_code=404, detail="Фото не найдено")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Фото не найдено")
    return FileResponse(path, media_type=storage.content_type_of(paths[idx]))


# ── internal: смена статуса из Telegram-бота ──
def require_internal(x_internal_token: str = Header(default="")):
    if not settings.internal_api_token or x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=403, detail="forbidden")


@internal_router.get("/applications/{app_id}")
def internal_get(app_id: int, _: None = Depends(require_internal), db: Session = Depends(get_db)):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "id": app.id,
        "contact_telegram": app.contact_telegram,
        "contact_whatsapp": app.contact_whatsapp,
        "email": app.email,
        "status": app.status,
        "status_label": status_label(app.status),
    }


@internal_router.patch("/applications/{app_id}/status")
def internal_set_status(
    app_id: int,
    payload: dict,
    _: None = Depends(require_internal),
    db: Session = Depends(get_db),
):
    app = db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="not found")
    new_status = str(payload.get("status", ""))
    actor = str(payload.get("actor", "бот"))
    _apply_status_change(db, app, new_status, actor)
    db.commit()
    db.refresh(app)
    return {"ok": True, "id": app.id, "status": app.status, "status_label": status_label(app.status)}
