import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..audit import log_action
from ..database import get_db
from ..deps import can_perform, can_view_agency, get_current_user
from ..models import Agency, User, WithdrawOperation
from ..services.net_debug import egress_ip, fingerprint
from ..services.sessions import sessions
from ..services.sync_service import ensure_session
from ..services.withdraw_service import (
    WithdrawError, get_withdraw_info, withdraw_by_agent, withdraw_by_agent_variant,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/withdraw", tags=["withdraw"])

def _client_info(request: Request | None) -> dict:
    """Кто и откуда дёрнул ручку. Нужно, чтобы сопоставить IP браузера администратора
    с egress-IP сервера — на этом расхождении и держится гипотеза про retCode -117."""
    if request is None:
        return {}
    return {
        "client_ip": request.client.host if request.client else None,
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "x_real_ip": request.headers.get("x-real-ip"),
        "user_agent": request.headers.get("user-agent"),
        "origin": request.headers.get("origin"),
        "referer": request.headers.get("referer"),
    }

def _dump(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)[:20000]
    except Exception:
        return repr(value)[:20000]

MIN_WITHDRAW_USD = 100.0

DIAGNOSTIC_VARIANTS = ["matched_har", "no_browser_headers", "creds_in_body", "form_encoded", "no_origin_referer"]

def _agency_or_404(db: Session, agency_id: int) -> Agency:
    agency = db.get(Agency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    return agency

def _require_withdraw_access(db: Session, user: User, agency_id: int) -> None:
    if not can_view_agency(db, user, agency_id):
        raise HTTPException(status_code=404, detail="Агентство не найдено")
    if not can_perform(db, user, agency_id, "can_withdraw"):
        raise HTTPException(status_code=403, detail="У вас нет прав на вывод средств для этого агентства")

def _check_configured(agency: Agency) -> None:
    if not (agency.withdraw_account_name and agency.withdraw_password
            and agency.withdraw_domain and agency.withdraw_port
            and agency.withdraw_info_domain and agency.withdraw_info_port):
        raise HTTPException(
            status_code=400,
            detail="Для этого агентства не заданы реквизиты вывода — заполните их в настройках агентства",
        )

def _serialize(op: WithdrawOperation) -> dict:
    return {
        "id": op.id,
        "agency_id": op.agency_id,
        "agency_name": op.agency_name,
        "network": op.network,
        "address": op.address,
        "status": op.status,
        "message": op.message,
        "created_at": op.created_at.isoformat() if op.created_at else None,
        "finished_at": op.finished_at.isoformat() if op.finished_at else None,
    }

def _do_preview(db: Session, agency: Agency) -> dict:
    status = ensure_session(db, agency)
    if status != "ok":
        return {"status": status}

    parser = sessions.get_active(agency.id)

    balance = parser.get_agent_balance()
    if balance["usd"] < MIN_WITHDRAW_USD:
        return {
            "status": "insufficient_balance",
            "balance_usd": balance["usd"],
            "min_withdraw_usd": MIN_WITHDRAW_USD,
        }

    # Токен выписывается на КОНКРЕТНОГО агента, и мировой сервер потом сверяет его
    # с accountName. agency.name — это отображаемое имя в CRM («Tos Agency»), оно может
    # не совпадать с именем агента в Halo («TosAgency-Ukraine»). createWithdrawToken имя
    # не валидирует (любая строка даёт code:0), поэтому расхождение всплывает только
    # на самом выводе как retCode -117.
    token = parser.create_withdraw_token(agency.withdraw_account_name or agency.name)
    if not token:
        raise HTTPException(status_code=502, detail="Не удалось получить токен на вывод у Halo Live")

    try:
        info = get_withdraw_info(agency.withdraw_info_domain, agency.withdraw_info_port, agency.withdraw_account_name)
    except WithdrawError as e:
        raise HTTPException(status_code=502, detail=str(e))

    logger.warning(
        "[withdraw-debug] preview готов: agency=%s token_fp=%s address_fp=%s network=%s "
        "balance_usd=%s egress_ip_сервера(тот_же_IP_создал_токен)=%s",
        agency.name, fingerprint(token), fingerprint(info["address"]), info["network"],
        balance["usd"], egress_ip(),
    )

    sessions.set_pending_withdraw(agency.id, token, info["address"], info["network"])
    return {
        "status": "ready",
        "address": info["address"],
        "network": info["network"],
        "balance_usd": balance["usd"],
    }

@router.post("/{agency_id}/preview")
def preview(agency_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Готовит вывод: логинится в панель (если нужно — вернёт need_tfa), проверяет баланс
    (минимум $100 у Halo Live), получает токен и адрес для подтверждения — деньги ещё НЕ списаны."""
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)
    _check_configured(agency)
    return _do_preview(db, agency)

@router.post("/verify-2fa")
def verify_2fa_and_preview(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    agency_id = payload.get("agency_id")
    code = payload.get("code")
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)
    result = ensure_session(db, agency, tfa_code=code)
    if result != "ok":
        raise HTTPException(status_code=400, detail=f"Не удалось войти: {result}")
    return _do_preview(db, agency)

@router.post("/{agency_id}/confirm")
def confirm(agency_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Выполняет реальный вывод по токену, полученному в /preview, ПРЯМО С СЕРВЕРА.
    Оставлено для сравнения/отладки — рабочий путь для реального вывода теперь
    /client-request + /client-result (см. ниже). Необратимо."""
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)

    pending = sessions.get_pending_withdraw(agency_id)
    if not pending:
        raise HTTPException(status_code=400, detail="Токен вывода истёк или не был запрошен — начните заново")

    op = WithdrawOperation(
        user_id=user.id,
        agency_id=agency_id,
        agency_name=agency.name,
        network=pending["network"],
        address=pending["address"],
        status="running",
    )
    db.add(op)
    db.commit()
    db.refresh(op)

    try:
        withdraw_by_agent(
            agency.withdraw_domain, agency.withdraw_port,
            agency.withdraw_account_name, agency.withdraw_password,
            pending["token"], pending["address"], pending["network"],
        )
        op.status = "ok"
        op.message = "Успешно"
    except WithdrawError as e:
        op.status = "error"
        op.message = str(e)
    finally:
        sessions.drop_pending_withdraw(agency_id)
        op.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(op)

    log_action(
        db, user, "withdraw", agency_name=agency.name,
        status=op.status, message=op.message,
        target=pending["address"],
    )

    if op.status != "ok":
        raise HTTPException(status_code=502, detail=op.message)
    return _serialize(op)

@router.post("/{agency_id}/client-request")
def client_request(agency_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Отдаёт браузеру администратора готовый запрос WithdrawByAgent, чтобы тот выполнил
    его сам, со своего устройства.

    Halo Live принимает финальный вызов вывода только с обычного IP: тот же самый запрос
    с этого сервера стабильно получает retCode -117 (см. информация.md). Логин, 2FA,
    токен и реквизиты по-прежнему делает бэкенд — наружу уходит только последний шаг.

    Операция сразу пишется в историю со статусом running; результат браузер возвращает
    в /client-result.
    """
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)
    _check_configured(agency)

    pending = sessions.get_pending_withdraw(agency_id)
    if not pending:
        raise HTTPException(status_code=400, detail="Токен вывода истёк или не был запрошен — начните заново")

    op = WithdrawOperation(
        user_id=user.id,
        agency_id=agency_id,
        agency_name=agency.name,
        network=pending["network"],
        address=pending["address"],
        status="running",
    )
    db.add(op)
    db.commit()
    db.refresh(op)

    client_info = _client_info(request)
    logger.warning(
        "[withdraw-debug] client-request отдан браузеру: agency=%s op_id=%s token_fp=%s "
        "address_fp=%s\n"
        "  client_info (IP/UA браузера админа, из этого же IP уйдёт запрос к Halo): %s\n"
        "  egress_ip_сервера (тот_IP, с которого был создан токен): %s",
        agency.name, op.id, fingerprint(pending["token"]), fingerprint(pending["address"]),
        client_info, egress_ip(),
    )

    query = urlencode({"accountName": agency.withdraw_account_name, "password": agency.withdraw_password})
    return {
        "op_id": op.id,
        "url": f"https://{agency.withdraw_domain}:{agency.withdraw_port}/api/AccountV2/WithdrawByAgent?{query}",
        # Только Content-Type: в CORS-преflight Halo Live разрешает единственный заголовок
        # (access-control-allow-headers: content-type), любой лишний — и браузер заблокирует
        # запрос ещё до отправки. Origin/Referer/User-Agent браузер проставит сам.
        "headers": {"Content-Type": "application/json;charset=UTF-8"},
        "body": {
            "withdrawType": 10,
            "withdrawAccountUSDT": {"address": pending["address"], "network": pending["network"]},
            "token": pending["token"],
        },
        "address": pending["address"],
        "network": pending["network"],
    }

@router.post("/{agency_id}/client-result")
def client_result(agency_id: int, payload: dict, request: Request, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Принимает от браузера исход вывода, выполненного через /client-request, и закрывает
    операцию в истории. Проверить результат независимо нельзя — у Halo Live нет API истории
    выводов, так что запись опирается на то, что вернул браузер."""
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)

    op = db.get(WithdrawOperation, payload.get("op_id") or 0)
    if op is None or op.agency_id != agency_id:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    if op.status != "running":
        raise HTTPException(status_code=400, detail="Эта операция уже завершена")

    ret_code = payload.get("ret_code")
    message = (payload.get("message") or "").strip()
    client_info = _client_info(request)

    elapsed_s = None
    try:
        created = op.created_at
        if created is not None:
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            elapsed_s = round((now_naive - created).total_seconds(), 2)
    except Exception:
        elapsed_s = None

    logger.warning(
        "[withdraw-debug] client-result получен: agency=%s op_id=%s ret_code=%s message=%s\n"
        "  client_info (должен совпадать по IP с тем, что было в client-request): %s\n"
        "  egress_ip_сервера (для справки, сервер тут ни при чём — запрос шёл из браузера): %s\n"
        "  elapsed_s_с_момента_client-request: %s\n"
        "  raw_payload_от_браузера: %s",
        agency.name, op.id, ret_code, message, client_info, egress_ip(), elapsed_s, _dump(payload),
    )

    if ret_code == 0:
        op.status = "ok"
        op.message = "Успешно (вывод выполнен из браузера администратора)"
    else:
        op.status = "error"
        op.message = message or f"Halo Live отклонил вывод (retCode {ret_code})"

    op.finished_at = datetime.now(timezone.utc)
    sessions.drop_pending_withdraw(agency_id)
    db.commit()
    db.refresh(op)

    log_action(
        db, user, "withdraw", agency_name=agency.name,
        status=op.status, message=op.message, target=op.address,
    )
    return _serialize(op)

@router.post("/{agency_id}/diagnose")
def diagnose(agency_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Перебирает несколько форм запроса WithdrawByAgent подряд, каждый раз со свежим
    токеном, и логирует всё в journalctl. Останавливается на первом успехе (если он
    случится — деньги реально уйдут по этому варианту, дальнейшие остановятся)."""
    _require_withdraw_access(db, user, agency_id)
    agency = _agency_or_404(db, agency_id)
    _check_configured(agency)

    status = ensure_session(db, agency)
    if status != "ok":
        return {"status": status}

    parser = sessions.get_active(agency.id)
    results = []
    for variant in DIAGNOSTIC_VARIANTS:
        token = parser.create_withdraw_token(agency.withdraw_account_name or agency.name)
        if not token:
            results.append({"variant": variant, "error": "не удалось получить токен"})
            continue
        try:
            info = get_withdraw_info(agency.withdraw_info_domain, agency.withdraw_info_port, agency.withdraw_account_name)
        except WithdrawError as e:
            results.append({"variant": variant, "error": f"не удалось получить реквизиты: {e}"})
            continue

        outcome = withdraw_by_agent_variant(
            variant, agency.withdraw_domain, agency.withdraw_port,
            agency.withdraw_account_name, agency.withdraw_password,
            token, info["address"], info["network"],
        )
        results.append({"variant": variant, **outcome})

        if outcome["ok"]:
            op = WithdrawOperation(
                user_id=user.id, agency_id=agency_id, agency_name=agency.name,
                network=info["network"], address=info["address"],
                status="ok", message=f"Успешно (диагностика, вариант: {variant})",
                finished_at=datetime.now(timezone.utc),
            )
            db.add(op)
            db.commit()
            log_action(db, user, "withdraw", agency_name=agency.name, status="ok",
                       message=f"diagnose:{variant}", target=info["address"])
            break

    return {"status": "done", "results": results}

@router.get("/history")
def history(
    agency_id: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WithdrawOperation)
    if agency_id is not None:
        if not can_perform(db, user, agency_id, "can_withdraw"):
            raise HTTPException(status_code=403, detail="Нет доступа")
        q = q.filter(WithdrawOperation.agency_id == agency_id)
    elif not user.is_superadmin:
        from ..deps import accessible_agency_ids
        allowed_ids = [
            aid for aid in accessible_agency_ids(db, user)
            if can_perform(db, user, aid, "can_withdraw")
        ]
        q = q.filter(WithdrawOperation.agency_id.in_(allowed_ids or [-1]))
    total = q.count()
    ops = q.order_by(WithdrawOperation.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [_serialize(o) for o in ops], "total": total, "page": page, "limit": limit}
