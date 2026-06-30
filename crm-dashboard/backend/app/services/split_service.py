"""Логика Split: последовательная обработка девушек с балансом >= лимита."""
import json
import logging
import threading
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Agency, SplitOperation, User
from . import app_settings
from .halo_parser import SESSION_EXPIRED, normalize_host
from .levels import is_host_blocked
from .sessions import sessions
from .sync_service import ensure_session, persist_hosts

logger = logging.getLogger(__name__)

RESPLIT_COOLDOWN = 120.0
LIST_SETTLE_SECONDS = 25.0
DROP_FRACTION = 0.5
SPLIT_GAP = 2.0
SPLIT_MAX_ROUNDS = 6
SPLIT_AGENCY_COOLDOWN = 15 * 60
_recent_splits: dict[tuple[int, str], float] = {}
_recent_lock = threading.Lock()

def agency_cooldown_remaining(agency: Agency) -> int:
    """Сколько секунд осталось до следующего разрешённого сплита этого агентства (0 = можно)."""
    ts = agency.last_split_at
    if not ts:
        return 0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - ts).total_seconds()
    return max(0, int(SPLIT_AGENCY_COOLDOWN - elapsed))

def _recently_split(agency_id: int, account_id: str) -> bool:
    with _recent_lock:
        ts = _recent_splits.get((agency_id, account_id))
        return ts is not None and (time.time() - ts) < RESPLIT_COOLDOWN

def _mark_split(agency_id: int, account_id: str) -> None:
    with _recent_lock:
        now = time.time()
        _recent_splits[(agency_id, account_id)] = now
        for k, t in list(_recent_splits.items()):
            if now - t > RESPLIT_COOLDOWN * 4:
                _recent_splits.pop(k, None)

