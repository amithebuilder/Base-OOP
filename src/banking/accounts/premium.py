from __future__ import annotations

from banking.accounts.base import BaseAccount, AccountRecord
from banking.enums import Currency, TransactionType
from banking.exceptions import InsufficientFundsError, WithdrawalLimitError

__all__ = ["PremiumAccount"]


class PremiumAccount(BaseAccount):
    """Premium account: overdraft, high limits, per-withdrawal fee."""

    DAILY_WITHDRAWAL_LIMIT = 50_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
        overdraft_limit: float = 5_000.0,
        withdrawal_fee: float = 0.0,
    ) -> None:
        super().__init__(owner_id, currency, initial_balance)
        self._overdraft_limit = overdraft_limit
        self._withdrawal_fee = withdrawal_fee
        self._fees_charged = 0.0

    @property
    def overdraft_limit(self) -> float:
        return self._overdraft_limit

    @property
    def withdrawal_fee(self) -> float:
        return self._withdrawal_fee

    @property
    def fees_charged(self) -> float:
        return self._fees_charged

    @property
    def available_funds(self) -> float:
        return self._balance + self._overdraft_limit

    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
        self._assert_operable()
        self._validate_amount(amount)
        if amount > self.DAILY_WITHDRAWAL_LIMIT:
            raise WithdrawalLimitError(self.DAILY_WITHDRAWAL_LIMIT, amount)
        total_needed = amount + self._withdrawal_fee
        if total_needed > self.available_funds:
            raise InsufficientFundsError(self._balance, total_needed)
        self._balance -= amount
        rec = self._record(
            TransactionType.WITHDRAWAL, amount, description or "Withdrawal"
        )
        if self._withdrawal_fee > 0:
            self._balance -= self._withdrawal_fee
            self._fees_charged += self._withdrawal_fee
            self._record(
                TransactionType.FEE, self._withdrawal_fee, "Withdrawal fee"
            )
        return rec

    def get_account_info(self) -> dict:
        return {
            "type": "PremiumAccount",
            "account_id": self._account_id,
            "owner_id": self._owner_id,
            "balance": self._balance,
            "currency": self._currency.value,
            "status": self._status.value,
            "overdraft_limit": self._overdraft_limit,
            "available_funds": self.available_funds,
            "withdrawal_fee": self._withdrawal_fee,
            "fees_charged": self._fees_charged,
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"PremiumAccount [{self._account_id[:8]}] | "
            f"owner={self._owner_id} | "
            f"balance={self._balance:.2f} {self._currency.value} | "
            f"overdraft={self._overdraft_limit:.2f} | "
            f"available={self.available_funds:.2f} | "
            f"status={self._status.value}"
        )
