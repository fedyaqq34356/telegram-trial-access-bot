from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_manage_users
from ..models import Agency, User, UserAgencyAccess
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

def _to_out(db: Session, user: User) -> UserOut:
    names = {a.id: a.name for a in db.query(Agency).all()}
    accesses = [
        {
            "agency_id": acc.agency_id,
            "agency_name": names.get(acc.agency_id, ""),
            "can_view": acc.can_view,
            "can_change_ratio": acc.can_change_ratio,
            "can_split": acc.can_split,
        }
        for acc in user.accesses
    ]
    return UserOut(
        id=user.id, username=user.username, name=user.name, role=user.role,
        can_manage_users=user.can_manage_users, can_view_traffic=user.can_view_traffic,
        is_active=user.is_active,
        created_at=user.created_at, last_login=user.last_login, accesses=accesses,
    )

def _apply_accesses(db: Session, user: User, accesses: list) -> None:
    db.query(UserAgencyAccess).filter(UserAgencyAccess.user_id == user.id).delete()
    db.flush()
    for item in accesses:
        if db.get(Agency, item.agency_id) is None:
            continue
        db.add(UserAgencyAccess(
            user_id=user.id, agency_id=item.agency_id,
            can_view=item.can_view, can_change_ratio=item.can_change_ratio, can_split=item.can_split,
        ))

@router.get("", response_model=list[UserOut])
def list_users(admin: User = Depends(require_manage_users), db: Session = Depends(get_db)):
    return [_to_out(db, u) for u in db.query(User).order_by(User.id).all()]

@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, admin: User = Depends(require_manage_users), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Логин уже занят")
    role = payload.role if payload.role in ("admin", "superadmin") else "admin"
    if role == "superadmin" and not admin.is_superadmin:
        raise HTTPException(status_code=403, detail="Только главный администратор может создавать суперадминов")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=role,
        can_manage_users=payload.can_manage_users,
        can_view_traffic=payload.can_view_traffic,
    )
    db.add(user)
    db.flush()
    _apply_accesses(db, user, payload.accesses)
    db.commit()
    db.refresh(user)
    return _to_out(db, user)

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, admin: User = Depends(require_manage_users), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None and payload.role in ("admin", "superadmin"):
        if payload.role == "superadmin" and not admin.is_superadmin:
            raise HTTPException(status_code=403, detail="Недостаточно прав для назначения суперадмина")
        user.role = payload.role
    if payload.can_manage_users is not None:
        user.can_manage_users = payload.can_manage_users
    if payload.can_view_traffic is not None:
        user.can_view_traffic = payload.can_view_traffic
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.accesses is not None:
        _apply_accesses(db, user, payload.accesses)

    db.commit()
    db.refresh(user)
    return _to_out(db, user)

@router.delete("/{user_id}")
def delete_user(user_id: int, admin: User = Depends(require_manage_users), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    if user.is_superadmin and db.query(User).filter(User.role == "superadmin").count() <= 1:
        raise HTTPException(status_code=400, detail="Нельзя удалить последнего главного администратора")
    db.delete(user)
    db.commit()
    return {"ok": True}
