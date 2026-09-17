#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ARM64 disassembly / decompilation (requires androguard[arm]).

No APK needed — uses a tiny NOP; RET snippet.

Run::

    python -m examples.arm
"""

from __future__ import annotations

from androguard.core import arm

from examples.common import require_modules


def main(argv: list[str] | None = None) -> int:
    del argv  # unused
    require_modules("arm_disassembler", "arm_decompiler")

    one = arm.decode_one(0xD503201F)
    assert one["mnemonic"] == "nop", one
    print("decode_one:", one)

    code = bytes.fromhex("1f2003d5c0035fd6")  # nop; ret
    insns = arm.disassemble(code)
    assert len(insns) == 2
    assert insns[0]["mnemonic"] == "nop"
    for ins in insns:
        print(f"  {ins['vaddr']:08x}  {ins['text']}")

    out = arm.decompile(code, name="foo")
    assert "foo" in out["source"]
    print(out["source"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
