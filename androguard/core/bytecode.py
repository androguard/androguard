"""
Dalvik bytecode via [dex-bytecode](https://github.com/androguard/dex-bytecode).

Install::

    pip install 'androguard[disasm]'
"""

from __future__ import annotations

from typing import Any, Callable, Iterator

_MOD: Any = None


class BytecodeNotAvailable(ImportError):
    """Raised when dex-bytecode Python bindings are not installed."""


def _ensure_loaded() -> Any:
    global _MOD
    if _MOD is not None:
        return _MOD
    try:
        import dex_bytecode_py
    except ImportError as exc:
        raise BytecodeNotAvailable(
            "dex-bytecode is not installed. "
            "Install with: pip install 'androguard[disasm]' "
            "or build dex-bytecode-py from "
            "https://github.com/androguard/dex-bytecode"
        ) from exc
    _MOD = dex_bytecode_py
    return _MOD


def disassemble(data: bytes, offset: int = 0) -> list[dict[str, Any]]:
    """Decode all instructions in ``data`` starting at ``offset``."""
    return _ensure_loaded().disassemble(data, offset)


def decode_instruction(data: bytes, offset: int = 0) -> dict[str, Any]:
    """Decode a single instruction at ``offset``."""
    return _ensure_loaded().decode_instruction(data, offset)


def branch_targets(data: bytes, offset: int = 0) -> set[int]:
    """Return absolute byte offsets of branch targets in ``data``."""
    return _ensure_loaded().get_branch_targets(data, offset)


def basic_blocks(data: bytes, offset: int = 0) -> list[dict[str, Any]]:
    """
    Split bytecode into basic blocks.

    Each block has ``start_offset``, ``end_offset``, ``successors``,
    ``fallthrough_to``.
    """
    return _ensure_loaded().basic_blocks(data, offset)


def cfg_edges(data: bytes, offset: int = 0) -> list[dict[str, Any]]:
    """Return CFG edges as dicts with ``from`` / ``to`` offsets."""
    return _ensure_loaded().cfg_edges(data, offset)


def patch_branch(
    data: bytes, from_offset: int, to_offset: int
) -> bytes:
    """Rewrite the branch at ``from_offset`` to jump to ``to_offset``."""
    return bytes(_ensure_loaded().patch_branch(data, from_offset, to_offset))


def encode_nop() -> bytes:
    return bytes(_ensure_loaded().encode_nop_bytes())


def encode_return_void() -> bytes:
    return bytes(_ensure_loaded().encode_return_void_bytes())


def encode_goto(rel_units: int) -> bytes:
    return bytes(_ensure_loaded().encode_goto_bytes(rel_units))


def encode_instruction(
    mnemonic: str,
    operands: str = "",
    *,
    branch_rel_units: int | None = None,
) -> bytes:
    """
    Encode one Dalvik instruction from mnemonic + operand text.

    Pool refs use index form (``method@33``, ``string@5``, …).
    """
    return bytes(
        _ensure_loaded().encode_instruction(
            mnemonic, operands, branch_rel_units
        )
    )


def opcode_of(mnemonic: str) -> int | None:
    """Return the opcode byte for ``mnemonic``, or ``None`` if unknown."""
    return _ensure_loaded().opcode_of(mnemonic)


def exception_edges(
    data: bytes,
    try_entries: list[tuple[int, int, int, int | None]],
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Exception CFG edges from try/catch ranges.

    Each ``try_entries`` item is
    ``(start_offset, end_offset, handler_offset, type_index|None)``.
    """
    return _ensure_loaded().exception_edges(data, try_entries, offset)


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
    """Extract raw instruction bytes from a dexparser ``code_item``."""
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
    """Disassemble the instruction bytes of a dexparser ``code_item``."""
    insns = method_insns_bytes(code_item)
    if not insns:
        return []
    return disassemble(insns, 0)


def method_basic_blocks(code_item: Any) -> list[dict[str, Any]]:
    """Basic blocks for a method ``code_item``."""
    insns = method_insns_bytes(code_item)
    if not insns:
        return []
    return basic_blocks(insns, 0)


def method_cfg_edges(code_item: Any) -> list[dict[str, Any]]:
    """CFG edges for a method ``code_item``."""
    insns = method_insns_bytes(code_item)
    if not insns:
        return []
    return cfg_edges(insns, 0)
