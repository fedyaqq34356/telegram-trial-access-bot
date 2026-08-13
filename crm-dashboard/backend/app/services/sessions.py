"""Хранилище активных Halo-сессий в памяти процесса."""
import time

from .halo_parser import HaloLiveParser

WITHDRAW_TOKEN_TTL_SECONDS = 5 * 60

class SessionManager:
    def __init__(self):
        self._active: dict[int, HaloLiveParser] = {}
        self._pending: dict[int, HaloLiveParser] = {}
        self._pending_withdraw: dict[int, dict] = {}

    def get_active(self, agency_id: int) -> HaloLiveParser | None:
        return self._active.get(agency_id)

    def set_active(self, agency_id: int, parser: HaloLiveParser) -> None:
        self._active[agency_id] = parser
        self._pending.pop(agency_id, None)

    def drop_active(self, agency_id: int) -> None:
        self._active.pop(agency_id, None)

    def set_pending(self, agency_id: int, parser: HaloLiveParser) -> None:
        self._pending[agency_id] = parser

    def get_pending(self, agency_id: int) -> HaloLiveParser | None:
        return self._pending.get(agency_id)

    def drop_pending(self, agency_id: int) -> None:
        self._pending.pop(agency_id, None)

    def set_pending_withdraw(self, agency_id: int, token: str, address: str, network: str) -> None:
        self._pending_withdraw[agency_id] = {
            "token": token,
            "address": address,
            "network": network,
            "expires_at": time.time() + WITHDRAW_TOKEN_TTL_SECONDS,
        }

    def get_pending_withdraw(self, agency_id: int) -> dict | None:
        entry = self._pending_withdraw.get(agency_id)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            self._pending_withdraw.pop(agency_id, None)
            return None
        return entry

    def drop_pending_withdraw(self, agency_id: int) -> None:
        self._pending_withdraw.pop(agency_id, None)

sessions = SessionManager()
