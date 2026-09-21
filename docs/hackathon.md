# Hackathon submission guide

**Project:** Local-First Financial Agent (LFFA)  
**Event:** Decentralize AI Hackathon (HackerNoon, Nosana, Arweave)  
**Repository:** https://github.com/ennydev-2026/local-first-financial-agent

## Problem

Personal finance assistants often require sending transaction history and natural-language questions to centralized inference APIs. Users lose control of the system of record and the inference boundary.

## Solution

LFFA keeps a **SQLite ledger on the user’s device**, builds agent context locally, answers routine questions with **Ollama** when available, and routes **oversized context** to **Nosana** only when configured and over the char budget. **Arweave** stores integrity metadata (SHA-256) with honest upload status — not a replacement database.

## Stack

| Layer | Technology | Hackathon role |
|-------|------------|----------------|
| Ledger | SQLite, stdlib | Local-first source of truth |
| CLI | `argparse`, `lffa` | Demo + developer UX |
| Embeddings | Stub hash vectors | Placeholder for on-device retrieval |
| Local inference | Ollama HTTP | Real offline-capable path |
| Overflow | Nosana REST API | Decentralized GPU when context is large |
| Provenance | Arweave gateway + JWK path | Optional audit trail (upload TODO) |

## What works offline

- `seed`, `add`, `list`, `summary`, `export`, `import`
- Agent turn with **stub SLM** (no Ollama, no Nosana)
- Routing decisions and `--json` telemetry
- Provenance **hash** line (no chain upload)

## What needs network / setup

| Feature | Requirement |
|---------|-------------|
| Real local answers | Ollama running + model pulled |
| Nosana balance check | `NOSANA_API_KEY` or `LFFA_NOSANA_API_KEY` |
| Nosana job post | Above + `NOSANA_IPFS_HASH` (+ market, timeout) |
| Arweave wallet validation | `LFFA_ARWEAVE_WALLET_JWK_PATH` pointing at JWK file |

## Nosana credits

Claim flow and safe usage: [nosana-credits.md](./nosana-credits.md).  
With only an API key, LFFA verifies credits and prepares overflow work — it does **not** post a GPU job until `NOSANA_IPFS_HASH` is set.

## Judge demo script (~3 minutes)

```bash
pip install -e .
lffa doctor
lffa seed
lffa summary --by category
lffa demo
lffa demo --long-context
lffa export -o /tmp/lffa-backup.json
```

**Optional (if Ollama installed):**

```bash
ollama pull llama3.2:1b
lffa ask "How am I doing on food spending?" --json
```

Point judges at the `routing` object in JSON: `route`, `reason`, `force_local`, `within_local_budget`.

**Optional (if Nosana key in `.env`):**

```bash
lffa demo --long-context
```

Expect `Overflow backend: nosana` when the API key validates; job post only if IPFS hash is configured.

## Honesty about stubs

- Embeddings are **not** semantic models.
- Overflow **agent text** is still a placeholder until you wire live inference output from a Nosana job.
- Arweave **does not** submit transactions in this repo version (`upload_not_implemented` when wallet is present).
- No crypto trading, no MEXC, no exchange integrations.

## Links

- [README](../README.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
- [HackerNoon draft](./hackernoon-draft.md)
- [Nosana API](https://learn.nosana.com/api/intro.html)
- [Arweave](https://www.arweave.org/)

## Tags

`#decentralize-ai` `#decentralize-ai-hackathon` `#agentic-ai` `#ai-inference` `#developer-tools`
