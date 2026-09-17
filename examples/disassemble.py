#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dalvik disassembly, CFG, and encode helpers (requires androguard[disasm]).

Run::

    python -m examples.disassemble [path/to.apk]
"""

from __future__ import annotations

from androguard import Application
from androguard.core.bytecode import (
    basic_blocks,
    cfg_edges,
    disassemble,
    encode_goto,
    encode_instruction,
    encode_nop,
    encode_return_void,
)

from examples.common import require_modules, resolve_apk


def main(argv: list[str] | None = None) -> int:
    require_modules("dex_bytecode_py")
    apk_path = resolve_apk(argv)

    nop_ret = encode_nop() + encode_return_void()
    insns = disassemble(nop_ret)
    assert [i["mnemonic"] for i in insns] == ["nop", "return-void"]
    assert encode_instruction("nop", "").hex() == "0000"
    print("raw:", " | ".join(i["disasm"] for i in insns))

    branched = encode_nop() + encode_goto(1) + encode_return_void()
    blocks = basic_blocks(branched)
    edges = cfg_edges(branched)
    assert len(blocks) >= 2, blocks
    assert edges, edges
    print("cfg edges:", edges)

    app = Application(apk_path)
    method = next(
        app.iter_methods(
            class_pattern=r"TestActivity",
            method_pattern=r"^onCreate$",
            with_code=True,
        )
    )
    lines = list(app.iter_disassembly(method))
    assert len(lines) > 5, lines
    print(f"# {method.class_name}.{method.name}")
    for line in lines[:8]:
        print(line)
    print("blocks:", app.method_basic_blocks(method)[:2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
