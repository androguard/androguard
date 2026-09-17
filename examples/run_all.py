#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run every example script (exit 0 = ok or skipped optional dep).

Usage::

    python -m examples.run_all
"""

from __future__ import annotations

import importlib
import sys

EXAMPLES = (
    "examples.application_summary",
    "examples.apk_and_dex",
    "examples.disassemble",
    "examples.decompile",
    "examples.arm",
    "examples.patch_decode",
)


def main(argv: list[str] | None = None) -> int:
    del argv
    failed = 0
    for name in EXAMPLES:
        mod = importlib.import_module(name)
        print(f"=== {name} ===")
        try:
            code = mod.main([])
        except SystemExit as exc:
            code = int(exc.code) if isinstance(exc.code, int) else 1
        if code not in (0, None):
            print(f"FAIL {name} exit={code}", file=sys.stderr)
            failed += 1
        else:
            print(f"ok {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
