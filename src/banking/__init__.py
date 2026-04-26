"""
Banking platform: accounts, customers, core bank, transactions, audit, reports.

Public API surface — import from here in scripts and tests.
"""

from banking.accounts import (
    AbstractAccount,
    AccountRecord,
    AssetType,
    BankAccount,
    InvestmentAccount,
    InvestmentAsset,
    PremiumAccount,
    SavingsAccount,
)
from banking.audit import (
    AuditEntry,
    AuditLog,
    RiskAnalyzer,
    RiskLevel,
    RiskReport,
    Severity,
)
from banking.core import ACCOUNT_FACTORIES, Bank
from banking.customers import Client
from banking.enums import AccountStatus, Currency, TransactionType
from banking.exceptions import (
    AccountClosedError,
    AccountFrozenError,
    BankingError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidOperationError,
    OperationTimeError,
    WithdrawalLimitError,
    MinimumBalanceError,
)
from banking.reports import ReportBuilder
from banking.transactions import (
    Transaction,
    TransactionProcessor,
    TransactionQueue,
    TxPriority,
    TxStatus,
    TxType,
    convert,
)

__all__ = [
    # Accounts
    "AbstractAccount",
    "AccountRecord",
    "AccountStatus",
    "AssetType",
    "BankAccount",
    "InvestmentAccount",
    "InvestmentAsset",
    "PremiumAccount",
    "SavingsAccount",
    # Audit
    "AuditEntry",
    "AuditLog",
    "RiskAnalyzer",
    "RiskLevel",
    "RiskReport",
    "Severity",
    # Bank / clients
    "ACCOUNT_FACTORIES",
    "Bank",
    "Client",
    # Enums
    "Currency",
    "TransactionType",
    # Exceptions
    "AccountClosedError",
    "AccountFrozenError",
    "BankingError",
    "InsufficientFundsError",
    "InvalidAmountError",
    "InvalidOperationError",
    "MinimumBalanceError",
    "OperationTimeError",
    "WithdrawalLimitError",
    # Reports
    "ReportBuilder",
    # Transactions
    "Transaction",
    "TransactionProcessor",
    "TransactionQueue",
    "TransactionType",
    "TxPriority",
    "TxStatus",
    "TxType",
    "convert",
]

__version__ = "0.2.0"
