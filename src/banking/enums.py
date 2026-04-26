"""Domain enumerations."""

from __future__ import annotations

from enum import Enum


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"
    KZT = "KZT"
    CNY = "CNY"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    INTEREST = "interest"
    FEE = "fee"
