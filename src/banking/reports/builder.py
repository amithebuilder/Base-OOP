from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Optional

from banking.audit import AuditLog, RiskAnalyzer
from banking.core import Bank
from banking.customers import Client
from banking.enums import Currency
from banking.transactions import Transaction, TxStatus
from banking.transactions.fx import convert

__all__ = ["ReportBuilder"]


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


class ReportBuilder:
    def __init__(
        self,
        bank: Bank,
        transactions: list[Transaction],
        audit_log: AuditLog,
        risk_analyzer: RiskAnalyzer,
        output_dir: str = "var/reports",
    ) -> None:
        self._bank = bank
        self._txs = transactions
        self._audit = audit_log
        self._analyzer = risk_analyzer
        self._out = output_dir
        os.makedirs(self._out, exist_ok=True)

    def client_report(self, client: Client) -> dict:
        accounts_info = []
        for aid in client.account_ids:
            try:
                acc = self._bank.get_account(aid)
                info = acc.get_account_info()
                info["history_count"] = len(acc.history)
                accounts_info.append(info)
            except Exception:
                pass

        acc_set = set(client.account_ids)
        client_txs = [
            t
            for t in self._txs
            if t.sender_id in acc_set or t.receiver_id in acc_set
        ]
        completed = [t for t in client_txs if t.status == TxStatus.COMPLETED]
        failed = [t for t in client_txs if t.status == TxStatus.FAILED]
        total_in = sum(
            convert(t.amount, t.currency, Currency.USD)
            for t in completed
            if t.receiver_id and t.receiver_id in acc_set
        )
        total_out = sum(
            convert(t.amount, t.currency, Currency.USD)
            for t in completed
            if t.sender_id and t.sender_id in acc_set
        )
        risk_profile = self._analyzer.client_risk_profile(list(client.account_ids))
        return {
            "report_type": "client",
            "generated_at": datetime.now().isoformat(),
            "client_id": client.client_id,
            "full_name": client.full_name,
            "email": client.email,
            "age": client.age,
            "is_blocked": client.is_blocked,
            "is_suspicious": client.is_suspicious,
            "accounts": accounts_info,
            "transaction_count": len(client_txs),
            "completed_txs": len(completed),
            "failed_txs": len(failed),
            "total_incoming": round(total_in, 2),
            "total_outgoing": round(total_out, 2),
            "net_flow": round(total_in - total_out, 2),
            "risk_profile": risk_profile,
        }

    def bank_report(self) -> dict:
        ranking = self._bank.get_clients_ranking()
        all_accs = list(self._bank.iter_accounts())
        by_type: dict[str, dict] = {}
        for acc in all_accs:
            t = acc.__class__.__name__
            if t not in by_type:
                by_type[t] = {"count": 0, "total_balance_usd": 0.0}
            by_type[t]["count"] += 1
            by_type[t]["total_balance_usd"] = round(
                by_type[t]["total_balance_usd"]
                + convert(acc.balance, acc.currency, Currency.USD),
                2,
            )
        completed = [t for t in self._txs if t.status == TxStatus.COMPLETED]
        failed = [t for t in self._txs if t.status == TxStatus.FAILED]
        total_vol = sum(convert(t.amount, t.currency, Currency.USD) for t in completed)
        total_fee = sum(convert(t.fee_charged, t.currency, Currency.USD) for t in completed)
        by_tx_type: dict[str, int] = {}
        for t in self._txs:
            k = t.tx_type.value
            by_tx_type[k] = by_tx_type.get(k, 0) + 1
        n_clients = sum(1 for _ in self._bank.iter_clients())
        n_acc = sum(1 for _ in self._bank.iter_accounts())
        return {
            "report_type": "bank",
            "generated_at": datetime.now().isoformat(),
            "bank_name": self._bank.name,
            "total_clients": n_clients,
            "total_accounts": n_acc,
            "total_balance": self._bank.get_total_balance(),
            "accounts_by_type": by_type,
            "transactions_total": len(self._txs),
            "transactions_completed": len(completed),
            "transactions_failed": len(failed),
            "total_volume": round(total_vol, 2),
            "total_fees": round(total_fee, 2),
            "by_tx_type": by_tx_type,
            "top_clients": ranking[:5],
            "audit_stats": self._audit.stats(),
        }

    def risk_report(self) -> dict:
        suspicious = self._analyzer.suspicious_report()
        by_level: dict[str, int] = {}
        for ev in suspicious:
            sev = ev.get("severity", "UNKNOWN")
            if isinstance(sev, str):
                by_level[sev] = by_level.get(sev, 0) + 1
        flagged_accounts: dict[str, int] = {}
        for ev in suspicious:
            aid = ev.get("account_id") or "unknown"
            if isinstance(aid, str):
                key = aid[:8] if len(aid) >= 8 else aid
                flagged_accounts[key] = flagged_accounts.get(key, 0) + 1
        return {
            "report_type": "risk",
            "generated_at": datetime.now().isoformat(),
            "total_alerts": len(suspicious),
            "by_severity": by_level,
            "flagged_accounts": flagged_accounts,
            "error_rate": self._audit.error_rate(),
            "recent_alerts": suspicious[-10:],
        }

    def render_text(self, report: dict) -> str:
        rtype = report.get("report_type", "report")
        lines = [
            "=" * 60,
            f"  REPORT: {str(rtype).upper()}",
            f"  Generated: {report.get('generated_at', '')}",
            "=" * 60,
        ]

        def add(k: str, v: object) -> None:
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for dk, dv in v.items():
                    lines.append(f"    {dk}: {dv}")
            elif isinstance(v, list):
                lines.append(f"  {k}: [{len(v)} items]")
            else:
                lines.append(f"  {k}: {v}")

        skip = {
            "report_type",
            "generated_at",
            "recent_alerts",
            "accounts",
            "risk_profile",
        }
        for k, v in report.items():
            if k not in skip:
                add(k, v)
        return "\n".join(lines)

    def print_report(self, report: dict) -> None:
        print(self.render_text(report))

    def export_to_json(self, report: dict, filename: str) -> str:
        path = os.path.join(self._out, filename)
        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return path

    def export_to_csv(self, rows: list[dict], filename: str) -> str:
        if not rows:
            return ""
        path = os.path.join(self._out, filename)
        _ensure_dir(path)
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def transactions_to_csv(self, filename: str = "transactions.csv") -> str:
        rows = [
            {
                "tx_id": t.tx_id,
                "type": t.tx_type.value,
                "status": t.status.value,
                "amount": t.amount,
                "currency": t.currency.value,
                "fee": t.fee_charged,
                "sender_id": t.sender_id or "",
                "receiver_id": t.receiver_id or "",
                "created_at": t.created_at.isoformat(),
                "executed_at": t.executed_at.isoformat() if t.executed_at else "",
                "retries": t.retry_count,
                "failure": t.failure_reason or "",
            }
            for t in self._txs
        ]
        return self.export_to_csv(rows, filename)

    def save_charts(self, show: bool = False) -> list[str]:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("[ReportBuilder] matplotlib not installed; skipping charts.")
            return []
        saved: list[str] = []
        saved += self._chart_account_types_pie(plt)
        saved += self._chart_tx_status_bar(plt)
        saved += self._chart_top_clients_bar(plt)
        saved += self._chart_volume_by_type_bar(plt)
        saved += self._chart_balance_line(plt)
        if show:
            plt.show()
        return saved

    def _save_fig(self, plt: object, filename: str) -> str:
        path = os.path.join(self._out, filename)
        plt.savefig(path, bbox_inches="tight", dpi=100)  # type: ignore[union-attr]
        plt.close()
        return path

    def _chart_account_types_pie(self, plt: object) -> list[str]:
        all_accs = list(self._bank.iter_accounts())
        counts: dict[str, int] = {}
        for acc in all_accs:
            t = acc.__class__.__name__
            counts[t] = counts.get(t, 0) + 1
        if not counts:
            return []
        fig, ax = plt.subplots(figsize=(6, 6))  # type: ignore[union-attr]
        ax.pie(
            counts.values(),
            labels=counts.keys(),
            autopct="%1.1f%%",
            startangle=140,
        )
        ax.set_title("Account Distribution by Type")
        return [self._save_fig(plt, "chart_account_types_pie.png")]

    def _chart_tx_status_bar(self, plt: object) -> list[str]:
        counts: dict[str, int] = {}
        for t in self._txs:
            k = t.status.value
            counts[k] = counts.get(k, 0) + 1
        if not counts:
            return []
        fig, ax = plt.subplots(figsize=(7, 4))  # type: ignore[union-attr]
        bars = ax.bar(  # type: ignore[union-attr]
            list(counts.keys()),
            list(counts.values()),
            color=["#4caf50", "#f44336", "#ff9800", "#9e9e9e", "#2196f3", "#607d8b"],
        )
        ax.set_title("Transaction Count by Status")
        ax.set_ylabel("Count")
        for bar, val in zip(bars, counts.values()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                str(val),
                ha="center",
                va="bottom",
                fontsize=10,
            )
        return [self._save_fig(plt, "chart_tx_status_bar.png")]

    def _chart_top_clients_bar(self, plt: object) -> list[str]:
        ranking = self._bank.get_clients_ranking()[:7]
        names = [r["full_name"] for r in ranking]
        bals = [r["total_balance"] for r in ranking]
        fig, ax = plt.subplots(figsize=(8, 4))  # type: ignore[union-attr]
        bars = ax.barh(names[::-1], bals[::-1], color="#1976d2")  # type: ignore[union-attr]
        ax.set_title("Top Clients by Total Balance")
        ax.set_xlabel("Balance (USD)")
        for bar, val in zip(bars, bals[::-1]):
            ax.text(
                bar.get_width() + 100,
                bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}",
                va="center",
                fontsize=9,
            )
        return [self._save_fig(plt, "chart_top_clients_bar.png")]

    def _chart_volume_by_type_bar(self, plt: object) -> list[str]:
        completed = [t for t in self._txs if t.status == TxStatus.COMPLETED]
        vol: dict[str, float] = {}
        for t in completed:
            k = t.tx_type.value
            vol[k] = round(vol.get(k, 0.0) + convert(t.amount, t.currency, Currency.USD), 2)
        if not vol:
            return []
        fig, ax = plt.subplots(figsize=(7, 4))  # type: ignore[union-attr]
        bars = ax.bar(  # type: ignore[union-attr]
            list(vol.keys()),
            list(vol.values()),
            color=["#0288d1", "#43a047", "#f57c00"],
        )
        ax.set_title("Transaction Volume by Type (completed)")
        ax.set_ylabel("Volume (USD)")
        for bar, val in zip(bars, vol.values()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 50,
                f"${val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        return [self._save_fig(plt, "chart_volume_by_type.png")]

    def _chart_balance_line(self, plt: object) -> list[str]:
        sample = list(self._bank.iter_accounts())[:3]
        if not sample:
            return []
        fig, ax = plt.subplots(figsize=(10, 5))  # type: ignore[union-attr]
        colors = ["#e53935", "#1e88e5", "#43a047"]
        for acc, color in zip(sample, colors):
            if not acc.history:
                continue
            timestamps = [r.timestamp for r in acc.history]
            balances = [r.balance_after for r in acc.history]
            label = f"{acc.__class__.__name__} [{acc.account_id[:6]}]"
            ax.plot(  # type: ignore[union-attr]
                timestamps,
                balances,
                marker="o",
                markersize=4,
                label=label,
                color=color,
            )
        ax.set_title("Balance Over Time (sample accounts)")
        ax.set_ylabel("Balance (USD)")
        ax.set_xlabel("Time")
        ax.legend()
        fig.autofmt_xdate()  # type: ignore[union-attr]
        return [self._save_fig(plt, "chart_balance_line.png")]
