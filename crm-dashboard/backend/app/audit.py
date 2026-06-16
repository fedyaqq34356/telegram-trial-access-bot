from sqlalchemy.orm import Session

from .models import ActionLog, SecurityLog, User


def log_action(db: Session, user: User | None, action_type: str, **kwargs) -> None:
    entry = ActionLog(
        user_id=user.id if user else None,
        username=user.username if user else "",
        action_type=action_type,
        agency_name=kwargs.get("agency_name", ""),
        anchor_id=kwargs.get("anchor_id", ""),
        target=kwargs.get("target", ""),
        old_value=str(kwargs.get("old_value", "")),
        new_value=str(kwargs.get("new_value", "")),
        status=kwargs.get("status", ""),
        message=kwargs.get("message", ""),
    )
    db.add(entry)
    db.commit()


def log_security(db: Session, user: User | None, action: str, ip: str = "", ua: str = "") -> None:
    entry = SecurityLog(
        user_id=user.id if user else None,
        username=user.username if user else "",
        action=action,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(entry)
    db.commit()
