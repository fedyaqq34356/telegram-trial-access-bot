"""Вывод средств агентства: реквизиты и сам вывод на "мировом" сервере Halo Live.

Домен/порт мира, имя аккаунта и пароль для этого шага — отдельные от логина
в панель admin.livegirl.me, задаются один раз в настройках агентства (CRM)."""
import logging
import random
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20

class WithdrawError(Exception):
    pass

def _gen_request_id() -> str:
    # Похоже на формат, который использует lib.iwlive.club: <epoch_ms><произвольный хвост>
    return f"{int(datetime.now(timezone.utc).timestamp() * 1000)}{random.randint(100, 999)}050999999999"

def _browser_headers() -> dict:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0",
        "Origin": "https://lib.iwlive.club",
        "Referer": "https://lib.iwlive.club/",
        "X-Request-ID": _gen_request_id(),
    }

def _mask(params: dict) -> dict:
    return {k: ("***" if k == "password" else v) for k, v in params.items()}

def _log_request(tag: str, method: str, url: str, headers: dict, params: dict | None, json_body: dict | None):
    logger.warning(
        f"[withdraw-debug] --> {tag} {method} {url}\n"
        f"  headers: {dict(headers)}\n"
        f"  params: {_mask(params or {})}\n"
        f"  json_body: {json_body}"
    )

def _log_response(tag: str, r: requests.Response):
    logger.warning(
        f"[withdraw-debug] <-- {tag} status={r.status_code}\n"
        f"  response_headers: {dict(r.headers)}\n"
        f"  raw_body: {r.text[:3000]}"
    )

def get_withdraw_info(domain: str, port: int, agent_name: str) -> dict:
    """Реквизиты вывода (адрес USDT и т.п.), которые Halo хранит для агента."""
    url = f"https://{domain}:{port}/api/AccountV2/GetAgentWithdrawInfo"
    params = {"agent": agent_name, "t": datetime.now(timezone.utc).isoformat()}
    headers = _browser_headers()
    _log_request("GetAgentWithdrawInfo", "GET", url, headers, params, None)
    try:
        r = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        _log_response("GetAgentWithdrawInfo", r)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning(f"[withdraw-debug] GetAgentWithdrawInfo исключение: {e!r}")
        raise WithdrawError(f"Не удалось получить реквизиты вывода: {e}") from e

    if data.get("retCode") != 0:
        raise WithdrawError(data.get("message") or "Ошибка получения реквизитов вывода")

    info = data.get("data") or {}
    usdt = info.get("withdrawAccountUSDT")
    if not usdt or not usdt.get("address"):
        raise WithdrawError("У агентства не задан адрес USDT для вывода на стороне Halo Live")

    return {
        "address": usdt["address"],
        "network": usdt.get("network", "TRX"),
        "raw": info,
    }

def withdraw_by_agent(domain: str, port: int, account_name: str, password: str,
                        token: str, address: str, network: str) -> dict:
    """Сам вывод. Необратимо — вызывать только после подтверждения адмном суммы/адреса."""
    url = f"https://{domain}:{port}/api/AccountV2/WithdrawByAgent"
    params = {"accountName": account_name, "password": password}
    headers = {**_browser_headers(), "Content-Type": "application/json;charset=UTF-8"}
    body = {
        "withdrawType": 10,
        "withdrawAccountUSDT": {"address": address, "network": network},
        "token": token,
    }
    _log_request("WithdrawByAgent", "POST", url, headers, params, body)
    try:
        r = requests.post(url, params=params, json=body, headers=headers, timeout=REQUEST_TIMEOUT)
        _log_response("WithdrawByAgent", r)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning(f"[withdraw-debug] WithdrawByAgent исключение: {e!r}")
        raise WithdrawError(f"Не удалось выполнить вывод: {e}") from e

    if data.get("retCode") != 0:
        raise WithdrawError(data.get("message") or "Halo Live отклонил вывод")

    return data

def withdraw_by_agent_variant(variant: str, domain: str, port: int, account_name: str, password: str,
                                token: str, address: str, network: str) -> dict:
    """Пробует ОДИН конкретный вариант формы запроса — для диагностики. Возвращает
    {'ok': bool, 'retCode': ..., 'message': ..., 'raw': ...} и никогда не бросает исключение
    наружу (чтобы перебор мог продолжаться дальше по списку)."""
    url = f"https://{domain}:{port}/api/AccountV2/WithdrawByAgent"
    base_body = {
        "withdrawType": 10,
        "withdrawAccountUSDT": {"address": address, "network": network},
        "token": token,
    }

    if variant == "matched_har":
        # Максимально точное повторение реального перехвата: креды в query,
        # тело JSON, полный набор "браузерных" заголовков.
        params = {"accountName": account_name, "password": password}
        headers = {**_browser_headers(), "Content-Type": "application/json;charset=UTF-8"}
        kwargs = dict(params=params, json=base_body, headers=headers)

    elif variant == "no_browser_headers":
        # То же самое, но без Origin/Referer/User-Agent/X-Request-ID — совсем "голый" запрос.
        params = {"accountName": account_name, "password": password}
        headers = {"Content-Type": "application/json;charset=UTF-8", "Accept": "application/json"}
        kwargs = dict(params=params, json=base_body, headers=headers)

    elif variant == "creds_in_body":
        # Креды не в query, а прямо в теле JSON вместе с остальным.
        headers = {**_browser_headers(), "Content-Type": "application/json;charset=UTF-8"}
        body = {**base_body, "accountName": account_name, "password": password}
        kwargs = dict(json=body, headers=headers)

    elif variant == "form_encoded":
        # Всё как form-urlencoded, без query-параметров.
        headers = {**_browser_headers(), "Content-Type": "application/x-www-form-urlencoded"}
        import json as _json
        form = {
            "accountName": account_name,
            "password": password,
            "withdrawType": 10,
            "withdrawAccountUSDT": _json.dumps({"address": address, "network": network}),
            "token": token,
        }
        kwargs = dict(data=form, headers=headers)

    elif variant == "no_origin_referer":
        # Только UA + X-Request-ID, без Origin/Referer (вдруг именно они триггерят анти-фрод).
        headers = _browser_headers()
        headers.pop("Origin", None)
        headers.pop("Referer", None)
        headers["Content-Type"] = "application/json;charset=UTF-8"
        params = {"accountName": account_name, "password": password}
        kwargs = dict(params=params, json=base_body, headers=headers)

    else:
        raise ValueError(f"unknown variant {variant}")

    _log_request(f"WithdrawByAgent[{variant}]", "POST", url, kwargs.get("headers", {}),
                 kwargs.get("params"), kwargs.get("json") or kwargs.get("data"))
    try:
        r = requests.post(url, timeout=REQUEST_TIMEOUT, **kwargs)
        _log_response(f"WithdrawByAgent[{variant}]", r)
        data = r.json()
        return {"ok": data.get("retCode") == 0, "retCode": data.get("retCode"),
                "message": data.get("message"), "raw": data}
    except Exception as e:
        logger.warning(f"[withdraw-debug] WithdrawByAgent[{variant}] исключение: {e!r}")
        return {"ok": False, "retCode": None, "message": str(e), "raw": None}
