"""Build JSON/CSV reports and optional matplotlib charts. Run from project root."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
VAR_REPORTS = ROOT / "var" / "reports"
VAR_REPORTS.mkdir(parents=True, exist_ok=True)

from banking import (  # noqa: E402
    AuditLog,
    ReportBuilder,
    RiskAnalyzer,
    TransactionProcessor,
    TransactionQueue,
)
from scenario_data import build_bank, build_transactions  # noqa: E402


def main() -> None:
    bank, clients, accounts = build_bank()
    audit = AuditLog(log_file=str(VAR_REPORTS / "audit.jsonl"))
    analyzer = RiskAnalyzer(audit)
    txs = build_transactions(accounts)
    queue: TransactionQueue = TransactionQueue()
    proc = TransactionProcessor(bank, risk_analyzer=analyzer)
    for tx in txs:
        queue.enqueue(tx)
    proc.process_queue(queue)
    rb = ReportBuilder(
        bank, txs, audit, analyzer, output_dir=str(VAR_REPORTS)
    )
    print(rb.render_text(rb.bank_report())[:2000])
    print("\nExports:")
    print(" ", rb.export_to_json(rb.bank_report(), "bank_report.json"))
    print(" ", rb.export_to_json(rb.client_report(clients["Alice"]), "alice_report.json"))
    print(" ", rb.export_to_json(rb.risk_report(), "risk_report.json"))
    print(" ", rb.transactions_to_csv("transactions.csv"))
    saved = rb.save_charts(show=False)
    for p in saved:
        print(" ", p)


if __name__ == "__main__":
    main()
