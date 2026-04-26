"""
Day 1 — Base account model.

AbstractAccount  — ABC that defines the mandatory interface (Day 1).
BankAccount      — Concrete general-purpose account that implements it (Day 1).
AccountRecord    — Lightweight history entry stored inside BankAccount.

Inheritance tree (Days 1–2):
    AbstractAccount  (ABC)
        └── BankAccount          (Day 1 — standard account)
                ├── SavingsAccount   (Day 2)
                ├── PremiumAccount   (Day 2)
                └── InvestmentAccount (Day 2)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from banking.enums import AccountStatus, Currency, TransactionType
from banking.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidOperationError,
    WithdrawalLimitError,
)

__all__ = ["AccountRecord", "AbstractAccount", "BankAccount"]


# ─────────────────────────────────────────────────────────────────────
# History record (used by BankAccount and all subclasses)
# ─────────────────────────────────────────────────────────────────────

class AccountRecord:
    """One ledger entry stored in BankAccount's internal history."""

    def __init__(
        self,
        tx_type: TransactionType,
        amount: float,
        balance_after: float,
        description: str = "",
        currency: Currency = Currency.USD,
    ) -> None:
        self.record_id: str = uuid.uuid4().hex[:8]
        self.tx_type: TransactionType = tx_type
        self.amount: float = amount
        self.balance_after: float = balance_after
        self.description: str = description
        self.currency: Currency = currency
        self.timestamp: datetime = datetime.now()

    def __str__(self) -> str:
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M:%S}]"
            f" {self.tx_type.value:12s}"
            f" {self.amount:>10.2f} {self.currency.value}"
            f" | balance after: {self.balance_after:.2f}"
            f" | {self.description}"
        )

    def __repr__(self) -> str:
        return (
            f"AccountRecord(id={self.record_id}, "
            f"type={self.tx_type.value}, amount={self.amount})"
        )


# ─────────────────────────────────────────────────────────────────────
# Day 1 — AbstractAccount  (contract / interface)
# ─────────────────────────────────────────────────────────────────────

class AbstractAccount(ABC):
    """
    Abstract base class that establishes the mandatory interface for
    every account type in the banking platform (Day 1).

    Concrete subclasses MUST implement:
        deposit(amount, description)      — credit funds
        withdraw(amount, description)     — debit funds
        get_account_info()               — return a structured dict
        __str__()                        — single-line human summary
    """

    def __init__(self, owner_id: str) -> None:
        # 8-char hex identifier (no dashes) — short UUID
        self._account_id: str = uuid.uuid4().hex[:8]
        self._owner_id: str = owner_id
        self._balance: float = 0.0
        self._status: AccountStatus = AccountStatus.ACTIVE

    # ── read-only properties ──────────────────────────────────────────

    @property
    def account_id(self) -> str:
        """Unique 8-char account identifier."""
        return self._account_id

    @property
    def owner_id(self) -> str:
        """ID of the client who owns this account."""
        return self._owner_id

    @property
    def balance(self) -> float:
        """Current account balance (protected — not directly settable)."""
        return self._balance

    @property
    def status(self) -> AccountStatus:
        """ACTIVE | FROZEN | CLOSED."""
        return self._status

    # ── abstract contract ─────────────────────────────────────────────

    @abstractmethod
    def deposit(self, amount: float, description: str = "") -> AccountRecord:
        """Credit *amount* to this account. Must return an AccountRecord."""

    @abstractmethod
    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
        """Debit *amount* from this account. Must return an AccountRecord."""

    @abstractmethod
    def get_account_info(self) -> dict:
        """Return a structured dictionary with full account details."""

    @abstractmethod
    def __str__(self) -> str:
        """Human-readable single-line summary."""


# ─────────────────────────────────────────────────────────────────────
# Day 1 — BankAccount  (standard concrete account)
# ─────────────────────────────────────────────────────────────────────

