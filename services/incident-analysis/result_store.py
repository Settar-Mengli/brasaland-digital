"""In-memory owner-scoped analysis results with TTL."""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from incident_analysis.types import AnalysisResult

DEFAULT_TTL_SECONDS = 3600


@dataclass(frozen=True)
class StoredAnalysis:
    result_id: str
    owner_user_uuid: str
    result: AnalysisResult
    expires_at: datetime


class AnalysisResultStore:
    """Process-local store; entries expire after TTL and are purged on access."""

    def __init__(self, *, ttl_seconds: int | None = None) -> None:
        self._ttl_seconds = (
            DEFAULT_TTL_SECONDS if ttl_seconds is None else max(1, ttl_seconds)
        )
        self._lock = threading.Lock()
        self._entries: dict[str, StoredAnalysis] = {}

    def store(self, owner_user_uuid: str, result: AnalysisResult) -> StoredAnalysis:
        now = datetime.now(timezone.utc)
        entry = StoredAnalysis(
            result_id=str(uuid.uuid4()),
            owner_user_uuid=owner_user_uuid,
            result=result,
            expires_at=now + timedelta(seconds=self._ttl_seconds),
        )
        with self._lock:
            self._purge_expired(now)
            self._entries[entry.result_id] = entry
        return entry

    def get(self, result_id: str) -> StoredAnalysis | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._purge_expired(now)
            return self._entries.get(result_id)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _purge_expired(self, now: datetime) -> None:
        expired = [
            key
            for key, entry in self._entries.items()
            if entry.expires_at <= now
        ]
        for key in expired:
            del self._entries[key]


def _ttl_from_env() -> int:
    raw = os.environ.get("ANALYSIS_RESULT_TTL_SECONDS", str(DEFAULT_TTL_SECONDS))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TTL_SECONDS


result_store = AnalysisResultStore(ttl_seconds=_ttl_from_env())
