from __future__ import annotations

from datetime import datetime
from enum import Enum
import uuid
from typing import Optional

from banking.enums import Currency
from banking.exceptions import BankingError

__all__ = ["TxType", "TxStatus", "TxPriority", "Transaction"]


class TxType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TxStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TxPriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1


class Transaction:
    def __init__(
        self,
        tx_type: TxType,
        amount: float,
        currency: Currency,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        description: str = "",
        priority: TxPriority = TxPriority.NORMAL,
        execute_after: Optional[datetime] = None,
        fee_rate: float = 0.0,
    ) -> None:
        if amount <= 0:
            raise BankingError(f"Transaction amount must be > 0 (got {amount}).")
        self._tx_id = str(uuid.uuid4())
        self._tx_type = tx_type
        self._amount = amount
        self._currency = currency
        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._description = description
        self._priority = priority
        self._execute_after = execute_after or datetime.now()
        self._fee_rate = fee_rate
        self._status: TxStatus = TxStatus.PENDING
        self._failure_reason: Optional[str] = None
        self._created_at = datetime.now()
        self._executed_at: Optional[datetime] = None
        self._retry_count = 0
        self._fee_charged = 0.0

    @property
    def tx_id(self) -> str:
        return self._tx_id

    @property
    def tx_type(self) -> TxType:
        return self._tx_type

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def sender_id(self) -> Optional[str]:
        return self._sender_id

    @property
    def receiver_id(self) -> Optional[str]:
        return self._receiver_id

    @property
    def priority(self) -> TxPriority:
        return self._priority

    @property
    def status(self) -> TxStatus:
        return self._status

    @property
    def failure_reason(self) -> Optional[str]:
        return self._failure_reason

    @property
    def fee_charged(self) -> float:
        return self._fee_charged

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def execute_after(self) -> datetime:
        return self._execute_after

    @property
    def description(self) -> str:
        return self._description

    @property
    def fee_rate(self) -> float:
        return self._fee_rate

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def executed_at(self) -> Optional[datetime]:
        return self._executed_at

    def _mark_queued(self) -> None:
        self._status = TxStatus.QUEUED

    def _mark_executing(self) -> None:
        self._status = TxStatus.EXECUTING

    def _mark_completed(self, fee: float = 0.0) -> None:
        self._status = TxStatus.COMPLETED
        self._executed_at = datetime.now()
        self._fee_charged = fee

    def _mark_failed(self, reason: str) -> None:
        self._status = TxStatus.FAILED
        self._failure_reason = reason
        self._executed_at = datetime.now()

    def _mark_cancelled(self) -> None:
        self._status = TxStatus.CANCELLED

    def _increment_retry(self) -> None:
        self._retry_count += 1

    def __str__(self) -> str:
        parts = [
            f"TX[{self._tx_id[:8]}]",
            f"{self._tx_type.value:12s}",
            f"{self._amount:>10.2f} {self._currency.value}",
            f"fee={self._fee_charged:.2f}",
            f"status={self._status.value}",
        ]
        if self._sender_id:
            parts.append(f"from={self._sender_id[:8]}")
        if self._receiver_id:
            parts.append(f"to={self._receiver_id[:8]}")
        if self._failure_reason:
            parts.append(f"reason={self._failure_reason}")
        return " | ".join(parts)
