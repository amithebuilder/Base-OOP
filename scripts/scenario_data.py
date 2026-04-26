from __future__ import annotations
from datetime import date, datetime, timedelta
from banking.accounts import AbstractAccount
from banking import (
    Bank,
    Client,
    Currency,
    Transaction,
    TxPriority,
    TxType,
)

def build_bank() -> tuple[Bank, dict[str, Client], dict[str, AbstractAccount]]:
    bank = Bank("PyBank Demo", enforce_hours=False)
    raw = [
        ("Alice", "Smith", date(1990, 3, 15), "alice@pybank.io", "+1-555-0001", "pw_alice"),
        ("Bob", "Jones", date(1985, 7, 22), "bob@pybank.io", "+1-555-0002", "pw_bob"),
        ("Carol", "White", date(2000, 11, 1), "carol@pybank.io", "+1-555-0003", "pw_carol"),
        ("David", "Brown", date(1978, 5, 30), "david@pybank.io", "+1-555-0004", "pw_david"),
        ("Eva", "Green", date(1995, 2, 18), "eva@pybank.io", "+1-555-0005", "pw_eva"),
        ("Frank", "Black", date(1970, 9, 3), "frank@pybank.io", "+1-555-0006", "pw_frank"),
        ("Grace", "Taylor", date(2001, 6, 25), "grace@pybank.io", "+1-555-0007", "pw_grace"),
    ]
    clients: dict[str, Client] = {}
    for fn, ln, bd, em, ph, pw in raw:
        c = Client(fn, ln, bd, em, ph, pw)
        bank.add_client(c)
        clients[fn] = c
    alice, bob, carol, david, eva, frank, grace = (
        clients[n] for n in ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace"]
    )
    accounts: dict[str, AbstractAccount] = {}

    def open_acc(label: str, cid: str, atype: str, **kw: object) -> None:
        acc = bank.open_account(cid, atype, **kw)
        accounts[label] = acc

    open_acc("alice_sav", alice.client_id, "savings", initial_balance=8_000, min_balance=500)
    open_acc("alice_inv", alice.client_id, "investment", initial_balance=20_000)
    open_acc(
        "bob_prem",
        bob.client_id,
        "premium",
        initial_balance=5_000,
        overdraft_limit=10_000,
        withdrawal_fee=2,
    )
    open_acc("bob_sav", bob.client_id, "savings", initial_balance=2_000)
    open_acc("carol_sav", carol.client_id, "savings", initial_balance=1_200, min_balance=200)
    open_acc(
        "david_prem", david.client_id, "premium", initial_balance=30_000, overdraft_limit=20_000
    )
    open_acc("david_inv", david.client_id, "investment", initial_balance=50_000)
    open_acc("eva_sav", eva.client_id, "savings", initial_balance=3_500)
    open_acc("eva_prem", eva.client_id, "premium", initial_balance=12_000, overdraft_limit=5_000)
    open_acc("frank_sav", frank.client_id, "savings", initial_balance=900, min_balance=100)
    open_acc("frank_prem", frank.client_id, "premium", initial_balance=7_000)
    open_acc("grace_sav", grace.client_id, "savings", initial_balance=2_800)
    return bank, clients, accounts


