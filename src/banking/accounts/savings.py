"""Day 2 — SavingsAccount: minimum balance + monthly interest."""

from __future__ import annotations

from banking.accounts.base import AccountRecord, BankAccount
from banking.enums import Currency, TransactionType
from banking.exceptions import InvalidAmountError, MinimumBalanceError, WithdrawalLimitError

__all__ = ["SavingsAccount"]


class SavingsAccount(BankAccount):
    """
    Savings account (Day 2).

    Extends BankAccount with:
    - Minimum balance guard: withdraw() refuses if balance would drop below min.
    - Monthly interest: apply_monthly_interest() credits earnings to balance.
    - Reduced daily withdrawal limit (5 000 vs 10 000 for BankAccount).
    """

    DAILY_WITHDRAWAL_LIMIT: float = 5_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
        min_balance: float = 100.0,
        monthly_rate: float = 0.005,        # 0.5 % per month
    ) -> None:
        super().__init__(owner_id, currency, initial_balance)
        if min_balance < 0:
            raise InvalidAmountError(min_balance)
        self._min_balance: float = min_balance
        self._monthly_rate: float = monthly_rate
        self._interest_paid: float = 0.0

    # ── properties ────────────────────────────────────────────────────

    @property
    def min_balance(self) -> float:
        return self._min_balance

    @property
    def monthly_rate(self) -> float:
        return self._monthly_rate

    @property
    def interest_paid(self) -> float:
        return self._interest_paid

    # ── overrides ─────────────────────────────────────────────────────

    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
        self._assert_operable()
        self._validate_amount(amount)
        if amount > self.DAILY_WITHDRAWAL_LIMIT:
            raise WithdrawalLimitError(self.DAILY_WITHDRAWAL_LIMIT, amount)
        remaining = self._balance - amount
        if remaining < self._min_balance:
            raise MinimumBalanceError(self._min_balance, remaining)
        self._balance -= amount
        return self._record(
            TransactionType.WITHDRAWAL, amount, description or "Withdrawal"
        )

    def get_account_info(self) -> dict:
        return {
            "type": "SavingsAccount",
            "account_id": self._account_id,
            "owner_id": self._owner_id,
            "balance": self._balance,
            "currency": self._currency.value,
            "status": self._status.value,
            "min_balance": self._min_balance,
            "monthly_rate": f"{self._monthly_rate * 100:.2f}%",
            "interest_paid": self._interest_paid,
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"SavingsAccount [...{self._account_id[-4:]}] | "
            f"owner={self._owner_id} | "
            f"balance={self._balance:.2f} {self._currency.value} | "
            f"min={self._min_balance:.2f} | "
            f"rate={self._monthly_rate * 100:.2f}%/mo | "
            f"status={self._status.value}"
        )

    # ── savings-specific operation ─────────────────────────────────────

    def apply_monthly_interest(self) -> AccountRecord:
        """Credit monthly interest based on current balance."""
        self._assert_operable()
        interest = round(self._balance * self._monthly_rate, 2)
        self._balance += interest
        self._interest_paid += interest
        return self._record(
            TransactionType.INTEREST,
            interest,
            f"Monthly interest @ {self._monthly_rate * 100:.2f}%",
        )
