"""CLI entrypoint for Local-First Financial Agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lffa import __version__
from lffa import agent
from lffa import config
from lffa import doctor
from lffa import ledger
from lffa import nosana_overflow
from lffa import output


EPILOG = """
Examples:
  lffa seed
  lffa add "Coffee" -450 --category food --tags commute,caffeine
  lffa summary --by category
  lffa ask "How much did I spend on food?" --json
  lffa demo --long-context
  lffa export -o backup.json
  lffa doctor

Environment: see .env.example and README.md (LFFA_* preferred).
"""


def default_db_path() -> Path:
    return config.load_config().ledger_db


def _db_from_args(args: argparse.Namespace) -> Path:
    return Path(args.db)


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"lffa {__version__}")
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    ids = list(ledger.seed_sample_transactions(db))
    if getattr(args, "json", False):
        output.print_json(
            {"seeded": len(ids), "ids": ids, "db": str(db), "skipped": len(ids) == 0}
        )
        return 0
    if not ids:
        print(output.warn("Ledger already has transactions; no samples added."))
    else:
        print(output.ok(f"Added {len(ids)} sample transaction(s) to {db}"))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    tx_id = ledger.add_transaction(
        db,
        description=args.description,
        amount_cents=args.amount_cents,
        category=args.category,
        notes=args.notes or "",
        tags=args.tags or "",
    )
    if getattr(args, "json", False):
        output.print_json(
            {
                "id": tx_id,
                "description": args.description,
                "amount_cents": args.amount_cents,
                "category": args.category,
            }
        )
        return 0
    print(
        output.ok(
            f"Added transaction id={tx_id} ({args.description}: "
            f"{ledger.format_cents(args.amount_cents)})"
        )
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    txs = ledger.list_transactions(db, limit=args.limit)
    if getattr(args, "json", False):
        output.print_json({"transactions": [ledger.transaction_to_dict(t) for t in txs]})
        return 0
    if not txs:
        print("No transactions yet. Try: lffa seed")
        return 0
    for tx in txs:
        tag_part = f"  tags={tx.tags}" if tx.tags else ""
        print(
            f"{tx.id:4d}  {tx.occurred_at[:19]}  {ledger.format_cents(tx.amount_cents):>10}  "
            f"[{tx.category}]{tag_part}  {tx.description}"
        )
    return 0


def _print_breakdown(title: str, amounts: dict[str, int]) -> None:
    if not amounts:
        return
    print(output.heading(title))
    for key, cents in sorted(amounts.items(), key=lambda x: x[0]):
        print(f"  {key}: {ledger.format_cents(cents)}")


def cmd_summary(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    s = ledger.summarize(db)
    by = getattr(args, "by", None)

    if getattr(args, "json", False):
        payload = s.to_dict()
        if by == "category":
            payload = {"by": "category", "breakdown": s.by_category, **payload}
        elif by == "tag":
            payload = {"by": "tag", "breakdown": s.by_tag, **payload}
        output.print_json(payload)
        return 0

    if by == "category":
        _print_breakdown("By category", s.by_category)
        return 0
    if by == "tag":
        _print_breakdown("By tag", s.by_tag)
        return 0

    print(f"Transactions: {s.transaction_count}")
    print(f"Income:  {ledger.format_cents(s.total_income_cents)}")
    print(f"Expense: {ledger.format_cents(s.total_expense_cents)}")
    print(f"Net:     {ledger.format_cents(s.net_cents)}")
    if s.by_category:
        print()
        _print_breakdown("By category", s.by_category)
    return 0


def _print_agent_turn(turn: agent.AgentTurnResult, *, as_json: bool = False) -> None:
    if as_json:
        output.print_json(turn.to_dict())
        return
    print(f"Question: {turn.user_message}\n")
    print(output.heading("--- Inference routing ---"))
    route_label = turn.routing.route.value
    if turn.routing.route == nosana_overflow.InferenceRoute.NOSANA_OVERFLOW:
        route_label = output.warn(route_label)
    else:
        route_label = output.ok(route_label)
    print(f"Route: {route_label}")
    print(f"Reason: {turn.routing.reason}")
    print(f"Context chars: {turn.routing.estimated_context_chars} / budget {turn.routing.local_max_chars}")
    print(f"Force local: {turn.routing.force_local}")
    print(f"Nosana credentials configured: {turn.routing.nosana_configured}")
    print(f"Embedding (local stub): {turn.embedding_model}")
    if turn.routing.route.value == "local_slm":
        print(f"SLM backend: {turn.slm_backend}")
    else:
        print(f"Overflow backend: {turn.overflow_backend or 'stub'}")
    print()
    if turn.routing.route.value == "nosana_overflow":
        label = (
            "Agent (Nosana overflow)"
            if turn.overflow_backend == "nosana"
            else "Agent (overflow stub)"
        )
    else:
        label = (
            "Agent"
            if turn.slm_backend == "ollama"
            else "Agent (stub fallback)"
        )
    print(output.heading(f"--- {label} ---"))
    if turn.slm_notice:
        print(output.warn(turn.slm_notice), file=sys.stderr)
    if turn.overflow_notice:
        print(output.warn(turn.overflow_notice), file=sys.stderr)
    print(turn.assistant_reply)
    print()
    print(turn.provenance_line)


def cmd_ask(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    turn = agent.run_turn(db, args.question)
    _print_agent_turn(turn, as_json=getattr(args, "json", False))
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """End-to-end demo: seed if empty, summary, routing decision, agent turn."""
    db = _db_from_args(args)
    ledger.seed_sample_transactions(db)
    as_json = getattr(args, "json", False)

    if as_json:
        question = args.question or "How am I doing on food spending this month?"
        turn = agent.run_turn(db, question)
        payload = {
            "demo": True,
            "summary": ledger.summarize(db).to_dict(),
            "turn": turn.to_dict(),
        }
        if args.long_context:
            big = "x" * (turn.routing.local_max_chars + 500)
            overflow = nosana_overflow.decide_route(big)
            job = nosana_overflow.build_overflow_job(big)
            submit = nosana_overflow.submit_overflow_job(job)
            payload["overflow_probe"] = {
                "routing": overflow.to_dict(),
                "submit_backend": submit.backend,
                "submit_status": (submit.payload or {}).get("status"),
            }
        output.print_json(payload)
        return 0

    print(output.heading("=== Local-First Financial Agent ===\n"))
    cmd_summary(args)
    print()

    question = args.question or "How am I doing on food spending this month?"
    turn = agent.run_turn(db, question)
    _print_agent_turn(turn)

    if args.long_context:
        big = "x" * (turn.routing.local_max_chars + 500)
        overflow = nosana_overflow.decide_route(big)
        job = nosana_overflow.build_overflow_job(big)
        submit = nosana_overflow.submit_overflow_job(job)
        print()
        print(output.heading("--- Overflow probe (synthetic large context) ---"))
        print(f"Route: {overflow.route.value}")
        print(f"Reason: {overflow.reason}")
        print(f"Overflow backend: {submit.backend}")
        if submit.notice:
            print(output.warn(submit.notice), file=sys.stderr)

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    text = ledger.export_ledger_json(db)
    out = Path(args.output) if args.output else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        if getattr(args, "json", False):
            output.print_json({"exported_to": str(out), "bytes": len(text.encode("utf-8"))})
        else:
            print(output.ok(f"Exported ledger to {out}"))
    else:
        print(text)
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    db = _db_from_args(args)
    src = Path(args.file)
    if not src.is_file():
        print(output.err(f"File not found: {src}"), file=sys.stderr)
        return 2
    raw = src.read_text(encoding="utf-8")
    try:
        count = ledger.import_ledger_json(db, raw, merge=args.merge)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(output.err(f"Import failed: {exc}"), file=sys.stderr)
        return 1
    if getattr(args, "json", False):
        output.print_json({"imported": count, "merge": args.merge, "db": str(db)})
    else:
        mode = "merged into" if args.merge else "imported into"
        print(output.ok(f"{count} transaction(s) {mode} {db}"))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config.reset_config_cache()
    cfg = config.load_config()
    checks = doctor.run_doctor(cfg)
    summary = doctor.doctor_summary(checks)
    if getattr(args, "json", False):
        output.print_json(summary)
    else:
        print(output.heading("lffa doctor"))
        print(f"Config ledger: {cfg.ledger_db}\n")
        for check in checks:
            mark = output.ok("ok") if check.ok else output.err("FAIL")
            print(f"  [{mark}] {check.name}: {check.detail}")
        if not summary["all_ok"]:
            print(
                "\n"
                + output.warn("Some checks failed — demo may still run with stubs."),
                file=sys.stderr,
            )
    return 0 if summary["all_ok"] else 1


def _shared_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--db",
        default=None,
        help="SQLite ledger path (default: LFFA_LEDGER_DB or ./.lffa/ledger.db)",
    )
    shared.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output",
    )
    return shared


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lffa",
        description=(
            "Local-First Financial Agent — personal SQLite ledger, local Ollama SLM, "
            "optional Nosana overflow and Arweave provenance stubs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    shared = _shared_parser()
    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    sub.add_parser(
        "version",
        parents=[shared],
        help="Print version and exit (same as --version)",
    ).set_defaults(func=cmd_version)

    sub.add_parser(
        "seed",
        parents=[shared],
        help="Insert sample transactions when the ledger is empty",
    ).set_defaults(func=cmd_seed)

    add_p = sub.add_parser(
        "add",
        parents=[shared],
        help="Add a transaction (amount in cents, e.g. -1299)",
    )
    add_p.add_argument("description", help="Short label (e.g. Coffee shop)")
    add_p.add_argument("amount_cents", type=int, help="Signed integer cents; negative = expense")
    add_p.add_argument("--category", default="uncategorized", help="Budget category")
    add_p.add_argument("--tags", default="", help="Comma-separated tags (optional)")
    add_p.add_argument("--notes", default="", help="Free-form notes")
    add_p.set_defaults(func=cmd_add)

    list_p = sub.add_parser(
        "list",
        parents=[shared],
        help="List recent transactions (newest first)",
    )
    list_p.add_argument("--limit", type=int, default=20, help="Max rows (default: 20)")
    list_p.set_defaults(func=cmd_list)

    sum_p = sub.add_parser(
        "summary",
        parents=[shared],
        help="Income, expense, net, and category breakdown",
    )
    sum_p.add_argument(
        "--by",
        choices=("category", "tag"),
        default=None,
        help="Print only a category or tag breakdown",
    )
    sum_p.set_defaults(func=cmd_summary)

    ask_p = sub.add_parser(
        "ask",
        parents=[shared],
        help="Ask a natural-language question (routes to Ollama or overflow)",
    )
    ask_p.add_argument("question", help="Question about your ledger")
    ask_p.set_defaults(func=cmd_ask)

    demo_p = sub.add_parser(
        "demo",
        parents=[shared],
        help="Seed if needed, print summary, run one agent turn (hackathon walkthrough)",
    )
    demo_p.add_argument("--question", default=None, help="Override the default demo question")
    demo_p.add_argument(
        "--long-context",
        action="store_true",
        help="Also run a synthetic overflow routing probe",
    )
    demo_p.set_defaults(func=cmd_demo)

    exp_p = sub.add_parser(
        "export",
        parents=[shared],
        help="Export ledger to JSON (stdout or file)",
    )
    exp_p.add_argument("-o", "--output", default=None, help="Write JSON to this path")
    exp_p.set_defaults(func=cmd_export)

    imp_p = sub.add_parser(
        "import",
        parents=[shared],
        help="Import ledger from JSON export",
    )
    imp_p.add_argument("file", help="Path to JSON file from lffa export")
    imp_p.add_argument(
        "--merge",
        action="store_true",
        help="Keep existing rows; default replaces all transactions",
    )
    imp_p.set_defaults(func=cmd_import)

    sub.add_parser(
        "doctor",
        parents=[shared],
        help="Check Ollama, Nosana key presence, and ledger path writability",
    ).set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    config.reset_config_cache()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.db is None:
        args.db = str(default_db_path())
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
