from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..audit import log_action, log_security
from ..database import get_db
from ..deps import accessible_agency_ids, client_ip, get_current_user
from ..models import User
from ..schemas import LoginRequest, RefreshRequest, TokenResponse
from ..security import create_access_token, create_refresh_token, decode_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учётная запись отключена")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    log_security(db, user, "login", client_ip(request), request.headers.get("user-agent", ""))
    log_action(db, user, "login", status="done", message=f"Вход в систему · IP {client_ip(request)}")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    user_id = decode_token(payload.refresh_token, "refresh")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh токен")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_security(db, user, "logout", client_ip(request), request.headers.get("user-agent", ""))
    return {"ok": True}

@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "is_superadmin": user.is_superadmin,
        "can_manage_users": user.is_superadmin or user.can_manage_users,
        "accessible_agency_ids": accessible_agency_ids(db, user),
    }
