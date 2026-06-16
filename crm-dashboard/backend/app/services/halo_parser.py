"""Клиент Halo Live (admin.livegirl.me).

Портирован из рабочего телеграм-бота и расширен методами для CRM:
fetch_all_hosts (пагинация), set_ratio (смена %), split_coins (split).
Работает через requests + cookies. Двухшаговый логин + опциональная 2FA.
"""
import json
import logging
from urllib.parse import urlsplit

import requests

logger = logging.getLogger(__name__)

SESSION_EXPIRED = "SESSION_EXPIRED"


class HaloLiveParser:
    def __init__(self, url, account, password, aemail, apassword):
        self.url = self._normalize_url(url)
        self.account = account
        self.password = password
        self.aemail = aemail
        self.apassword = apassword
        self.session = requests.Session()
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
        }
        self.is_logged_in = False

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Берём только scheme://host, отбрасывая путь (юзер мог вставить URL после входа)."""
        raw = (url or "https://admin.livegirl.me").strip()
        if "://" not in raw:
            raw = "https://" + raw
        parts = urlsplit(raw)
        scheme = parts.scheme or "https"
        host = parts.netloc or parts.path.split("/")[0]
        return f"{scheme}://{host}".rstrip("/")

    @property
    def _domain(self) -> str:
        return self.url.replace("https://", "").replace("http://", "")

    def _ref(self, path: str = "/anchor/anchorManage/waibu_anchorInfo?in_iframe=1") -> dict:
        return {**self.headers, "Referer": f"{self.url}{path}"}

    # ── сессии ──
    def restore_from_cookies(self, phpsessid: str, acuid: str) -> bool:
        try:
            self.session.cookies.set("PHPSESSID", phpsessid, domain=self._domain)
            self.session.cookies.set("acuid", acuid, domain=self._domain)
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 1},
                headers=self._ref(),
                timeout=15,
            )
            data = json.loads(r.text)
            if "data" in data:
                self.is_logged_in = True
                return True
        except Exception as e:
            logger.warning(f"restore_from_cookies failed: {e}")
        return False

    def restore_all_cookies(self, cookies: dict) -> bool:
        """Восстановить сессию из полного набора cookies (включая trusted_device и пр.)."""
        try:
            for name, value in (cookies or {}).items():
                if value:
                    self.session.cookies.set(name, value, domain=self._domain)
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 1},
                headers=self._ref(),
                timeout=15,
            )
            if "data" in json.loads(r.text):
                self.is_logged_in = True
                return True
        except Exception as e:
            logger.warning(f"restore_all_cookies failed: {e}")
        return False

    def get_cookies(self) -> dict:
        return {c.name: c.value for c in self.session.cookies}

    def login(self, tfa_code=None):
        """True | 'need_tfa' | 'timeout' | 'network' | False"""
        try:
            self.session.get(f"{self.url}/admin/auth/login", headers=self.headers, timeout=15)
            self.session.post(
                f"{self.url}/admin/auth/verify",
                data={"account": self.account, "password": self.password},
                headers=self.headers,
                timeout=15,
            )
            r = self.session.post(
                f"{self.url}/admin/auth/dologin",
                data={"aemail": self.aemail, "apassword": self.apassword, "aonline": "1"},
                headers=self._ref("/admin/auth/login_view_load"),
                timeout=15,
            )
            try:
                needs_tfa = json.loads(r.text).get("mfa") is not None
            except Exception:
                needs_tfa = False

            if needs_tfa:
                if tfa_code is None:
                    return "need_tfa"
                self.session.post(
                    f"{self.url}/admin/auth/verifyGoogleCode",
                    data={"code": str(tfa_code), "status": "1", "from": "login"},
                    headers=self._ref("/admin/auth/login_view_load"),
                    timeout=15,
                )
                # тело verifyGoogleCode бывает пустым — проверяем успех реальным запросом данных
                if not self._auth_probe():
                    return False

            self.is_logged_in = True
            return True
        except requests.exceptions.Timeout:
            return "timeout"
        except requests.exceptions.ConnectionError:
            return "network"
        except Exception as e:
            logger.error(f"login error: {e}")
            return False

    def _auth_probe(self) -> bool:
        """Проверка, что сессия реально авторизована (запрос 1 записи данных)."""
        try:
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 1},
                headers=self._ref(),
                timeout=15,
            )
            return "data" in json.loads(r.text)
        except Exception:
            return False

    # ── данные ──
    def fetch_all_hosts(self) -> list | str:
        """Все девушки агентства. SESSION_EXPIRED если сессия истекла."""
        if not self.is_logged_in:
            return SESSION_EXPIRED
        try:
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/loadExtAnchorInfoList",
                params={"page": 1, "limit": 9999},
                headers=self._ref(),
                timeout=40,
            )
            try:
                data = json.loads(r.text)
            except json.JSONDecodeError:
                self.is_logged_in = False
                return SESSION_EXPIRED
            if "data" not in data:
                self.is_logged_in = False
                return SESSION_EXPIRED
            return data["data"]
        except Exception as e:
            logger.error(f"fetch_all_hosts error: {e}")
            return SESSION_EXPIRED

    # ── действия ──
    def set_ratio(self, display_account_id: str, ratio_value: int, agent_name: str) -> dict:
        """ratio_value — уже * 100 (20% = 2000). Возвращает {ok, code, msg}."""
        try:
            r = self.session.post(
                f"{self.url}/anchor/anchorManage/setAgentRatio",
                data={"id": str(display_account_id), "ratio": str(ratio_value), "agent": agent_name},
                headers=self._ref(),
                timeout=20,
            )
            try:
                resp = json.loads(r.text)
            except json.JSONDecodeError:
                self.is_logged_in = False
                return {"ok": False, "code": -1, "msg": "session_expired"}
            return {"ok": resp.get("code") == 0, "code": resp.get("code"), "msg": resp.get("msg", "")}
        except Exception as e:
            logger.error(f"set_ratio error: {e}")
            return {"ok": False, "code": -1, "msg": str(e)}

    def split_one(self, account_id: str) -> dict:
        """Сплит одной девушки. Halo ждёт ВНУТРЕННИЙ AccountId в ids (подтверждено
        перехватом JS: singleCheck(..., data.AccountId, ...) → splitCoins {ids}).
        DisplayAccountId возвращает code:0, но НИЧЕГО не сплитит (ложный успех)."""
        try:
            r = self.session.post(
                f"{self.url}/anchor/anchorManage/splitCoins",
                data={"ids": str(account_id)},
                headers=self._ref(),
                timeout=20,
            )
            try:
                resp = json.loads(r.text)
            except json.JSONDecodeError:
                self.is_logged_in = False
                return {"ok": False, "code": -1, "msg": "session_expired"}
            return {"ok": resp.get("code") == 0, "code": resp.get("code"), "msg": resp.get("msg", "")}
        except Exception as e:
            logger.error(f"split_one error: {e}")
            return {"ok": False, "code": -1, "msg": str(e)}

    def refresh_panel(self) -> None:
        """Имитирует перезагрузку официальной панели: GET страницы waibu_anchorInfo.
        Halo обновляет серверное представление данных при загрузке страницы панели —
        вызываем перед сплитом, чтобы работать со свежими цифрами."""
        try:
            self.session.get(
                f"{self.url}/anchor/anchorManage/waibu_anchorInfo",
                params={"in_iframe": 1},
                headers=self._ref(),
                timeout=20,
            )
        except Exception as e:
            logger.warning(f"refresh_panel failed: {e}")

    def get_agent_balance(self) -> dict:
        """«Готово к выводу» — баланс агентства. Halo рендерит его прямо в страницу
        waibu_anchorInfo как JS-переменные v2WithdrawBalance (coins) и pendingWithdrawUSD ($)."""
        try:
            r = self.session.get(
                f"{self.url}/anchor/anchorManage/waibu_anchorInfo",
                params={"in_iframe": 1},
                headers=self._ref(),
                timeout=20,
            )
            import re
            coins = re.search(r"v2WithdrawBalance\s*=\s*([\d.]+)", r.text)
            usd = re.search(r"pendingWithdrawUSD\s*=\s*([\d.]+)", r.text)
            return {
                "coins": int(float(coins.group(1))) if coins else 0,
                "usd": float(usd.group(1)) if usd else 0.0,
            }
        except Exception as e:
            logger.warning(f"get_agent_balance failed: {e}")
            return {"coins": 0, "usd": 0.0}


