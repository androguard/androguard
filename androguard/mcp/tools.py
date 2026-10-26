"""MCP tool implementations (plain functions → dict payloads)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from androguard.core.bytecode import BytecodeNotAvailable
from androguard.core.decompiler import DecompilerNotAvailable
from androguard.core.patch import PatchNotAvailable, build as patch_build
from androguard.mcp import dex_txt
from androguard.mcp.errors import McpToolError
from androguard.mcp.session import Session, SessionStore
from androguard.mcp.truncate import (
    default_findrefs_limit,
    default_list_limit,
    default_text_chars,
    default_vulns_limit,
    jsonable,
    page_items,
    truncate_text,
)


def _writes_allowed() -> bool:
    return os.environ.get("ANDROGUARD_MCP_ALLOW_WRITE", "").strip() in (
        "1",
        "true",
        "True",
        "yes",
    )


def _require_writes(tool: str) -> None:
    if not _writes_allowed():
        raise McpToolError(
            "path_denied",
            f"{tool} requires ANDROGUARD_MCP_ALLOW_WRITE=1",
            hint="set ANDROGUARD_MCP_ALLOW_WRITE=1 to enable mutating / heavy decode tools",
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
            names.extend(str(x) for x in (getattr(perms_obj, "declared_permissions", {}) or {}))
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
    out = truncate_text(src, max_chars=max_chars, meta={"class_name": class_name})
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
            method_pattern=rf"^{re.escape(method_name)}$" if separator else r".*",
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


def method_cfg(
    store: SessionStore,
    session_id: str,
    class_name: str,
    method_name: str,
    *,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Decompiler CFG for one method (needs ``[decompile]``)."""
    if max_nodes is None:
        max_nodes = default_list_limit()
    if max_edges is None:
        max_edges = default_list_limit()
    if max_rows is None:
        max_rows = default_list_limit()
    try:
        rows, nodes, edges = _app(store, session_id).method_cfg(
            class_name, method_name
        )
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    except ValueError as exc:
        raise McpToolError("not_found", str(exc)) from exc

    rows_j = jsonable(rows)
    nodes_j = jsonable(nodes)
    edges_j = jsonable(edges)
    if not isinstance(rows_j, list):
        rows_j = [rows_j]
    if not isinstance(nodes_j, list):
        nodes_j = [nodes_j]
    if not isinstance(edges_j, list):
        edges_j = [edges_j]

    return {
        "ok": True,
        "class_name": class_name,
        "method_name": method_name,
        "bytecode_rows": rows_j[: max(0, max_rows)],
        "bytecode_rows_total": len(rows_j),
        "nodes": nodes_j[: max(0, max_nodes)],
        "nodes_total": len(nodes_j),
        "edges": edges_j[: max(0, max_edges)],
        "edges_total": len(edges_j),
        "truncated": (
            len(rows_j) > max_rows
            or len(nodes_j) > max_nodes
            or len(edges_j) > max_edges
        ),
    }


def dalvik_cfg(
    store: SessionStore,
    session_id: str,
    *,
    class_pattern: str,
    method_pattern: str,
    limit_methods: int = 1,
) -> dict[str, Any]:
    """Dalvik CFG edges for matching methods (needs ``[disasm]``)."""
    app = _app(store, session_id)
    methods_out: list[dict[str, Any]] = []
    try:
        for method in app.iter_methods(
            class_pattern=class_pattern,
            method_pattern=method_pattern,
            with_code=True,
        ):
            edges = jsonable(app.method_cfg_edges(method))
            if not isinstance(edges, list):
                edges = [edges]
            blocks = app.method_basic_blocks(method)
            methods_out.append(
                {
                    "class_name": method.class_name,
                    "method_name": method.name,
                    "block_count": len(blocks),
                    "edges": edges,
                    "edge_count": len(edges),
                }
            )
            if len(methods_out) >= max(1, limit_methods):
                break
    except BytecodeNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[disasm]'",
        ) from exc
    if not methods_out:
        raise McpToolError(
            "not_found",
            "no methods with code matched the given patterns",
        )
    return {
        "ok": True,
        "class_pattern": class_pattern,
        "method_pattern": method_pattern,
        "methods": methods_out,
    }


def taint_solve(
    store: SessionStore,
    session_id: str,
    *,
    config_json: str | None = None,
    max_iterations: int | None = None,
    max_chars: int | None = None,
) -> dict[str, Any]:
    """Run taint solver across DEX files (needs ``[decompile]``)."""
    if max_chars is None:
        max_chars = default_text_chars()
    try:
        reports = _app(store, session_id).taint_solve(
            config_json=config_json,
            max_iterations=max_iterations,
        )
    except DecompilerNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[decompile]'",
        ) from exc
    except Exception as exc:
        raise McpToolError("internal", str(exc)) from exc

    parsed: list[Any] = []
    for raw in reports:
        try:
            parsed.append(json.loads(raw) if isinstance(raw, str) else raw)
        except (TypeError, json.JSONDecodeError):
            parsed.append(raw)

    # Keep payload LLM-sized: serialize then truncate.
    blob = json.dumps(jsonable(parsed), ensure_ascii=False, default=str)
    out = truncate_text(
        blob,
        max_chars=max_chars,
        meta={
            "dex_count": len(reports),
            "max_iterations": max_iterations,
        },
    )
    out["ok"] = True
    out["format"] = "json"
    return out


