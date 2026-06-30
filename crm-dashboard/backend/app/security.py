from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import settings

def _to_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except Exception:
        return False

def _create_token(data: dict, expires: timedelta, token_type: str) -> str:
    payload = data.copy()
    payload.update({
        "exp": datetime.now(timezone.utc) + expires,
        "type": token_type,
    })
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_access_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(minutes=settings.access_token_minutes),
        "access",
    )

def create_refresh_token(user_id: int) -> str:
    return _create_token(
        {"sub": str(user_id)},
        timedelta(days=settings.refresh_token_days),
        "refresh",
    )

def decode_token(token: str, expected_type: str = "access") -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            return None
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError):
        return None
