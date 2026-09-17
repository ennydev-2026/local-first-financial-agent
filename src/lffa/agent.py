"""Personal financial agent loop — STUB orchestration over local ledger + routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lffa import embeddings
from lffa import ledger
from lffa import nosana_overflow
from lffa import slm
from lffa.arweave_provenance import build_artifact, format_artifact_line


@dataclass(frozen=True)
class AgentTurnResult:
    user_message: str
    assistant_reply: str
    routing: nosana_overflow.RoutingDecision
    embedding_model: str
    slm_backend: str
    slm_notice: str | None
    provenance_line: str


def _build_context(db_path: Path, user_message: str) -> str:
    summary = ledger.summarize(db_path)
    txs = ledger.list_transactions(db_path, limit=10)
    lines = [
        "You are a local-first personal budgeting assistant (hackathon demo).",
        f"Ledger: {summary.transaction_count} transactions, net {ledger.format_cents(summary.net_cents)}.",
        "Recent transactions:",
    ]
    for tx in txs:
        lines.append(
            f"  - {tx.description}: {ledger.format_cents(tx.amount_cents)} ({tx.category})"
        )
    lines.append("")
    lines.append(f"User: {user_message}")
    return "\n".join(lines)


def run_turn(db_path: Path, user_message: str) -> AgentTurnResult:
    """One agent step: embed locally, route inference, reply via Ollama or stub."""
    context = _build_context(db_path, user_message)
    emb = embeddings.embed_text(user_message)
    routing = nosana_overflow.decide_route(context)

    if routing.route == nosana_overflow.InferenceRoute.NOSANA_OVERFLOW:
        job = nosana_overflow.build_overflow_job(context)
        nosana_overflow.submit_overflow_job(job)
        reply = (
            "[stub] Heavy context would run on Nosana GPU. "
            "Locally we only show routing + ledger-aware placeholder text."
        )
    else:
        completion = slm.complete_local(context, embedding_model=emb.model)
        reply = completion.text
        slm_backend = completion.backend
        slm_notice = completion.notice
    if routing.route == nosana_overflow.InferenceRoute.NOSANA_OVERFLOW:
        slm_backend = "n/a"
        slm_notice = None

    artifact = build_artifact(
        "agent_turn",
        {
            "user_message": user_message,
            "route": routing.route.value,
            "slm_backend": slm_backend,
            "reply_preview": reply[:200],
        },
    )
    return AgentTurnResult(
        user_message=user_message,
        assistant_reply=reply,
        routing=routing,
        embedding_model=emb.model,
        slm_backend=slm_backend,
        slm_notice=slm_notice,
        provenance_line=format_artifact_line(artifact),
    )
