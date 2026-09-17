"""Arweave provenance artifacts — local hash + optional upload attempt.

Default: SHA-256 artifact metadata only (stub). When ``LFFA_ARWEAVE_WALLET_JWK_PATH`` or
``ARWEAVE_WALLET_JWK_PATH`` points at a readable JWK file, we validate configuration and
return an honest not-yet-uploaded status (signing a transaction requires extra tooling).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProvenanceArtifact:
    kind: str
    payload_sha256: str
    created_at: str
    gateway_url: str
    tx_id: str | None


def gateway_url() -> str:
    for name in ("LFFA_ARWEAVE_GATEWAY_URL", "ARWEAVE_GATEWAY_URL"):
        value = os.environ.get(name, "").strip()
        if value:
            return value.rstrip("/")
    return "https://arweave.net"


def wallet_jwk_path() -> Path | None:
    for name in ("LFFA_ARWEAVE_WALLET_JWK_PATH", "ARWEAVE_WALLET_JWK_PATH"):
        raw = os.environ.get(name, "").strip()
        if raw:
            return Path(raw)
    return None


def arweave_configured() -> bool:
    path = wallet_jwk_path()
    return path is not None and path.is_file()


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


def format_artifact_line(artifact: ProvenanceArtifact, upload_status: str | None = None) -> str:
    if artifact.tx_id:
        tx = artifact.tx_id
    elif upload_status:
        tx = upload_status
    else:
        tx = "(not uploaded — stub)"
    return (
        f"[provenance] kind={artifact.kind} sha256={artifact.payload_sha256[:16]}… "
        f"gateway={artifact.gateway_url} tx={tx}"
    )


def _wallet_key_type(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return str(data.get("kty") or "")


def upload_artifact(artifact: ProvenanceArtifact, payload: dict[str, Any]) -> dict[str, str]:
    """Attempt upload when wallet path is configured; never fabricate a tx id."""
    path = wallet_jwk_path()
    if path is None:
        return {
            "status": "stub_not_uploaded",
            "message": "Arweave wallet not configured — metadata hash only.",
            "payload_sha256": artifact.payload_sha256,
            "gateway": artifact.gateway_url,
        }
    if not path.is_file():
        return {
            "status": "wallet_missing",
            "message": f"Arweave JWK path does not exist: {path}",
            "payload_sha256": artifact.payload_sha256,
            "gateway": artifact.gateway_url,
        }

    kty = _wallet_key_type(path)
    if not kty:
        return {
            "status": "wallet_invalid",
            "message": "Could not read Arweave wallet JWK JSON.",
            "payload_sha256": artifact.payload_sha256,
            "gateway": artifact.gateway_url,
        }

    # TODO: sign and POST /tx to gateway (needs RSA-PSS + transaction builder; use arweave-python or arweave.js).
    return {
        "status": "upload_not_implemented",
        "message": (
            f"Wallet loaded (kty={kty}) but on-chain upload is not implemented in LFFA yet. "
            "Artifact SHA-256 is ready for a future anchor step."
        ),
        "payload_sha256": artifact.payload_sha256,
        "gateway": artifact.gateway_url,
        "bytes_ready": str(len(json.dumps(payload, sort_keys=True).encode("utf-8"))),
    }
