"""
DEX structure parsing via [dex-parser](https://github.com/androguard/dex-parser).

The parser uses a Rust core (``dexparser-rs``) exposed to Python through PyO3.
"""

from dexparser import (
    ClassHelper,
    DEX,
    DEX_from_source,
    DEXHelper,
    FieldHelper,
    MethodHelper,
    is_dex,
)

__all__ = [
    "ClassHelper",
    "DEX",
    "DEX_from_source",
    "DEXHelper",
    "FieldHelper",
    "MethodHelper",
    "is_dex",
]
