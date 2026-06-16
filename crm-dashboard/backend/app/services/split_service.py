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

# splitCoins ВСЕГДА отвечает code:0 (даже когда сплитить нечего), а доля агентства
# зачисляется в баланс с НЕПРЕДСКАЗУЕМОЙ задержкой (трикл 15-30с) — по ответу и по
# балансу в реальном времени реальный сплит не определить.
#
# Надёжный признак: после РЕАЛЬНОГО сплита поле Diamond девушки в списке обнуляется
# (оседает за ~10-20с), а у фантома (сплитить было нечего) — остаётся прежним.
# Поэтому: сплитим → ждём оседания списка → перечитываем → у кого Diamond упал, тот
# сплитнут реально, и его доля = Diamond_до × ratio (точная формула, проверено
# на живых данных: 760→152, 307→61, сумма = реальная дельта баланса).
#
# Кулдаун обязателен: в окне быстрых повторных кликов список показывает stale-high
# Diamond уже сплитнутой девушки; без кулдауна он за наши 25с осядет до 0 и даст
# ЛОЖНО-положительный «реальный сплит». Кулдаун пропускает недавно сплитнутых.
RESPLIT_COOLDOWN = 120.0      # не сплитить ту же девушку повторно в течение, сек
LIST_SETTLE_SECONDS = 25.0    # ждать оседания списка Diamond перед проверкой
DROP_FRACTION = 0.5           # Diamond упал ниже этой доли от исходного → реальный сплит
# Halo лимитит частоту сплитов: за один заход проходит не всё, остальные отвечают code:0,
# но реально не списываются. Поэтому не принятых (Diamond не упал) повторяем несколькими
# раундами с паузой — почти всегда берёт со 2-3 попытки в рамках ОДНОГО прогона.
SPLIT_GAP = 2.0               # пауза между отдельными вызовами splitCoins, сек
SPLIT_MAX_ROUNDS = 6          # раундов повтора не принятых Halo (~25с каждый → до ~2.5 мин)
# Кулдаун на агентство: повторный сплит ОДНОГО агентства не раньше, чем через 15 мин.
# У каждого агентства свой независимый таймер (хранится в Agency.last_split_at).
SPLIT_AGENCY_COOLDOWN = 15 * 60   # сек
_recent_splits: dict[tuple[int, str], float] = {}
_recent_lock = threading.Lock()


def agency_cooldown_remaining(agency: Agency) -> int:
    """Сколько секунд осталось до следующего разрешённого сплита этого агентства (0 = можно)."""
    ts = agency.last_split_at
    if not ts:
        return 0
    if ts.tzinfo is None:                      # из SQLite приходит naive — считаем как UTC
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
        # подчистка старых записей, чтобы словарь не рос
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
        except Exception as e:  # noqa: BLE001
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
        # Кулдаун 15 мин на агентство: повторный сплит того же агентства блокируется.
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

        # Фиксируем момент сплита СРАЗУ — кулдаун стартует с начала прогона и блокирует
        # повторные клики, пока агентство обрабатывается (~80с).
        agency.last_split_at = datetime.now(timezone.utc)
        db.commit()

        parser = sessions.get_active(agency.id)
        # Свежие данные перед сплитом: «перезагружаем» панель и тянем актуальный список.
        parser.refresh_panel()
        raw = parser.fetch_all_hosts()
        if raw is SESSION_EXPIRED:
            sessions.drop_active(agency.id)
            errors += 1
            per_agency.append({"agency": agency.name, "status": "session_expired"})
            bump("ошибка получения данных")
            continue
        # Сохраняем свежие данные в кеш CRM, чтобы отображение тоже обновилось.
        try:
            persist_hosts(db, agency, raw)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"persist_hosts {agency.name}: {e}")

        # attempted: {account_id: (balance_до, frac, name)} — все, кому отправили splitCoins
        attempted: dict[str, tuple[int, float, str]] = {}

        for raw_host in raw:
            data = normalize_host(raw_host)
            if not show_blocked and is_host_blocked(data["ban_status"]):
                a_skipped += 1
                bump("пользователь заблокирован")
                continue
            # Сплитятся ТЕКУЩИЕ pending-коины = поле Diamond (balance_coins).
            # SplitDiamond — это УЖЕ сплитнутые коины (трогать нельзя, иначе ложный успех).
            balance = data["balance_coins"]
            if balance < min_balance:
                a_skipped += 1
                bump("баланс ниже лимита")
                continue
            # Halo блокирует сплит при dislike rate >= 0.4. Dislike rate = DownRate (не ReceiveRate!)
            if data["down_rate"] >= skip_receive:
                a_skipped += 1
                bump("высокий коэффициент дизлайков")
                continue
            account_id = data["account_id"]
            # Кулдаун: список Diamond отстаёт, повторный сплит недавно сплитнутой = ложный успех.
            if _recently_split(agency.id, account_id):
                a_skipped += 1
                bump("уже сплитнута недавно")
                continue
            # splitCoins ждёт ВНУТРЕННИЙ AccountId (подтверждено перехватом JS)
            res = parser.split_one(account_id)
            if not res["ok"]:
                a_errors += 1
                if res["code"] == -1:
                    sessions.drop_active(agency.id)
                    bump("ошибка выполнения операции")
                continue
            # code:0 = запрос принят. Реальность проверим по падению Diamond ниже.
            _mark_split(agency.id, account_id)
            frac = min(max(int(data.get("ratio") or 0) / 10000.0, 0.0), 0.99)
            attempted[account_id] = (balance, frac, data.get("nickname") or account_id)
            time.sleep(SPLIT_GAP)

        # Подтверждаем сплиты по падению Diamond и ПОВТОРЯЕМ не принятых Halo (rate-limit).
        pending = dict(attempted)   # account_id -> (bal0, frac, name) — ещё не подтверждённые
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
            # засчитываем тех, у кого Diamond реально упал
            for account_id, (bal0, frac, name) in list(pending.items()):
                nd = new_diamond.get(account_id, bal0)
                if nd < bal0 * DROP_FRACTION:        # Diamond списан → реальный сплит
                    a_processed += 1
                    a_total += bal0
                    a_agency += round(bal0 * frac)
                    pending.pop(account_id)
            if not pending or rounds >= SPLIT_MAX_ROUNDS:
                break
            # повторяем оставшихся (Halo не принял с первого раза), разнося по времени
            for account_id in list(pending):
                r = parser.split_one(account_id)
                if not r["ok"] and r["code"] == -1:
                    sessions.drop_active(agency.id)
                    break
                time.sleep(SPLIT_GAP)

        # не принятые Halo после всех раундов
        for account_id in pending:
            a_skipped += 1
            bump("сплит не выполнен (Halo не принял, повторите позже)")

        # Обновляем «Готово к выводу» (баланс растёт с задержкой, но к следующему sync осядет).
        try:
            agency.withdrawable_coins = parser.get_agent_balance().get("coins", agency.withdrawable_coins)
        except Exception:
            pass

        # сворачиваем agency-local в глобальные итоги
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
