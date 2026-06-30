"""Хранилище активных Halo-сессий в памяти процесса."""
from .halo_parser import HaloLiveParser

class SessionManager:
    def __init__(self):
        self._active: dict[int, HaloLiveParser] = {}
        self._pending: dict[int, HaloLiveParser] = {}

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

sessions = SessionManager()
