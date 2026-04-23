from __future__ import annotations

from datetime import date, datetime
import hashlib
import uuid

from banking.exceptions import ClientBlockedError, UnderageError

__all__ = ["Client"]


class Client:
    """Bank customer: identity, password hash, account ids, risk flags."""

    MAX_FAILED_ATTEMPTS = 3

    def __init__(
        self,
        first_name: str,
        last_name: str,
        birthdate: date,
        email: str,
        phone: str,
        password: str,
        client_id: str | None = None,
    ) -> None:
        age = self._calc_age(birthdate)
        if age < 18:
            raise UnderageError(age)

        self._client_id: str = client_id or str(uuid.uuid4())
        self._first_name: str = first_name.strip()
        self._last_name: str = last_name.strip()
        self._birthdate: date = birthdate
        self._email: str = email.strip().lower()
        self._phone: str = phone.strip()
        self._password_hash: str = self._hash(password)

        self._account_ids: list[str] = []
        self._is_blocked: bool = False
        self._failed_attempts: int = 0
        self._suspicious: bool = False
        self._created_at: datetime = datetime.now()

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _calc_age(birthdate: date) -> int:
        today = date.today()
        return (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
        )

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def age(self) -> int:
        return self._calc_age(self._birthdate)

    @property
    def is_blocked(self) -> bool:
        return self._is_blocked

    @property
    def is_suspicious(self) -> bool:
        return self._suspicious

    @property
    def account_ids(self) -> list[str]:
        return list(self._account_ids)

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    def check_password(self, password: str) -> bool:
        if self._is_blocked:
            raise ClientBlockedError(self._client_id)
        if self._hash(password) == self._password_hash:
            self._failed_attempts = 0
            return True
        self._failed_attempts += 1
        if self._failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            self._is_blocked = True
        return False

    def unblock(self) -> None:
        self._is_blocked = False
        self._failed_attempts = 0

    def mark_suspicious(self) -> None:
        self._suspicious = True

    def clear_suspicious(self) -> None:
        self._suspicious = False

    def _add_account(self, account_id: str) -> None:
        if account_id not in self._account_ids:
            self._account_ids.append(account_id)

    def _remove_account(self, account_id: str) -> None:
        self._account_ids = [a for a in self._account_ids if a != account_id]

    def get_info(self) -> dict:
        return {
            "client_id": self._client_id,
            "full_name": self.full_name,
            "email": self._email,
            "phone": self._phone,
            "age": self.age,
            "is_blocked": self._is_blocked,
            "is_suspicious": self._suspicious,
            "accounts": self._account_ids,
            "created_at": self._created_at.isoformat(),
        }

    def __str__(self) -> str:
        flags: list[str] = []
        if self._is_blocked:
            flags.append("BLOCKED")
        if self._suspicious:
            flags.append("SUSPICIOUS")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return (
            f"Client {self._client_id[:8]} | {self.full_name} | "
            f"age={self.age} | {self._email}{flag_str} | "
            f"accounts={len(self._account_ids)}"
        )

    def __repr__(self) -> str:
        return f"Client(id={self._client_id[:8]}, name={self.full_name!r})"
