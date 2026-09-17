# My Financial Agent Never Had to Phone Home for a Budget Answer

**Subtitle:** A local-first personal ledger, on-device embeddings (stub today), and a small language model on Ollama — with Nosana and Arweave only where decentralization actually earns its keep.

---

## Context

Personal finance apps are quietly becoming surveillance products. You paste a question about groceries, and somewhere between “summarize my spending” and the chat bubble, your transaction history crosses a vendor boundary you never opted into with clear eyes.

For the **Decentralize AI Hackathon** (HackerNoon, Nosana, Arweave), I wanted a counter-story: an **agentic budgeting assistant** that treats your laptop as the system of record. Not a crypto trading bot. Not an exchange dashboard. Just **SQLite, a CLI, and inference routing** that defaults to **local** and only *signals* overflow when the job is too heavy for the machine in front of you.

The repo is honest scaffolding: the ledger is real; Ollama integration is real when you run it; Nosana job submission and Arweave uploads are **interfaces and stubs** until someone wires credentials and HTTP. That transparency is part of the hackathon narrative — show the architecture, ship one working local path, don’t pretend the rest is production.

## Strategy: local-first, decentralize on purpose

**1. Own the ledger.** Transactions live in `./.lffa/ledger.db` (configurable). Export, delete, backup — your file, your rules.

**2. Embed on-device (incrementally).** Today we use a deterministic local embedding stub (`stub-sha256-local-v0`) so retrieval plumbing exists without downloading models. The next step is a small on-device encoder; the constraint is unchanged: **no cloud embedding API required for the demo.**

**3. Answer routine questions with a local SLM.** When context fits the local budget (`LFFA_LOCAL_MAX_CONTEXT_CHARS`), the agent builds a prompt from ledger summary + recent rows and calls **Ollama** at `http://127.0.0.1:11434` (model default: `llama3.2:1b`). If Ollama is down or the model isn’t pulled, you still get a **stub reply and a one-line notice** — the CLI doesn’t crash, which matters for judges cloning the repo on a plane.

**4. Overflow to Nosana only when the heuristic says so.** Oversized context routes to a **Nosana overflow stub**: we log the decision and the job shape, but we do **not** claim live GPU jobs in v0.1. That’s the hackathon “second act”: decentralized compute for bursty inference, not for every `lffa list`.

**5. Provenance on Arweave, optionally.** Each turn can emit a canonical JSON artifact and SHA-256 fingerprint (`arweave_provenance.py`). Upload to Arweave is stubbed — integrity metadata without pretending your ledger lives on chain.

## Stack

| Layer | What ships in the repo | Why |
|-------|------------------------|-----|
| **Ledger** | SQLite + `lffa` CLI (`seed`, `add`, `list`, `summary`) | Boring, portable, offline |
| **Embeddings** | Stub vectors (labeled) | Privacy-preserving placeholder for retrieval |
| **Agent** | `agent.py` orchestration | Builds context, routes, calls SLM |
| **Local SLM** | `slm.py` → Ollama HTTP (stdlib `urllib`) | Real local inference path |
| **Overflow** | `nosana_overflow.py` | Routing + job struct; **no live API** |
| **Provenance** | `arweave_provenance.py` | Hash + metadata; **no live upload** |

**Model routing (demo heuristic):** under the character budget → `local_slm` → Ollama; over budget → `nosana_overflow` → stub GPU job narrative. Set `LFFA_FORCE_LOCAL=1` to always stay on-device for demos.

## Try it (what actually works)

```bash
pip install -e .
lffa seed
lffa demo
```

With Ollama:

```bash
# https://ollama.com — install, then:
ollama pull llama3.2:1b
lffa ask "How am I doing on food spending?"
```

You should see `SLM backend: ollama` in the routing section. Without Ollama, the same commands print a clear fallback line on stderr and a stub answer — still a valid demo.

Force overflow routing (still stubbed Nosana):

```bash
lffa demo --long-context
```

## What I’d tell a skeptical developer

- **Privacy:** Your transactions never leave disk unless *you* choose a future sync path. The agent prompt is assembled locally; Ollama is localhost.
- **Latency:** Small models on CPU/GPU you already own beat round-trips for “what did I spend on food?”
- **Decentralization where it fits:** Nosana is for **overflow**, not CRUD. Arweave is for **audit trails**, not your primary database.
- **Honest gaps:** No semantic embeddings yet. No Nosana HTTP. No Arweave wallet flow. The README table says so.

## Roadmap (post-hackathon)

1. Swap embedding stub for a tiny on-device model.
2. One real Nosana job template for overflow prompts.
3. Optional Arweave anchor for turn artifacts with wallet JWK from env.
4. Retrieval over embedded transaction notes — still local index first.

## Closing

Local-first isn’t nostalgia for SQLite; it’s a **default stance** for agentic tools that touch sensitive life data. This project is a hackathon-sized proof: **working ledger, working local SLM path, deliberate stubs everywhere else** — so the story stays true when you paste it into a blog or a judge’s terminal.

Repo: [github.com/ennydev-2026/local-first-financial-agent](https://github.com/ennydev-2026/local-first-financial-agent)

---

**Author footer (do not publish as body — tag hints for HackerNoon / contest):**

Suggested tags: `#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`  
Nosana-related (if the publication form allows): `#nosana` `#decentralized-gpu` `#gpu-inference`  
Arweave-related (optional): `#arweave` `#data-provenance`
