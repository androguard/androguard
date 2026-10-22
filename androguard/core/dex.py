"""
DEX structure parsing via [dex-parser](https://github.com/androguard/dex-parser).

The parser uses a Rust core (``dexparser-rs``) exposed to Python through PyO3.
"""

from pathlib import Path

from dexparser import (
    DEX,
    ClassHelper,
    DEXHelper,
    FieldHelper,
    MethodHelper,
)

try:
    from dexparser import DEX_from_source
except ImportError:

    def DEX_from_source(source):
        if isinstance(source, (str, Path)):
            with open(source, "rb") as f:
                data = f.read()
        elif isinstance(source, bytes):
            data = source
        elif hasattr(source, "read"):
            data = source.read()
        else:
            data = bytes(source)
        try:
            from hachoir.stream import StringInputStream

            return DEX(StringInputStream(data))
        except Exception:
            return DEXHelper.from_string(data)


try:
    from dexparser import is_dex
except ImportError:

    def is_dex(data) -> bool:
        if isinstance(data, (str, Path)):
            with open(data, "rb") as f:
                header = f.read(8)
        elif isinstance(data, (bytes, bytearray)):
            header = bytes(data[:8])
        elif hasattr(data, "read"):
            pos = data.tell() if hasattr(data, "tell") else 0
            header = data.read(8)
            if hasattr(data, "seek"):
                data.seek(pos)
        else:
            return False
        return any(
            header.startswith(magic)
            for magic in (
                b"dex\n035\0",
                b"dex\n036\0",
                b"dex\n037\0",
                b"dex\n038\0",
                b"dex\n039\0",
            )
        )


if not hasattr(DEX, "from_path"):

    @classmethod
    def _dex_from_path(cls, path):
        return DEX_from_source(path)

    setattr(DEX, "from_path", _dex_from_path)


__all__ = [
    "ClassHelper",
    "DEX",
    "DEX_from_source",
    "DEXHelper",
    "FieldHelper",
    "MethodHelper",
    "is_dex",
]
