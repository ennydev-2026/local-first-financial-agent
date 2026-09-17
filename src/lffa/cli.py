"""CLI entrypoint for Local-First Financial Agent (hackathon demo)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from lffa import __version__
from lffa import agent
from lffa import ledger
from lffa import nosana_overflow


def default_db_path() -> Path:
    raw = os.environ.get("LFFA_LEDGER_DB", "./.lffa/ledger.db")
    return Path(raw)


def cmd_seed(args: argparse.Namespace) -> int:
    db = Path(args.db)
    ids = list(ledger.seed_sample_transactions(db))
    if not ids:
        print("Ledger already has transactions; no samples added.")
    else:
        print(f"Added {len(ids)} sample transaction(s) to {db}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    db = Path(args.db)
    tx_id = ledger.add_transaction(
        db,
        description=args.description,
        amount_cents=args.amount_cents,
        category=args.category,
        notes=args.notes or "",
    )
    print(f"Added transaction id={tx_id} ({args.description}: {ledger.format_cents(args.amount_cents)})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    db = Path(args.db)
    txs = ledger.list_transactions(db, limit=args.limit)
    if not txs:
        print("No transactions yet. Try: lffa seed")
        return 0
    for tx in txs:
        print(
            f"{tx.id:4d}  {tx.occurred_at[:19]}  {ledger.format_cents(tx.amount_cents):>10}  "
            f"[{tx.category}]  {tx.description}"
        )
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    db = Path(args.db)
    s = ledger.summarize(db)
    print(f"Transactions: {s.transaction_count}")
    print(f"Income:  {ledger.format_cents(s.total_income_cents)}")
    print(f"Expense: {ledger.format_cents(s.total_expense_cents)}")
    print(f"Net:     {ledger.format_cents(s.net_cents)}")
    if s.by_category:
        print("By category:")
        for cat, cents in sorted(s.by_category.items(), key=lambda x: x[0]):
            print(f"  {cat}: {ledger.format_cents(cents)}")
    return 0


def _print_agent_turn(turn: agent.AgentTurnResult) -> None:
    print(f"Question: {turn.user_message}\n")
    print("--- Inference routing ---")
    print(f"Route: {turn.routing.route.value}")
    print(f"Reason: {turn.routing.reason}")
    print(f"Nosana credentials configured: {turn.routing.nosana_configured}")
    print(f"Embedding (local stub): {turn.embedding_model}")
    if turn.routing.route.value == "local_slm":
        print(f"SLM backend: {turn.slm_backend}")
    print()
    label = "Agent" if turn.slm_backend == "ollama" else "Agent (stub fallback)" if turn.slm_backend == "stub" else "Agent (overflow stub)"
    print(f"--- {label} ---")
    if turn.slm_notice:
        print(turn.slm_notice, file=sys.stderr)
    print(turn.assistant_reply)
    print()
    print(turn.provenance_line)


def cmd_ask(args: argparse.Namespace) -> int:
    db = Path(args.db)
    turn = agent.run_turn(db, args.question)
    _print_agent_turn(turn)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """End-to-end demo: seed if empty, summary, routing decision, agent turn (Ollama or stub)."""
    db = Path(args.db)
    ledger.seed_sample_transactions(db)
    print("=== Local-First Financial Agent (hackathon demo) ===\n")
    cmd_summary(args)
    print()

    question = args.question or "How am I doing on food spending this month?"
    turn = agent.run_turn(db, question)
    _print_agent_turn(turn)

    if args.long_context:
        big = "x" * (turn.routing.local_max_chars + 500)
        overflow = nosana_overflow.decide_route(big)
        print("\n--- Overflow probe (synthetic large context) ---")
        print(f"Route: {overflow.route.value}")
        print(f"Reason: {overflow.reason}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lffa",
        description="Local-First Financial Agent — personal ledger + routing demo (hackathon scaffold).",
    )
    p.add_argument("--version", action="version", version=f"lffa {__version__}")
    p.add_argument("--db", default=str(default_db_path()), help="SQLite ledger path")

    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="Add sample transactions if ledger is empty").set_defaults(func=cmd_seed)

    add_p = sub.add_parser("add", help="Add a transaction (amount in cents)")
    add_p.add_argument("description")
    add_p.add_argument("amount_cents", type=int, help="e.g. -1299 for -$12.99")
    add_p.add_argument("--category", default="uncategorized")
    add_p.add_argument("--notes", default="")
    add_p.set_defaults(func=cmd_add)

    list_p = sub.add_parser("list", help="List recent transactions")
    list_p.add_argument("--limit", type=int, default=20)
    list_p.set_defaults(func=cmd_list)

    sub.add_parser("summary", help="Print ledger summary").set_defaults(func=cmd_summary)

    ask_p = sub.add_parser("ask", help="Ask the agent a question (local Ollama SLM or stub fallback)")
    ask_p.add_argument("question", help="Natural-language question about your ledger")
    ask_p.set_defaults(func=cmd_ask)

    demo_p = sub.add_parser("demo", help="Run demo: summary + local vs Nosana routing")
    demo_p.add_argument(
        "--question",
        default=None,
        help="User question for the agent turn",
    )
    demo_p.add_argument(
        "--long-context",
        action="store_true",
        help="Also print a synthetic overflow routing decision",
    )
    demo_p.set_defaults(func=cmd_demo)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
