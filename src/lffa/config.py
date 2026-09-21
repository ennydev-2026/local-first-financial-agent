"""Central configuration: environment variables, defaults, and validation.

All LFFA settings are read here. Prefer ``LFFA_*`` prefixes; legacy names
(NOSANA_API_KEY, ARWEAVE_*) are supported for compatibility — see ``.env.example``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
DEFAULT_NOSANA_API_BASE = "https://api.nosana.com"
DEFAULT_NOSANA_MARKET = "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf"
DEFAULT_ARWEAVE_GATEWAY = "https://arweave.net"
DEFAULT_LOCAL_MAX_CONTEXT_CHARS = 4000
DEFAULT_DATA_DIR = "./.lffa"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    return default


def _bool_env(name: str, default: bool = False) -> bool:
    raw = _env(name, "1" if default else "0").lower()
    return raw in ("1", "true", "yes", "on")


def _int_env(name: str, default: int, minimum: int | None = None) -> int:
    raw = _env(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = default
    if minimum is not None:
        value = max(minimum, value)
    return value


@dataclass(frozen=True)
class LffaConfig:
    """Snapshot of effective configuration (from environment at load time)."""

    data_dir: Path
    ledger_db: Path
    ollama_base_url: str
    ollama_model: str
    local_max_context_chars: int
    force_local: bool
    nosana_api_key: str | None
    nosana_api_base: str
    nosana_market: str
    nosana_ipfs_hash: str | None
    nosana_job_timeout_seconds: int
    arweave_gateway_url: str
    arweave_wallet_jwk_path: Path | None

    def mask_secret(self, value: str | None, visible: int = 4) -> str:
        if not value:
            return "(not set)"
        if len(value) <= visible:
            return "*" * len(value)
        return value[:visible] + "…" + ("*" * min(4, len(value) - visible))

    def nosana_configured(self) -> bool:
        return self.nosana_api_key is not None

    def arweave_wallet_configured(self) -> bool:
        path = self.arweave_wallet_jwk_path
        return path is not None and path.is_file()

    def to_public_dict(self) -> dict[str, Any]:
        """Safe for logs / ``--json`` (no raw secrets)."""
        return {
            "data_dir": str(self.data_dir),
            "ledger_db": str(self.ledger_db),
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "local_max_context_chars": self.local_max_context_chars,
            "force_local": self.force_local,
            "nosana_api_base": self.nosana_api_base,
            "nosana_api_key": self.mask_secret(self.nosana_api_key),
            "nosana_configured": self.nosana_configured(),
            "nosana_market": self.nosana_market,
            "nosana_ipfs_hash_set": bool(self.nosana_ipfs_hash),
            "arweave_gateway_url": self.arweave_gateway_url,
            "arweave_wallet_configured": self.arweave_wallet_configured(),
        }


def load_config(environ: dict[str, str] | None = None) -> LffaConfig:
    """Load configuration from ``environ`` or ``os.environ``."""
    env = environ if environ is not None else os.environ

    def g(name: str, default: str = "") -> str:
        return env.get(name, default).strip()

    def first(*names: str, default: str = "") -> str:
        for name in names:
            v = g(name)
            if v:
                return v
        return default

    data_raw = first("LFFA_DATA_DIR", default=DEFAULT_DATA_DIR)
    data_dir = Path(data_raw)
    ledger_raw = first("LFFA_LEDGER_DB")
    ledger_db = Path(ledger_raw) if ledger_raw else data_dir / "ledger.db"

    nosana_key = first("LFFA_NOSANA_API_KEY", "NOSANA_API_KEY") or None
    ipfs = g("NOSANA_IPFS_HASH") or None

    wallet_raw = first("LFFA_ARWEAVE_WALLET_JWK_PATH", "ARWEAVE_WALLET_JWK_PATH")
    wallet_path = Path(wallet_raw) if wallet_raw else None

    return LffaConfig(
        data_dir=data_dir,
        ledger_db=ledger_db,
        ollama_base_url=first("LFFA_OLLAMA_BASE_URL", default=DEFAULT_OLLAMA_BASE_URL).rstrip("/"),
        ollama_model=first("LFFA_OLLAMA_MODEL", default=DEFAULT_OLLAMA_MODEL) or DEFAULT_OLLAMA_MODEL,
        local_max_context_chars=_int_env_from(env, "LFFA_LOCAL_MAX_CONTEXT_CHARS", DEFAULT_LOCAL_MAX_CONTEXT_CHARS, 256),
        force_local=_bool_env_from(env, "LFFA_FORCE_LOCAL", False),
        nosana_api_key=nosana_key,
        nosana_api_base=first("LFFA_NOSANA_API_BASE", "NOSANA_API_URL", default=DEFAULT_NOSANA_API_BASE).rstrip("/"),
        nosana_market=first("NOSANA_MARKET", "LFFA_NOSANA_MARKET", default=DEFAULT_NOSANA_MARKET),
        nosana_ipfs_hash=ipfs,
        nosana_job_timeout_seconds=_int_env_from(env, "NOSANA_JOB_TIMEOUT", 600, 60),
        arweave_gateway_url=first(
            "LFFA_ARWEAVE_GATEWAY_URL", "ARWEAVE_GATEWAY_URL", default=DEFAULT_ARWEAVE_GATEWAY
        ).rstrip("/"),
        arweave_wallet_jwk_path=wallet_path,
    )


def _bool_env_from(env: dict[str, str], name: str, default: bool) -> bool:
    raw = env.get(name, "1" if default else "0").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _int_env_from(env: dict[str, str], name: str, default: int, minimum: int) -> int:
    raw = env.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, value)


@dataclass(frozen=True)
class ConfigCheck:
    name: str
    ok: bool
    detail: str


def validate_config(cfg: LffaConfig) -> list[ConfigCheck]:
    """Non-fatal configuration checks (for ``lffa doctor``)."""
    checks: list[ConfigCheck] = []

    if cfg.local_max_context_chars < 256:
        checks.append(
            ConfigCheck("local_max_context_chars", False, "Must be at least 256.")
        )
    else:
        checks.append(
            ConfigCheck(
                "local_max_context_chars",
                True,
                f"{cfg.local_max_context_chars} characters",
            )
        )

    try:
        cfg.ledger_db.parent.mkdir(parents=True, exist_ok=True)
        test_file = cfg.ledger_db.parent / ".lffa_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        checks.append(ConfigCheck("ledger_db_parent_writable", True, str(cfg.ledger_db.parent)))
    except OSError as exc:
        checks.append(
            ConfigCheck("ledger_db_parent_writable", False, f"Cannot write: {exc}")
        )

    if cfg.nosana_api_key and not cfg.nosana_ipfs_hash:
        checks.append(
            ConfigCheck(
                "nosana_job_post",
                True,
                "API key set; job post needs NOSANA_IPFS_HASH (overflow can still verify credits).",
            )
        )
    elif cfg.nosana_api_key:
        checks.append(ConfigCheck("nosana_job_post", True, "API key and IPFS hash set."))
    else:
        checks.append(
            ConfigCheck(
                "nosana_credentials",
                True,
                "No API key — overflow uses stub path (expected for offline demo).",
            )
        )

    if cfg.arweave_wallet_jwk_path and not cfg.arweave_wallet_configured():
        checks.append(
            ConfigCheck(
                "arweave_wallet",
                False,
                f"JWK path missing or not a file: {cfg.arweave_wallet_jwk_path}",
            )
        )
    elif cfg.arweave_wallet_configured():
        checks.append(ConfigCheck("arweave_wallet", True, "Wallet JWK file readable."))
    else:
        checks.append(
            ConfigCheck("arweave_wallet", True, "Not configured — provenance hash only.")
        )

    return checks


# Module-level cached config (tests can patch load_config or set env before import side effects)
_cached: LffaConfig | None = None


def get_config() -> LffaConfig:
    global _cached
    if _cached is None:
        _cached = load_config()
    return _cached


def reset_config_cache() -> None:
    global _cached
    _cached = None
