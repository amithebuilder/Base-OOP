from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from banking.accounts import AbstractAccount  # noqa: F401 (used in type hints)
from banking.core import Bank
from banking.exceptions import BankingError
from banking.transactions.fx import convert
from banking.transactions.models import Transaction, TxType
from banking.transactions.queue import TransactionQueue

# Avoid circular import (audit.risk → transactions.models → transactions.__init__
# → transactions.processor → audit.risk).  Only import for type-checker; at
# runtime the module is already initialised by the time _execute() is called.
if TYPE_CHECKING:
    from banking.audit.risk import RiskAnalyzer

__all__ = ["TransactionProcessor"]


class TransactionProcessor:
    """
    Executes transactions from a queue against bank accounts.

    Business rules enforced here (Day 3 + Day 5 requirements):
    - Night-time restriction (00:00–05:00) blocks ALL operations, not only account opening.
    - HIGH-risk transactions assessed by RiskAnalyzer are rejected before execution.
    - External transfers (different owners) carry a 1 % fee.
    - Transient banking errors trigger up to MAX_RETRIES retries.
    """

    MAX_RETRIES: int = 2
    EXTERNAL_FEE_RATE: float = 0.01

    def __init__(
        self,
        bank: Bank,
        risk_analyzer: Optional[RiskAnalyzer] = None,
    ) -> None:
        self._bank = bank
        self._risk_analyzer = risk_analyzer
        self._error_log: list[dict] = []

    # ── public interface ──────────────────────────────────────────────

    def process_queue(self, queue: TransactionQueue) -> list[Transaction]:
        """Drain all ready transactions from *queue* and return them."""
        processed: list[Transaction] = []
        while True:
            tx = queue.pop_ready()
            if tx is None:
                break
            self._execute(tx)
            processed.append(tx)
        return processed

    def process_one(self, tx: Transaction) -> Transaction:
        """Execute a single transaction outside the queue."""
        self._execute(tx)
        return tx

    def get_error_log(self) -> list[dict]:
        return list(self._error_log)

    def stats(self) -> dict:
        return {"error_count": len(self._error_log)}

    # ── execution pipeline ────────────────────────────────────────────

    def _execute(self, tx: Transaction) -> None:
        tx._mark_executing()

        # --- Day 5: risk gate (assessed before any attempt) ---
        if self._risk_analyzer is not None:
            from banking.audit.risk import RiskLevel  # lazy: safe at call time
            report = self._risk_analyzer.assess(tx)
            if report.risk_level == RiskLevel.HIGH:
                reason = (
                    f"Blocked by risk policy (HIGH risk): "
                    f"{', '.join(report.triggers)}"
                )
                tx._mark_failed(reason)
                self._log_error(tx, reason)
                return

        # --- retry loop ---
        for attempt in range(1, self.MAX_RETRIES + 2):
            try:
                self._dispatch(tx)
                return
            except BankingError as exc:
                tx._increment_retry()
                if attempt > self.MAX_RETRIES:
                    reason = str(exc)
                    tx._mark_failed(reason)
                    self._log_error(tx, reason)
                    return

    def _dispatch(self, tx: Transaction) -> None:
        # --- Day 3: time restriction applies to ALL banking operations ---
        self._bank.check_business_hours()

        if tx.tx_type == TxType.DEPOSIT:
            self._do_deposit(tx)
        elif tx.tx_type == TxType.WITHDRAWAL:
            self._do_withdrawal(tx)
        elif tx.tx_type == TxType.TRANSFER:
            self._do_transfer(tx)
        else:
            raise BankingError(f"Unknown transaction type: {tx.tx_type}")

    # ── operation handlers ────────────────────────────────────────────

    def _do_deposit(self, tx: Transaction) -> None:
        acc = self._get_account(tx.receiver_id or tx.sender_id)
        converted = convert(tx.amount, tx.currency, acc.currency)
        acc.deposit(converted, tx.description)
        tx._mark_completed()

    def _do_withdrawal(self, tx: Transaction) -> None:
        acc = self._get_account(tx.sender_id)
        converted = convert(tx.amount, tx.currency, acc.currency)
        acc.withdraw(converted, tx.description)
        tx._mark_completed()

    def _do_transfer(self, tx: Transaction) -> None:
        if not tx.sender_id or not tx.receiver_id:
            raise BankingError("Transfer requires both sender_id and receiver_id.")

        sender = self._get_account(tx.sender_id)
        receiver = self._get_account(tx.receiver_id)

        is_external = sender.owner_id != receiver.owner_id
        fee_rate = self.EXTERNAL_FEE_RATE if is_external else tx.fee_rate
        fee_amount = round(tx.amount * fee_rate, 2)
        total_debit = tx.amount + fee_amount

        debit_amount = convert(total_debit, tx.currency, sender.currency)
        sender.withdraw(debit_amount, f"Transfer to ...{tx.receiver_id[-4:]}")

        credit_amount = convert(tx.amount, tx.currency, receiver.currency)
        receiver.deposit(credit_amount, f"Transfer from ...{tx.sender_id[-4:]}")

        tx._mark_completed(fee=fee_amount)

    # ── helpers ───────────────────────────────────────────────────────

    def _get_account(self, account_id: Optional[str]) -> AbstractAccount:
        if not account_id:
            raise BankingError("account_id is required.")
        return self._bank.get_account(account_id)

    def _log_error(self, tx: Transaction, reason: str) -> None:
        self._error_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "tx_id": tx.tx_id,
                "tx_type": tx.tx_type.value,
                "amount": tx.amount,
                "currency": tx.currency.value,
                "reason": reason,
                "retries": tx.retry_count,
            }
        )
