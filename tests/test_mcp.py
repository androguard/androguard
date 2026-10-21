# -*- coding: utf-8 -*-
"""Tests for the optional Androguard MCP server."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.helpers import (
    HAS_BYTECODE,
    HAS_DECOMPILER,
    HAS_MCP,
    TEST_APK,
    file_exists,
)


class McpTruncateTest(unittest.TestCase):
    """Pure helpers — no APK / mcp SDK required."""

    def test_page_items(self):
        from androguard.mcp.truncate import page_items

        page = page_items(list(range(10)), offset=0, limit=3)
        self.assertEqual(page["items"], [0, 1, 2])
        self.assertEqual(page["total"], 10)
        self.assertTrue(page["truncated"])
        self.assertEqual(page["next_offset"], 3)

        last = page_items(list(range(10)), offset=9, limit=5)
        self.assertEqual(last["items"], [9])
        self.assertFalse(last["truncated"])

    def test_truncate_text(self):
        from androguard.mcp.truncate import truncate_text

        text = truncate_text("abcdefghij", max_chars=4, meta={"k": 1})
        self.assertEqual(text["source"], "abcd")
        self.assertEqual(text["chars"], 10)
        self.assertTrue(text["truncated"])
        self.assertEqual(text["k"], 1)

    def test_jsonable(self):
        from androguard.mcp.truncate import jsonable

        self.assertEqual(
            jsonable({"a": 1, "b": [b"x", None]}),
            {"a": 1, "b": ["x", None]},
        )

    def test_error_payload(self):
        from androguard.mcp.errors import McpToolError, error_payload

        err = McpToolError("path_denied", "nope", hint="set ROOTS")
        d = err.to_dict()
        self.assertFalse(d["ok"])
        self.assertEqual(d["error"]["code"], "path_denied")
        self.assertEqual(d["error"]["hint"], "set ROOTS")
        self.assertEqual(
            error_payload("not_found", "missing")["error"]["code"],
            "not_found",
        )

    def test_startup_banner_logs(self):
        import io
        import logging

        from androguard.mcp.server import _configure_logging, _log_startup
        from androguard.mcp.session import SessionStore

        _configure_logging("INFO")
        log = logging.getLogger("androguard.mcp")
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setLevel(logging.INFO)
        log.addHandler(handler)
        try:
            _log_startup(
                SessionStore(allow_any=True),
                transport="stdio",
                log_tools=True,
            )
        finally:
            log.removeHandler(handler)
        text = buf.getvalue()
        self.assertIn("Androguard MCP server starting", text)
        self.assertIn("tools (", text)
        self.assertIn("Ready — waiting for MCP client", text)
        self.assertIn("ALLOW ANY", text)
        self.assertIn("tool call logging  on", text)

    def test_parse_args(self):
        from androguard.mcp.server import _parse_args

        args = _parse_args(["--log-level", "DEBUG", "--log-tools"])
        self.assertEqual(args.log_level, "DEBUG")
        self.assertTrue(args.log_tools)
        defaults = _parse_args([])
        self.assertEqual(defaults.log_level, "INFO")
        self.assertFalse(defaults.log_tools)


class McpInspectTest(unittest.TestCase):
    """Mocked dispatch tests run without optional decompiler/disasm bindings."""

    def test_java_method_paging(self):
        from androguard.mcp import tools as T

        with patch.object(T, "decompile_method") as method:
            method.return_value = {
                "source": "abcdefgh", "chars": 12, "truncated": True
            }
            page = T.inspect_code(
                None, "session", "com.example.Auth#login",
                offset=3, max_chars=5,
            )
        method.assert_called_once_with(
            None, "session", "com.example.Auth#login", max_chars=8
        )
        self.assertEqual(page["source"], "defgh")
        self.assertEqual(page["next_offset"], 8)
        self.assertEqual(page["chars"], 12)
        self.assertEqual(page["scope"], "method")

    def test_java_class_dex_name_and_last_page(self):
        from androguard.mcp import tools as T

        with patch.object(T, "get_class") as get_class:
            get_class.return_value = {
                "source": "abcdefghij", "chars": 10, "truncated": False
            }
            page = T.inspect_code(
                None, "session", "Lcom/example/Auth;",
                offset=8, max_chars=5,
            )
        get_class.assert_called_once_with(
            None, "session", "com.example.Auth", max_chars=13
        )
        self.assertEqual(page["source"], "ij")
        self.assertFalse(page["truncated"])
        self.assertNotIn("next_offset", page)

    def test_dalvik_literal_selection(self):
        from androguard.mcp import tools as T

        with (
            patch.object(
                T, "_app", return_value=SimpleNamespace(methods=[1, 2, 3])
            ),
            patch.object(T, "disassemble_method") as disasm,
        ):
            disasm.return_value = {
                "source": "# example", "chars": 9, "methods": 2
            }
            page = T.inspect_code(
                None, "session", "com.example.A$B#on.Create", format="dalvik"
            )
        self.assertEqual(page["methods"], 2)
        self.assertEqual(page["source"], "# example")
        self.assertEqual(
            disasm.call_args.kwargs["class_pattern"], r"^Lcom/example/A\$B;$"
        )
        self.assertEqual(
            disasm.call_args.kwargs["method_pattern"], r"^on\.Create$"
        )
        self.assertEqual(disasm.call_args.kwargs["limit_methods"], 3)

    def test_invalid_parameters(self):
        from androguard.mcp import tools as T
        from androguard.mcp.errors import McpToolError

        for kwargs in (
            {"selector": ""},
            {"selector": "Foo#"},
            {"selector": "Foo#a#b"},
            {"selector": "Foo", "format": "smali"},
            {"selector": "Foo", "offset": -1},
            {"selector": "Foo", "max_chars": 0},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(McpToolError) as ctx:
                    T.inspect_code(None, "session", **kwargs)
                self.assertEqual(ctx.exception.code, "invalid_argument")


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk missing")
class McpSessionTest(unittest.TestCase):
    def setUp(self):
        from androguard.mcp.errors import McpToolError
        from androguard.mcp.session import SessionStore

        self.McpToolError = McpToolError
        self.store = SessionStore(
            roots=[TEST_APK.resolve().parent.parent],  # tests/data
            max_sessions=2,
            ttl_seconds=600,
            allow_any=False,
        )

    def test_open_summary_close(self):
        from androguard.mcp import tools as T

        opened = self.store.open(TEST_APK)
        self.assertTrue(opened["ok"])
        sid = opened["session_id"]
        self.assertEqual(opened["summary"]["package"], "tests.androguard")
        summary = T.apk_summary(self.store, sid)
        self.assertTrue(summary["ok"])
        classes = T.list_classes(
            self.store, sid, pattern=r"TestActivity", limit=20
        )
        self.assertTrue(classes["ok"])
        self.assertGreater(classes["total"], 0)
        methods = T.list_methods(
            self.store,
            sid,
            class_pattern=r"TestActivity",
            method_pattern=r"onCreate",
            with_code=True,
            limit=10,
        )
        self.assertTrue(methods["ok"])
        self.assertGreaterEqual(methods["total"], 1)
        closed = self.store.close(sid)
        self.assertTrue(closed["closed"])

    def test_list_strings_and_permissions(self):
        from androguard.mcp import tools as T

        sid = self.store.open(TEST_APK)["session_id"]
        strings = T.list_strings(self.store, sid, needle="android", limit=10)
        self.assertTrue(strings["ok"])
        self.assertLessEqual(len(strings["items"]), 10)
        searched = T.search_strings(self.store, sid, "Test", limit=5)
        self.assertTrue(searched["ok"])
        perms = T.list_permissions(self.store, sid, limit=50)
        self.assertTrue(perms["ok"])
        self.assertIn("items", perms)
        sessions = self.store.list_sessions()
        self.assertTrue(sessions["ok"])
        self.assertEqual(len(sessions["sessions"]), 1)

    def test_path_denied_outside_roots(self):
        with self.assertRaises(self.McpToolError) as ctx:
            self.store.open("/etc/hosts")
        self.assertEqual(ctx.exception.code, "path_denied")

    def test_file_not_found(self):
        missing = TEST_APK.resolve().parent / "does-not-exist.apk"
        with self.assertRaises(self.McpToolError) as ctx:
            self.store.open(missing)
        self.assertEqual(ctx.exception.code, "not_found")

    def test_unknown_session(self):
        from androguard.mcp import tools as T

        with self.assertRaises(self.McpToolError) as ctx:
            T.apk_summary(self.store, "no-such-session")
        self.assertEqual(ctx.exception.code, "session_expired")

    def test_max_sessions_evicts(self):
        first = self.store.open(TEST_APK)["session_id"]
        second = self.store.open(TEST_APK)["session_id"]
        self.assertNotEqual(first, second)
        # max_sessions=2 → opening a third drops the oldest
        third = self.store.open(TEST_APK)["session_id"]
        self.assertEqual(len(self.store.list_sessions()["sessions"]), 2)
        with self.assertRaises(self.McpToolError) as ctx:
            self.store.get(first)
        self.assertEqual(ctx.exception.code, "session_expired")
        self.store.get(second)
        self.store.get(third)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk missing")
@unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
class McpDecompileTest(unittest.TestCase):
    def setUp(self):
        from androguard.mcp.session import SessionStore

        self.store = SessionStore(allow_any=True, max_sessions=2)

    def test_decompile_method_and_find_refs(self):
        from androguard.mcp import tools as T

        sid = self.store.open(TEST_APK)["session_id"]
        java = T.decompile_method(
            self.store,
            sid,
            "tests.androguard.TestActivity#onCreate",
            max_chars=8000,
        )
        self.assertTrue(java["ok"])
        self.assertIn("onCreate", java["source"])
        refs = T.find_refs(self.store, sid, "string", "Hello", limit=20)
        self.assertTrue(refs["ok"])
        vulns = T.scan_vulns(self.store, sid, limit=20)
        self.assertTrue(vulns["ok"])
        self.assertIn("items", vulns)

    def test_inspect_code_java(self):
        from androguard.mcp import tools as T

        sid = self.store.open(TEST_APK)["session_id"]
        method = T.inspect_code(
            self.store, sid,
            "tests.androguard.TestActivity#onCreate", max_chars=8000,
        )
        self.assertIn("onCreate", method["source"])
        cls = T.inspect_code(
            self.store, sid, "tests.androguard.TestActivity",
            max_chars=16000,
        )
        self.assertIn("TestActivity", cls["source"])


    def test_get_class(self):
        from androguard.mcp import tools as T

        sid = self.store.open(TEST_APK)["session_id"]
        out = T.get_class(
            self.store,
            sid,
            "tests.androguard.TestActivity",
            max_chars=16000,
        )
        self.assertTrue(out["ok"])
        self.assertIn("TestActivity", out["source"])

    def test_decompile_method_not_found(self):
        from androguard.mcp import tools as T
        from androguard.mcp.errors import McpToolError

        sid = self.store.open(TEST_APK)["session_id"]
        with self.assertRaises(McpToolError) as ctx:
            T.decompile_method(
                self.store, sid, "tests.androguard.NoSuch#missing"
            )
        self.assertEqual(ctx.exception.code, "not_found")

    def test_find_refs_invalid_kind(self):
        from androguard.mcp import tools as T
        from androguard.mcp.errors import McpToolError

        sid = self.store.open(TEST_APK)["session_id"]
        with self.assertRaises(McpToolError) as ctx:
            T.find_refs(self.store, sid, "nope", "x")
        self.assertEqual(ctx.exception.code, "not_found")

    def test_decompile_package_writes(self):
        from androguard.mcp import tools as T

        sid = self.store.open(TEST_APK)["session_id"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = T.decompile_package(
                self.store,
                sid,
                "tests.androguard",
                out_dir=str(out),
            )
            self.assertTrue(result["ok"])
            self.assertGreater(result["classes_written"], 0)
            self.assertTrue(any(out.rglob("*.java")))


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk missing")
@unittest.skipUnless(HAS_BYTECODE, "dex-bytecode not installed")
class McpDisasmTest(unittest.TestCase):
    def test_disassemble(self):
        from androguard.mcp import tools as T
        from androguard.mcp.session import SessionStore

        store = SessionStore(allow_any=True)
        sid = store.open(TEST_APK)["session_id"]
        out = T.disassemble_method(
            store,
            sid,
            class_pattern=r"TestActivity",
            method_pattern=r"^onCreate$",
            limit_methods=1,
            max_chars=8000,
        )
        self.assertTrue(out["ok"])
        self.assertIn("onCreate", out["source"])

    def test_inspect_code_dalvik(self):
        from androguard.mcp import tools as T
        from androguard.mcp.session import SessionStore

        store = SessionStore(allow_any=True)
        sid = store.open(TEST_APK)["session_id"]
        method = T.inspect_code(
            store, sid, "tests.androguard.TestActivity#onCreate",
            format="dalvik", max_chars=8000,
        )
        self.assertIn("onCreate", method["source"])
        self.assertGreaterEqual(method["methods"], 1)
        cls = T.inspect_code(
            store, sid, "Ltests/androguard/TestActivity;",
            format="dalvik", max_chars=200000,
        )
        self.assertIn("onCreate", cls["source"])


    def test_disassemble_no_match(self):
        from androguard.mcp import tools as T
        from androguard.mcp.errors import McpToolError
        from androguard.mcp.session import SessionStore

        store = SessionStore(allow_any=True)
        sid = store.open(TEST_APK)["session_id"]
        with self.assertRaises(McpToolError) as ctx:
            T.disassemble_method(
                store,
                sid,
                class_pattern=r"NoSuchClassXYZ",
                method_pattern=r"^nope$",
            )
        self.assertEqual(ctx.exception.code, "not_found")


@unittest.skipUnless(HAS_MCP, "mcp package not installed")
class McpServerRegistrationTest(unittest.TestCase):
    def test_create_server_lists_tools(self):
        import asyncio

        from androguard.mcp.server import create_server
        from androguard.mcp.session import SessionStore

        server = create_server(SessionStore(allow_any=True))
        tools = asyncio.run(server.list_tools())
        names = {t.name for t in tools}
        for expected in (
            "open_apk",
            "close_apk",
            "list_sessions",
            "apk_summary",
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
        ):
            self.assertIn(expected, names)

    def test_open_apk_tool_json(self):
        import asyncio

        from androguard.mcp.server import create_server
        from androguard.mcp.session import SessionStore

        if not file_exists(TEST_APK):
            self.skipTest("TestActivity.apk missing")
        server = create_server(SessionStore(allow_any=True))
        result = asyncio.run(
            server.call_tool("open_apk", {"path": str(TEST_APK)})
        )
        text = result.content[0].text
        payload = json.loads(text)
        self.assertTrue(payload.get("ok"))
        self.assertIn("session_id", payload)

        bad = asyncio.run(
            server.call_tool("apk_summary", {"session_id": "missing"})
        )
        err = json.loads(bad.content[0].text)
        self.assertFalse(err.get("ok"))
        self.assertEqual(err["error"]["code"], "session_expired")

    def test_call_list_classes_tool(self):
        import asyncio

        from androguard.mcp.server import create_server
        from androguard.mcp.session import SessionStore

        if not file_exists(TEST_APK):
            self.skipTest("TestActivity.apk missing")
        server = create_server(SessionStore(allow_any=True))
        opened = json.loads(
            asyncio.run(
                server.call_tool("open_apk", {"path": str(TEST_APK)})
            ).content[0].text
        )
        sid = opened["session_id"]
        listed = json.loads(
            asyncio.run(
                server.call_tool(
                    "list_classes",
                    {
                        "session_id": sid,
                        "pattern": "TestActivity",
                        "limit": 20,
                    },
                )
            ).content[0].text
        )
        self.assertTrue(listed["ok"])
        self.assertGreater(listed["total"], 0)


if __name__ == "__main__":
    unittest.main()
