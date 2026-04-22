"""Custom exceptions."""


class BankingError(Exception):
    """Root exception for all banking errors."""


class InsufficientFundsError(BankingError):
    def __init__(self, balance: float, amount: float) -> None:
        super().__init__(
            f"Insufficient funds: balance={balance:.2f}, requested={amount:.2f}"
        )
        self.balance = balance
        self.amount = amount


class AccountFrozenError(BankingError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} is frozen.")
        self.account_id = account_id


class AccountClosedError(BankingError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account {account_id} is closed.")
        self.account_id = account_id


class MinimumBalanceError(BankingError):
    def __init__(self, min_balance: float, after_withdrawal: float) -> None:
        super().__init__(
            f"Operation would breach minimum balance {min_balance:.2f} "
            f"(result: {after_withdrawal:.2f})."
        )


class WithdrawalLimitError(BankingError):
    def __init__(self, limit: float, amount: float) -> None:
        super().__init__(f"Withdrawal {amount:.2f} exceeds limit {limit:.2f}.")


class InvalidAmountError(BankingError):
    def __init__(self, amount: float) -> None:
        super().__init__(f"Invalid amount: {amount}. Must be > 0.")


class OperationTimeError(BankingError):
    def __init__(self, hour: int) -> None:
        super().__init__(
            f"Operations are not allowed between 00:00 and 05:00 (current hour: {hour})."
        )


class ClientNotFoundError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client '{client_id}' not found.")


class AccountNotFoundError(BankingError):
    def __init__(self, account_id: str) -> None:
        super().__init__(f"Account '{account_id}' not found.")


class AuthenticationError(BankingError):
    pass


class ClientBlockedError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(
            f"Client '{client_id}' is blocked due to too many failed login attempts."
        )


class UnderageError(BankingError):
    def __init__(self, age: int) -> None:
        super().__init__(f"Client must be at least 18 years old (provided age: {age}).")


class DuplicateClientError(BankingError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client '{client_id}' already exists.")
