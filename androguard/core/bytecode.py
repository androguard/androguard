"""
Dalvik bytecode disassembly via [dex-bytecode](https://github.com/androguard/dex-bytecode).

Install the optional bindings with::

    pip install 'androguard[disasm]'

or build from the dex-bytecode repository::

    pip install maturin
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop -m dex-bytecode-py/Cargo.toml
"""

from __future__ import annotations

from typing import Any, Callable, Iterator

_DISASM: Callable[[bytes, int], list[dict[str, Any]]] | None = None
_DECODE_ONE: Callable[[bytes, int], dict[str, Any]] | None = None
_BRANCH_TARGETS: Callable[[bytes, int], set[int]] | None = None


class BytecodeNotAvailable(ImportError):
    """Raised when dex-bytecode Python bindings are not installed."""


def _ensure_loaded() -> None:
    global _DISASM, _DECODE_ONE, _BRANCH_TARGETS
    if _DISASM is not None:
        return
    try:
        from dex_bytecode_py import (
            decode_instruction,
            disassemble,
            get_branch_targets,
        )
    except ImportError as exc:
        raise BytecodeNotAvailable(
            "dex-bytecode is not installed. "
            "Install with: pip install 'androguard[disasm]' "
            "or build dex-bytecode-py from "
            "https://github.com/androguard/dex-bytecode"
        ) from exc
    _DISASM = disassemble
    _DECODE_ONE = decode_instruction
    _BRANCH_TARGETS = get_branch_targets


def disassemble(data: bytes, offset: int = 0) -> list[dict[str, Any]]:
    """Decode all instructions in ``data`` starting at ``offset``."""
    _ensure_loaded()
    assert _DISASM is not None
    return _DISASM(data, offset)


def decode_instruction(data: bytes, offset: int = 0) -> dict[str, Any]:
    """Decode a single instruction at ``offset``."""
    _ensure_loaded()
    assert _DECODE_ONE is not None
    return _DECODE_ONE(data, offset)


def branch_targets(data: bytes, offset: int = 0) -> set[int]:
    """Return absolute byte offsets of branch targets in ``data``."""
    _ensure_loaded()
    assert _BRANCH_TARGETS is not None
    return _BRANCH_TARGETS(data, offset)


def format_instruction(ins: dict[str, Any], show_address: bool = True) -> str:
    line = f"{ins['mnemonic']} {ins['operands']}".rstrip()
    if show_address:
        return f"{ins['offset']:08x}  {ins['opcode']:02x}  {line}"
    return line


def disassemble_lines(
    data: bytes,
    offset: int = 0,
    *,
    labels: bool = False,
    show_address: bool = True,
) -> Iterator[str]:
    """Yield human-readable disassembly lines for ``data``."""
    instructions = disassemble(data, offset)
    label_set: set[int] = set()
    if labels:
        try:
            label_set = branch_targets(data, offset)
        except ValueError:
            label_set = set()
    for ins in instructions:
        if labels and ins["offset"] in label_set:
            yield f":L{ins['offset']:08x}"
        yield format_instruction(ins, show_address=show_address)


def method_insns_bytes(code_item: Any) -> bytes:
    """
    Extract raw instruction bytes from a dexparser ``code_item``.

    Supports the Rust-backed ``PyCodeItem`` (attributes or ``[\"insns\"].value``).
    """
    if code_item is None:
        return b""
    insns = getattr(code_item, "insns", None)
    if isinstance(insns, (bytes, bytearray)):
        return bytes(insns)
    try:
        field = code_item["insns"]
        value = getattr(field, "value", field)
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
    except (TypeError, KeyError, AttributeError):
        pass
    return b""


def disassemble_method_code(code_item: Any) -> list[dict[str, Any]]:
    """
    Disassemble the instruction bytes of a dexparser ``code_item``.

    :param code_item: return value of ``MethodHelper.get_code()``
    """
    insns = method_insns_bytes(code_item)
    if not insns:
        return []
    return disassemble(insns, 0)
