"""Nosana decentralized GPU overflow — STUB + interface.

This module does NOT call Nosana APIs. It models how a heavy inference job
would be routed off-device when local SLM context or compute is insufficient.

Wire-up TODO: use NOSANA_* env vars from .env.example when implementing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InferenceRoute(str, Enum):
    LOCAL_SLM = "local_slm"
    NOSANA_OVERFLOW = "nosana_overflow"


@dataclass(frozen=True)
class RoutingDecision:
    route: InferenceRoute
    reason: str
    estimated_context_chars: int
    local_max_chars: int
    nosana_configured: bool


def _local_max_chars() -> int:
    raw = os.environ.get("LFFA_LOCAL_MAX_CONTEXT_CHARS", "4000")
    try:
        return max(256, int(raw))
    except ValueError:
        return 4000


def _force_local() -> bool:
    return os.environ.get("LFFA_FORCE_LOCAL", "0").strip() in ("1", "true", "yes")


def nosana_credentials_present() -> bool:
    return bool(os.environ.get("NOSANA_API_URL") and os.environ.get("NOSANA_API_KEY"))


def decide_route(
    prompt: str,
    *,
    local_max_chars: Optional[int] = None,
) -> RoutingDecision:
    """Choose local SLM vs Nosana overflow based on context size (demo heuristic)."""
    limit = local_max_chars if local_max_chars is not None else _local_max_chars()
    size = len(prompt)
    configured = nosana_credentials_present()

    if _force_local():
        return RoutingDecision(
            route=InferenceRoute.LOCAL_SLM,
            reason="LFFA_FORCE_LOCAL is set — always run on-device in this demo.",
            estimated_context_chars=size,
            local_max_chars=limit,
            nosana_configured=configured,
        )

    if size <= limit:
        return RoutingDecision(
            route=InferenceRoute.LOCAL_SLM,
            reason=f"Context ({size} chars) fits local SLM budget (≤ {limit}).",
            estimated_context_chars=size,
            local_max_chars=limit,
            nosana_configured=configured,
        )

    return RoutingDecision(
        route=InferenceRoute.NOSANA_OVERFLOW,
        reason=(
            f"Context ({size} chars) exceeds local budget ({limit}). "
            "Would submit overflow job to Nosana (stub — no network call)."
        ),
        estimated_context_chars=size,
        local_max_chars=limit,
        nosana_configured=configured,
    )


@dataclass(frozen=True)
class NosanaJobRequest:
    """Shape of a future Nosana job payload (not sent in scaffold)."""

    job_type: str
    prompt: str
    metadata: dict[str, str]


def build_overflow_job(prompt: str, job_type: str = "financial_qa") -> NosanaJobRequest:
    return NosanaJobRequest(
        job_type=job_type,
        prompt=prompt,
        metadata={"source": "lffa", "status": "stub"},
    )


def submit_overflow_job(request: NosanaJobRequest) -> dict[str, str]:
    """STUB: returns a fake job id. Implement HTTP client against Nosana later."""
    return {
        "status": "stub_not_submitted",
        "message": "Nosana overflow is not implemented in this hackathon scaffold.",
        "job_type": request.job_type,
        "prompt_chars": str(len(request.prompt)),
    }