class BankAccount(AbstractAccount):
    """
    Standard concrete bank account (Day 1 mandatory entity).

    Adds on top of AbstractAccount:
    - Multi-currency support: USD, EUR, RUB, KZT, CNY
    - Per-operation history (list[AccountRecord])
    - Input validation (amount > 0, no negatives)
    - Status guards (frozen / closed block all operations)
    - Status management: freeze(), unfreeze(), close()
    - Daily withdrawal limit
    - __str__() shows last 4 chars of account number

    Subclasses (SavingsAccount, PremiumAccount, InvestmentAccount)
    override withdraw(), get_account_info(), and __str__() while
    reusing all protected helpers defined here.
    """

    DAILY_WITHDRAWAL_LIMIT: float = 10_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
    ) -> None:
        if initial_balance < 0:
            raise InvalidOperationError(
                f"Initial balance cannot be negative (got {initial_balance:.2f})."
            )
        super().__init__(owner_id)
        self._currency: Currency = currency
        self._history: list[AccountRecord] = []
        self._created_at: datetime = datetime.now()

        if initial_balance > 0:
            self._balance = initial_balance
            self._record(TransactionType.DEPOSIT, initial_balance, "Initial deposit")

    # ── additional properties ─────────────────────────────────────────

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def history(self) -> list[AccountRecord]:
        """Defensive copy of the internal history list."""
        return list(self._history)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ── status management ─────────────────────────────────────────────

    def freeze(self) -> None:
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)
        self._status = AccountStatus.FROZEN

    def unfreeze(self) -> None:
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)
        self._status = AccountStatus.ACTIVE

    def close(self) -> None:
        self._status = AccountStatus.CLOSED

    def is_active(self) -> bool:
        return self._status == AccountStatus.ACTIVE

    # ── AbstractAccount contract implementation ───────────────────────

    def deposit(self, amount: float, description: str = "") -> AccountRecord:
        self._assert_operable()
        self._validate_amount(amount)
        self._balance += amount
        return self._record(TransactionType.DEPOSIT, amount, description or "Deposit")

    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
        """Standard withdrawal: checks daily limit and sufficient balance."""
        self._assert_operable()
        self._validate_amount(amount)
        if amount > self.DAILY_WITHDRAWAL_LIMIT:
            raise WithdrawalLimitError(self.DAILY_WITHDRAWAL_LIMIT, amount)
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount)
        self._balance -= amount
        return self._record(
            TransactionType.WITHDRAWAL, amount, description or "Withdrawal"
        )

    def get_account_info(self) -> dict:
        return {
            "type": "BankAccount",
            "account_id": self._account_id,
            "owner_id": self._owner_id,
            "balance": self._balance,
            "currency": self._currency.value,
            "status": self._status.value,
            "daily_limit": self.DAILY_WITHDRAWAL_LIMIT,
            "history_count": len(self._history),
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"BankAccount [...{self._account_id[-4:]}] | "
            f"owner={self._owner_id} | "
            f"balance={self._balance:.2f} {self._currency.value} | "
            f"status={self._status.value}"
        )

    # ── convenience helpers ───────────────────────────────────────────

    def get_balance(self) -> float:
        return self._balance

    def get_statement(self, last_n: int = 10) -> str:
        lines = [
            f"Statement [{self._account_id}] (last {last_n} records):"
        ]
        for rec in self._history[-last_n:]:
            lines.append(f"  {rec}")
        return "\n".join(lines)

    # ── protected helpers (shared by all subclasses) ──────────────────

    def _assert_operable(self) -> None:
        """Raise if the account cannot be operated on."""
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(self._account_id)
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)

    def _validate_amount(self, amount: float) -> None:
        """Raise InvalidAmountError (subclass of InvalidOperationError) for bad amounts."""
        if amount <= 0:
            raise InvalidAmountError(amount)

    def _record(
        self,
        tx_type: TransactionType,
        amount: float,
        description: str = "",
    ) -> AccountRecord:
        """Append one AccountRecord to history and return it."""
        rec = AccountRecord(
            tx_type=tx_type,
            amount=amount,
            balance_after=self._balance,
            description=description,
            currency=self._currency,
        )
        self._history.append(rec)
        return rec

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self._account_id}, "
            f"owner={self._owner_id}, "
            f"balance={self._balance:.2f} {self._currency.value}, "
            f"status={self._status.value})"
        )
