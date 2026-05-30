import requests
import json
import logging

logger = logging.getLogger(__name__)

SESSION_EXPIRED = "SESSION_EXPIRED"


class HaloLiveParser:
    def __init__(self, url, account, password, aemail, apassword):
        self.url = url.rstrip('/')
        self.account = account
        self.password = password
        self.aemail = aemail
        self.apassword = apassword
        self.session = requests.Session()
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
        }
        self.is_logged_in = False

    def restore_from_cookies(self, phpsessid: str, acuid: str) -> bool:
        """Восстанавливает сессию из сохранённых кук. Возвращает True если сессия живая."""
        try:
            self.session.cookies.set("PHPSESSID", phpsessid, domain=self.url.replace("https://", "").replace("http://", ""))
            self.session.cookies.set("acuid", acuid, domain=self.url.replace("https://", "").replace("http://", ""))

            # Проверяем что сессия живая — делаем тестовый запрос
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 1},
                headers={**self.headers, "Referer": f"{self.url}/anchor/anchorManage/waibu_anchorInfo?in_iframe=1"},
                timeout=15
            )
            try:
                data = json.loads(r.text)
                if "data" in data:
                    self.is_logged_in = True
                    logger.info("Session restored from cookies successfully")
                    return True
            except Exception:
                pass
            return False
        except Exception as e:
            logger.error(f"restore_from_cookies error: {e}")
            return False

    def get_cookies(self) -> dict:
        """Возвращает текущие куки сессии."""
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
        return cookies

    def login(self, tfa_code=None):
        """
        Returns:
            True        — success
            'need_tfa'  — 2FA required, no code given
            'timeout'   — request timed out
            'network'   — connection error
            False       — other failure
        """
        try:
            self.session.get(f"{self.url}/admin/auth/login", headers=self.headers, timeout=15)

            self.session.post(
                f"{self.url}/admin/auth/verify",
                data={"account": self.account, "password": self.password},
                headers=self.headers,
                timeout=15
            )

            r = self.session.post(
                f"{self.url}/admin/auth/dologin",
                data={"aemail": self.aemail, "apassword": self.apassword, "aonline": "0"},
                headers={**self.headers, "Referer": f"{self.url}/admin/auth/login_view_load"},
                timeout=15
            )

            try:
                resp = json.loads(r.text)
                needs_tfa = resp.get("mfa") is not None
            except Exception:
                needs_tfa = False

            if needs_tfa:
                if tfa_code is None:
                    return "need_tfa"
                r2 = self.session.post(
                    f"{self.url}/admin/auth/verifyGoogleCode",
                    data={"code": str(tfa_code), "status": "0", "from": "login"},
                    headers={**self.headers, "Referer": f"{self.url}/admin/auth/login_view_load"},
                    timeout=15
                )
                if "1000" not in r2.text:
                    return False

            self.is_logged_in = True
            return True

        except requests.exceptions.Timeout as e:
            logger.error(f"Login timeout: {e}")
            return "timeout"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Login network error: {e}")
            return "network"
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def find_by_id(self, anchor_id):
        """
        Returns:
            dict            — girl's data (found)
            None            — not found
            SESSION_EXPIRED — session expired
        """
        if not self.is_logged_in:
            return None
        try:
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 9999},
                headers={**self.headers, "Referer": f"{self.url}/anchor/anchorManage/waibu_anchorInfo?in_iframe=1"},
                timeout=30
            )
            try:
                data = json.loads(r.text)
            except json.JSONDecodeError:
                self.is_logged_in = False
                logger.warning("Session expired (response is not JSON)")
                return SESSION_EXPIRED

            if "data" not in data:
                self.is_logged_in = False
                logger.warning(f"Session expired (unexpected response: {str(data)[:100]})")
                return SESSION_EXPIRED

            hosts = data["data"]
            return next(
                (h for h in hosts if str(h.get("DisplayAccountId")) == str(anchor_id)),
                None
            )
        except Exception as e:
            logger.error(f"Data fetch error: {e}")
            return None
