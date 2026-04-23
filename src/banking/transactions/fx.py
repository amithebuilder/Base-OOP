from __future__ import annotations

from banking.enums import Currency
from banking.exceptions import BankingError

_FX_RATES: dict[tuple[str, str], float] = {
    ("USD", "EUR"): 0.92,
    ("EUR", "USD"): 1.09,
    ("USD", "RUB"): 90.0,
    ("RUB", "USD"): 0.011,
    ("EUR", "RUB"): 98.0,
    ("RUB", "EUR"): 0.010,
    ("USD", "GBP"): 0.79,
    ("GBP", "USD"): 1.27,
}


def convert(amount: float, from_: Currency, to: Currency) -> float:
    if from_ == to:
        return amount
    key = (from_.value, to.value)
    rate = _FX_RATES.get(key)
    if rate is None:
        raise BankingError(f"No FX rate for {from_.value} to {to.value}")
    return round(amount * rate, 2)
