"""CLI output helpers: optional ANSI colors and JSON printing (stdlib only)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def use_color() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("LFFA_NO_COLOR", "").strip() in ("1", "true", "yes"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"


def style(text: str, *codes: str) -> str:
    if not use_color():
        return text
    return "".join(codes) + text + _C.RESET


def ok(text: str) -> str:
    return style(text, _C.GREEN)


def warn(text: str) -> str:
    return style(text, _C.YELLOW)


def err(text: str) -> str:
    return style(text, _C.RED)


def heading(text: str) -> str:
    return style(text, _C.BOLD, _C.CYAN)


def print_json(data: Any, indent: int = 2) -> None:
    print(json.dumps(data, indent=indent, sort_keys=True, default=str))
