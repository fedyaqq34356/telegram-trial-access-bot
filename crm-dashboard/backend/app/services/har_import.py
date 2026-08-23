"""Разбор HAR-файла для автозаполнения реквизитов вывода агентства.

Пользователь один раз делает реальный вывод через lib.iwlive.club с открытым
DevTools → Network, сохраняет весь лог как HAR и загружает его в CRM. Отсюда
достаём всё, что нужно для шага 3 (GetAgentWithdrawInfo) и шага 4 (WithdrawByAgent):
домены/порты «мировых» серверов и креды accountName/password самого вывода.

Ничего не пишем в БД — только возвращаем найденное, чтобы форма агентства
подставила значения, а супер-админ их проверил и сохранил обычным способом."""
import json
import logging
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__name__)

class HarImportError(Exception):
    pass

def _iter_entries(har: dict):
    log = har.get("log") if isinstance(har, dict) else None
    entries = (log or {}).get("entries") if isinstance(log, dict) else None
    if not isinstance(entries, list):
        raise HarImportError("Файл не похож на HAR: нет log.entries")
    for e in entries:
        req = (e or {}).get("request") or {}
        url = req.get("url") or ""
        if url:
            yield req, url

def _host_port(url: str) -> tuple[str, int]:
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = parts.port or (443 if parts.scheme == "https" else 80)
    return host, int(port)

def _query_creds(req: dict, url: str) -> tuple[str, str]:
    """accountName/password вывода лежат в query WithdrawByAgent; на всякий случай
    смотрим и в теле запроса, если вдруг перенесены туда."""
    q = parse_qs(urlsplit(url).query)
    account = (q.get("accountName") or [""])[0]
    password = (q.get("password") or [""])[0]
    if account and password:
        return account, password
    post = req.get("postData") or {}
    for p in post.get("params") or []:
        if p.get("name") == "accountName" and not account:
            account = p.get("value") or ""
        if p.get("name") == "password" and not password:
            password = p.get("value") or ""
    text = post.get("text") or ""
    if text and (not account or not password):
        try:
            body = json.loads(text)
            account = account or body.get("accountName") or ""
            password = password or body.get("password") or ""
        except Exception:
            pass
    return account, password

def _trusted_device(req: dict) -> str:
    """Кука trusted_device из запросов к admin.livegirl.me, если попала в HAR."""
    for h in req.get("headers") or []:
        if (h.get("name") or "").lower() == "cookie":
            for chunk in (h.get("value") or "").split(";"):
                k, _, v = chunk.strip().partition("=")
                if k == "trusted_device" and v:
                    return v
    return ""

def parse_har(raw: bytes) -> dict:
    """Возвращает найденные реквизиты вывода. Бросает HarImportError, если
    ключевой запрос WithdrawByAgent в логе не найден."""
    try:
        har = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:
        raise HarImportError(f"Не удалось разобрать JSON HAR: {e}") from e

    result = {
        "withdraw_account_name": "", "withdraw_password": "",
        "withdraw_domain": "", "withdraw_port": 0,
        "withdraw_info_domain": "", "withdraw_info_port": 0,
        "trusted_device_cookie": "",
    }
    found_withdraw = False

    for req, url in _iter_entries(har):
        if "WithdrawByAgent" in url:
            host, port = _host_port(url)
            account, password = _query_creds(req, url)
            result["withdraw_domain"] = host
            result["withdraw_port"] = port
            if account:
                result["withdraw_account_name"] = account
            if password:
                result["withdraw_password"] = password
            found_withdraw = True
        elif "GetAgentWithdrawInfo" in url:
            host, port = _host_port(url)
            result["withdraw_info_domain"] = host
            result["withdraw_info_port"] = port
        if not result["trusted_device_cookie"] and "admin.livegirl.me" in url:
            td = _trusted_device(req)
            if td:
                result["trusted_device_cookie"] = td

    if not found_withdraw:
        raise HarImportError(
            "В HAR не найден запрос WithdrawByAgent — убедитесь, что вывод "
            "реально выполнялся при записи (DevTools → Network → Export HAR)"
        )
    if not result["withdraw_account_name"] or not result["withdraw_password"]:
        raise HarImportError(
            "Запрос WithdrawByAgent найден, но в нём нет accountName/password — "
            "экспортируйте HAR «with content» и повторите"
        )

    logger.warning(
        "[har-import] извлечено: account=%s pass=*** info=%s:%s withdraw=%s:%s trusted_device=%s",
        result["withdraw_account_name"], result["withdraw_info_domain"], result["withdraw_info_port"],
        result["withdraw_domain"], result["withdraw_port"], "да" if result["trusted_device_cookie"] else "нет",
    )
    return result
