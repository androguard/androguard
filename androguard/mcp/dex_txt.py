"""Helpers for editing apk-patch dex-txt class files."""

from __future__ import annotations

import re
from typing import Iterator


_METHOD_RE = re.compile(
    r"(?ms)^(\.method\b[^\n]*\n)(.*?)(^\.end method\s*(?:\n|$))"
)


def java_to_descriptor(class_name: str) -> str:
    """``com.example.Foo`` / ``Lcom/example/Foo;`` → ``Lcom/example/Foo;``."""
    name = class_name.strip()
    if name.startswith("L") and name.endswith(";"):
        return name
    return "L" + name.replace(".", "/") + ";"


def descriptor_to_rel_path(descriptor: str) -> str:
    """``Lcom/example/Foo;`` → ``com/example/Foo.dex.txt``."""
    inner = descriptor[1:-1] if descriptor.startswith("L") and descriptor.endswith(";") else descriptor
    return f"{inner}.dex.txt"


def class_file_candidates(project_root: str, class_name: str) -> list[str]:
    """Possible project paths for a class under common dex dirs."""
    desc = java_to_descriptor(class_name)
    rel = descriptor_to_rel_path(desc)
    root = project_root.rstrip("/")
    return [
        f"{root}/dex/{rel}",
        f"{root}/dex_classes2/{rel}",
        f"{root}/dex_classes3/{rel}",
        f"{root}/dex_classes4/{rel}",
    ]


def find_class_path(files: dict[str, bytes], project_root: str, class_name: str) -> str | None:
    for path in class_file_candidates(project_root, class_name):
        if path in files:
            return path
    # Fallback: suffix match (multi-dex custom dirs).
    rel = descriptor_to_rel_path(java_to_descriptor(class_name))
    suffix = "/" + rel
    for path in files:
        if path.endswith(suffix) and path.endswith(".dex.txt"):
            return path
    return None


def iter_methods(text: str) -> Iterator[tuple[str, str, str, int, int]]:
    """
    Yield ``(header, body, full, start, end)`` for each method block.

    ``header`` includes the ``.method …`` line and trailing newline.
    ``full`` is header+body+``.end method``.
    """
    for match in _METHOD_RE.finditer(text):
        header, body, end = match.group(1), match.group(2), match.group(3)
        yield header, body, header + body + end, match.start(), match.end()


def method_header_signature(header: str) -> str:
    """
    Extract ``name(params)return`` from a ``.method`` line.

    Example: ``.method public onCreate(Landroid/os/Bundle;)V`` →
    ``onCreate(Landroid/os/Bundle;)V``.
    """
    line = header.strip().splitlines()[0]
    # Drop ".method" and access flags; signature is the last token.
    parts = line.split()
    if len(parts) < 2:
        return line
    return parts[-1]


def find_method_block(
    text: str, method_signature: str
) -> tuple[str, int, int] | None:
    """Return ``(full_block, start, end)`` for an exact signature match."""
    needle = "".join(method_signature.split())
    if "(" not in needle or ")" not in needle:
        raise ValueError(
            "method_signature must include name, params and return "
            "(e.g. onCreate(Landroid/os/Bundle;)V)"
        )
    for _header, _body, full, start, end in iter_methods(text):
        sig = "".join(method_header_signature(_header).split())
        if sig == needle:
            return full, start, end
    return None


def replace_method_block(
    text: str, method_signature: str, new_method: str
) -> str:
    """Replace one method block; ``new_method`` must include ``.method``/``.end method``."""
    found = find_method_block(text, method_signature)
    if found is None:
        raise KeyError(f"method not found: {method_signature}")
    _full, start, end = found
    replacement = new_method
    if not replacement.endswith("\n"):
        replacement += "\n"
    return text[:start] + replacement + text[end:]
