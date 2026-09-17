#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Java decompilation and ASC helpers (requires androguard[decompile]).

Run::

    python -m examples.decompile [path/to.apk]
"""

from __future__ import annotations

from androguard import Application
from androguard.core.decompiler import descriptor_to_java, getclass

from examples.common import require_modules, resolve_apk


def main(argv: list[str] | None = None) -> int:
    require_modules("dex_decompiler")
    apk_path = resolve_apk(argv)
    app = Application(apk_path)

    assert (
        descriptor_to_java("Ltests/androguard/TestActivity;")
        == "tests.androguard.TestActivity"
    )

    java = app.decompile_method_selector(
        "tests.androguard.TestActivity#onCreate"
    )
    assert "onCreate" in java
    assert "setContentView" in java
    print("// decompile_method_selector")
    print(java[:400], "...\n" if len(java) > 400 else "\n", sep="")

    klass = getclass(apk_path.read_bytes(), "tests.androguard.TestActivity")
    assert "class TestActivity" in klass or "TestActivity" in klass
    print("// getclass (first 300 chars)")
    print(klass[:300], "...\n" if len(klass) > 300 else "\n", sep="")

    emu = app.emulate(
        "tests.androguard.TestActivity", "onCreate", max_steps=64
    )
    assert "steps" in emu and "registers" in emu
    print("emulate:", {k: emu[k] for k in ("steps", "finished")})

    rows, nodes, _edges = app.method_cfg(
        "tests.androguard.TestActivity", "onCreate"
    )
    assert rows and nodes
    print(f"cfg: {len(rows)} insns, {len(nodes)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
