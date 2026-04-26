from __future__ import annotations

from datetime import datetime
from typing import Iterator, Optional

from banking.accounts import (
    AbstractAccount,
    BankAccount,
    InvestmentAccount,
    PremiumAccount,
    SavingsAccount,
)
from banking.customers import Client
from banking.enums import AccountStatus, Currency
from banking.exceptions import (
    AccountNotFoundError,
    BankingError,
    ClientNotFoundError,
    DuplicateClientError,
    OperationTimeError,
)

__all__ = ["Bank", "AccountTypeStr", "ACCOUNT_FACTORIES"]

ACCOUNT_FACTORIES: dict[str, type[AbstractAccount]] = {
    "bank": BankAccount,
    "savings": SavingsAccount,
    "premium": PremiumAccount,
    "investment": InvestmentAccount,
}

AccountTypeStr = str


class Bank:
    """Central registry of clients, accounts, auth, and policies."""

    RESTRICTED_START_HOUR = 0
    RESTRICTED_END_HOUR = 5

    def __init__(self, name: str, enforce_hours: bool = True) -> None:
        self._name = name
        self._enforce_hours = enforce_hours
        self._clients: dict[str, Client] = {}
        self._accounts: dict[str, AbstractAccount] = {}
        self._suspicious_log: list[dict] = []

    @property
    def name(self) -> str:
        return self._name

    def _assert_business_hours(self) -> None:
        if not self._enforce_hours:
            return
        hour = datetime.now().hour
        if self.RESTRICTED_START_HOUR <= hour < self.RESTRICTED_END_HOUR:
            raise OperationTimeError(hour)

    # Public alias used by TransactionProcessor so it respects the same flag.
    def check_business_hours(self) -> None:
        """Raise OperationTimeError if transactions are currently forbidden."""
        self._assert_business_hours()

    def iter_accounts(self) -> Iterator[AbstractAccount]:
        return iter(self._accounts.values())

    def iter_clients(self) -> Iterator[Client]:
        return iter(self._clients.values())

    def add_client(self, client: Client) -> Client:
        if client.client_id in self._clients:
            raise DuplicateClientError(client.client_id)
        self._clients[client.client_id] = client
        return client

    def get_client(self, client_id: str) -> Client:
        try:
            return self._clients[client_id]
        except KeyError as e:
            raise ClientNotFoundError(client_id) from e

    def authenticate_client(self, client_id: str, password: str) -> bool:
        client = self.get_client(client_id)
        result = client.check_password(password)
        if not result and client.is_blocked:
            self._flag_suspicious(
                client_id, None, "Account blocked after too many failed login attempts"
            )
        return result

    def open_account(
        self,
        client_id: str,
        account_type: AccountTypeStr,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
        **kwargs: object,
    ) -> AbstractAccount:
        self._assert_business_hours()
        self.get_client(client_id)
        factory = ACCOUNT_FACTORIES.get(account_type.lower())
        if factory is None:
            raise BankingError(
                f"Unknown account type '{account_type}'. "
                f"Choose from: {list(ACCOUNT_FACTORIES)}"
            )
        account = factory(client_id, currency, initial_balance, **kwargs)
        self._accounts[account.account_id] = account
        self._clients[client_id]._add_account(account.account_id)
        return account

    def close_account(self, account_id: str) -> None:
        account = self._get_account(account_id)
        account.close()
        for cl in self._clients.values():
            cl._remove_account(account_id)

    def freeze_account(self, account_id: str, reason: str = "") -> None:
        account = self._get_account(account_id)
        account.freeze()
        self._flag_suspicious(None, account_id, f"Account frozen. Reason: {reason}")

    def unfreeze_account(self, account_id: str) -> None:
        account = self._get_account(account_id)
        account.unfreeze()

    def get_account(self, account_id: str) -> AbstractAccount:
        return self._get_account(account_id)

    def _get_account(self, account_id: str) -> AbstractAccount:
        try:
            return self._accounts[account_id]
        except KeyError as e:
            raise AccountNotFoundError(account_id) from e

    def search_accounts(
        self,
        owner_id: Optional[str] = None,
        status: Optional[AccountStatus] = None,
        account_type: Optional[type] = None,
    ) -> list[AbstractAccount]:
        results = list(self._accounts.values())
        if owner_id:
            results = [a for a in results if a.owner_id == owner_id]
        if status:
            results = [a for a in results if a.status == status]
        if account_type:
            results = [a for a in results if isinstance(a, account_type)]
        return results

    def search_clients(self, query: str) -> list[Client]:
        q = query.lower()
        return [
            c
            for c in self._clients.values()
            if q in c.full_name.lower() or q in c.email or q in c.phone
        ]

    def get_total_balance(self) -> float:
        return round(
            sum(
                a.balance
                for a in self._accounts.values()
                if a.status == AccountStatus.ACTIVE
            ),
            2,
        )

    def get_clients_ranking(self) -> list[dict]:
        ranking: list[dict] = []
        for cl in self._clients.values():
            total = sum(
                self._accounts[aid].balance
                for aid in cl.account_ids
                if aid in self._accounts
                and self._accounts[aid].status == AccountStatus.ACTIVE
            )
            ranking.append(
                {
                    "client_id": cl.client_id,
                    "full_name": cl.full_name,
                    "total_balance": round(total, 2),
                    "accounts": len(cl.account_ids),
                }
            )
        ranking.sort(key=lambda x: x["total_balance"], reverse=True)
        return ranking

    def _flag_suspicious(
        self, client_id: Optional[str], account_id: Optional[str], reason: str
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id,
            "account_id": account_id,
            "reason": reason,
        }
        self._suspicious_log.append(entry)
        if client_id and client_id in self._clients:
            self._clients[client_id].mark_suspicious()

    def get_suspicious_log(self) -> list[dict]:
        return list(self._suspicious_log)

    def summary(self) -> str:
        lines = [
            f"Bank: {self._name}",
            f"  Clients : {len(self._clients)}",
            f"  Accounts: {len(self._accounts)}",
            f"  Total balance: {self.get_total_balance():,.2f}",
            f"  Suspicious events: {len(self._suspicious_log)}",
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()
