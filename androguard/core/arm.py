"""
ARM64 disassembly / decompilation via ecosystem crates.

Install::

    pip install 'androguard[arm]'

Or build from source::

    cd arm_disassembler/arm_disassembler-py && maturin develop
    cd arm_decompiler/arm_decompiler-py && maturin develop
"""

from __future__ import annotations

from typing import Any

_DISASM: Any = None
_DECOMP: Any = None


class ArmDisasmNotAvailable(ImportError):
    """Raised when arm_disassembler Python bindings are missing."""


class ArmDecompilerNotAvailable(ImportError):
    """Raised when arm_decompiler Python bindings are missing."""


def _ensure_disasm() -> Any:
    global _DISASM
    if _DISASM is not None:
        return _DISASM
    try:
        import arm_disassembler
    except ImportError as exc:
        raise ArmDisasmNotAvailable(
            "arm_disassembler is not installed. "
            "Install with: pip install 'androguard[arm]' "
            "or build arm_disassembler-py"
        ) from exc
    _DISASM = arm_disassembler
    return _DISASM


def _ensure_decomp() -> Any:
    global _DECOMP
    if _DECOMP is not None:
        return _DECOMP
    try:
        import arm_decompiler
    except ImportError as exc:
        raise ArmDecompilerNotAvailable(
            "arm_decompiler is not installed. "
            "Install with: pip install 'androguard[arm]' "
            "or build arm_decompiler-py"
        ) from exc
    _DECOMP = arm_decompiler
    return _DECOMP


def disassemble(data: bytes, base_vaddr: int = 0) -> list[dict[str, Any]]:
    """Disassemble ARM64 machine code to instruction dicts."""
    return _ensure_disasm().disassemble(data, base_vaddr)


def decode_one(raw: int, vaddr: int = 0) -> dict[str, Any]:
    """Decode a single 32-bit A64 instruction word."""
    return _ensure_disasm().decode_one(raw, vaddr)


def decode_bytes(data: bytes, vaddr: int = 0) -> dict[str, Any]:
    """Decode one instruction from 4 little-endian bytes."""
    return _ensure_disasm().decode_bytes(data, vaddr)


def decompile(
    code: bytes,
    *,
    base_vaddr: int = 0,
    name: str = "sub_0",
    symbols: dict[int, str] | None = None,
) -> dict[str, Any]:
    """
    Decompile an ARM64 code slice to C-like source.

    Returns a dict with ``source``, ``name``, ``start_vaddr``, ``end_vaddr``.
    """
    return _ensure_decomp().decompile(code, base_vaddr, name, symbols)
