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
    ("USD", "KZT"): 460.0,
    ("KZT", "USD"): 0.00217,
    ("EUR", "KZT"): 501.0,
    ("KZT", "EUR"): 0.002,
    ("RUB", "KZT"): 5.1,
    ("KZT", "RUB"): 0.196,
    ("USD", "CNY"): 7.24,
    ("CNY", "USD"): 0.138,
    ("EUR", "CNY"): 7.89,
    ("CNY", "EUR"): 0.127,
    ("RUB", "CNY"): 0.080,
    ("CNY", "RUB"): 12.5,
}


def convert(amount: float, from_: Currency, to: Currency) -> float:
    if from_ == to:
        return amount
    key = (from_.value, to.value)
    rate = _FX_RATES.get(key)
    if rate is None:
        raise BankingError(f"No FX rate for {from_.value} to {to.value}")
    return round(amount * rate, 2)
