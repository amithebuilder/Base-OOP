from __future__ import annotations

from datetime import datetime
from typing import Literal

from banking.accounts.base import BaseAccount, AccountRecord
from banking.enums import Currency, TransactionType
from banking.exceptions import InsufficientFundsError, InvalidAmountError, WithdrawalLimitError

__all__ = ["AssetType", "InvestmentAsset", "InvestmentAccount"]

AssetType = Literal["stocks", "bonds", "etf"]

_ASSET_RATES: dict[str, float] = {
    "stocks": 0.12,
    "bonds": 0.05,
    "etf": 0.08,
}


class InvestmentAsset:
    def __init__(
        self,
        asset_type: AssetType,
        name: str,
        quantity: float,
        unit_price: float,
    ) -> None:
        if asset_type not in _ASSET_RATES:
            raise ValueError(f"Unknown asset type: {asset_type}")
        self.asset_type = asset_type
        self.name = name
        self.quantity = quantity
        self.unit_price = unit_price
        self.bought_at = datetime.now()

    @property
    def market_value(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def expected_annual_return(self) -> float:
        return _ASSET_RATES[self.asset_type]

    def __str__(self) -> str:
        return (
            f"{self.asset_type.upper():6s} | {self.name:20s} | "
            f"qty={self.quantity:.4f} | price={self.unit_price:.2f} | "
            f"value={self.market_value:.2f}"
        )


class InvestmentAccount(BaseAccount):
    """Cash + virtual portfolio; withdrawals from cash only."""

    DAILY_WITHDRAWAL_LIMIT = 20_000.0

    def __init__(
        self,
        owner_id: str,
        currency: Currency = Currency.USD,
        initial_balance: float = 0.0,
    ) -> None:
        super().__init__(owner_id, currency, initial_balance)
        self._portfolio: list[InvestmentAsset] = []

    def buy_asset(
        self,
        asset_type: AssetType,
        name: str,
        quantity: float,
        unit_price: float,
    ) -> InvestmentAsset:
        self._assert_operable()
        cost = round(quantity * unit_price, 2)
        if cost > self._balance:
            raise InsufficientFundsError(self._balance, cost)
        self._balance -= cost
        asset = InvestmentAsset(asset_type, name, quantity, unit_price)
        self._portfolio.append(asset)
        self._record(
            TransactionType.WITHDRAWAL, cost, f"Buy {name} ({asset_type})"
        )
        return asset

    def sell_asset(self, name: str, quantity: float | None = None) -> float:
        self._assert_operable()
        for asset in self._portfolio:
            if asset.name == name:
                qty = quantity or asset.quantity
                if qty > asset.quantity:
                    raise InvalidAmountError(qty)
                proceeds = round(qty * asset.unit_price, 2)
                asset.quantity -= qty
                if asset.quantity <= 0:
                    self._portfolio.remove(asset)
                self._balance += proceeds
                self._record(
                    TransactionType.DEPOSIT,
                    proceeds,
                    f"Sell {name} ({asset.asset_type})",
                )
                return proceeds
        raise ValueError(f"Asset '{name}' not found in portfolio.")

    @property
    def portfolio_value(self) -> float:
        return round(sum(a.market_value for a in self._portfolio), 2)

    @property
    def total_value(self) -> float:
        return round(self._balance + self.portfolio_value, 2)

    def project_yearly_growth(self, years: int = 1) -> dict:
        projections: dict[str, float] = {}
        portfolio_now = self.portfolio_value
        for asset in self._portfolio:
            rate = asset.expected_annual_return
            future = round(asset.market_value * ((1 + rate) ** years), 2)
            projections[asset.name] = future
        projected_portfolio = round(sum(projections.values()), 2)
        gain = round(projected_portfolio - portfolio_now, 2)
        return {
            "years": years,
            "cash_balance": self._balance,
            "portfolio_now": portfolio_now,
            "projected_portfolio": projected_portfolio,
            "projected_gain": gain,
            "projected_total": round(self._balance + projected_portfolio, 2),
            "asset_breakdown": projections,
        }

    def withdraw(self, amount: float, description: str = "") -> AccountRecord:
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
            "type": "InvestmentAccount",
            "account_id": self._account_id,
            "owner_id": self._owner_id,
            "cash_balance": self._balance,
            "portfolio_value": self.portfolio_value,
            "total_value": self.total_value,
            "currency": self._currency.value,
            "status": self._status.value,
            "assets": [str(a) for a in self._portfolio],
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        return (
            f"InvestmentAccount [{self._account_id[:8]}] | "
            f"owner={self._owner_id} | "
            f"cash={self._balance:.2f} | "
            f"portfolio={self.portfolio_value:.2f} | "
            f"total={self.total_value:.2f} {self._currency.value} | "
            f"status={self._status.value}"
        )
