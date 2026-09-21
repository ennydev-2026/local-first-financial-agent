# CLI reference

Entry point: `lffa` (installed via `pip install -e .`).

## Global options (per subcommand)

| Flag | Description |
|------|-------------|
| `--db PATH` | SQLite ledger file (default from `LFFA_LEDGER_DB` or `./.lffa/ledger.db`) |
| `--json` | Print structured JSON instead of human text (where supported) |

Top-level only:

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Help |
| `--version` | Version string |

## Commands

### `lffa version`

Print `lffa 0.2.0` and exit `0`.

### `lffa seed`

Insert demo transactions when the ledger is empty. Exit `0`. With `--json`, returns `{ "seeded", "ids", "db", "skipped" }`.

### `lffa add DESCRIPTION AMOUNT_CENTS`

| Flag | Default | Notes |
|------|---------|-------|
| `--category` | `uncategorized` | Budget category |
| `--tags` | empty | Comma-separated tags |
| `--notes` | empty | Free text |

Amounts are **integer cents** (e.g. `-1299` = −$12.99).

### `lffa list`

| Flag | Default |
|------|---------|
| `--limit` | `20` |

### `lffa summary`

Print income, expense, net, and category breakdown.

| Flag | Effect |
|------|--------|
| `--by category` | Only category breakdown |
| `--by tag` | Only tag breakdown |

### `lffa ask QUESTION`

Run one agent turn. Stderr may contain Ollama/Nosana fallback notices. `--json` emits full `AgentTurnResult` including `routing` telemetry.

### `lffa demo`

Seeds if needed, prints summary, runs default question (override with `--question`). `--long-context` adds synthetic overflow probe.

### `lffa export`

Writes ledger JSON to stdout, or to `-o` / `--output` path.

### `lffa import FILE`

Replace ledger contents from export (use `--merge` to keep existing rows and append).

### `lffa doctor`

Checks config validation, Ollama reachability/model, Nosana key presence (masked), ledger directory writable. Exit `0` if all checks pass, `1` otherwise. `--json` for automation.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Command error (e.g. import parse failure, doctor failure) |
| `2` | Usage error (argparse) |
| `130` | Interrupted (Ctrl+C) |

## Environment

See [README](../README.md#environment-variables) and [.env.example](../.env.example).

## Color output

ANSI colors apply on TTY stdout unless `NO_COLOR` or `LFFA_NO_COLOR=1` is set.
