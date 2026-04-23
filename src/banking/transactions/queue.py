from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import heapq
from typing import Optional

from banking.transactions.models import Transaction

__all__ = ["TransactionQueue"]


@dataclass(order=True)
class _QueueEntry:
    priority_value: int
    created_ts: str
    tx: Transaction = field(compare=False)


class TransactionQueue:
    def __init__(self) -> None:
        self._heap: list[_QueueEntry] = []
        self._cancelled: set[str] = set()

    def enqueue(self, tx: Transaction) -> None:
        entry = _QueueEntry(
            priority_value=tx.priority.value,
            created_ts=tx.created_at.isoformat(),
            tx=tx,
        )
        heapq.heappush(self._heap, entry)
        tx._mark_queued()

    def cancel(self, tx_id: str) -> bool:
        self._cancelled.add(tx_id)
        return True

    def pop_ready(self) -> Optional[Transaction]:
        now = datetime.now()
        temp_stack: list[_QueueEntry] = []
        result: Optional[Transaction] = None
        while self._heap:
            entry = heapq.heappop(self._heap)
            tx = entry.tx
            if tx.tx_id in self._cancelled:
                tx._mark_cancelled()
                continue
            if tx.execute_after > now:
                temp_stack.append(entry)
                continue
            result = tx
            break
        for e in temp_stack:
            heapq.heappush(self._heap, e)
        return result

    def __len__(self) -> int:
        return len(self._heap)

    def pending_count(self) -> int:
        return sum(1 for e in self._heap if e.tx.tx_id not in self._cancelled)
