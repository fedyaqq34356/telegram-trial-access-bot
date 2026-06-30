from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..audit import log_action
from ..database import get_db
from ..deps import get_current_user, resolve_scope
from ..models import User
from ..services.sync_service import sync_all

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("")
def trigger_sync(agency_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scope = resolve_scope(db, user, agency_id)
    results = sync_all(db, scope)
    log_action(db, user, "sync", status="done", message=f"Обновлено агентств: {len(results)}")
    return {"results": results}
