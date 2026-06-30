"""Синхронизация данных из Halo Live в локальный кеш (таблица hosts)."""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Agency, Host
from .halo_parser import SESSION_EXPIRED, HaloLiveParser, normalize_host
from .sessions import sessions

logger = logging.getLogger(__name__)

def _save_session_cookies(db: Session, agency: Agency, parser: HaloLiveParser) -> None:
    cookies = parser.get_cookies()
    agency.phpsessid = cookies.get("PHPSESSID", agency.phpsessid)
    agency.acuid = cookies.get("acuid", agency.acuid)
    agency.cookies_json = json.dumps(cookies)
    agency.session_updated_at = datetime.now(timezone.utc)
    db.commit()

def ensure_session(db: Session, agency: Agency, tfa_code: str | None = None) -> str:
    """Гарантирует живую сессию для агентства.

    Возвращает: 'ok' | 'need_tfa' | 'login_failed' | 'timeout' | 'network'.
    """
    parser = sessions.get_active(agency.id)
    if parser and parser.is_logged_in:
        return "ok"

    if not tfa_code and (agency.cookies_json or agency.phpsessid or agency.acuid):
        candidate = HaloLiveParser(agency.url, agency.account, agency.password, agency.aemail, agency.apassword)
        stored = {}
        if agency.cookies_json:
            try:
                stored = json.loads(agency.cookies_json)
            except Exception:
                stored = {}
        ok = candidate.restore_all_cookies(stored) if stored else \
            candidate.restore_from_cookies(agency.phpsessid, agency.acuid)
        if ok:
            sessions.set_active(agency.id, candidate)
            return "ok"

    parser = sessions.get_pending(agency.id) or HaloLiveParser(
        agency.url, agency.account, agency.password, agency.aemail, agency.apassword
    )
    result = parser.login(tfa_code)

    if result is True:
        sessions.set_active(agency.id, parser)
        _save_session_cookies(db, agency, parser)
        return "ok"
    if result == "need_tfa":
        sessions.set_pending(agency.id, parser)
        return "need_tfa"
    if result in ("timeout", "network"):
        return result
    return "login_failed"

def sync_agency(db: Session, agency: Agency) -> dict:
    """Тянет данные одного агентства и обновляет кеш. Возвращает статус."""
    status = ensure_session(db, agency)
    if status != "ok":
        return {"agency": agency.name, "status": status, "count": 0}

    parser = sessions.get_active(agency.id)
    raw = parser.fetch_all_hosts()
    if raw is SESSION_EXPIRED:
        sessions.drop_active(agency.id)
        agency.phpsessid = ""
        agency.acuid = ""
        db.commit()
        return {"agency": agency.name, "status": "session_expired", "count": 0}

    count = persist_hosts(db, agency, raw)

    try:
        bal = parser.get_agent_balance()
        agency.withdrawable_coins = bal.get("coins", 0)
    except Exception as e:
        logger.warning(f"get_agent_balance {agency.name}: {e}")

    db.commit()
    _save_session_cookies(db, agency, parser)
    return {"agency": agency.name, "status": "ok", "count": count}

def persist_hosts(db: Session, agency: Agency, raw: list) -> int:
    """Сохраняет свежий список девушек из Halo в локальный кеш (таблица hosts).

    Вынесено отдельно, чтобы Split мог обновить отображаемые в CRM данные «на лету»
    (свежие данные перед сплитом — как перезагрузка официальной панели)."""
    existing = {h.display_account_id: h for h in db.query(Host).filter(Host.agency_id == agency.id).all()}
    seen = set()
    count = 0
    for raw_host in raw:
        data = normalize_host(raw_host)
        did = data["display_account_id"]
        if not did:
            continue
        seen.add(did)
        host = existing.get(did)
        if host is None:
            host = Host(agency_id=agency.id, display_account_id=did)
            db.add(host)
        for key, value in data.items():
            setattr(host, key, value)
        count += 1

    for did, host in existing.items():
        if did not in seen:
            db.delete(host)

    agency.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return count

def sync_all(db: Session, agency_ids: list[int] | None = None) -> list[dict]:
    query = db.query(Agency).filter(Agency.is_active == True)
    if agency_ids is not None:
        query = query.filter(Agency.id.in_(agency_ids))
    results = []
    for agency in query.all():
        try:
            results.append(sync_agency(db, agency))
        except Exception as e:
            logger.error(f"sync_agency {agency.name} failed: {e}")
            results.append({"agency": agency.name, "status": "error", "count": 0})
    return results
