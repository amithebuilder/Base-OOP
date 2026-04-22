"""Abstract base account and in-account history records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from banking.enums import AccountStatus, Currency, TransactionType
from banking.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InvalidAmountError,
)

__all__ = ["AccountRecord", "BaseAccount"]


class AccountRecord:
    """Lightweight record stored in an account's own history."""

    def __init__(
        self,
        tx_type: TransactionType,
        amount: float,
        balance_after: float,
        description: str = "",
        currency: Currency = Currency.USD,
    ) -> None:
        self.record_id = str(uuid.uuid4())[:8]
        self.tx_type = tx_type
        self.amount = amount
        self.balance_after = balance_after
        self.description = description
        self.currency = currency
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] "
            f"{self.tx_type.value:12s} {self.amount:>10.2f} {self.currency.value} "
            f"| balance after: {self.balance_after:.2f} | {self.description}"
        )


class BaseAccount(ABC):
    """
    Abstract base class for all account types.

    Subclasses must implement withdraw(), get_account_info(), and __str__.
    """

    DAILY_WITHDRAWAL_LIMIT: float = 10_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
    ) -> None:
        if initial_balance < 0:
            raise InvalidAmountError(initial_balance)

        self._account_id: str = str(uuid.uuid4())
        self._owner_id: str = owner_id
        self._balance: float = initial_balance
        self._currency: Currency = currency
        self._status: AccountStatus = AccountStatus.ACTIVE
        self._history: list[AccountRecord] = []
        self._created_at: datetime = datetime.now()

        if initial_balance > 0:
            self._record(TransactionType.DEPOSIT, initial_balance, "Initial deposit")

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def owner_id(self) -> str:
        return self._owner_id

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def status(self) -> AccountStatus:
        return self._status

    @property
    def history(self) -> list[AccountRecord]:
        return list(self._history)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def freeze(self) -> None:
        self._status = AccountStatus.FROZEN

    def unfreeze(self) -> None:
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)
        self._status = AccountStatus.ACTIVE

    def close(self) -> None:
        self._status = AccountStatus.CLOSED

    def is_active(self) -> bool:
        return self._status == AccountStatus.ACTIVE

    def _assert_operable(self) -> None:
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(self._account_id)
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)

    def _validate_amount(self, amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError(amount)

    def deposit(self, amount: float, description: str = "") -> AccountRecord:
        self._assert_operable()
        self._validate_amount(amount)
        self._balance += amount
        return self._record(
            TransactionType.DEPOSIT, amount, description or "Deposit"
        )

    @abstractmethod
    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
        pass

    def get_balance(self) -> float:
        return self._balance

    def get_statement(self, last_n: int = 10) -> str:
        lines = [f"Statement for account {self._account_id} (last {last_n} records):"]
        for rec in self._history[-last_n:]:
            lines.append(f"  {rec}")
        return "\n".join(lines)

    @abstractmethod
    def get_account_info(self) -> dict:
        pass

    def _record(
        self,
        tx_type: TransactionType,
        amount: float,
        description: str = "",
    ) -> AccountRecord:
        rec = AccountRecord(
            tx_type=tx_type,
            amount=amount,
            balance_after=self._balance,
            description=description,
            currency=self._currency,
        )
        self._history.append(rec)
        return rec

    @abstractmethod
    def __str__(self) -> str: ...

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self._account_id[:8]}, "
            f"owner={self._owner_id}, "
            f"balance={self._balance:.2f} {self._currency.value}, "
            f"status={self._status.value})"
        )
