"""Arweave provenance artifacts — STUB.

Optional: anchor summaries of agent decisions or ledger checkpoints.
No Arweave uploads in this scaffold.

Wire-up TODO: ARWEAVE_* env vars from .env.example.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ProvenanceArtifact:
    kind: str
    payload_sha256: str
    created_at: str
    gateway_url: str
    tx_id: str | None


def gateway_url() -> str:
    return os.environ.get("ARWEAVE_GATEWAY_URL", "https://arweave.net").rstrip("/")


def build_artifact(kind: str, payload: dict[str, Any]) -> ProvenanceArtifact:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return ProvenanceArtifact(
        kind=kind,
        payload_sha256=digest,
        created_at=datetime.now(timezone.utc).isoformat(),
        gateway_url=gateway_url(),
        tx_id=None,
    )


def format_artifact_line(artifact: ProvenanceArtifact) -> str:
    tx = artifact.tx_id or "(not uploaded — stub)"
    return (
        f"[provenance stub] kind={artifact.kind} sha256={artifact.payload_sha256[:16]}… "
        f"gateway={artifact.gateway_url} tx={tx}"
    )


def upload_artifact(artifact: ProvenanceArtifact, payload: dict[str, Any]) -> dict[str, str]:
    """STUB: would sign and post to Arweave; returns honest not-implemented status."""
    return {
        "status": "stub_not_uploaded",
        "message": "Arweave provenance is not implemented in this hackathon scaffold.",
        "payload_sha256": artifact.payload_sha256,
        "gateway": artifact.gateway_url,
    }