def normalize_host(raw: dict) -> dict:
    """Преобразует сырой ответ Halo Live в поля модели Host."""
    def to_int(v):
        try:
            return int(float(v))
        except Exception:
            return 0

    def to_float(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    rank = raw.get("MonthlyIncomeRanking")
    try:
        rank = int(rank) if rank not in (None, "") else None
    except Exception:
        rank = None

    return {
        "display_account_id": str(raw.get("DisplayAccountId", "")),
        "account_id": str(raw.get("AccountId", "")),
        "nickname": raw.get("AnchorName") or raw.get("NickName") or "",
        "avatar_url": raw.get("Avatar") or "",
        "agent_name": raw.get("Agent") or "",
        "email": raw.get("Email") or "",
        "ratio": to_int(raw.get("ExtAgentSplitRatio")),
        "down_rate": to_float(raw.get("DownRate")),
        "real_down_rate": to_float(raw.get("RealDownRate")),
        "receive_rate": to_float(raw.get("ReceiveRate")),
        "monthly_income": to_int(raw.get("MonthlyIncome")),
        "weekly_income": to_int(raw.get("WeeklyIncome")),
        "last_day_income": to_int(raw.get("PreIncome")),
        "monthly_online": str(raw.get("MonthlyAvailable") or ""),
        "weekly_online": str(raw.get("WeeklyAvailable") or ""),
        "last_day_online": str(raw.get("PreAvailable") or ""),
        "balance_coins": to_int(raw.get("Diamond")),
        "split_diamond": to_int(raw.get("SplitDiamond")),
        "anchor_grade": str(raw.get("AnchorGrade") or ""),
        "monthly_income_ranking": rank,
        "ban_status": str(raw.get("BanStatus", "2")),
        "fake": str(raw.get("Fake") or ""),
        "approval_date": str(raw.get("JudgeDate") or ""),
    }
