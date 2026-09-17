"""Transaction / note embeddings — STUB (local-first placeholder).

TODO: Replace with on-device model (e.g. small sentence-transformer) or
chunked hash embedding for demo privacy. No network calls in this scaffold.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EmbeddingRecord:
    text: str
    vector: tuple[float, ...]
    model: str


def _stub_vector(text: str, dims: int = 16) -> tuple[float, ...]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    out: list[float] = []
    for i in range(dims):
        byte = digest[i % len(digest)]
        out.append((byte / 255.0) * 2.0 - 1.0)
    return tuple(out)


def embed_text(text: str, dims: int = 16) -> EmbeddingRecord:
    """Deterministic local stub embedding (not semantic — labeled honestly)."""
    return EmbeddingRecord(
        text=text,
        vector=_stub_vector(text, dims=dims),
        model="stub-sha256-local-v0",
    )


def embed_transactions(descriptions: Sequence[str]) -> list[EmbeddingRecord]:
    return [embed_text(d) for d in descriptions]


def serialize_embedding(record: EmbeddingRecord) -> str:
    payload = {
        "model": record.model,
        "dims": len(record.vector),
        "vector": list(record.vector),
        "text_preview": record.text[:120],
    }
    return json.dumps(payload, sort_keys=True)