def decode_project(
    store: SessionStore,
    session_id: str,
    *,
    only_manifest: bool = False,
    no_src: bool = False,
    no_res: bool = False,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    """
    Decode APK to an in-memory apk-patch project and list entry paths.

    Requires ``ANDROGUARD_MCP_ALLOW_WRITE=1`` (heavy / potentially sensitive).
    File contents are not returned — only paths and counts.
    Does not keep an editable workspace; use ``open_patch_project`` to edit.
    """
    _require_writes("decode_project")
    try:
        project = _app(store, session_id).decode_project(
            only_manifest=only_manifest,
            no_src=no_src,
            no_res=no_res,
        )
    except PatchNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[patch]'",
        ) from exc
    except Exception as exc:
        raise McpToolError("internal", str(exc)) from exc

    files = project.get("files") or {}
    paths = sorted(str(p) for p in files.keys())
    page = page_items(paths, offset=offset, limit=limit)
    page["ok"] = True
    page["project_root"] = project.get("project_root")
    page["entry_count"] = project.get("entry_count", len(paths))
    page["dex_class_count"] = project.get("dex_class_count")
    page["only_manifest"] = only_manifest
    return page


def _require_patch_session(store: SessionStore, session_id: str) -> Session:
    session = store.get(session_id)
    if not session.patch_files or not session.patch_project_root:
        raise McpToolError(
            "not_found",
            "no patch project open for this session",
            hint="call open_patch_project first",
        )
    return session


def open_patch_project(
    store: SessionStore,
    session_id: str,
    *,
    all_src: bool = True,
    no_res: bool = False,
    only_manifest: bool = False,
) -> dict[str, Any]:
    """
    Decode APK into an editable in-memory apk-patch workspace on the session.

    Requires ``ANDROGUARD_MCP_ALLOW_WRITE=1``. Prefer ``all_src=True`` so
    classes are available as ``*.dex.txt`` for class/method edits.
    """
    _require_writes("open_patch_project")
    session = store.get(session_id)
    try:
        project = session.app.decode_project(
            all_src=all_src,
            no_res=no_res,
            only_manifest=only_manifest,
        )
    except TypeError:
        # Older Application.decode_project may not accept all_src.
        project = session.app.decode_project(
            no_res=no_res,
            only_manifest=only_manifest,
        )
    except PatchNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[patch]'",
        ) from exc
    except Exception as exc:
        raise McpToolError("internal", str(exc)) from exc

    files = dict(project.get("files") or {})
    root = str(project.get("project_root") or "project")
    session.patch_files = files
    session.patch_project_root = root
    session.patch_dirty = False
    dex_txt_n = sum(1 for p in files if str(p).endswith(".dex.txt"))
    return {
        "ok": True,
        "session_id": session_id,
        "project_root": root,
        "entry_count": project.get("entry_count", len(files)),
        "dex_class_count": project.get("dex_class_count"),
        "dex_txt_count": dex_txt_n,
        "all_src": all_src,
        "hint": (
            "use list_patch_classes / get_patch_class / put_patch_class / "
            "get_patch_method / put_patch_method then rebuild_apk"
        ),
    }