def build_transactions(accounts: dict[str, AbstractAccount]) -> list[Transaction]:
    a = accounts
    return [
        Transaction(
            TxType.TRANSFER,
            1_000,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["bob_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rent share",
        ),
        Transaction(
            TxType.TRANSFER,
            500,
            Currency.USD,
            sender_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Gift",
        ),
        Transaction(
            TxType.TRANSFER,
            250,
            Currency.USD,
            sender_id=a["eva_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Lunch split",
        ),
        Transaction(
            TxType.TRANSFER,
            3_000,
            Currency.USD,
            sender_id=a["david_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Consulting fee",
        ),
        Transaction(
            TxType.TRANSFER,
            800,
            Currency.USD,
            sender_id=a["frank_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["eva_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Freelance payment",
        ),
        Transaction(
            TxType.DEPOSIT, 2_000, Currency.USD, receiver_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Salary",
        ),
        Transaction(
            TxType.DEPOSIT, 5_000, Currency.USD, receiver_id=a["frank_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Bonus",
        ),
        Transaction(
            TxType.DEPOSIT, 1_500, Currency.EUR, receiver_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="EUR income",
        ),
        Transaction(
            TxType.DEPOSIT, 10_000, Currency.USD, receiver_id=a["david_inv"].account_id,  # type: ignore[union-attr, index, misc]
            description="Investment top-up",
        ),
        Transaction(
            TxType.DEPOSIT, 300, Currency.USD, receiver_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Side income",
        ),
        Transaction(
            TxType.WITHDRAWAL, 400, Currency.USD, sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="ATM",
        ),
        Transaction(
            TxType.WITHDRAWAL, 600, Currency.USD, sender_id=a["eva_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Shopping",
        ),
        Transaction(
            TxType.WITHDRAWAL, 1_500, Currency.USD, sender_id=a["david_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Equipment",
        ),
        Transaction(
            TxType.WITHDRAWAL, 200, Currency.USD, sender_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Utilities",
        ),
        Transaction(
            TxType.WITHDRAWAL, 100, Currency.USD, sender_id=a["frank_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Transport",
        ),
        Transaction(
            TxType.TRANSFER,
            25_000,
            Currency.USD,
            sender_id=a["david_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Large consulting payment",
            priority=TxPriority.HIGH,
        ),
        Transaction(
            TxType.TRANSFER,
            18_000,
            Currency.USD,
            sender_id=a["david_inv"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Large investment transfer",
        ),
        Transaction(
            TxType.WITHDRAWAL, 12_000, Currency.USD, sender_id=a["eva_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Large withdrawal",
        ),
        Transaction(
            TxType.TRANSFER,
            100,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["bob_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rapid tx 1",
        ),
        Transaction(
            TxType.TRANSFER,
            100,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rapid tx 2",
        ),
        Transaction(
            TxType.TRANSFER,
            100,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["eva_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rapid tx 3",
        ),
        Transaction(
            TxType.TRANSFER,
            100,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["frank_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rapid tx 4",
        ),
        Transaction(
            TxType.TRANSFER,
            100,
            Currency.USD,
            sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Rapid tx 5",
        ),
        Transaction(
            TxType.WITHDRAWAL, 999_999, Currency.USD, sender_id=a["frank_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Should FAIL: way too large",
        ),
        Transaction(
            TxType.WITHDRAWAL, 999_999, Currency.USD, sender_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Should FAIL: way too large",
        ),
        Transaction(
            TxType.TRANSFER,
            999_999,
            Currency.USD,
            sender_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Should FAIL: way too large",
        ),
        Transaction(
            TxType.WITHDRAWAL, 7_900, Currency.USD, sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Should FAIL: min balance breach",
        ),
        Transaction(
            TxType.TRANSFER,
            50,
            Currency.USD,
            sender_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Delayed transfer",
            execute_after=datetime.now() + timedelta(hours=2),
        ),
        Transaction(
            TxType.DEPOSIT, 1_000, Currency.EUR, receiver_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="EUR salary",
        ),
        Transaction(
            TxType.TRANSFER,
            500,
            Currency.EUR,
            sender_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["eva_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="EUR transfer",
        ),
        Transaction(
            TxType.DEPOSIT, 500, Currency.CNY, receiver_id=a["david_inv"].account_id,  # type: ignore[union-attr, index, misc]
            description="CNY income",
        ),
        Transaction(
            TxType.TRANSFER,
            200,
            Currency.USD,
            sender_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["frank_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Loan repayment",
        ),
        Transaction(
            TxType.TRANSFER,
            750,
            Currency.USD,
            sender_id=a["eva_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Shared project payment",
        ),
        Transaction(
            TxType.DEPOSIT, 600, Currency.USD, receiver_id=a["eva_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Freelance income",
        ),
        Transaction(
            TxType.WITHDRAWAL, 300, Currency.USD, sender_id=a["bob_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Subscription",
        ),
        Transaction(
            TxType.TRANSFER,
            1_200,
            Currency.USD,
            sender_id=a["david_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["grace_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Payment for design work",
        ),
        Transaction(
            TxType.DEPOSIT, 400, Currency.USD, receiver_id=a["frank_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Gig economy",
        ),
        Transaction(
            TxType.WITHDRAWAL, 150, Currency.USD, sender_id=a["alice_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Books",
        ),
        Transaction(
            TxType.TRANSFER,
            900,
            Currency.USD,
            sender_id=a["frank_prem"].account_id,  # type: ignore[union-attr, index, misc]
            receiver_id=a["carol_sav"].account_id,  # type: ignore[union-attr, index, misc]
            description="Office supplies",
        ),
        Transaction(
            TxType.DEPOSIT, 2_200, Currency.USD, receiver_id=a["bob_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Client invoice",
        ),
        Transaction(
            TxType.WITHDRAWAL, 500, Currency.USD, sender_id=a["david_prem"].account_id,  # type: ignore[union-attr, index, misc]
            description="Miscellaneous",
        ),
    ]
