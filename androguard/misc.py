"""
Convenience entry points for scripts and legacy call sites.
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Tuple, Union

from dexparser import DEX, DEXHelper, DEX_from_source

from androguard.application import Application
from androguard.core.apk import APK as CoreAPK

PathLike = Union[str, Path]


def AnalyzeAPK(
    filename: PathLike | bytes | BinaryIO,
    raw: bool = False,
    session=None,
) -> Tuple[CoreAPK, list[DEXHelper], Application]:
    """
    Load an APK and return ``(apk, dex_helpers, application)``.

    ``session`` is accepted for compatibility with older Androguard APIs but
    is not used in v5.

    :param filename: path, raw bytes, or file-like object
    :param raw: when ``True``, ``filename`` is treated as raw APK bytes
    """
    del session
    if raw and isinstance(filename, (bytes, bytearray)):
        source = bytes(filename)
    else:
        source = filename
    app = Application(
        source,
        axml=True,
        signature=True,
        permissions=False,
    )
    return app.apk, app.dex, app


def AnalyzeDex(dexdata: bytes | str) -> DEXHelper:
    """
    Parse a single DEX file or blob.

    :param dexdata: raw ``bytes`` or a path to a ``.dex`` file
    """
    if isinstance(dexdata, (bytes, bytearray)):
        return DEXHelper.from_string(bytes(dexdata))
    return DEXHelper.from_rawdex(DEX_from_source(dexdata))


def clean_file_name(filename: str, unique: bool = True) -> str:
    """Sanitize a string for use as a filesystem name (legacy helper)."""
    import re
    import tempfile

    cleaned = re.sub(r"[^\w.\-]+", "_", filename)
    if len(cleaned) > 230:
        root, ext = (cleaned[:226], cleaned[226:]) if "." in cleaned[-10:] else (cleaned[:230], "")
        cleaned = root + ext
    if unique:
        try:
            with tempfile.NamedTemporaryFile(prefix=cleaned + "_") as fp:
                return fp.name.split("/")[-1]
        except OSError:
            pass
    return cleaned
