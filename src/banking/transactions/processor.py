from __future__ import annotations

from datetime import datetime
from typing import Optional

from banking.accounts import BaseAccount
from banking.core import Bank
from banking.exceptions import BankingError
from banking.transactions.fx import convert
from banking.transactions.models import Transaction, TxType
from banking.transactions.queue import TransactionQueue

__all__ = ["TransactionProcessor"]


class TransactionProcessor:
    MAX_RETRIES = 2
    EXTERNAL_FEE_RATE = 0.01
    LARGE_TX_THRESHOLD = 5_000.0

    def __init__(self, bank: Bank) -> None:
        self._bank = bank
        self._error_log: list[dict] = []

    def process_queue(self, queue: TransactionQueue) -> list[Transaction]:
        processed: list[Transaction] = []
        while True:
            tx = queue.pop_ready()
            if tx is None:
                break
            self._execute(tx)
            processed.append(tx)
        return processed

    def process_one(self, tx: Transaction) -> Transaction:
        self._execute(tx)
        return tx

    def _execute(self, tx: Transaction) -> None:
        tx._mark_executing()
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
        if tx.tx_type == TxType.DEPOSIT:
            self._do_deposit(tx)
        elif tx.tx_type == TxType.WITHDRAWAL:
            self._do_withdrawal(tx)
        elif tx.tx_type == TxType.TRANSFER:
            self._do_transfer(tx)
        else:
            raise BankingError(f"Unknown transaction type: {tx.tx_type}")

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
        sender.withdraw(debit_amount, f"Transfer to {tx.receiver_id[:8]}")
        credit_amount = convert(tx.amount, tx.currency, receiver.currency)
        receiver.deposit(credit_amount, f"Transfer from {tx.sender_id[:8]}")
        tx._mark_completed(fee=fee_amount)

    def _get_account(self, account_id: Optional[str]) -> BaseAccount:
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

    def get_error_log(self) -> list[dict]:
        return list(self._error_log)

    def stats(self) -> dict:
        return {"error_count": len(self._error_log)}
