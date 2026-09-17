"""SQLite-backed personal transaction ledger (local-first)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Transaction:
    id: int
    occurred_at: str
    description: str
    amount_cents: int
    category: str
    notes: str


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                description TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                category TEXT NOT NULL DEFAULT 'uncategorized',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.commit()


def add_transaction(
    db_path: Path,
    description: str,
    amount_cents: int,
    category: str = "uncategorized",
    notes: str = "",
    occurred_at: Optional[str] = None,
) -> int:
    init_db(db_path)
    ts = occurred_at or datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions (occurred_at, description, amount_cents, category, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ts, description, amount_cents, category, notes),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_transactions(db_path: Path, limit: int = 50) -> list[Transaction]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, occurred_at, description, amount_cents, category, notes
            FROM transactions
            ORDER BY occurred_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        Transaction(
            id=row["id"],
            occurred_at=row["occurred_at"],
            description=row["description"],
            amount_cents=row["amount_cents"],
            category=row["category"],
            notes=row["notes"],
        )
        for row in rows
    ]


@dataclass(frozen=True)
class LedgerSummary:
    transaction_count: int
    total_income_cents: int
    total_expense_cents: int
    net_cents: int
    by_category: dict[str, int]


def summarize(db_path: Path) -> LedgerSummary:
    init_db(db_path)
    with _connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
        rows = conn.execute(
            "SELECT category, amount_cents FROM transactions"
        ).fetchall()

    income = 0
    expense = 0
    by_category: dict[str, int] = {}
    for row in rows:
        amt = int(row["amount_cents"])
        cat = str(row["category"])
        by_category[cat] = by_category.get(cat, 0) + amt
        if amt >= 0:
            income += amt
        else:
            expense += amt

    return LedgerSummary(
        transaction_count=int(count),
        total_income_cents=income,
        total_expense_cents=expense,
        net_cents=income + expense,
        by_category=by_category,
    )


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    abs_cents = abs(cents)
    return f"{sign}${abs_cents / 100:.2f}"


def seed_sample_transactions(db_path: Path) -> Iterable[int]:
    """Insert demo rows if the ledger is empty."""
    init_db(db_path)
    if summarize(db_path).transaction_count > 0:
        return []
    ids = []
    samples = [
        ("Coffee shop", -450, "food"),
        ("Monthly salary", 320000, "income"),
        ("Bus pass", -6500, "transport"),
        ("Groceries", -8725, "food"),
    ]
    for desc, cents, cat in samples:
        ids.append(add_transaction(db_path, desc, cents, category=cat))
    return ids
