"""MCP tool implementations (plain functions → dict payloads)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from androguard.core.bytecode import BytecodeNotAvailable
from androguard.core.decompiler import DecompilerNotAvailable
from androguard.mcp.errors import McpToolError
from androguard.mcp.session import SessionStore
from androguard.mcp.truncate import (
    default_findrefs_limit,
    default_list_limit,
    default_text_chars,
    default_vulns_limit,
    jsonable,
    page_items,
    truncate_text,
)


def _app(store: SessionStore, session_id: str):
    return store.get(session_id).app


def apk_summary(store: SessionStore, session_id: str) -> dict[str, Any]:
    return {"ok": True, "summary": _app(store, session_id).summary()}


def list_permissions(
    store: SessionStore,
    session_id: str,
    *,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    app = _app(store, session_id)
    perms_obj = getattr(app.apk, "permissions", None)
    names: list[str] = []
    if perms_obj is not None:
        raw = getattr(perms_obj, "permissions", None)
        if isinstance(raw, list) and raw:
            names = [str(x) for x in raw]
        else:
            uses = getattr(perms_obj, "uses_permissions", None) or []
            # uses_permissions may be list of tuples/str
            for item in uses:
                if isinstance(item, (list, tuple)) and item:
                    names.append(str(item[0]))
                else:
                    names.append(str(item))
            names.extend(
                str(x)
                for x in (getattr(perms_obj, "declared_permissions", {}) or {})
            )
    page = page_items(names, offset=offset, limit=limit)
    page["ok"] = True
    return page


def list_classes(
    store: SessionStore,
    session_id: str,
    *,
    pattern: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    names = list(_app(store, session_id).class_names)
    if pattern:
        cre = re.compile(pattern)
        names = [n for n in names if cre.search(n)]
    page = page_items(names, offset=offset, limit=limit)
    page["ok"] = True
    return page


def list_methods(
    store: SessionStore,
    session_id: str,
    *,
    class_pattern: str | None = None,
    method_pattern: str | None = None,
    with_code: bool = False,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    items = []
    for m in _app(store, session_id).iter_methods(
        class_pattern=class_pattern,
        method_pattern=method_pattern,
        with_code=with_code,
    ):
        items.append(
            {
                "class_name": m.class_name,
                "name": m.name,
                "descriptor": f"{m.class_name}->{m.name}",
            }
        )
    page = page_items(items, offset=offset, limit=limit)
    page["ok"] = True
    return page


def list_strings(
    store: SessionStore,
    session_id: str,
    *,
    needle: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    strings = list(_app(store, session_id).strings)
    if needle:
        strings = [s for s in strings if needle in s]
    page = page_items(strings, offset=offset, limit=limit)
    page["ok"] = True
    return page


def search_strings(
    store: SessionStore,
    session_id: str,
    needle: str,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    if limit is None:
        limit = default_list_limit()
    return list_strings(
        store, session_id, needle=needle, offset=0, limit=limit
    )


def decompile_method(
    store: SessionStore,
    session_id: str,
    selector: str,
    *,
    max_chars: int | None = None,
) -> dict[str, Any]:
    try:
        src = _app(store, session_id).decompile_method_selector(selector)
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    except ValueError as exc:
        raise McpToolError("not_found", str(exc)) from exc
    if max_chars is None:
        max_chars = default_text_chars()
    out = truncate_text(src, max_chars=max_chars, meta={"selector": selector})
    out["ok"] = True
    return out


def get_class(
    store: SessionStore,
    session_id: str,
    class_name: str,
    *,
    max_chars: int | None = None,
) -> dict[str, Any]:
    try:
        src = _app(store, session_id).getclass(class_name)
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    except Exception as exc:
        raise McpToolError("not_found", str(exc)) from exc
    if max_chars is None:
        max_chars = default_text_chars()
    out = truncate_text(
        src, max_chars=max_chars, meta={"class_name": class_name}
    )
    out["ok"] = True
    return out


def inspect_code(
    store: SessionStore,
    session_id: str,
    selector: str,
    *,
    format: str = "java",
    offset: int = 0,
    max_chars: int | None = None,
) -> dict[str, Any]:
    """Inspect a class or method as Java or Dalvik, with resumable output."""
    if format not in {"java", "dalvik"}:
        raise McpToolError("invalid_argument", "format must be java or dalvik")
    if offset < 0:
        raise McpToolError("invalid_argument", "offset must be non-negative")
    if max_chars is None:
        max_chars = default_text_chars()
    if max_chars <= 0:
        raise McpToolError("invalid_argument", "max_chars must be positive")

    class_name, separator, method_name = selector.strip().partition("#")
    if not class_name or (separator and not method_name) or "#" in method_name:
        raise McpToolError(
            "invalid_argument", "selector must be Class or Class#method"
        )
    if class_name.startswith("L") and class_name.endswith(";"):
        class_name = class_name[1:-1]
    class_name = class_name.replace("/", ".")
    dex_class = f"L{class_name.replace('.', '/')};"
    normalized = f"{class_name}#{method_name}" if separator else class_name

    # Reuse existing tool backends, including dependency and error handling.
    end = offset + max_chars
    if format == "java":
        if separator:
            result = decompile_method(
                store, session_id, normalized, max_chars=end
            )
        else:
            result = get_class(store, session_id, class_name, max_chars=end)
    else:
        app = _app(store, session_id)
        result = disassemble_method(
            store,
            session_id,
            class_pattern=rf"^{re.escape(dex_class)}$",
            method_pattern=(
                rf"^{re.escape(method_name)}$" if separator else r".*"
            ),
            limit_methods=len(app.methods),
            max_chars=end,
        )

    total = result["chars"]
    source = result["source"][offset:end]
    next_offset = offset + len(source)
    out = {
        "ok": True,
        "selector": normalized,
        "format": format,
        "scope": "method" if separator else "class",
        "source": source,
        "chars": total,
        "returned_chars": len(source),
        "offset": offset,
        "truncated": next_offset < total,
    }
    if format == "dalvik":
        out["methods"] = result["methods"]
    if out["truncated"]:
        out["next_offset"] = next_offset
        out["hint"] = f"call inspect_code again with offset={next_offset}"
    return out


def decompile_package(
    store: SessionStore,
    session_id: str,
    only_package: str,
    *,
    exclude: list[str] | None = None,
    out_dir: str | None = None,
) -> dict[str, Any]:
    session = store.get(session_id)
    if out_dir:
        dest = store.resolve_output_dir(out_dir)
    else:
        pkg_slug = only_package.replace(".", "_")
        dest = store.resolve_output_dir(
            Path.cwd() / "workspace" / "output" / pkg_slug
        )
    try:
        n = session.app.decompile_apk_to_dir(
            dest, only_package=only_package, exclude=exclude
        )
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    session.output_dir = dest
    return {
        "ok": True,
        "classes_written": n,
        "out_dir": str(dest),
        "only_package": only_package,
    }


def find_refs(
    store: SessionStore,
    session_id: str,
    kind: str,
    value: str,
    *,
    class_name: str | None = None,
    fuzzy_class: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    kind_l = kind.lower().strip()
    if kind_l not in {"string", "type", "method", "field"}:
        raise McpToolError(
            "not_found",
            f"invalid kind {kind!r}; expected string|type|method|field",
        )
    if limit is None:
        limit = default_findrefs_limit()
    try:
        hits = _app(store, session_id).findrefs(
            kind_l,
            value,
            class_name=class_name,
            fuzzy_class=fuzzy_class,
        )
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    items = jsonable(hits)
    if not isinstance(items, list):
        items = [items]
    page = page_items(items, offset=0, limit=limit)
    page["ok"] = True
    page["kind"] = kind_l
    page["value"] = value
    return page


def scan_vulns(
    store: SessionStore,
    session_id: str,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    if limit is None:
        limit = default_vulns_limit()
    try:
        findings = _app(store, session_id).scan_vulns()
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    items = jsonable(findings)
    if not isinstance(items, list):
        items = [items]
    page = page_items(items, offset=0, limit=limit)
    page["ok"] = True
    return page


def disassemble_method(
    store: SessionStore,
    session_id: str,
    *,
    class_pattern: str,
    method_pattern: str,
    limit_methods: int = 1,
    max_chars: int | None = None,
) -> dict[str, Any]:
    if max_chars is None:
        max_chars = default_text_chars()
    app = _app(store, session_id)
    blocks: list[str] = []
    count = 0
    try:
        for method in app.iter_methods(
            class_pattern=class_pattern,
            method_pattern=method_pattern,
            with_code=True,
        ):
            lines = [f"# {method.class_name}.{method.name}"]
            for line in app.iter_disassembly(method):
                lines.append(line)
            blocks.append("\n".join(lines))
            count += 1
            if count >= max(1, limit_methods):
                break
    except BytecodeNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[disasm]'",
        ) from exc
    if not blocks:
        raise McpToolError(
            "not_found",
            "no methods with code matched the given patterns",
        )
    text = "\n\n".join(blocks)
    out = truncate_text(
        text,
        max_chars=max_chars,
        meta={
            "class_pattern": class_pattern,
            "method_pattern": method_pattern,
            "methods": count,
        },
    )
    out["ok"] = True
    return out


def get_manifest(
    store: SessionStore,
    session_id: str,
    *,
    max_chars: int | None = None,
) -> dict[str, Any]:
    app = _app(store, session_id)
    xml = app.get_manifest_xml()
    if not xml:
        raise McpToolError(
            "not_found", "AndroidManifest.xml not found or empty"
        )
    if max_chars is None:
        max_chars = default_text_chars()
    out = truncate_text(xml, max_chars=max_chars, meta={"format": "xml"})
    out["ok"] = True
    return out


def list_components(
    store: SessionStore,
    session_id: str,
    *,
    component_type: str = "all",
    exported_only: bool = False,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    app = _app(store, session_id)
    try:
        comps = app.get_components(
            component_type=component_type,
            exported_only=exported_only,
        )
    except ValueError as exc:
        raise McpToolError("invalid_argument", str(exc)) from exc
    page = page_items(comps, offset=offset, limit=limit)
    page["ok"] = True
    page["component_type"] = component_type
    page["exported_only"] = exported_only
    return page


def get_signature_info(
    store: SessionStore,
    session_id: str,
) -> dict[str, Any]:
    app = _app(store, session_id)
    sig_info = app.get_signature_info()
    return {"ok": True, "signature": jsonable(sig_info)}


def emulate_method(
    store: SessionStore,
    session_id: str,
    selector: str,
    *,
    max_steps: int | None = None,
) -> dict[str, Any]:
    from androguard.core.decompiler import (
        DecompilerNotAvailable,
        parse_method_selector,
    )

    try:
        cls_name, meth_name = parse_method_selector(selector)
    except ValueError as exc:
        raise McpToolError("invalid_argument", str(exc)) from exc
    try:
        result = _app(store, session_id).emulate(
            cls_name, meth_name, max_steps=max_steps
        )
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    except ValueError as exc:
        raise McpToolError("not_found", str(exc)) from exc
    except Exception as exc:
        raise McpToolError("internal", str(exc)) from exc
    return {"ok": True, "selector": selector, "emulation": jsonable(result)}
