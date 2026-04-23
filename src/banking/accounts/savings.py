from __future__ import annotations

from banking.accounts.base import BaseAccount, AccountRecord
from banking.enums import Currency, TransactionType
from banking.exceptions import InvalidAmountError, MinimumBalanceError, WithdrawalLimitError

__all__ = ["SavingsAccount"]


class SavingsAccount(BaseAccount):
    """Savings account: minimum balance and monthly interest."""

    DAILY_WITHDRAWAL_LIMIT = 5_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
        min_balance: float = 100.0,
        monthly_rate: float = 0.005,
    ) -> None:
        super().__init__(owner_id, currency, initial_balance)
        if min_balance < 0:
            raise InvalidAmountError(min_balance)
        self._min_balance = min_balance
        self._monthly_rate = monthly_rate
        self._interest_paid = 0.0

    @property
    def min_balance(self) -> float:
        return self._min_balance

    @property
    def monthly_rate(self) -> float:
        return self._monthly_rate

    @property
    def interest_paid(self) -> float:
        return self._interest_paid

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

    def apply_monthly_interest(self) -> AccountRecord:
        self._assert_operable()
        interest = round(self._balance * self._monthly_rate, 2)
        self._balance += interest
        self._interest_paid += interest
        return self._record(
            TransactionType.INTEREST,
            interest,
            f"Monthly interest @ {self._monthly_rate*100:.2f}%",
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
            "monthly_rate": f"{self._monthly_rate*100:.2f}%",
            "interest_paid": self._interest_paid,
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"SavingsAccount [{self._account_id[:8]}] | "
            f"owner={self._owner_id} | "
            f"balance={self._balance:.2f} {self._currency.value} | "
            f"min={self._min_balance:.2f} | "
            f"rate={self._monthly_rate*100:.2f}%/mo | "
            f"status={self._status.value}"
        )
