# Local-First Financial Agent (LFFA)

Personal budgeting CLI for the **Decentralize AI Hackathon** (HackerNoon, Nosana, Arweave). Your ledger lives in **SQLite on your machine**. Routine questions go to a **local SLM** (Ollama). **Large context** can overflow to **Nosana** when configured. **Arweave** is an optional provenance layer (hash today; on-chain upload not implemented).

This is an open-source hackathon scaffold — **not** a Finanzalia product, **not** a trading bot, **not** a cloud SaaS.

Tags: `#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`

*Agente financiero local-first: el libro mayor en tu dispositivo; inferencia local por defecto.*

## Why local-first

Most “AI finance” flows send your transaction history to a vendor API. LFFA keeps the **system of record on disk**, builds agent context locally, and only touches decentralized services when you configure them and the routing heuristic says the job is too large for on-device inference.

## Quick start

**Requirements:** Python 3.10+, no runtime dependencies beyond the stdlib.

```bash
git clone https://github.com/ennydev-2026/local-first-financial-agent.git
cd local-first-financial-agent
pip install -e .
cp .env.example .env   # optional
```

```bash
lffa seed
lffa demo
lffa doctor            # Ollama, Nosana key, writable DB path
```

Ledger file default: `./.lffa/ledger.db` (override with `LFFA_LEDGER_DB`).

### Optional: Ollama (real local SLM)

1. Install [Ollama](https://ollama.com/).
2. `ollama pull llama3.2:1b`
3. Ensure the daemon listens at `http://127.0.0.1:11434` (default).

```bash
lffa ask "How much did I spend on food?"
lffa ask "How much did I spend on food?" --json   # machine-readable routing telemetry
```

If Ollama is down or the model is missing, you get a **stub reply** and a one-line notice on stderr — exit code stays `0`.

## What works vs stub

| Component | Status |
|-----------|--------|
| SQLite ledger, `add` / `list` / `summary`, categories & tags | **Working** |
| `export` / `import` JSON backup | **Working** |
| Config module (`lffa.config`), `lffa doctor` | **Working** |
| Embeddings | **Stub** (`stub-sha256-local-v0`, deterministic, not semantic) |
| Local SLM | **Ollama** via stdlib HTTP, else **stub** |
| Routing (`local_slm` vs `nosana_overflow`) | **Working** (char budget + `LFFA_FORCE_LOCAL`) |
| Nosana overflow | **HTTP client** when API key set; **stub** without key or on failure |
| Arweave | **SHA-256 artifact**; wallet path validated; **upload not implemented** |

We do **not** invent live Nosana job success or fake Arweave `tx_id` values.

## CLI reference

Global options on each subcommand: `--db PATH`, `--json`.

| Command | Purpose |
|---------|---------|
| `lffa version` | Print version (`0.2.0`) |
| `lffa seed` | Sample transactions if ledger is empty |
| `lffa add DESC CENTS` | Add row (`--category`, `--tags`, `--notes`) |
| `lffa list` | Recent transactions (`--limit`) |
| `lffa summary` | Totals; `--by category` or `--by tag` |
| `lffa ask QUESTION` | Agent turn with routing telemetry |
| `lffa demo` | Seed + summary + ask; `--long-context` for overflow probe |
| `lffa export` | JSON backup (`-o file.json`) |
| `lffa import FILE` | Restore backup (`--merge` to append) |
| `lffa doctor` | Health checks (exit `1` if any check fails) |

Full flag detail: [docs/cli.md](./docs/cli.md).

## Environment variables

Prefer **`LFFA_*`** names. Legacy `NOSANA_*` / `ARWEAVE_*` aliases are supported — see [.env.example](./.env.example).

| Variable | Default | Role |
|----------|---------|------|
| `LFFA_LEDGER_DB` | `./.lffa/ledger.db` | SQLite path |
| `LFFA_DATA_DIR` | `./.lffa` | Data directory (used when `LFFA_LEDGER_DB` unset) |
| `LFFA_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API |
| `LFFA_OLLAMA_MODEL` | `llama3.2:1b` | Model tag |
| `LFFA_LOCAL_MAX_CONTEXT_CHARS` | `4000` | Local vs overflow threshold |
| `LFFA_FORCE_LOCAL` | `0` | If `1`, never route to overflow |
| `LFFA_NOSANA_API_KEY` / `NOSANA_API_KEY` | — | Nosana bearer token |
| `LFFA_NOSANA_API_BASE` | `https://api.nosana.com` | API base |
| `NOSANA_IPFS_HASH` | — | Required to **post** a real GPU job |
| `LFFA_ARWEAVE_WALLET_JWK_PATH` | — | Wallet JWK (validated only) |

Loaded and validated in `src/lffa/config.py`.

## Architecture

```
lffa CLI → agent.run_turn()
         → ledger (SQLite)
         → embeddings (stub)
         → nosana_overflow.decide_route()
              ├─ local_slm → slm.complete_local() → Ollama | stub
              └─ nosana_overflow → submit_overflow_job() → HTTP | stub
         → arweave_provenance (hash + optional upload attempt)
```

Diagram and extension points: [ARCHITECTURE.md](./ARCHITECTURE.md).

## Hackathon context

- **Problem:** Sensitive personal finance data routed through centralized inference by default.
- **Approach:** Local ledger + local SLM first; Nosana for overflow; Arweave for optional integrity metadata.
- **Nosana credits:** [docs/nosana-credits.md](./docs/nosana-credits.md)
- **Judge demo script:** [docs/hackathon.md](./docs/hackathon.md)
- **Blog draft:** [docs/hackernoon-draft.md](./docs/hackernoon-draft.md)

## Project layout

```
src/lffa/
  config.py              # env loading, validation, public config dict
  cli.py                 # entrypoint
  ledger.py              # SQLite + export/import
  agent.py               # agent turn orchestration
  slm.py                 # Ollama + stub
  nosana_overflow.py     # routing + Nosana HTTP
  arweave_provenance.py  # provenance artifacts
  doctor.py              # health checks
  embeddings.py          # embedding stub
tests/
docs/
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Issues and PRs welcome; keep changes small and tested.

## License

MIT — [LICENSE](./LICENSE).
