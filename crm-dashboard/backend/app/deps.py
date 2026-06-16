from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Agency, User, UserAgencyAccess
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
    user_id = decode_token(creds.credentials, "access")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден или отключён")
    return user


def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права главного администратора")
    return user


def require_manage_users(user: User = Depends(get_current_user)) -> User:
    if not (user.is_superadmin or user.can_manage_users):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на управление пользователями")
    return user


# ── контроль доступа к агентствам ──

def accessible_agency_ids(db: Session, user: User) -> list[int]:
    if user.is_superadmin:
        return [a.id for a in db.query(Agency).all()]
    rows = db.query(UserAgencyAccess).filter(
        UserAgencyAccess.user_id == user.id,
        UserAgencyAccess.can_view == True,  # noqa: E712
    ).all()
    return [r.agency_id for r in rows]


def access_map(db: Session, user: User) -> dict[int, UserAgencyAccess]:
    if user.is_superadmin:
        return {}  # суперадмин имеет все права без записей
    return {r.agency_id: r for r in db.query(UserAgencyAccess).filter(UserAgencyAccess.user_id == user.id).all()}


def can_view_agency(db: Session, user: User, agency_id: int) -> bool:
    if user.is_superadmin:
        return True
    return agency_id in accessible_agency_ids(db, user)


def can_perform(db: Session, user: User, agency_id: int, perm: str) -> bool:
    """perm: 'can_change_ratio' | 'can_split' | 'can_view'"""
    if user.is_superadmin:
        return True
    row = db.query(UserAgencyAccess).filter(
        UserAgencyAccess.user_id == user.id,
        UserAgencyAccess.agency_id == agency_id,
    ).first()
    return bool(row and getattr(row, perm, False))


def resolve_scope(db: Session, user: User, agency_id: int | None) -> list[int]:
    """Возвращает список agency_id с учётом фильтра и прав.

    agency_id=None → все доступные агентства.
    Если выбрано недоступное агентство — 403.
    """
    allowed = accessible_agency_ids(db, user)
    if agency_id is None:
        return allowed
    if agency_id not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому агентству")
    return [agency_id]


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else ""
