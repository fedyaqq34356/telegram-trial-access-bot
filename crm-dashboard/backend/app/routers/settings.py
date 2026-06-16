import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_superadmin
from ..models import User
from ..schemas import SettingsUpdate
from ..services import app_settings, scheduler

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = app_settings.get_all_settings(db)
    grade_config = app_settings.get_grade_config(db)
    return {**data, "grade_config": grade_config}


@router.put("")
def update_settings(payload: SettingsUpdate, admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    for key, value in payload.values.items():
        if key == "grade_config":
            # валидируем JSON
            try:
                json.loads(value)
            except Exception:
                raise HTTPException(status_code=400, detail="grade_config: невалидный JSON")
        app_settings.set_setting(db, key, value)

    if "sync_interval_minutes" in payload.values:
        try:
            scheduler.reschedule(int(float(payload.values["sync_interval_minutes"])))
        except Exception:
            pass

    data = app_settings.get_all_settings(db)
    return {**data, "grade_config": app_settings.get_grade_config(db)}
