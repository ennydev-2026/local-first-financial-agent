"""Health checks for ``lffa doctor``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lffa import config
from lffa import slm


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def run_doctor(cfg: config.LffaConfig | None = None) -> list[DoctorCheck]:
    cfg = cfg or config.load_config()
    checks: list[DoctorCheck] = []

    for c in config.validate_config(cfg):
        checks.append(DoctorCheck(c.name, c.ok, c.detail))

    if slm.ollama_reachable():
        if slm.ollama_model_available():
            checks.append(
                DoctorCheck(
                    "ollama",
                    True,
                    f"Reachable at {cfg.ollama_base_url}; model `{cfg.ollama_model}` available.",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    "ollama",
                    False,
                    f"Reachable at {cfg.ollama_base_url} but model `{cfg.ollama_model}` not in tags — run `ollama pull`.",
                )
            )
    else:
        checks.append(
            DoctorCheck(
                "ollama",
                False,
                f"Cannot reach Ollama at {cfg.ollama_base_url} (stub SLM fallback will apply).",
            )
        )

    if cfg.nosana_configured():
        checks.append(
            DoctorCheck(
                "nosana_api_key",
                True,
                f"Present ({cfg.mask_secret(cfg.nosana_api_key)}).",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                "nosana_api_key",
                True,
                "Not set — overflow stub path (OK for local-only demo).",
            )
        )

    return checks


def doctor_summary(checks: list[DoctorCheck]) -> dict[str, Any]:
    cfg = config.load_config()
    return {
        "config": cfg.to_public_dict(),
        "checks": [c.to_dict() for c in checks],
        "all_ok": all(c.ok for c in checks),
    }
