"""Local SLM inference — Ollama (HTTP) with stub fallback.

Uses stdlib urllib only. Configure via LFFA_OLLAMA_BASE_URL and LFFA_OLLAMA_MODEL.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from lffa import config

DEFAULT_OLLAMA_BASE_URL = config.DEFAULT_OLLAMA_BASE_URL
DEFAULT_OLLAMA_MODEL = config.DEFAULT_OLLAMA_MODEL


@dataclass(frozen=True)
class SlmCompletion:
    text: str
    backend: str  # "ollama" | "stub"
    notice: str | None = None


class LocalSlmBackend(Protocol):
    def complete(self, prompt: str) -> SlmCompletion: ...


def ollama_base_url() -> str:
    return config.get_config().ollama_base_url


def ollama_model() -> str:
    return config.get_config().ollama_model


def stub_local_reply(prompt: str, embedding_model: str) -> str:
    return (
        "[stub local SLM] On-device path selected (Ollama unavailable). "
        f"Net balance hint: see ledger summary in prompt. Embedding model: {embedding_model}."
    )


def _http_json(
    method: str,
    url: str,
    body: dict | None = None,
    timeout: float = 120.0,
) -> tuple[int, dict | list]:
    data = None
    headers = {"Accept": "application/json"}
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


def ollama_reachable() -> bool:
    """True if Ollama responds on the configured base URL."""
    url = f"{ollama_base_url()}/api/tags"
    try:
        status, _ = _http_json("GET", url, timeout=3.0)
        return status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def ollama_model_available(model: str | None = None) -> bool:
    """True if the configured model name appears in Ollama's tag list."""
    name = model or ollama_model()
    url = f"{ollama_base_url()}/api/tags"
    try:
        status, payload = _http_json("GET", url, timeout=5.0)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    if status != 200 or not isinstance(payload, dict):
        return False
    models = payload.get("models") or []
    base = name.split(":")[0]
    for entry in models:
        if not isinstance(entry, dict):
            continue
        tag_name = entry.get("name") or ""
        if tag_name == name or tag_name.startswith(f"{base}:"):
            return True
    return False


def _fallback_notice(reason: str) -> str:
    return (
        f"LFFA: Ollama unavailable ({reason}) — using stub local SLM reply. "
        f"Install Ollama, run `ollama pull {ollama_model()}`, then retry."
    )


def complete_with_ollama(prompt: str) -> SlmCompletion:
    """Call Ollama /api/generate; raises on transport errors (caller may catch)."""
    url = f"{ollama_base_url()}/api/generate"
    body = {
        "model": ollama_model(),
        "prompt": prompt,
        "stream": False,
    }
    status, payload = _http_json("POST", url, body=body, timeout=180.0)
    if status != 200:
        err = payload.get("error") if isinstance(payload, dict) else str(payload)
        raise RuntimeError(err or f"HTTP {status}")
    if not isinstance(payload, dict):
        raise RuntimeError("unexpected Ollama response")
    response = (payload.get("response") or "").strip()
    if not response:
        raise RuntimeError("empty response from Ollama")
    return SlmCompletion(text=response, backend="ollama")


def complete_local(prompt: str, *, embedding_model: str) -> SlmCompletion:
    """Prefer Ollama; fall back to stub with a one-line notice (never raises)."""
    if not ollama_reachable():
        return SlmCompletion(
            text=stub_local_reply(prompt, embedding_model),
            backend="stub",
            notice=_fallback_notice("cannot reach Ollama at " + ollama_base_url()),
        )
    if not ollama_model_available():
        return SlmCompletion(
            text=stub_local_reply(prompt, embedding_model),
            backend="stub",
            notice=_fallback_notice(f"model `{ollama_model()}` not pulled"),
        )
    try:
        return complete_with_ollama(prompt)
    except (urllib.error.URLError, TimeoutError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        return SlmCompletion(
            text=stub_local_reply(prompt, embedding_model),
            backend="stub",
            notice=_fallback_notice(str(exc)),
        )
