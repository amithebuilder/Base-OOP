from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import Enum
import json
import os
from typing import Optional

__all__ = ["Severity", "AuditEntry", "AuditLog"]


class Severity(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ALERT = 3
    CRITICAL = 4


class AuditEntry:
    def __init__(
        self,
        severity: Severity,
        message: str,
        category: str = "general",
        client_id: Optional[str] = None,
        account_id: Optional[str] = None,
        tx_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        self.timestamp = datetime.now()
        self.severity = severity
        self.message = message
        self.category = category
        self.client_id = client_id
        self.account_id = account_id
        self.tx_id = tx_id
        self.extra = extra or {}

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.name,
            "category": self.category,
            "message": self.message,
            "client_id": self.client_id,
            "account_id": self.account_id,
            "tx_id": self.tx_id,
            "extra": self.extra,
        }

    def __str__(self) -> str:
        parts = [
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}]",
            f"{self.severity.name:8s}",
            f"[{self.category}]",
            self.message,
        ]
        if self.client_id:
            parts.append(f"client={self.client_id[:8]}")
        if self.account_id:
            parts.append(f"account={self.account_id[:8]}")
        if self.tx_id:
            parts.append(f"tx={self.tx_id[:8]}")
        return " | ".join(parts)


class AuditLog:
    def __init__(self, log_file: Optional[str] = None) -> None:
        self._entries: list[AuditEntry] = []
        self._log_file: Optional[str] = log_file
        if log_file:
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    def log(
        self,
        severity: Severity,
        message: str,
        category: str = "general",
        client_id: Optional[str] = None,
        account_id: Optional[str] = None,
        tx_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            severity=severity,
            message=message,
            category=category,
            client_id=client_id,
            account_id=account_id,
            tx_id=tx_id,
            extra=extra,
        )
        self._entries.append(entry)
        if self._log_file:
            self._write_to_file(entry)
        return entry

    def debug(self, msg: str, **kw: object) -> AuditEntry:
        return self.log(Severity.DEBUG, msg, **kw)  # type: ignore[arg-type]

    def info(self, msg: str, **kw: object) -> AuditEntry:
        return self.log(Severity.INFO, msg, **kw)  # type: ignore[arg-type]

    def warning(self, msg: str, **kw: object) -> AuditEntry:
        return self.log(Severity.WARNING, msg, **kw)  # type: ignore[arg-type]

    def alert(self, msg: str, **kw: object) -> AuditEntry:
        return self.log(Severity.ALERT, msg, **kw)  # type: ignore[arg-type]

    def critical(self, msg: str, **kw: object) -> AuditEntry:
        return self.log(Severity.CRITICAL, msg, **kw)  # type: ignore[arg-type]

    def _write_to_file(self, entry: AuditEntry) -> None:
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:  # type: ignore[arg-type]
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass

    def filter(
        self,
        min_severity: Optional[Severity] = None,
        category: Optional[str] = None,
        client_id: Optional[str] = None,
        account_id: Optional[str] = None,
        tx_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> list[AuditEntry]:
        results = self._entries
        if min_severity is not None:
            results = [e for e in results if e.severity.value >= min_severity.value]
        if category:
            results = [e for e in results if e.category == category]
        if client_id:
            results = [e for e in results if e.client_id == client_id]
        if account_id:
            results = [e for e in results if e.account_id == account_id]
        if tx_id:
            results = [e for e in results if e.tx_id == tx_id]
        if since:
            results = [e for e in results if e.timestamp >= since]
        if until:
            results = [e for e in results if e.timestamp <= until]
        return results

    def suspicious_entries(self) -> list[AuditEntry]:
        return self.filter(category="risk")

    def stats(self) -> dict:
        counts: dict[str, int] = defaultdict(int)
        for e in self._entries:
            counts[e.severity.name] += 1
        return {"total": len(self._entries), "by_level": dict(counts)}

    def error_rate(self) -> float:
        if not self._entries:
            return 0.0
        high_sev = sum(
            1 for e in self._entries if e.severity.value >= Severity.WARNING.value
        )
        return round(high_sev / len(self._entries), 4)

    def __len__(self) -> int:
        return len(self._entries)
