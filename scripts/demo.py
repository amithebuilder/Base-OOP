"""
Full end-to-end demo: clients, accounts, risk assessment, transaction queue.
Run from project root: python scripts/demo.py
With editable install: pip install -e . && python scripts/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
VAR = ROOT / "var"
VAR.mkdir(parents=True, exist_ok=True)

from banking import (  # noqa: E402
    AuditLog,
    RiskAnalyzer,
    TransactionProcessor,
    TransactionQueue,
)
from scenario_data import build_bank, build_transactions  # noqa: E402

SEPARATOR = "=" * 70


def section(title: str) -> None:
    print(f"\n{SEPARATOR}\n  {title}\n{SEPARATOR}")


def run_demo() -> None:
    section("1. INITIALISATION")
    bank, clients, accounts = build_bank()
    print(f"Bank: '{bank.name}' | clients: {len(clients)} | accounts: {len(accounts)}")

    audit = AuditLog(log_file=str(VAR / "demo_audit.jsonl"))
    analyzer = RiskAnalyzer(audit)
    queue = TransactionQueue()
    proc = TransactionProcessor(bank, risk_analyzer=analyzer)
    audit.info("Demo started", category="system")

    section("2. TRANSACTIONS -- QUEUE & RISK")
    txs = build_transactions(accounts)
    print(f"Transactions built: {len(txs)}")

    for tx in txs:
        queue.enqueue(tx)
    print(f"Queue size: {queue.pending_count()}")

    section("3. PROCESSING QUEUE")
    done = proc.process_queue(queue)
    completed = [t for t in done if t.status.value == "completed"]
    failed = [t for t in done if t.status.value == "failed"]
    cancelled = [t for t in done if t.status.value == "cancelled"]
    delayed = [t for t in txs if t.status.value == "queued"]
    risk_blocked = [
        t for t in failed
        if t.failure_reason and "HIGH risk" in t.failure_reason
    ]
    biz_failed = [t for t in failed if t not in risk_blocked]
    print(
        f"Completed: {len(completed)} | Failed: {len(failed)} | "
        f"Cancelled: {len(cancelled)} | Still queued (delayed): {len(delayed)}"
    )
    print(f"\nBlocked by risk policy ({len(risk_blocked)}):")
    for tx in risk_blocked:
        print(f"  [{tx.tx_id[:8]}] {tx.tx_type.value:12s} {tx.amount:>10,.2f} | {tx.failure_reason}")
    print(f"\nFailed by business rules ({len(biz_failed)}):")
    for tx in biz_failed[:8]:
        print(f"  [{tx.tx_id[:8]}] {tx.tx_type.value:12s} {tx.amount:>10,.2f} | {tx.failure_reason}")

    section("4. USER SCENARIOS")
    alice = clients["Alice"]
    print("Alice accounts:")
    for aid in alice.account_ids:
        print(f"  {bank.get_account(aid)}")
    alice_sav = accounts["alice_sav"]
    print(f"\nAlice savings (last 8):\n{alice_sav.get_statement(8)}")
    sup = analyzer.suspicious_report()
    print(f"\nSuspicious events (first 5 of {len(sup)}):")
    for ev in sup[:5]:
        print(f"  {ev.get('message', '')[:80]}")

    section("5. AUTH (Bob, wrong password x3)")
    bob = clients["Bob"]
    print("correct:", bank.authenticate_client(bob.client_id, "pw_bob"))
    for _ in range(3):
        print(" wrong:", bank.authenticate_client(bob.client_id, "wrong"))
    print("blocked:", bob.is_blocked)

    section("6. REPORTS")
    ranking = bank.get_clients_ranking()
    print("Top-3 by balance:")
    for i, e in enumerate(ranking[:3], 1):
        print(f"  {i}. {e['full_name']!s:15s}  ${e['total_balance']:>12,.2f}")
    print(f"Bank total balance: {bank.get_total_balance():,.2f}")
    audit.info("Demo finished", category="system")
    section("DONE (see var/ for logs)")


if __name__ == "__main__":
    run_demo()
