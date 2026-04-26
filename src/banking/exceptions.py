"""
Custom exception hierarchy for the banking platform.

Day 1 required exceptions
--------------------------
AccountFrozenError      — operation on a frozen account
AccountClosedError      — operation on a closed account
InsufficientFundsError  — not enough balance to debit
InvalidOperationError   — any business-rule violation
    ├── InvalidAmountError     (amount <= 0)
    ├── WithdrawalLimitError   (daily limit exceeded)
    ├── MinimumBalanceError    (would breach min balance)
    └── OperationTimeError     (outside business hours)
"""


class BankingError(Exception):
    """Root exception for the entire banking system."""


# ── Day 1: four mandatory exceptions ─────────────────────────────────

class AccountFrozenError(BankingError):
    """Raised when an operation is attempted on a frozen account."""

    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account '{account_id}' is frozen.")
        self.account_id = account_id


class AccountClosedError(BankingError):
    """Raised when an operation is attempted on a closed account."""

    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account '{account_id}' is closed.")
        self.account_id = account_id


class InsufficientFundsError(BankingError):
    """Raised when a debit would make the balance go below the allowed floor."""

    def __init__(self, balance: float, amount: float) -> None:
        super().__init__(
            f"Insufficient funds: balance={balance:.2f}, requested={amount:.2f}"
        )
        self.balance = balance
        self.amount = amount


class InvalidOperationError(BankingError):
    """
    Root for all 'operation is not permitted' violations.

    Raised directly for generic business-rule failures; specialised
    subclasses cover the most common cases below.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


# ── Specialised InvalidOperationError subclasses ──────────────────────

class InvalidAmountError(InvalidOperationError):
    """Amount is zero or negative."""

    def __init__(self, amount: float) -> None:
        super().__init__(f"Invalid amount: {amount}. Must be > 0.")
        self.amount = amount


class WithdrawalLimitError(InvalidOperationError):
    """Single withdrawal exceeds the daily limit."""

    def __init__(self, limit: float, amount: float) -> None:
        super().__init__(
            f"Withdrawal {amount:.2f} exceeds the daily limit of {limit:.2f}."
        )
        self.limit = limit
        self.amount = amount


class MinimumBalanceError(InvalidOperationError):
    """Withdrawal would leave the account below its required minimum balance."""

    def __init__(self, min_balance: float, after_withdrawal: float) -> None:
        super().__init__(
            f"Operation would breach minimum balance {min_balance:.2f} "
            f"(result would be {after_withdrawal:.2f})."
        )
        self.min_balance = min_balance
        self.after_withdrawal = after_withdrawal


class OperationTimeError(InvalidOperationError):
    """Operations are forbidden during the night window (00:00 – 05:00)."""

    def __init__(self, hour: int) -> None:
        super().__init__(
            f"Operations are not allowed between 00:00 and 05:00 "
            f"(current hour: {hour:02d}:xx)."
        )
        self.hour = hour


# ── Client / account lifecycle ────────────────────────────────────────

class ClientNotFoundError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client '{client_id}' not found.")


class AccountNotFoundError(BankingError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account '{account_id}' not found.")


class AuthenticationError(BankingError):
    """Generic authentication failure (wrong credentials)."""


class ClientBlockedError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(
            f"Client '{client_id}' is blocked "
            f"due to too many failed login attempts."
        )


class UnderageError(BankingError):
    def __init__(self, age: int) -> None:
        super().__init__(
            f"Client must be at least 18 years old (provided age: {age})."
        )


class DuplicateClientError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client '{client_id}' already registered.")
