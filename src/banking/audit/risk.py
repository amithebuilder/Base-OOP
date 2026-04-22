from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

from banking.audit.log import AuditLog, Severity
from banking.transactions.models import Transaction, TxType

__all__ = ["RiskLevel", "RiskReport", "RiskAnalyzer"]


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskReport:
    def __init__(
        self, tx: Transaction, risk_level: RiskLevel, triggers: list[str]
    ) -> None:
        self.tx = tx
        self.risk_level = risk_level
        self.triggers = triggers
        self.timestamp = datetime.now()

    def is_dangerous(self) -> bool:
        return self.risk_level == RiskLevel.HIGH

    def __str__(self) -> str:
        return (
            f"RiskReport[{self.tx.tx_id[:8]}] "
            f"level={self.risk_level.value} | "
            f"triggers=[{', '.join(self.triggers)}]"
        )


class RiskAnalyzer:
    LARGE_AMOUNT_THRESHOLD = 10_000.0
    FREQUENT_TX_WINDOW = 10
    FREQUENT_TX_COUNT = 5
    NIGHT_HOURS = (0, 5)

    def __init__(self, audit_log: AuditLog) -> None:
        self._audit = audit_log
        self._tx_history: dict[str, list[datetime]] = defaultdict(list)
        self._known_receivers: dict[str, set[str]] = defaultdict(set)

    def assess(self, tx: Transaction) -> RiskReport:
        triggers: list[str] = []
        if self._is_large_amount(tx):
            triggers.append("large_amount")
        if self._is_frequent(tx):
            triggers.append("frequent_operations")
        if self._is_new_receiver(tx):
            triggers.append("new_receiver_account")
        if self._is_night_operation(tx):
            triggers.append("night_operation")

        risk_level = self._compute_level(triggers)
        report = RiskReport(tx, risk_level, triggers)

        if risk_level != RiskLevel.LOW:
            sev = (
                Severity.CRITICAL
                if risk_level == RiskLevel.HIGH
                else Severity.ALERT
            )
            self._audit.log(
                severity=sev,
                message=f"Risk {risk_level.value.upper()}: {', '.join(triggers)}",
                category="risk",
                account_id=tx.sender_id,
                tx_id=tx.tx_id,
                extra={"triggers": triggers, "amount": tx.amount},
            )

        self._record_tx(tx)
        return report

    def assess_many(self, txs: list[Transaction]) -> list[RiskReport]:
        return [self.assess(tx) for tx in txs]

    def _is_large_amount(self, tx: Transaction) -> bool:
        return tx.amount >= self.LARGE_AMOUNT_THRESHOLD

    def _is_frequent(self, tx: Transaction) -> bool:
        if not tx.sender_id:
            return False
        cutoff = datetime.now() - timedelta(minutes=self.FREQUENT_TX_WINDOW)
        recent = [t for t in self._tx_history[tx.sender_id] if t >= cutoff]  # type: ignore[index]
        return len(recent) >= self.FREQUENT_TX_COUNT

    def _is_new_receiver(self, tx: Transaction) -> bool:
        if tx.tx_type != TxType.TRANSFER:
            return False
        if not tx.sender_id or not tx.receiver_id:
            return False
        return tx.receiver_id not in self._known_receivers[tx.sender_id]

    def _is_night_operation(self, tx: Transaction) -> bool:
        hour = tx.created_at.hour
        start, end = self.NIGHT_HOURS
        return start <= hour < end

    @staticmethod
    def _compute_level(triggers: list[str]) -> RiskLevel:
        if not triggers:
            return RiskLevel.LOW
        if len(triggers) >= 3:
            return RiskLevel.HIGH
        if "large_amount" in triggers and len(triggers) >= 2:
            return RiskLevel.HIGH
        if len(triggers) == 2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _record_tx(self, tx: Transaction) -> None:
        if tx.sender_id:
            self._tx_history[tx.sender_id].append(tx.created_at)
        if tx.tx_type == TxType.TRANSFER and tx.sender_id and tx.receiver_id:
            self._known_receivers[tx.sender_id].add(tx.receiver_id)

    def client_risk_profile(self, client_account_ids: list[str]) -> dict:
        suspicious_txs = self._audit.filter(category="risk")
        relevant = [
            e
            for e in suspicious_txs
            if e.account_id and e.account_id in client_account_ids
        ]
        levels: dict[str, int] = defaultdict(int)
        for e in relevant:
            levels[e.severity.name] += 1
        return {
            "accounts": client_account_ids,
            "total_alerts": len(relevant),
            "by_severity": dict(levels),
        }

    def suspicious_report(self) -> list[dict]:
        return [e.to_dict() for e in self._audit.filter(category="risk")]

    def error_stats(self) -> dict:
        return self._audit.stats()
