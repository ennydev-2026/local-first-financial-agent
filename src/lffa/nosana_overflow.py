"""Nosana decentralized GPU overflow — HTTP client with stub fallback.

When ``NOSANA_API_KEY`` or ``LFFA_NOSANA_API_KEY`` is set, the client talks to the
Nosana HTTP API (default base ``https://api.nosana.com``). Full GPU jobs still need
an IPFS-pinned job definition (``NOSANA_IPFS_HASH`` + ``NOSANA_MARKET``); without
those, we verify the API key and return an honest overflow work payload without
claiming a live job was started.

See ``docs/nosana-credits.md`` and https://learn.nosana.com/api/jobs.html
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from lffa import config

DEFAULT_NOSANA_API_BASE = config.DEFAULT_NOSANA_API_BASE
DEFAULT_NOSANA_MARKET = config.DEFAULT_NOSANA_MARKET


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
    force_local: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route.value,
            "reason": self.reason,
            "estimated_context_chars": self.estimated_context_chars,
            "local_max_chars": self.local_max_chars,
            "nosana_configured": self.nosana_configured,
            "force_local": self.force_local,
            "within_local_budget": self.estimated_context_chars <= self.local_max_chars,
        }


@dataclass(frozen=True)
class NosanaJobRequest:
    """Overflow work sent to Nosana (metadata + prompt for GPU inference)."""

    job_type: str
    prompt: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class NosanaSubmitResult:
    backend: str  # "nosana" | "stub"
    notice: str | None = None
    payload: dict[str, str] | None = None


def _cfg() -> config.LffaConfig:
    return config.get_config()


def nosana_api_key() -> str | None:
    return _cfg().nosana_api_key


def nosana_api_base() -> str:
    return _cfg().nosana_api_base


def nosana_market() -> str:
    return _cfg().nosana_market


def nosana_ipfs_hash() -> str | None:
    return _cfg().nosana_ipfs_hash


def nosana_job_timeout_seconds() -> int:
    return _cfg().nosana_job_timeout_seconds


def nosana_credentials_present() -> bool:
    return _cfg().nosana_configured()


def decide_route(
    prompt: str,
    *,
    local_max_chars: Optional[int] = None,
) -> RoutingDecision:
    """Choose local SLM vs Nosana overflow based on context size (demo heuristic)."""
    cfg = _cfg()
    limit = local_max_chars if local_max_chars is not None else cfg.local_max_context_chars
    size = len(prompt)
    configured = cfg.nosana_configured()
    force = cfg.force_local

    if force:
        return RoutingDecision(
            route=InferenceRoute.LOCAL_SLM,
            reason="LFFA_FORCE_LOCAL is set — always run on-device in this demo.",
            estimated_context_chars=size,
            local_max_chars=limit,
            nosana_configured=configured,
            force_local=True,
        )

    if size <= limit:
        return RoutingDecision(
            route=InferenceRoute.LOCAL_SLM,
            reason=f"Context ({size} chars) fits local SLM budget (≤ {limit}).",
            estimated_context_chars=size,
            local_max_chars=limit,
            nosana_configured=configured,
            force_local=False,
        )

    suffix = (
        "Nosana API key set — overflow client will attempt HTTP."
        if configured
        else "No Nosana API key — overflow stays on stub path."
    )
    return RoutingDecision(
        route=InferenceRoute.NOSANA_OVERFLOW,
        reason=(
            f"Context ({size} chars) exceeds local budget ({limit}). {suffix}"
        ),
        estimated_context_chars=size,
        local_max_chars=limit,
        nosana_configured=configured,
        force_local=False,
    )


def build_overflow_job(prompt: str, job_type: str = "financial_qa") -> NosanaJobRequest:
    return NosanaJobRequest(
        job_type=job_type,
        prompt=prompt,
        metadata={"source": "lffa", "kind": "overflow_inference"},
    )


def build_overflow_work_body(request: NosanaJobRequest) -> dict[str, Any]:
    """JSON work description for overflow (embedded in job meta when pinning off-repo)."""
    preview = request.prompt[:500]
    return {
        "source": "lffa",
        "job_type": request.job_type,
        "prompt_chars": len(request.prompt),
        "prompt_preview": preview,
        "metadata": dict(request.metadata),
    }


def build_container_job_definition(request: NosanaJobRequest) -> dict[str, Any]:
    """Minimal container job definition shape from Nosana docs (for IPFS pin + post)."""
    work = build_overflow_work_body(request)
    return {
        "version": "0.1",
        "type": "container",
        "meta": {
            "trigger": "lffa-overflow",
            "lffa_overflow": work,
        },
        "ops": [
            {
                "type": "container/run",
                "id": "lffa-overflow-placeholder",
                "args": {
                    "image": "docker.io/library/alpine:3.20",
                    "cmd": ["echo", "lffa-overflow-job-placeholder"],
                    "gpu": False,
                },
            }
        ],
    }


def _auth_headers() -> dict[str, str]:
    key = nosana_api_key()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _http_json(
    method: str,
    url: str,
    body: dict | None = None,
    timeout: float = 60.0,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, dict | list]:
    data = None
    headers = {"Accept": "application/json", **_auth_headers()}
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {"error": str(exc)}
        except json.JSONDecodeError:
            payload = {"error": raw or str(exc)}
        return exc.code, payload


def fetch_credits_balance() -> tuple[int, dict | list]:
    url = f"{nosana_api_base()}/api/credits/balance"
    return _http_json("GET", url, timeout=15.0)


def post_job_to_network(ipfs_hash: str, market: str, timeout: int) -> tuple[int, dict | list]:
    """POST /api/jobs/list — documented Nosana job post route (credits)."""
    url = f"{nosana_api_base()}/api/jobs/list"
    body = {
        "ipfsHash": ipfs_hash,
        "market": market,
        "timeout": timeout,
    }
    idem = str(uuid.uuid4())
    return _http_json(
        "POST",
        url,
        body=body,
        timeout=90.0,
        extra_headers={"Idempotency-Key": idem},
    )


def _stub_result(request: NosanaJobRequest, notice: str) -> NosanaSubmitResult:
    return NosanaSubmitResult(
        backend="stub",
        notice=notice,
        payload={
            "status": "stub_not_submitted",
            "job_type": request.job_type,
            "prompt_chars": str(len(request.prompt)),
        },
    )


def _emit_notice(notice: str) -> None:
    print(notice, file=sys.stderr)


def submit_overflow_job(request: NosanaJobRequest) -> NosanaSubmitResult:
    """Submit overflow work to Nosana when configured; otherwise stub (never raises)."""
    if not nosana_api_key():
        notice = (
            "LFFA: No Nosana API key — overflow stub only. "
            "Set NOSANA_API_KEY or LFFA_NOSANA_API_KEY (see docs/nosana-credits.md)."
        )
        _emit_notice(notice)
        return _stub_result(request, notice)

    work = build_overflow_work_body(request)
    ipfs_hash = nosana_ipfs_hash()
    market = nosana_market()
    timeout = nosana_job_timeout_seconds()

    try:
        if ipfs_hash:
            status, job_resp = post_job_to_network(ipfs_hash, market, timeout)
            if status in (200, 201):
                job_id = ""
                if isinstance(job_resp, dict):
                    job_id = str(job_resp.get("job") or job_resp.get("jobAddress") or "")
                return NosanaSubmitResult(
                    backend="nosana",
                    payload={
                        "status": "job_posted",
                        "job": job_id,
                        "ipfs_hash": ipfs_hash,
                        "market": market,
                        "work": json.dumps(work, sort_keys=True),
                    },
                )
            err = job_resp if isinstance(job_resp, dict) else {"error": str(job_resp)}
            notice = (
                f"LFFA: Nosana job post failed (HTTP {status}) — overflow stub. "
                f"Details: {err.get('message') or err.get('error') or err}"
            )
            _emit_notice(notice)
            return _stub_result(request, notice)

        status, balance_resp = fetch_credits_balance()
        if status != 200:
            err = balance_resp if isinstance(balance_resp, dict) else {"error": str(balance_resp)}
            notice = (
                f"LFFA: Nosana API unreachable or unauthorized (HTTP {status}) — overflow stub. "
                f"Details: {err.get('message') or err.get('error') or err}"
            )
            _emit_notice(notice)
            return _stub_result(request, notice)

        balance_hint = ""
        if isinstance(balance_resp, dict):
            balance_hint = str(balance_resp.get("balance") or balance_resp.get("credits") or "")

        notice = (
            "LFFA: Nosana API key OK; overflow work payload prepared but no GPU job posted "
            "(set NOSANA_IPFS_HASH after pinning a job definition — see README)."
        )
        _emit_notice(notice)
        return NosanaSubmitResult(
            backend="nosana",
            notice=notice,
            payload={
                "status": "overflow_work_prepared",
                "balance_hint": balance_hint,
                "market_default": market,
                "job_definition_hint": json.dumps(
                    build_container_job_definition(request),
                    sort_keys=True,
                )[:240],
                "work": json.dumps(work, sort_keys=True),
            },
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        notice = f"LFFA: Nosana request failed ({exc}) — overflow stub."
        _emit_notice(notice)
        return _stub_result(request, notice)
