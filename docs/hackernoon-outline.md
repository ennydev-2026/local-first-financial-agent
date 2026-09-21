# HackerNoon post outline — Local-First Financial Agent

Contest tags: `#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`

---

## Context

- Problem: Personal finance tools often ship transaction history and prompts to centralized AI APIs.
- Hackathon angle (HackerNoon / Nosana / Arweave): show **local-first** budgeting with **selective** decentralization — GPU only when needed, provenance only when you want it.
- Audience: developers building agentic tools who care about privacy and edge inference.

## Strategy

1. **Own the ledger** — SQLite on device; user controls export/delete.
2. **Embed locally** — Start with stub, swap in small on-device embedding model.
3. **Default to local SLM** — Routine questions stay on CPU/GPU you already have.
4. **Overflow deliberately** — Large context / heavy jobs → Nosana (document job shape, not hype).
5. **Prove optionally** — Hash agent summaries; Arweave as audit trail, not primary store.

## Stack

| Layer | Choice (scaffold) | Production path |
|-------|-------------------|-----------------|
| Ledger | SQLite (stdlib) | Same or sync to user-owned backup |
| Embeddings | Stub → local model | e.g. small transformer on device |
| Agent | Python orchestration | Same + real SLM runtime |
| Heavy inference | Nosana interface (stub) | Nosana API + job templates |
| Provenance | Arweave stub | Signed bundles via wallet JWK |

## Model (article structure)

1. **Hook** — "My financial agent never saw my transactions leave the laptop."
2. **Demo video / CLI** — `lffa demo` showing routing line.
3. **Architecture diagram** — Link to `ARCHITECTURE.md` in repo.
4. **Local-first wins** — Latency, privacy, offline.
5. **When decentralization helps** — Burst GPU, not everyday CRUD.
6. **Honest limitations** — Embedding stub; overflow reply placeholder; Arweave upload TODO; Nosana HTTP real when keyed.
7. **Roadmap** — Semantic embeddings, Nosana output polling, Arweave anchor, retrieval.
8. **Call to action** — Star repo, try hackathon scaffold, feedback welcome.

## Spanish blurb (optional lead)

*Agente financiero personal que guarda transacciones y contexto en tu dispositivo; IA ligera local y GPU descentralizada solo cuando hace falta.*
