# -*- coding: utf-8 -*-
"""Shared helpers for runnable examples (also used by tests)."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APK = REPO_ROOT / "tests" / "data" / "APK" / "TestActivity.apk"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def require_modules(*names: str) -> None:
    """Exit with code 0 (skip) if an optional dependency is missing."""
    missing = [n for n in names if not has_module(n)]
    if missing:
        print(
            f"skip: missing optional module(s): {', '.join(missing)}",
            file=sys.stderr,
        )
        raise SystemExit(0)


def resolve_apk(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "apk",
        nargs="?",
        default=str(DEFAULT_APK),
        help=f"APK path (default: {DEFAULT_APK})",
    )
    args = parser.parse_args(argv)
    path = Path(args.apk)
    if not path.is_file():
        raise SystemExit(f"APK not found: {path}")
    return path
