"""Personal financial agent loop — local ledger + routing + inference backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lffa import embeddings
from lffa import ledger
from lffa import nosana_overflow
from lffa import slm
from lffa.arweave_provenance import build_artifact, format_artifact_line, upload_artifact


@dataclass(frozen=True)
class AgentTurnResult:
    user_message: str
    assistant_reply: str
    routing: nosana_overflow.RoutingDecision
    embedding_model: str
    slm_backend: str
    slm_notice: str | None
    overflow_backend: str | None
    overflow_notice: str | None
    provenance_line: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_message": self.user_message,
            "assistant_reply": self.assistant_reply,
            "routing": self.routing.to_dict(),
            "embedding_model": self.embedding_model,
            "slm_backend": self.slm_backend,
            "slm_notice": self.slm_notice,
            "overflow_backend": self.overflow_backend,
            "overflow_notice": self.overflow_notice,
            "provenance_line": self.provenance_line,
        }


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
    """One agent step: embed locally, route inference, reply via Ollama/stub or Nosana overflow."""
    context = _build_context(db_path, user_message)
    emb = embeddings.embed_text(user_message)
    routing = nosana_overflow.decide_route(context)

    overflow_backend: str | None = None
    overflow_notice: str | None = None
    slm_backend = "n/a"
    slm_notice: str | None = None

    if routing.route == nosana_overflow.InferenceRoute.NOSANA_OVERFLOW:
        job = nosana_overflow.build_overflow_job(context)
        submit = nosana_overflow.submit_overflow_job(job)
        overflow_backend = submit.backend
        overflow_notice = submit.notice
        status = (submit.payload or {}).get("status", "unknown")
        reply = (
            f"[Nosana overflow — backend={submit.backend}] "
            f"Heavy context routed off-device (status={status}). "
            "Ledger-aware placeholder; configure NOSANA_IPFS_HASH to post a real GPU job."
        )
    else:
        completion = slm.complete_local(context, embedding_model=emb.model)
        reply = completion.text
        slm_backend = completion.backend
        slm_notice = completion.notice

    artifact = build_artifact(
        "agent_turn",
        {
            "user_message": user_message,
            "route": routing.route.value,
            "slm_backend": slm_backend,
            "overflow_backend": overflow_backend,
            "reply_preview": reply[:200],
        },
    )
    upload = upload_artifact(artifact, {"user_message": user_message, "route": routing.route.value})
    provenance_line = format_artifact_line(artifact, upload_status=upload.get("status"))

    return AgentTurnResult(
        user_message=user_message,
        assistant_reply=reply,
        routing=routing,
        embedding_model=emb.model,
        slm_backend=slm_backend,
        slm_notice=slm_notice,
        overflow_backend=overflow_backend,
        overflow_notice=overflow_notice,
        provenance_line=provenance_line,
    )