def list_patch_classes(
    store: SessionStore,
    session_id: str,
    *,
    pattern: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None
    paths = sorted(
        p for p in session.patch_files if str(p).endswith(".dex.txt")
    )
    if pattern:
        try:
            cre = re.compile(pattern)
        except re.error as exc:
            raise McpToolError("invalid_argument", str(exc)) from exc
        paths = [p for p in paths if cre.search(p)]
    page = page_items(paths, offset=offset, limit=limit)
    page["ok"] = True
    page["dirty"] = session.patch_dirty
    return page


def get_patch_class(
    store: SessionStore,
    session_id: str,
    class_name: str,
    *,
    max_chars: int | None = None,
) -> dict[str, Any]:
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None and session.patch_project_root
    path = dex_txt.find_class_path(
        session.patch_files, session.patch_project_root, class_name
    )
    if path is None:
        raise McpToolError(
            "not_found",
            f"class not found in patch project: {class_name}",
        )
    text = session.patch_files[path].decode("utf-8", errors="replace")
    if max_chars is None:
        max_chars = default_text_chars()
    out = truncate_text(
        text,
        max_chars=max_chars,
        meta={"class_name": class_name, "path": path, "format": "dex-txt"},
    )
    out["ok"] = True
    return out


def put_patch_class(
    store: SessionStore,
    session_id: str,
    class_name: str,
    content: str,
) -> dict[str, Any]:
    """Replace an entire class ``*.dex.txt`` (or create under ``dex/``)."""
    _require_writes("put_patch_class")
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None and session.patch_project_root
    path = dex_txt.find_class_path(
        session.patch_files, session.patch_project_root, class_name
    )
    created = False
    if path is None:
        # Create under primary dex/ tree.
        rel = dex_txt.descriptor_to_rel_path(
            dex_txt.java_to_descriptor(class_name)
        )
        path = f"{session.patch_project_root.rstrip('/')}/dex/{rel}"
        created = True
    if not content.endswith("\n"):
        content += "\n"
    session.patch_files[path] = content.encode("utf-8")
    session.patch_dirty = True
    return {
        "ok": True,
        "path": path,
        "created": created,
        "chars": len(content),
        "dirty": True,
    }


def get_patch_method(
    store: SessionStore,
    session_id: str,
    class_name: str,
    method_signature: str,
    *,
    max_chars: int | None = None,
) -> dict[str, Any]:
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None and session.patch_project_root
    path = dex_txt.find_class_path(
        session.patch_files, session.patch_project_root, class_name
    )
    if path is None:
        raise McpToolError(
            "not_found",
            f"class not found in patch project: {class_name}",
        )
    text = session.patch_files[path].decode("utf-8", errors="replace")
    try:
        found = dex_txt.find_method_block(text, method_signature)
    except ValueError as exc:
        raise McpToolError("invalid_argument", str(exc)) from exc
    if found is None:
        raise McpToolError(
            "not_found",
            f"method not found: {class_name}#{method_signature}",
        )
    block, _start, _end = found
    if max_chars is None:
        max_chars = default_text_chars()
    out = truncate_text(
        block,
        max_chars=max_chars,
        meta={
            "class_name": class_name,
            "method_signature": method_signature,
            "path": path,
            "format": "dex-txt",
        },
    )
    out["ok"] = True
    return out


def put_patch_method(
    store: SessionStore,
    session_id: str,
    class_name: str,
    method_signature: str,
    content: str,
) -> dict[str, Any]:
    """
    Replace one method block in a class dex-txt.

    ``content`` must be a full ``.method …`` / ``.end method`` block.
    """
    _require_writes("put_patch_method")
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None and session.patch_project_root
    path = dex_txt.find_class_path(
        session.patch_files, session.patch_project_root, class_name
    )
    if path is None:
        raise McpToolError(
            "not_found",
            f"class not found in patch project: {class_name}",
        )
    text = session.patch_files[path].decode("utf-8", errors="replace")
    try:
        updated = dex_txt.replace_method_block(
            text, method_signature, content
        )
    except ValueError as exc:
        raise McpToolError("invalid_argument", str(exc)) from exc
    except KeyError as exc:
        raise McpToolError("not_found", str(exc)) from exc
    session.patch_files[path] = updated.encode("utf-8")
    session.patch_dirty = True
    return {
        "ok": True,
        "path": path,
        "class_name": class_name,
        "method_signature": method_signature,
        "chars": len(content),
        "dirty": True,
    }


def rebuild_apk(
    store: SessionStore,
    session_id: str,
    out_path: str,
    *,
    sign: bool = True,
) -> dict[str, Any]:
    """
    Assemble the in-memory patch project and write a (signed) APK to ``out_path``.

    Requires ``ANDROGUARD_MCP_ALLOW_WRITE=1``. ``out_path`` must be under
    ``ANDROGUARD_MCP_ROOTS``.
    """
    _require_writes("rebuild_apk")
    session = _require_patch_session(store, session_id)
    assert session.patch_files is not None and session.patch_project_root
    dest = store.resolve_output_file(out_path)
    if dest.suffix.lower() != ".apk":
        raise McpToolError(
            "invalid_argument",
            f"out_path must end with .apk (got {dest.suffix!r})",
        )
    try:
        apk_bytes = patch_build(
            session.patch_files,
            project_root=session.patch_project_root,
            sign=sign,
        )
    except PatchNotAvailable as exc:
        raise McpToolError(
            "extra_missing",
            str(exc),
            hint="pip install 'androguard[patch]'",
        ) from exc
    except Exception as exc:
        raise McpToolError("internal", f"rebuild failed: {exc}") from exc

    dest.write_bytes(apk_bytes)
    session.patch_dirty = False
    return {
        "ok": True,
        "out_path": str(dest),
        "size": len(apk_bytes),
        "signed": sign,
        "dirty": False,
    }


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

