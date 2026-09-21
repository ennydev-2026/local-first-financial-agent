"""SQLite-backed personal transaction ledger (local-first)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

LEDGER_EXPORT_VERSION = 1


@dataclass(frozen=True)
class Transaction:
    id: int
    occurred_at: str
    description: str
    amount_cents: int
    category: str
    notes: str
    tags: str = ""

    def tag_list(self) -> list[str]:
        if not self.tags.strip():
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tags_column(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()}
    if "tags" not in cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN tags TEXT NOT NULL DEFAULT ''")


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
                notes TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _ensure_tags_column(conn)
        conn.commit()


def _normalize_tags(tags: str | list[str] | None) -> str:
    if tags is None:
        return ""
    if isinstance(tags, list):
        return ",".join(t.strip() for t in tags if t.strip())
    return tags.strip()


def add_transaction(
    db_path: Path,
    description: str,
    amount_cents: int,
    category: str = "uncategorized",
    notes: str = "",
    tags: str | list[str] | None = None,
    occurred_at: Optional[str] = None,
) -> int:
    init_db(db_path)
    ts = occurred_at or datetime.now(timezone.utc).isoformat()
    tag_str = _normalize_tags(tags)
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions (occurred_at, description, amount_cents, category, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ts, description, amount_cents, category, notes, tag_str),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_transactions(db_path: Path, limit: int = 50) -> list[Transaction]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, occurred_at, description, amount_cents, category, notes, tags
            FROM transactions
            ORDER BY occurred_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_transaction(row) for row in rows]


def _row_to_transaction(row: sqlite3.Row) -> Transaction:
    keys = row.keys()
    tags = str(row["tags"]) if "tags" in keys else ""
    return Transaction(
        id=row["id"],
        occurred_at=row["occurred_at"],
        description=row["description"],
        amount_cents=row["amount_cents"],
        category=row["category"],
        notes=row["notes"],
        tags=tags,
    )


@dataclass(frozen=True)
class LedgerSummary:
    transaction_count: int
    total_income_cents: int
    total_expense_cents: int
    net_cents: int
    by_category: dict[str, int]
    by_tag: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_count": self.transaction_count,
            "total_income_cents": self.total_income_cents,
            "total_expense_cents": self.total_expense_cents,
            "net_cents": self.net_cents,
            "by_category": dict(self.by_category),
            "by_tag": dict(self.by_tag),
        }


def summarize(db_path: Path) -> LedgerSummary:
    init_db(db_path)
    with _connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM transactions").fetchone()["c"]
        rows = conn.execute(
            "SELECT category, amount_cents, tags FROM transactions"
        ).fetchall()

    income = 0
    expense = 0
    by_category: dict[str, int] = {}
    by_tag: dict[str, int] = {}
    for row in rows:
        amt = int(row["amount_cents"])
        cat = str(row["category"])
        by_category[cat] = by_category.get(cat, 0) + amt
        tag_field = row["tags"] if "tags" in row.keys() else ""
        for tag in (t.strip() for t in str(tag_field).split(",") if t.strip()):
            by_tag[tag] = by_tag.get(tag, 0) + amt
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
        by_tag=by_tag,
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


def export_ledger_json(db_path: Path) -> str:
    """Serialize all transactions for local backup (local-first portability)."""
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT occurred_at, description, amount_cents, category, notes, tags
            FROM transactions
            ORDER BY occurred_at ASC, id ASC
            """
        ).fetchall()
    txs = [
        {
            "occurred_at": row["occurred_at"],
            "description": row["description"],
            "amount_cents": int(row["amount_cents"]),
            "category": row["category"],
            "notes": row["notes"],
            "tags": row["tags"] if "tags" in row.keys() else "",
        }
        for row in rows
    ]
    payload = {
        "lffa_export_version": LEDGER_EXPORT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "transaction_count": len(txs),
        "transactions": txs,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def import_ledger_json(
    db_path: Path,
    raw: str,
    *,
    merge: bool = False,
) -> int:
    """Import transactions from JSON export. Returns number of rows inserted."""
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Import file must be a JSON object.")
    txs = data.get("transactions")
    if not isinstance(txs, list):
        raise ValueError("Missing or invalid 'transactions' array.")

    if not merge:
        init_db(db_path)
        with _connect(db_path) as conn:
            conn.execute("DELETE FROM transactions")
            conn.commit()

    inserted = 0
    for item in txs:
        if not isinstance(item, dict):
            continue
        add_transaction(
            db_path,
            description=str(item.get("description", "")),
            amount_cents=int(item["amount_cents"]),
            category=str(item.get("category", "uncategorized")),
            notes=str(item.get("notes", "")),
            tags=str(item.get("tags", "")),
            occurred_at=item.get("occurred_at"),
        )
        inserted += 1
    return inserted


def transaction_to_dict(tx: Transaction) -> dict[str, Any]:
    d = asdict(tx)
    d["tags_list"] = tx.tag_list()
    return d
