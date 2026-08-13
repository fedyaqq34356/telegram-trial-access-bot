"""Служебное для разбора отказа Halo Live retCode -117 на выводе средств.

Две вещи, которых не хватало в логах:

- `egress_ip()` — с какого внешнего IP сервер уходит наружу. Токен на вывод создаёт сервер,
  а сам вывод выполняет браузер администратора со своего IP. Чтобы проверить гипотезу
  «Halo привязывает токен к IP, из которого он создан», оба IP должны быть в логах рядом.
- `fingerprint()` — короткий отпечаток секрета. В журнал нельзя писать живые токены и
  cookie, но нужно понимать «то же значение или другое» — отпечаток это даёт.
"""
import hashlib
import logging

import requests

logger = logging.getLogger(__name__)

_CACHED_IP: str | None = None

def egress_ip() -> str:
    """Внешний IP сервера. Определяется один раз за процесс и кэшируется."""
    global _CACHED_IP
    if _CACHED_IP is not None:
        return _CACHED_IP
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            r = requests.get(url, timeout=4)
            if r.ok and r.text.strip():
                _CACHED_IP = r.text.strip()
                logger.warning(f"[withdraw-debug] egress_ip={_CACHED_IP} (определён через {url})")
                return _CACHED_IP
        except Exception as e:
            logger.warning(f"[withdraw-debug] egress_ip через {url} не вышло: {e!r}")
    _CACHED_IP = "unknown"
    return _CACHED_IP

def fingerprint(value) -> str:
    """Короткий стабильный отпечаток вместо самого секрета: sha256, первые 12 символов."""
    if value is None:
        return "none"
    text = str(value)
    if not text:
        return "empty"
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]
