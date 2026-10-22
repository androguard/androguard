"""MCP server entry: register Androguard tools over stdio."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, Callable

from androguard.mcp import tools as T
from androguard.mcp.errors import McpToolError
from androguard.mcp.session import SessionStore
from androguard.mcp.truncate import (
    default_findrefs_limit,
    default_list_limit,
    default_text_chars,
    default_vulns_limit,
)

LOG = logging.getLogger("androguard.mcp")

# Set from CLI in ``main()``; tool wrappers read this at call time.
_LOG_TOOLS: bool = False

# Keep stdout clean for MCP JSON-RPC; all human logs go to stderr.
_TOOL_NAMES = (
    "open_apk",
    "close_apk",
    "list_sessions",
    "apk_summary",
    "get_manifest",
    "list_components",
    "get_signature_info",
    "list_permissions",
    "list_classes",
    "list_methods",
    "list_strings",
    "search_strings",
    "decompile_method",
    "get_class",
    "inspect_code",
    "decompile_package",
    "find_refs",
    "scan_vulns",
    "disassemble_method",
    "emulate_method",
)


def _require_mcp():
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        raise ImportError(
            "The MCP SDK is not installed. "
            "Install with: pip install 'androguard[mcp]'"
        ) from exc
    return MCPServer


def _extra_status() -> dict[str, bool]:
    return {
        "decompile": importlib.util.find_spec("dex_decompiler") is not None,
        "disasm": importlib.util.find_spec("dex_bytecode_py") is not None,
        "arm": importlib.util.find_spec("arm_disassembler") is not None,
        "patch": importlib.util.find_spec("apk_patch") is not None,
    }


def _configure_logging(level: str = "INFO") -> None:
    """Log to stderr so stdio MCP transport on stdout stays intact."""
    level_name = (level or "INFO").upper()
    log_level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger("androguard.mcp")
    if root.handlers:
        root.setLevel(log_level)
        for handler in root.handlers:
            handler.setLevel(log_level)
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [androguard-mcp] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(log_level)
    root.propagate = False


def _package_version(name: str) -> str:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:  # noqa: BLE001
        return "?"


def _log_startup(
    store: SessionStore,
    *,
    transport: str,
    log_tools: bool = False,
) -> None:
    from androguard import __version__ as ag_version

    extras = _extra_status()
    LOG.info("Androguard MCP server starting")
    LOG.info("  androguard         %s", ag_version)
    LOG.info("  mcp SDK            %s", _package_version("mcp"))
    LOG.info("  python             %s", sys.version.split()[0])
    LOG.info(
        "  transport          %s (JSON-RPC on stdout; logs on stderr)",
        transport,
    )
    LOG.info(
        "  tools (%d)         %s",
        len(_TOOL_NAMES),
        ", ".join(_TOOL_NAMES),
    )
    LOG.info(
        "  extras             decompile=%s disasm=%s arm=%s patch=%s",
        extras["decompile"],
        extras["disasm"],
        extras["arm"],
        extras["patch"],
    )
    if store.allow_any:
        LOG.info("  path policy        ALLOW ANY (ANDROGUARD_MCP_ALLOW_ANY)")
    elif store.roots:
        LOG.info("  path roots (%d)", len(store.roots))
        for root in store.roots:
            LOG.info("    - %s", root)
    else:
        LOG.info("  path roots         (empty → allow any resolved path)")
    LOG.info(
        "  sessions           max=%s ttl=%ss",
        store.max_sessions,
        int(store.ttl_seconds),
    )
    LOG.info(
        "  limits             list=%s text_chars=%s findrefs=%s vulns=%s",
        default_list_limit(),
        default_text_chars(),
        default_findrefs_limit(),
        default_vulns_limit(),
    )
    LOG.info(
        "  tool call logging  %s (--log-tools to enable)",
        "on" if log_tools else "off",
    )
    if not extras["decompile"]:
        LOG.warning(
            "dex-decompiler not installed — decompile/find_refs/scan_vulns "
            "will return extra_missing (pip install 'androguard[decompile]')"
        )
    if not extras["disasm"]:
        LOG.info(
            "dex-bytecode not installed — disassemble_method unavailable "
            "until pip install 'androguard[disasm]'"
        )
    LOG.info("Ready — waiting for MCP client on stdio")


def _log_tools_enabled() -> bool:
    return _LOG_TOOLS


def _parse_args(argv: list[str] | None = None):
    import argparse

    parser = argparse.ArgumentParser(
        prog="androguard-mcp",
        description=(
            "Androguard MCP server for LLM hosts. "
            "JSON-RPC on stdout; human logs on stderr."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for stderr (default: INFO)",
    )
    parser.add_argument(
        "--log-tools",
        action="store_true",
        help="Log each tool invocation on stderr",
    )
    return parser.parse_args(argv)


def _summarize_kwargs(kwargs: dict[str, Any]) -> str:
    parts = []
    for key, value in kwargs.items():
        if key == "store":
            continue
        text = str(value)
        if len(text) > 80:
            text = text[:77] + "..."
        parts.append(f"{key}={text!r}")
    return ", ".join(parts)


def _call(
    fn: Callable[..., dict[str, Any]],
    *,
    tool: str | None = None,
    **kwargs: Any,
) -> str:
    name = tool or getattr(fn, "__name__", "tool")
    if _log_tools_enabled():
        LOG.info("tool %s(%s)", name, _summarize_kwargs(kwargs))
    try:
        result = fn(**kwargs)
    except McpToolError as exc:
        result = exc.to_dict()
        LOG.warning(
            "tool %s error %s: %s",
            name,
            exc.code,
            exc.message,
        )
    except Exception as exc:  # noqa: BLE001 — surface as MCP tool error
        result = McpToolError("internal", str(exc)).to_dict()
        LOG.exception("tool %s internal error", name)
    else:
        if _log_tools_enabled():
            ok = result.get("ok", True) if isinstance(result, dict) else True
            LOG.info("tool %s → ok=%s", name, ok)
    return json.dumps(result, ensure_ascii=False, default=str)


def create_server(store: SessionStore | None = None):
    """Build an MCPServer with Androguard analysis tools registered."""
    MCPServer = _require_mcp()
    store = store or SessionStore.from_env()
    mcp = MCPServer(
        "androguard",
        instructions=(
            "Androguard APK analysis tools. Call open_apk first to get a "
            "session_id, then pass it to other tools. Responses are JSON."
        ),
    )

    # The APK/DEX Rust bindings contain unsendable PyO3 objects. MCP's
    # default worker pool may route consecutive sync calls to different
    # threads, so all session operations must use one persistent worker.
    executor = ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="androguard-mcp"
    )

    def tool(*args: Any, **kwargs: Any):
        def register(fn: Callable[..., str]):
            @wraps(fn)
            async def invoke(*fn_args: Any, **fn_kwargs: Any) -> str:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    executor, partial(fn, *fn_args, **fn_kwargs)
                )

            return mcp.tool(*args, **kwargs)(invoke)

        return register

    def shutdown() -> int:
        """Release sessions before stopping their dedicated worker."""
        try:
            return executor.submit(store.close_all).result()
        finally:
            executor.shutdown(wait=True)

    @tool(description="Open an APK/DEX and return session_id + summary.")
    def open_apk(path: str) -> str:
        return _call(store.open, tool="open_apk", path=path)

    @tool(description="Close an open APK session.")
    def close_apk(session_id: str) -> str:
        return _call(store.close, tool="close_apk", session_id=session_id)

    @tool(description="List open APK sessions.")
    def list_sessions() -> str:
        return _call(store.list_sessions, tool="list_sessions")

    @tool(description="Return APK metadata summary for a session.")
    def apk_summary(session_id: str) -> str:
        return _call(
            T.apk_summary,
            tool="apk_summary",
            store=store,
            session_id=session_id,
        )

    @tool(description="Get decoded AndroidManifest.xml as UTF-8 string.")
    def get_manifest(session_id: str, max_chars: int | None = None) -> str:
        return _call(
            T.get_manifest,
            tool="get_manifest",
            store=store,
            session_id=session_id,
            max_chars=max_chars,
        )

    @tool(description="List Android components and attack surface (paged).")
    def list_components(
        session_id: str,
        component_type: str = "all",
        exported_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> str:
        return _call(
            T.list_components,
            tool="list_components",
            store=store,
            session_id=session_id,
            component_type=component_type,
            exported_only=exported_only,
            offset=offset,
            limit=limit,
        )

    @tool(
        description=(
            "Get APK signature schemes (v1-v3) and certificate details."
        )
    )
    def get_signature_info(session_id: str) -> str:
        return _call(
            T.get_signature_info,
            tool="get_signature_info",
            store=store,
            session_id=session_id,
        )

    @tool(
        description="Emulate a method and trace execution (needs [decompile])."
    )
    def emulate_method(
        session_id: str, selector: str, max_steps: int | None = None
    ) -> str:
        return _call(
            T.emulate_method,
            tool="emulate_method",
            store=store,
            session_id=session_id,
            selector=selector,
            max_steps=max_steps,
        )

    @tool(description="List requested/declared permissions (paged).")
    def list_permissions(
        session_id: str, offset: int = 0, limit: int = 200
    ) -> str:
        return _call(
            T.list_permissions,
            tool="list_permissions",
            store=store,
            session_id=session_id,
            offset=offset,
            limit=limit,
        )

    @tool(description="List DEX class names (optional regex, paged).")
    def list_classes(
        session_id: str,
        pattern: str | None = None,
        offset: int = 0,
        limit: int = 200,
    ) -> str:
        return _call(
            T.list_classes,
            tool="list_classes",
            store=store,
            session_id=session_id,
            pattern=pattern,
            offset=offset,
            limit=limit,
        )

    @tool(description="List methods (optional class/method regex, paged).")
    def list_methods(
        session_id: str,
        class_pattern: str | None = None,
        method_pattern: str | None = None,
        with_code: bool = False,
        offset: int = 0,
        limit: int = 200,
    ) -> str:
        return _call(
            T.list_methods,
            tool="list_methods",
            store=store,
            session_id=session_id,
            class_pattern=class_pattern,
            method_pattern=method_pattern,
            with_code=with_code,
            offset=offset,
            limit=limit,
        )

    @tool(description="List or filter DEX strings (paged).")
    def list_strings(
        session_id: str,
        needle: str | None = None,
        offset: int = 0,
        limit: int = 200,
    ) -> str:
        return _call(
            T.list_strings,
            tool="list_strings",
            store=store,
            session_id=session_id,
            needle=needle,
            offset=offset,
            limit=limit,
        )

    @tool(description="Search DEX strings containing needle.")
    def search_strings(session_id: str, needle: str, limit: int = 200) -> str:
        return _call(
            T.search_strings,
            tool="search_strings",
            store=store,
            session_id=session_id,
            needle=needle,
            limit=limit,
        )

    @tool(
        description="Decompile one method: Java CLASS#METHOD (needs [decompile])."
    )
    def decompile_method(
        session_id: str, selector: str, max_chars: int = 32000
    ) -> str:
        return _call(
            T.decompile_method,
            tool="decompile_method",
            store=store,
            session_id=session_id,
            selector=selector,
            max_chars=max_chars,
        )

    @tool(description="Decompile one class (ASC getclass; needs [decompile]).")
    def get_class(
        session_id: str, class_name: str, max_chars: int = 32000
    ) -> str:
        return _call(
            T.get_class,
            tool="get_class",
            store=store,
            session_id=session_id,
            class_name=class_name,
            max_chars=max_chars,
        )

    @tool(
        description=(
            "Inspect Class or Class#method as java ([decompile]) or dalvik "
            "([disasm]); page long results with offset."
        )
    )
    def inspect_code(
        session_id: str,
        selector: str,
        format: str = "java",
        offset: int = 0,
        max_chars: int = 32000,
    ) -> str:
        return _call(
            T.inspect_code,
            tool="inspect_code",
            store=store,
            session_id=session_id,
            selector=selector,
            format=format,
            offset=offset,
            max_chars=max_chars,
        )

    @mcp.tool(
        description=(
            "Decompile a package tree to disk (needs [decompile]). "
            "Default out_dir: workspace/output/<package>."
        )
    )
    def decompile_package(
        session_id: str,
        only_package: str,
        out_dir: str | None = None,
    ) -> str:
        return _call(
            T.decompile_package,
            tool="decompile_package",
            store=store,
            session_id=session_id,
            only_package=only_package,
            out_dir=out_dir,
        )

    @tool(
        description=(
            "ASC findrefs: kind=string|type|method|field (needs [decompile])."
        )
    )
    def find_refs(
        session_id: str,
        kind: str,
        value: str,
        class_name: str | None = None,
        fuzzy_class: bool = False,
        limit: int = 100,
    ) -> str:
        return _call(
            T.find_refs,
            tool="find_refs",
            store=store,
            session_id=session_id,
            kind=kind,
            value=value,
            class_name=class_name,
            fuzzy_class=fuzzy_class,
            limit=limit,
        )

    @tool(description="Run vulnerability detectors (needs [decompile]).")
    def scan_vulns(session_id: str, limit: int = 100) -> str:
        return _call(
            T.scan_vulns,
            tool="scan_vulns",
            store=store,
            session_id=session_id,
            limit=limit,
        )

    @tool(description="Disassemble matching methods (needs [disasm]).")
    def disassemble_method(
        session_id: str,
        class_pattern: str,
        method_pattern: str,
        limit_methods: int = 1,
        max_chars: int = 32000,
    ) -> str:
        return _call(
            T.disassemble_method,
            tool="disassemble_method",
            store=store,
            session_id=session_id,
            class_pattern=class_pattern,
            method_pattern=method_pattern,
            limit_methods=limit_methods,
            max_chars=max_chars,
        )

    # Keep store on the server for tests.
    mcp._androguard_store = store  # type: ignore[attr-defined]
    mcp._androguard_shutdown = shutdown  # type: ignore[attr-defined]
    return mcp


def main(argv: list[str] | None = None) -> None:
    """Console entry: ``androguard-mcp`` / ``python -m androguard.mcp``."""
    global _LOG_TOOLS

    args = _parse_args(argv)
    _LOG_TOOLS = bool(args.log_tools)
    _configure_logging(args.log_level)
    store = SessionStore.from_env()
    _log_startup(store, transport="stdio", log_tools=_LOG_TOOLS)
    try:
        server = create_server(store)
    except ImportError as exc:
        LOG.error("%s", exc)
        raise SystemExit(1) from exc
    LOG.info("MCP server registered — entering stdio event loop")
    try:
        server.run(transport="stdio")
    except KeyboardInterrupt:
        LOG.info("Interrupted — shutting down")
    except Exception:
        LOG.exception("MCP server crashed")
        raise
    finally:
        open_n = server._androguard_shutdown()
        LOG.info("Stopped (%d session(s) were still open)", open_n)


if __name__ == "__main__":
    main()
