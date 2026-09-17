# Local-First Financial Agent (LFFA)

Hackathon demo scaffold for the **Decentralize AI Hackathon** (HackerNoon / Nosana / Arweave).  
**Not a production product** — a personal budgeting agent story: transactions, embeddings, and context stay **on your device**; a small **local SLM** handles routine questions when possible; **heavy jobs overflow to Nosana** (stub); **optional provenance** to Arweave (stub).

`#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`

*Agente financiero local-first: transacciones y contexto en tu dispositivo; GPU descentralizada solo para trabajos pesados (demo).*

## Pitch

Most “AI finance” apps send your ledger to the cloud. LFFA flips that: **SQLite ledger on disk**, **local embedding stub**, **routing logic** that prefers on-device inference and only marks **Nosana overflow** when context exceeds a budget. Arweave is a **optional integrity layer**, not your database.

No crypto trading. No exchange APIs. Personal ledger + budgeting agent only.

## Architecture (short)

```
CLI → Agent → SQLite ledger
           → Local embeddings (stub)
           → Route: local SLM  OR  Nosana overflow (stub)
           → Optional Arweave hash (stub)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for diagram and data flow.

## Quick start

Requires **Python 3.10+**.

```bash
git clone https://github.com/ennydev-2026/local-first-financial-agent.git
cd local-first-financial-agent
pip install -e .
# or: uv pip install -e .
```

Copy env template (optional — demo works without it):

```bash
cp .env.example .env
```

### Demo command (local-first vs overflow)

```bash
lffa demo
```

Example routing output:

```
--- Inference routing ---
Route: local_slm
Reason: Context (… chars) fits local SLM budget (≤ 4000).
```

Force an overflow decision without sending anything to the network:

```bash
lffa demo --long-context
```

### Other CLI commands

```bash
lffa seed                              # sample transactions (if empty)
lffa add "Lunch" -850 --category food  # amount in cents
lffa list
lffa summary
```

Data defaults to `./.lffa/ledger.db` (override with `LFFA_LEDGER_DB`).

## Stub vs real

| Piece | In this repo |
|-------|----------------|
| SQLite ledger, summary, CLI | **Real** |
| Embeddings | **Stub** (`stub-sha256-local-v0`) |
| Local SLM replies | **Stub** text; routing is real |
| Nosana jobs | **Stub** — `decide_route()` + `submit_overflow_job()` no HTTP |
| Arweave | **Stub** — SHA-256 artifact metadata only |

We do **not** claim live Nosana or Arweave integration until implemented.

## Project layout

```
src/lffa/
  ledger.py              # SQLite transactions
  embeddings.py          # local embedding stub
  agent.py               # agent turn + routing
  nosana_overflow.py     # overflow interface (stub)
  arweave_provenance.py  # provenance stub
  cli.py                 # entrypoint
docs/hackernoon-outline.md
```

## Environment variables

See [.env.example](./.env.example): `NOSANA_*`, `ARWEAVE_*`, `LFFA_LOCAL_MAX_CONTEXT_CHARS`, `LFFA_FORCE_LOCAL`.

## License

MIT — see [LICENSE](./LICENSE).

## Hackathon blog

Outline for a HackerNoon submission: [docs/hackernoon-outline.md](./docs/hackernoon-outline.md).
