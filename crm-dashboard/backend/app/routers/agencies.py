from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import (
    accessible_agency_ids,
    can_perform,
    get_current_user,
    require_superadmin,
)
from ..models import Agency, User
from ..schemas import AgencyCreate, AgencyOut, AgencyUpdate, TfaSubmit
from ..services.sessions import sessions
from ..services.split_service import agency_cooldown_remaining
from ..services.sync_service import ensure_session

router = APIRouter(prefix="/agencies", tags=["agencies"])


def _to_out(db: Session, agency: Agency, user: User) -> AgencyOut:
    return AgencyOut(
        id=agency.id,
        name=agency.name,
        url=agency.url,
        tfa_required=agency.tfa_required,
        is_active=agency.is_active,
        has_session=sessions.get_active(agency.id) is not None,
        last_synced_at=agency.last_synced_at,
        cooldown_remaining_seconds=agency_cooldown_remaining(agency),
        can_change_ratio=can_perform(db, user, agency.id, "can_change_ratio"),
        can_split=can_perform(db, user, agency.id, "can_split"),
    )


@router.get("", response_model=list[AgencyOut])
def list_agencies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = accessible_agency_ids(db, user)
    agencies = db.query(Agency).filter(Agency.id.in_(allowed)).order_by(Agency.name).all()
    return [_to_out(db, a, user) for a in agencies]


@router.post("", response_model=AgencyOut)
def create_agency(payload: AgencyCreate, user: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    if db.query(Agency).filter(Agency.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Агентство с таким названием уже существует")
    agency = Agency(**payload.model_dump())
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return _to_out(db, agency, user)


@router.put("/{agency_id}", response_model=AgencyOut)
def update_agency(
    agency_id: int,
    payload: AgencyUpdate,
    user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    agency = db.get(Agency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(agency, key, value)
    db.commit()
    db.refresh(agency)
    # сбросить сессию если меняли креды
    sessions.drop_active(agency_id)
    return _to_out(db, agency, user)


@router.delete("/{agency_id}")
def delete_agency(agency_id: int, user: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    agency = db.get(Agency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    sessions.drop_active(agency_id)
    db.delete(agency)
    db.commit()
    return {"ok": True}


@router.post("/{agency_id}/login")
def login_agency(agency_id: int, user: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    """Инициирует логин в Halo. Если нужна 2FA — вернёт need_tfa."""
    agency = db.get(Agency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    result = ensure_session(db, agency)
    return {"status": result}


@router.post("/verify-2fa")
def verify_2fa(payload: TfaSubmit, user: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    agency = db.get(Agency, payload.agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    result = ensure_session(db, agency, tfa_code=payload.code)
    if result != "ok":
        raise HTTPException(status_code=400, detail=f"Не удалось войти: {result}")
    return {"status": "ok"}
