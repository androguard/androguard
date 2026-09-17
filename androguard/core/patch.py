"""
APK decode/build via [apk-patch](https://github.com/androguard/apk-patch).

Install::

    pip install 'androguard[patch]'

Or from source::

    cd apk-patch/crates/apk-patch-py
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_PATCH: Any = None


class PatchNotAvailable(ImportError):
    """Raised when apk-patch Python bindings are not installed."""


def ensure_loaded() -> Any:
    global _PATCH
    if _PATCH is not None:
        return _PATCH
    try:
        import apk_patch
    except ImportError as exc:
        raise PatchNotAvailable(
            "apk-patch is not installed. "
            "Install with: pip install 'androguard[patch]' "
            "or build apk-patch-py from "
            "https://github.com/androguard/apk-patch"
        ) from exc
    _PATCH = apk_patch
    return _PATCH


def decode(
    apk_bytes: bytes,
    *,
    apk_name: str = "app.apk",
    no_src: bool = False,
    no_res: bool = False,
    all_src: bool = False,
    only_manifest: bool = False,
) -> dict[str, Any]:
    """
    Decode an APK into an in-memory project tree.

    Returns a dict with ``files`` (path → bytes), ``project_root``,
    ``entry_count``, ``dex_class_count``.
    """
    return ensure_loaded().decode(
        apk_bytes,
        apk_name,
        no_src=no_src,
        no_res=no_res,
        all_src=all_src,
        only_manifest=only_manifest,
    )


def build(
    files: dict[str, bytes],
    *,
    project_root: str = "project",
    sign: bool = True,
) -> bytes:
    """Build a project tree (from :func:`decode`) into APK bytes."""
    return bytes(
        ensure_loaded().build(files, project_root, sign=sign)
    )


def decode_file(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    """Decode an APK file from disk."""
    return decode(Path(path).read_bytes(), apk_name=Path(path).name, **kwargs)


def roundtrip(apk_bytes: bytes, *, sign: bool = True, **decode_kw: Any) -> bytes:
    """Decode then rebuild an APK (dex-txt / resources editable in between)."""
    project = decode(apk_bytes, **decode_kw)
    return build(
        project["files"],
        project_root=project["project_root"],
        sign=sign,
    )


def inject_goauld(
    apk_bytes: bytes,
    agent_so: bytes,
    *,
    apk_name: str = "app.apk",
    sign: bool = True,
) -> bytes:
    """
    Inject ``libgoauld_agent.so`` + early-load ContentProvider, then rebuild.

    Requires a valid arm64-v8a ``agent_so`` blob (see arm_goauld).
    """
    return bytes(
        ensure_loaded().inject_goauld(
            apk_bytes, agent_so, apk_name, sign=sign
        )
    )