def _create_op(db: Session, user_id: int | None, agencies: list[Agency], scope_label: str) -> SplitOperation:
    op = SplitOperation(
        user_id=user_id,
        scope_label=scope_label,
        agency_id=agencies[0].id if len(agencies) == 1 else None,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(op)
    db.commit()
    db.refresh(op)
    return op

def start_split_async(user_id: int | None, agency_ids: list[int], scope_label: str) -> int:
    """Создаёт операцию Split (status=running) и запускает обработку в фоне.

    Возвращает id операции сразу — HTTP-запрос не висит 60+ сек, фронт опрашивает историю.
    """
    db = SessionLocal()
    try:
        agencies = db.query(Agency).filter(Agency.id.in_(agency_ids)).order_by(Agency.name).all()
        op = _create_op(db, user_id, agencies, scope_label)
        op_id = op.id
    finally:
        db.close()

    def worker():
        wdb = SessionLocal()
        try:
            op = wdb.get(SplitOperation, op_id)
            ags = wdb.query(Agency).filter(Agency.id.in_(agency_ids)).order_by(Agency.name).all()
            _run_loop(wdb, op, ags)
        except Exception as e:
            logger.error(f"split worker {op_id} failed: {e}")
            try:
                op = wdb.get(SplitOperation, op_id)
                if op:
                    op.status = "error"
                    op.finished_at = datetime.now(timezone.utc)
                    op.details = json.dumps({"error": str(e)}, ensure_ascii=False)
                    wdb.commit()
            except Exception:
                pass
        finally:
            wdb.close()

    threading.Thread(target=worker, daemon=True, name=f"split-{op_id}").start()
    return op_id

def run_split(db: Session, user: User | None, agencies: list[Agency], scope_label: str) -> SplitOperation:
    """Синхронный запуск (для тестов/внутреннего использования). Веб использует start_split_async."""
    op = _create_op(db, user.id if user else None, agencies, scope_label)
    return _run_loop(db, op, agencies)

def _run_loop(db: Session, op: SplitOperation, agencies: list[Agency]) -> SplitOperation:
    min_balance = int(float(app_settings.get_setting(db, "split_min_balance")))
    skip_receive = float(app_settings.get_setting(db, "split_skip_receive_rate"))
    show_blocked = app_settings.get_setting(db, "show_blocked").strip().lower() in ("1", "true", "yes", "on")

    started = time.time()
    processed = skipped = errors = total = agency_total = 0
    skip_reasons: dict[str, int] = {}
    per_agency = []

    def bump(reason: str):
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    for agency in agencies:
        a_processed = a_skipped = a_errors = a_total = a_agency = 0
        remaining = agency_cooldown_remaining(agency)
        if remaining > 0:
            mins = (remaining + 59) // 60
            per_agency.append({
                "agency": agency.name, "status": "cooldown", "cooldown_seconds": remaining,
            })
            bump(f"агентство на кулдауне (ещё ~{mins} мин)")
            continue

        status = ensure_session(db, agency)
        if status != "ok":
            errors += 1
            per_agency.append({"agency": agency.name, "status": status})
            bump("ошибка получения данных")
            continue

        agency.last_split_at = datetime.now(timezone.utc)
        db.commit()

        parser = sessions.get_active(agency.id)
        parser.refresh_panel()
        raw = parser.fetch_all_hosts()
        if raw is SESSION_EXPIRED:
            sessions.drop_active(agency.id)
            errors += 1
            per_agency.append({"agency": agency.name, "status": "session_expired"})
            bump("ошибка получения данных")
            continue
        try:
            persist_hosts(db, agency, raw)
        except Exception as e:
            logger.warning(f"persist_hosts {agency.name}: {e}")

        attempted: dict[str, tuple[int, float, str]] = {}

        for raw_host in raw:
            data = normalize_host(raw_host)
            if not show_blocked and is_host_blocked(data["ban_status"]):
                a_skipped += 1
                bump("пользователь заблокирован")
                continue
            balance = data["balance_coins"]
            if balance < min_balance:
                a_skipped += 1
                bump("баланс ниже лимита")
                continue
            if data["down_rate"] >= skip_receive:
                a_skipped += 1
                bump("высокий коэффициент дизлайков")
                continue
            account_id = data["account_id"]
            if _recently_split(agency.id, account_id):
                a_skipped += 1
                bump("уже сплитнута недавно")
                continue
            res = parser.split_one(account_id)
            if not res["ok"]:
                a_errors += 1
                if res["code"] == -1:
                    sessions.drop_active(agency.id)
                    bump("ошибка выполнения операции")
                continue
            _mark_split(agency.id, account_id)
            frac = min(max(int(data.get("ratio") or 0) / 10000.0, 0.0), 0.99)
            attempted[account_id] = (balance, frac, data.get("nickname") or account_id)
            time.sleep(SPLIT_GAP)

        pending = dict(attempted)
        rounds = 0
        while pending and rounds < SPLIT_MAX_ROUNDS:
            rounds += 1
            time.sleep(LIST_SETTLE_SECONDS)
            raw2 = parser.fetch_all_hosts()
            if raw2 is SESSION_EXPIRED:
                sessions.drop_active(agency.id)
                break
            new_diamond: dict[str, int] = {}
            for h in raw2:
                d2 = normalize_host(h)
                new_diamond[d2["account_id"]] = d2["balance_coins"]
            for account_id, (bal0, frac, name) in list(pending.items()):
                nd = new_diamond.get(account_id, bal0)
                if nd < bal0 * DROP_FRACTION:
                    a_processed += 1
                    a_total += bal0
                    a_agency += round(bal0 * frac)
                    pending.pop(account_id)
            if not pending or rounds >= SPLIT_MAX_ROUNDS:
                break
            for account_id in list(pending):
                r = parser.split_one(account_id)
                if not r["ok"] and r["code"] == -1:
                    sessions.drop_active(agency.id)
                    break
                time.sleep(SPLIT_GAP)

        for account_id in pending:
            a_skipped += 1
            bump("сплит не выполнен (Halo не принял, повторите позже)")

        try:
            agency.withdrawable_coins = parser.get_agent_balance().get("coins", agency.withdrawable_coins)
        except Exception:
            pass

        processed += a_processed
        skipped += a_skipped
        errors += a_errors
        total += a_total
        agency_total += a_agency

        per_agency.append({
            "agency": agency.name,
            "status": "ok",
            "processed": a_processed,
            "skipped": a_skipped,
            "errors": a_errors,
            "amount": a_total,
            "agency_amount": a_agency,
        })

    op.processed = processed
    op.skipped = skipped
    op.errors = errors
    op.total_amount_coins = total
    op.agency_amount_coins = agency_total
    op.duration_seconds = round(time.time() - started, 2)
    op.finished_at = datetime.now(timezone.utc)
    op.details = json.dumps({"skip_reasons": skip_reasons, "agencies": per_agency}, ensure_ascii=False)

    if errors and processed:
        op.status = "partial"
    elif errors and not processed:
        op.status = "error"
    else:
        op.status = "done"

    db.commit()
    db.refresh(op)
    return op
