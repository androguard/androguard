# -*- coding: utf-8 -*-
"""CLI tests for the ``androguard`` entry point."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from androguard.cli.main import app as cli_app

from tests.helpers import (
    HAS_BYTECODE,
    HAS_DECOMPILER,
    HAS_PATCH,
    TEST_APK,
    file_exists,
)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class CliSummaryTest(unittest.TestCase):
    def _run(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            code = cli_app(["-i", str(TEST_APK), *argv])
        return code, buf.getvalue() + err.getvalue()

    def test_summary_exit_zero(self):
        code, out = self._run()
        self.assertEqual(code, 0)
        self.assertIn("TestsAndroguardApplication", out)
        self.assertIn("tests.androguard", out)
        self.assertIn("classes:", out)

    def test_list_classes(self):
        code, out = self._run("--list-classes")
        self.assertEqual(code, 0)
        self.assertIn("Ltests/androguard/TestActivity;", out)

    def test_list_methods(self):
        code, out = self._run("--list-methods")
        self.assertEqual(code, 0)
        self.assertIn("onCreate", out)
        self.assertIn("TestActivity", out)

    def test_disasm_requires_filter(self):
        code, out = self._run("--disasm")
        self.assertEqual(code, 1)
        self.assertIn("--class", out.lower() + out)

    @unittest.skipUnless(HAS_BYTECODE, "dex-bytecode not installed")
    def test_disasm_oncreate(self):
        code, out = self._run(
            "--disasm",
            "--class",
            "TestActivity",
            "--method",
            "onCreate",
        )
        self.assertEqual(code, 0)
        self.assertIn("onCreate", out)
        self.assertRegex(out, r"(invoke-super|invoke-virtual|return-void)")

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_decompile_method(self):
        code, out = self._run(
            "--decompile-method",
            "tests.androguard.TestActivity#onCreate",
        )
        self.assertEqual(code, 0)
        self.assertIn("onCreate", out)
        self.assertIn("setContentView", out)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_decompile_regex(self):
        code, out = self._run(
            "--decompile",
            "--class",
            "TestActivity",
            "--method",
            "onCreate",
        )
        self.assertEqual(code, 0)
        self.assertIn("void", out)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_decompile_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.java"
            code, _ = self._run(
                "--decompile",
                "-o",
                str(out_path),
            )
            self.assertEqual(code, 0)
            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertGreater(len(text), 100)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_getclass(self):
        code, out = self._run("--getclass", "tests.androguard.TestActivity")
        self.assertEqual(code, 0)
        self.assertIn("TestActivity", out)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_emulate(self):
        code, out = self._run(
            "--emulate", "tests.androguard.TestActivity#onCreate"
        )
        self.assertEqual(code, 0)
        self.assertIn("steps=", out)

    @unittest.skipUnless(HAS_BYTECODE, "dex-bytecode not installed")
    def test_disasm_cfg(self):
        code, out = self._run(
            "--disasm",
            "--cfg",
            "--class",
            "TestActivity",
            "--method",
            "onCreate",
        )
        self.assertEqual(code, 0)
        self.assertIn("basic block", out)

    @unittest.skipUnless(HAS_PATCH, "apk-patch not installed")
    def test_decode_project(self):
        code, out = self._run("--decode-project")
        self.assertEqual(code, 0)
        self.assertIn("project_root=", out)
        self.assertIn("AndroidManifest", out)

    def test_verbose_still_succeeds(self):
        code, out = self._run("-v")
        self.assertEqual(code, 0)
        self.assertIn("package:", out)

    def test_disasm_no_match(self):
        code, out = self._run(
            "--disasm", "--class", "NoSuchClassXYZ123"
        )
        self.assertEqual(code, 1)
        self.assertIn("No methods", out)

    def test_findrefs_requires_value(self):
        code, out = self._run("--findrefs", "string")
        self.assertEqual(code, 1)
        self.assertIn("--findrefs-value", out)

    def test_emulate_bad_selector(self):
        code, out = self._run("--emulate", "not-a-selector")
        self.assertEqual(code, 1)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_findrefs_string(self):
        code, out = self._run(
            "--findrefs", "string", "--findrefs-value", "this is a test"
        )
        self.assertEqual(code, 0)
        self.assertIn("#", out)

    @unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
    def test_scan_vulns_runs(self):
        code, out = self._run("--scan-vulns")
        self.assertEqual(code, 0)
        self.assertIn("classes:", out)


class CliUsageTest(unittest.TestCase):
    def test_missing_input_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            cli_app([])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_apk_raises(self):
        with self.assertRaises(FileNotFoundError):
            cli_app(["-i", "/tmp/androguard-missing-apk.apk"])


if __name__ == "__main__":
    unittest.main()
