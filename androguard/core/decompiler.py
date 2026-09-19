"""
Java decompilation and analysis via [dex-decompiler](https://github.com/androguard/dex-decompiler).

Install::

    pip install 'androguard[decompile]'

or from source::

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
    """Parse raw DEX bytes into a DexFile wrapper."""
    return ensure_loaded().parse_dex(data)


def descriptor_to_java(descriptor: str) -> str:
    """``Lcom/example/Foo;`` → ``com.example.Foo``."""
    if descriptor.startswith("L") and descriptor.endswith(";"):
        return descriptor[1:-1].replace("/", ".")
    return descriptor


def java_class_from_method(class_name: str) -> str:
    """Map dexparser class name (descriptor or Java) to decompiler input."""
    if class_name.startswith("L") and ";" in class_name:
        return descriptor_to_java(class_name)
    return class_name.replace("/", ".")


def to_dalvik(class_name: str) -> str:
    """Normalize Java/Dalvik names to ``L…;`` descriptors."""
    return ensure_loaded().to_dalvik(class_name)


def decompile_method(dex_data: bytes, class_name: str, method_name: str) -> str:
    """Decompile one method to Java-like source."""
    dex = parse_dex(dex_data)
    return dex.decompile_method(java_class_from_method(class_name), method_name)


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
) -> int:
    """Write decompiled sources under ``base_path``. Returns class count written."""
    from pathlib import Path

    dex = parse_dex(dex_data)
    Path(base_path).mkdir(parents=True, exist_ok=True)
    return int(
        dex.decompile_to_dir(
            base_path,
            only_package=only_package,
            exclude=exclude,
        )
        or 0
    )


def getclass(data: bytes, class_name: str) -> str:
    """
    Locate ``class_name`` in DEX/APK bytes, slice a minimal DEX, decompile it.

    Accepts full APK bytes (multi-DEX aware) or a single DEX blob.
    """
    return ensure_loaded().getclass(data, java_class_from_method(class_name))


def slice_class(data: bytes, class_name: str) -> bytes:
    """Slice a minimal DEX containing only ``class_name`` from DEX/APK bytes."""
    return ensure_loaded().slice_class(data, java_class_from_method(class_name))


def findrefs(
    data: bytes,
    kind: str,
    value: str,
    *,
    class_name: str | None = None,
    fuzzy_class: bool = False,
) -> list[dict[str, Any]]:
    """
    ASC findrefs over DEX or APK bytes.

    ``kind`` is one of ``string``, ``type``, ``method``, ``field``.
    """
    return ensure_loaded().findrefs(
        data,
        kind,
        value,
        class_name=class_name,
        fuzzy_class=fuzzy_class,
    )


def scan_vulns(dex_data: bytes) -> list[dict[str, Any]]:
    """Run vulnerability detectors; returns finding dicts."""
    return parse_dex(dex_data).scan_vulns()


def taint_solve(
    dex_data: bytes,
    *,
    config_json: str | None = None,
    max_iterations: int | None = None,
) -> str:
    """Run Mariana-Trench–style taint solver; returns JSON report string."""
    return parse_dex(dex_data).taint_solve(
        config_json=config_json,
        max_iterations=max_iterations,
    )


def emulate_method(
    dex_data: bytes,
    class_name: str,
    method_name: str,
    *,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Emulate a method; returns steps / finished / registers snapshot."""
    return parse_dex(dex_data).emulate(
        java_class_from_method(class_name),
        method_name,
        max_steps=max_steps,
    )


def export_json(dex_data: bytes, *, include_bodies: bool = False) -> str:
    """Export class inventory as JSON."""
    return parse_dex(dex_data).export_json(include_bodies=include_bodies)


def method_cfg(
    dex_data: bytes, class_name: str, method_name: str
) -> tuple[list, list, list]:
    """Return ``(bytecode_rows, cfg_nodes, cfg_edges)`` for a method."""
    return parse_dex(dex_data).get_method_bytecode_and_cfg(
        java_class_from_method(class_name), method_name
    )


def find_string_xrefs(dex_data: bytes, needle: str) -> list[dict[str, Any]]:
    """ASC string xrefs inside a single DEX."""
    return parse_dex(dex_data).find_string_xrefs(needle)


def find_type_xrefs(dex_data: bytes, needle: str) -> list[dict[str, Any]]:
    """ASC type xrefs inside a single DEX."""
    return parse_dex(dex_data).find_type_xrefs(needle)


def find_method_xrefs(
    dex_data: bytes,
    *,
    class_name: str | None = None,
    method_name: str | None = None,
    exact_class: bool = True,
) -> list[dict[str, Any]]:
    """ASC method invoke xrefs inside a single DEX."""
    return parse_dex(dex_data).find_method_xrefs(
        class_name=class_name,
        method_name=method_name,
        exact_class=exact_class,
    )


def find_field_xrefs(
    dex_data: bytes,
    *,
    class_name: str | None = None,
    field_name: str | None = None,
    exact_class: bool = True,
) -> list[dict[str, Any]]:
    """ASC field xrefs inside a single DEX."""
    return parse_dex(dex_data).find_field_xrefs(
        class_name=class_name,
        field_name=field_name,
        exact_class=exact_class,
    )


def find_method_callers(
    dex_data: bytes, method_idx: int, *, fast: bool = True
) -> dict[str, Any]:
    """Callers of ``method_ids[method_idx]`` (ASC fast path by default)."""
    dex = parse_dex(dex_data)
    if fast:
        return dex.find_method_callers_fast(method_idx)
    return dex.find_method_callers(method_idx)


def decompile_with_renames(
    dex_data: bytes,
    *,
    only_package: str | None = None,
    exclude: list[str] | None = None,
    package_renames: dict[str, str] | None = None,
    class_renames: dict[str, str] | None = None,
    method_renames: dict[str, str] | None = None,
    field_renames: dict[str, str] | None = None,
    variable_renames: dict[str, dict[str, str]] | None = None,
) -> str:
    """Decompile with optional package/class/method/field/variable renames."""
    return parse_dex(dex_data).decompile_with_renames(
        only_package=only_package,
        exclude=exclude,
        package_renames=package_renames,
        class_renames=class_renames,
        method_renames=method_renames,
        field_renames=field_renames,
        variable_renames=variable_renames,
    )


def parse_method_selector(selector: str) -> tuple[str, str]:
    """Parse ``CLASS#METHOD`` (Java form)."""
    if "#" not in selector:
        raise ValueError(
            "method selector must be CLASS#METHOD "
            "(e.g. tests.androguard.TestActivity#onCreate)"
        )
    class_name, method_name = selector.split("#", 1)
    return class_name.strip(), method_name.strip()
