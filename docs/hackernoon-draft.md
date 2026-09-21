# My Financial Agent Never Had to Phone Home for a Budget Answer

**Subtitle:** A local-first personal ledger, on-device embeddings (stub today), and a small language model on Ollama — with Nosana and Arweave only where decentralization actually earns its keep.

---

## Context

Personal finance apps are quietly becoming surveillance products. You paste a question about groceries, and somewhere between “summarize my spending” and the chat bubble, your transaction history crosses a vendor boundary you never opted into with clear eyes.

For the **Decentralize AI Hackathon** (HackerNoon, Nosana, Arweave), I wanted a counter-story: an **agentic budgeting assistant** that treats your laptop as the system of record. Not a crypto trading bot. Not an exchange dashboard. Just **SQLite, a CLI, and inference routing** that defaults to **local** and only *signals* overflow when the job is too heavy for the machine in front of you.

The repo is honest scaffolding: the ledger is real; Ollama integration is real when you run it; Nosana job submission is **real when you set an API key and IPFS hash**; Arweave uploads are **not implemented** — we hash artifacts and report status. That transparency is part of the hackathon narrative.

## Strategy: local-first, decentralize on purpose

**1. Own the ledger.** Transactions live in `./.lffa/ledger.db`. `lffa export` / `lffa import` give you a portable JSON backup — your file, your rules.

**2. Embed on-device (incrementally).** Today we use a deterministic local embedding stub (`stub-sha256-local-v0`) so retrieval plumbing exists without downloading models.

**3. Answer routine questions with a local SLM.** When context fits `LFFA_LOCAL_MAX_CONTEXT_CHARS`, the agent calls **Ollama** at `http://127.0.0.1:11434` (default model `llama3.2:1b`). If Ollama is down, stub reply + stderr notice.

**4. Overflow to Nosana when the heuristic says so.** Oversized context routes to the Nosana client: API key verifies credits; optional `NOSANA_IPFS_HASH` posts a job. Agent overflow **text** is still a placeholder until you wire live inference output.

**5. Provenance on Arweave, optionally.** Each turn emits SHA-256 metadata. Wallet JWK path is validated; on-chain upload returns `upload_not_implemented` — no fake transaction ids.

## Stack

| Layer | What ships in v0.2.0 |
|-------|----------------------|
| **Ledger** | SQLite + categories, tags, export/import |
| **Config** | `config.py` — single env surface + `lffa doctor` |
| **Embeddings** | Stub vectors (labeled) |
| **Agent** | `agent.py` + `--json` routing telemetry |
| **Local SLM** | Ollama HTTP (stdlib) |
| **Overflow** | Nosana HTTP + stub fallback |
| **Provenance** | Hash + honest upload status |

**Routing:** under budget → `local_slm` → Ollama; over budget → `nosana_overflow`. `LFFA_FORCE_LOCAL=1` keeps everything on-device for demos.

## Try it (what actually works)

```bash
pip install -e .
lffa doctor
lffa seed
lffa demo
lffa ask "How am I doing on food spending?" --json
```

With Ollama:

```bash
ollama pull llama3.2:1b
lffa ask "How much did I spend on food?"
```

Look for `slm_backend: ollama` in `--json` output. Without Ollama, `slm_backend: stub` with a clear notice.

Overflow probe:

```bash
lffa demo --long-context
```

## What I’d tell a skeptical developer

- **Privacy:** Transactions stay on disk unless you export them. Ollama is localhost by default.
- **Latency:** Small models on hardware you own beat round-trips for “what did I spend on food?”
- **Decentralization where it fits:** Nosana for **overflow**, not CRUD. Arweave for **audit metadata**, not your primary database.
- **Honest gaps:** No semantic embeddings yet. Overflow reply text is not live GPU output. Arweave upload is TODO.

## Roadmap (post-hackathon)

1. On-device embedding model.
2. Poll Nosana job output into the agent reply path.
3. Arweave anchor for turn artifacts.
4. Local retrieval over embedded transaction notes.

## Closing

Local-first isn’t nostalgia for SQLite; it’s a **default stance** for agentic tools that touch sensitive life data. This project is a hackathon-sized proof: **working ledger, working local SLM path, deliberate stubs everywhere else** — so the story stays true when you paste it into a blog or a judge’s terminal.

---

**Repo:** https://github.com/ennydev-2026/local-first-financial-agent  
**Tags:** `#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`
