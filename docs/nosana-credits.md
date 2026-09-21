# Nosana credits (Decentralize AI Hackathon)

Nosana sponsors GPU **overflow** for hackathon projects. LFFA uses Nosana only when local context exceeds your on-device budget — not for every CLI command.

## Claim ~$70 in credits (first 500 hackers)

1. Open the official hackathon claim flow: [https://decentralizeai.tech/claim/nosana](https://decentralizeai.tech/claim/nosana)  
   (If that URL moves, check [Decentralize AI](https://decentralizeai.tech/) for the current Nosana claim link.)
2. Follow the steps to connect your account and receive API access / credits.
3. Copy your **Nosana API key** into `.env`:

```bash
NOSANA_API_KEY=nos_xxx_your_key
# or
LFFA_NOSANA_API_KEY=nos_xxx_your_key
```

Optional API base (default is production):

```bash
LFFA_NOSANA_API_BASE=https://api.nosana.com
```

## Using credits without burning them accidentally

Hackathon docs warn that some **deployment strategies** (for example **Infinite** scaling) can keep spawning jobs and **drain credits quickly**. Prefer a **Simple** strategy or one-shot **Jobs** when you only need bursty inference for large prompts.

LFFA defaults to a safe path:

| Configuration | What LFFA does |
|---------------|----------------|
| API key only | Verifies `/api/credits/balance`, builds an overflow **work payload** — **no GPU job posted** |
| `NOSANA_IPFS_HASH` + `NOSANA_MARKET` | Attempts `POST /api/jobs/list` to start a real job (spends credits) |

Pin a job definition to IPFS first (Nosana Kit / CLI / your own Pinata JWT), then set:

```bash
NOSANA_IPFS_HASH=QmYourPinnedJobDefinition
NOSANA_MARKET=97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf
NOSANA_JOB_TIMEOUT=600
```

See [Nosana Jobs API](https://learn.nosana.com/api/jobs.html) and [inference endpoints](https://learn.nosana.com/inference/endpoints.html).

## Demo in LFFA

```bash
lffa doctor                    # confirms key presence (masked) without leaking secrets
lffa demo --long-context
lffa demo --long-context --json   # machine-readable routing + submit status
```

Look for `Overflow backend: nosana` or `stub` in the output (same idea as `SLM backend: ollama|stub` for local inference). In JSON mode, inspect `routing` and `overflow_probe.submit_backend`.

## Limitations (honest)

- LFFA does **not** bundle IPFS pinning; you must provide `NOSANA_IPFS_HASH` for on-network jobs.
- Overflow replies in the agent are still **placeholders** until you wire a live inference endpoint URL from a running Nosana job.
- No trading, no exchange APIs — personal ledger demo only.
