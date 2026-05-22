"""
Java decompilation via [dex-decompiler](https://github.com/androguard/dex-decompiler).

Install the optional bindings with::

    pip install 'androguard[decompile]'

or build from the dex-decompiler repository::

    pip install maturin
    cd dex-decompiler/dex-decompiler-py
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop --release
"""

from __future__ import annotations

from typing import Any

_DEX_DECOMPILER: Any = None


class DecompilerNotAvailable(ImportError):
    """Raised when dex-decompiler Python bindings are not installed."""


def ensure_loaded() -> Any:
    """Import and return the ``dex_decompiler`` module (raises if missing)."""
    global _DEX_DECOMPILER
    if _DEX_DECOMPILER is not None:
        return _DEX_DECOMPILER
    try:
        import dex_decompiler
    except ImportError as exc:
        raise DecompilerNotAvailable(
            "dex-decompiler is not installed. "
            "Install with: pip install 'androguard[decompile]' "
            "or build dex-decompiler-py from "
            "https://github.com/androguard/dex-decompiler"
        ) from exc
    _DEX_DECOMPILER = dex_decompiler
    return _DEX_DECOMPILER


def parse_dex(data: bytes) -> Any:
    """Parse raw DEX bytes into a :class:`DexFile` wrapper."""
    return ensure_loaded().parse_dex(data)


def descriptor_to_java(descriptor: str) -> str:
    """
    Convert a Dalvik type descriptor to a Java class name.

    ``Lcom/example/Foo;`` → ``com.example.Foo``
    """
    if descriptor.startswith("L") and descriptor.endswith(";"):
        return descriptor[1:-1].replace("/", ".")
    return descriptor


def java_class_from_method(class_name: str) -> str:
    """Map dexparser ``class_name`` (descriptor or Java) to decompiler input."""
    if class_name.startswith("L") and ";" in class_name:
        return descriptor_to_java(class_name)
    return class_name.replace("/", ".")


def decompile_method(dex_data: bytes, class_name: str, method_name: str) -> str:
    """
    Decompile one method to Java-like source.

    :param dex_data: raw ``classes*.dex`` bytes
    :param class_name: Java (``com.example.Main``) or Dalvik (``Lcom/example/Main;``)
    :param method_name: e.g. ``onCreate`` or ``<init>``
    """
    dex = parse_dex(dex_data)
    java_class = java_class_from_method(class_name)
    return dex.decompile_method(java_class, method_name)


def decompile_dex(
    dex_data: bytes,
    *,
    only_package: str | None = None,
    exclude: list[str] | None = None,
) -> str:
    """Decompile an entire DEX file to one Java source string."""
    dex = parse_dex(dex_data)
    if only_package or exclude:
        return dex.decompile_with_options(
            only_package=only_package,
            exclude=exclude,
        )
    return dex.decompile()


def decompile_dex_to_dir(
    dex_data: bytes,
    base_path: str,
    *,
    only_package: str | None = None,
    exclude: list[str] | None = None,
) -> None:
    """
    Write decompiled sources under ``base_path``.

    Without filters, uses package layout (one ``.java`` per class). With
    ``only_package`` / ``exclude``, writes a single ``Decompiled.java`` (the
    Python bindings do not expose filtered ``decompile_to_dir`` yet).
    """
    from pathlib import Path

    dex = parse_dex(dex_data)
    if only_package or exclude:
        java_src = dex.decompile_with_options(
            only_package=only_package,
            exclude=exclude,
        )
        Path(base_path).mkdir(parents=True, exist_ok=True)
        (Path(base_path) / "Decompiled.java").write_text(
            java_src, encoding="utf-8"
        )
        return
    dex.decompile_to_dir(base_path)


def parse_method_selector(selector: str) -> tuple[str, str]:
    """
    Parse ``CLASS#METHOD`` (Java form, as used by dex-decompiler CLI).

    Example: ``tests.androguard.TestActivity#onCreate``
    """
    if "#" not in selector:
        raise ValueError(
            "method selector must be CLASS#METHOD "
            "(e.g. tests.androguard.TestActivity#onCreate)"
        )
    class_name, method_name = selector.split("#", 1)
    return class_name.strip(), method_name.strip()

