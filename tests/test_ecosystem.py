# -*- coding: utf-8 -*-
"""Integration tests for the Androguard v5 ecosystem stack."""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from androguard import Application, AnalyzeAPK
from androguard.core import apk, axml, dex
from androguard.core.bytecode import (
    BytecodeNotAvailable,
    disassemble,
    disassemble_method_code,
    method_insns_bytes,
)
from androguard.core.decompiler import (
    decompile_method,
    parse_method_selector,
)
from androguard.misc import AnalyzeAPK as misc_analyze
from apkparser import APK as ApkParserAPK

from tests.helpers import (
    HAS_BYTECODE,
    HAS_DECOMPILER,
    MULTIDEX_APK,
    TEST_APK,
    file_exists,
    open_apk_stream,
    read_apk_bytes,
)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class ApplicationFixture(unittest.TestCase):
    """Shared Application instance for read-only integration tests."""

    @classmethod
    def setUpClass(cls):
        cls.app = Application(TEST_APK)

    def test_summary_fields(self):
        summary = self.app.summary()
        self.assertEqual(summary["app_name"], "TestsAndroguardApplication")
        self.assertIn("TestActivity", summary["main_activity"])
        self.assertEqual(summary["package"], "tests.androguard")
        self.assertEqual(summary["dex_files"], ["classes.dex"])
        self.assertTrue(summary["signed"])
        self.assertGreater(summary["classes"], 100)
        self.assertGreater(summary["strings"], 1000)
        self.assertGreater(summary["methods"], 1000)

    def test_lazy_properties_cached(self):
        classes1 = self.app.class_names
        classes2 = self.app.class_names
        self.assertIs(classes1, classes2)
        self.assertEqual(len(classes1), self.app.summary()["classes"])

    def test_apk_property(self):
        self.assertIsInstance(self.app.apk, ApkParserAPK)
        self.assertEqual(self.app.apk.get_app_name(), "TestsAndroguardApplication")

    def test_manifest_axml(self):
        self.assertIsNotNone(self.app.apk.axml)
        self.assertEqual(self.app.apk.axml.package, "tests.androguard")


class EcosystemImportTest(unittest.TestCase):
    def test_core_reexports(self):
        self.assertIs(apk.APK, ApkParserAPK)
        self.assertTrue(hasattr(axml, "AXMLPrinter"))
        self.assertTrue(hasattr(axml, "ARSCParser"))
        self.assertTrue(hasattr(dex, "DEXHelper"))
        self.assertTrue(hasattr(dex, "DEX_from_source"))


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class AnalyzeAPKTest(unittest.TestCase):
    def test_from_path(self):
        a, dex_helpers, app = AnalyzeAPK(TEST_APK)
        self.assertIsInstance(a, ApkParserAPK)
        self.assertEqual(len(dex_helpers), 1)
        self.assertIsInstance(app, Application)
        self.assertEqual(app.summary()["package"], "tests.androguard")

    def test_from_bytes_raw(self):
        data = read_apk_bytes(TEST_APK)
        a, dex_helpers, app = misc_analyze(data, raw=True)
        self.assertEqual(len(dex_helpers), 1)
        self.assertGreater(app.summary()["methods"], 0)

    def test_from_bytesio(self):
        app = Application(open_apk_stream(TEST_APK))
        self.assertGreater(len(app.dex), 0)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class DexIntegrationTest(unittest.TestCase):
    def test_dex_helper_from_apk_bytes(self):
        apk_obj = apk.APK(
            open_apk_stream(TEST_APK),
            {apk.OPTION_AXML: True},
        )
        raw = next(apk_obj.get_all_dex())
        dh = dex.DEXHelper.from_string(raw)
        methods = list(dh.get_methods())
        self.assertGreater(len(methods), 0)
        self.assertTrue(methods[0].name)

    def test_dex_from_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk_obj = apk.APK(
                open_apk_stream(TEST_APK),
                {apk.OPTION_AXML: True},
            )
            dex_path = Path(tmp) / "classes.dex"
            dex_path.write_bytes(next(apk_obj.get_all_dex()))
            d = dex.DEX.from_path(str(dex_path))
            dh = dex.DEXHelper.from_rawdex(d)
            self.assertGreater(len(list(dh.get_classes())), 0)
            header = d["header"]
            self.assertIn("class_defs_size", header)
            self.assertGreater(header["class_defs_size"], 0)

    def test_strings_contain_known_literal(self):
        app = Application(TEST_APK)
        joined = "\n".join(app.strings)
        self.assertIn("this is a test", joined)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class MethodFilterTest(unittest.TestCase):
    def setUp(self):
        self.app = Application(TEST_APK)

    def test_iter_methods_regex(self):
        matches = list(
            self.app.iter_methods(
                class_pattern=r"TestActivity",
                method_pattern=r"onCreate",
                with_code=True,
            )
        )
        self.assertEqual(len(matches), 1)
        m = matches[0]
        self.assertIn("TestActivity", m.class_name)
        self.assertEqual(m.name, "onCreate")
        self.assertIsNotNone(m.get_code())

    def test_iter_methods_class_only(self):
        matches = list(
            self.app.iter_methods(class_pattern=r"Ltests/androguard/TestActivity;")
        )
        self.assertGreater(len(matches), 0)
        for m in matches:
            self.assertIn("TestActivity", m.class_name)

    def test_iter_methods_with_code_excludes_abstract(self):
        all_oncreate = list(
            self.app.iter_methods(method_pattern=r"onCreate")
        )
        with_code = list(
            self.app.iter_methods(
                method_pattern=r"onCreate", with_code=True
            )
        )
        self.assertLessEqual(len(with_code), len(all_oncreate))


@unittest.skipUnless(
    file_exists(MULTIDEX_APK), "app-prod-debug.apk not present"
)
class MultiDexTest(unittest.TestCase):
    def test_multiple_dex_helpers(self):
        app = Application(MULTIDEX_APK)
        self.assertEqual(len(app.dex), 2)
        self.assertEqual(
            sorted(app.summary()["dex_files"]),
            ["classes.dex", "classes2.dex"],
        )

    def test_methods_aggregated_across_dex(self):
        app = Application(MULTIDEX_APK)
        per_dex = [len(list(dh.get_methods())) for dh in app.dex]
        self.assertEqual(sum(per_dex), app.summary()["methods"])


@unittest.skipUnless(HAS_BYTECODE and file_exists(TEST_APK), "dex-bytecode missing")
class BytecodeTest(unittest.TestCase):
    def setUp(self):
        self.app = Application(TEST_APK)

    def test_disassemble_nop_return(self):
        insns = disassemble(b"\x00\x00\x0e\x00")
        self.assertEqual(len(insns), 2)
        self.assertEqual(insns[0]["mnemonic"], "nop")
        self.assertEqual(insns[1]["mnemonic"], "return-void")

    def test_disassemble_oncreate_method(self):
        method = next(
            self.app.iter_methods(
                class_pattern=r"TestActivity",
                method_pattern=r"onCreate",
                with_code=True,
            )
        )
        code = method.get_code()
        raw = method_insns_bytes(code)
        self.assertGreater(len(raw), 0)
        insns = disassemble_method_code(code)
        self.assertGreater(len(insns), 5)
        mnemonics = {i["mnemonic"] for i in insns}
        self.assertTrue(
            mnemonics & {"invoke-virtual", "invoke-super", "return-void"}
        )

    def test_iter_disassembly_lines(self):
        method = next(
            self.app.iter_methods(
                class_pattern=r"TestActivity",
                method_pattern=r"onCreate",
                with_code=True,
            )
        )
        lines = list(self.app.iter_disassembly(method))
        self.assertGreater(len(lines), 5)
        self.assertTrue(all("  " in line for line in lines[:3]))


class BytecodeNotAvailableTest(unittest.TestCase):
    @unittest.skipIf(HAS_BYTECODE, "dex-bytecode is installed")
    def test_disassemble_raises(self):
        with self.assertRaises(BytecodeNotAvailable):
            disassemble(b"\x00\x00")


@unittest.skipUnless(
    HAS_DECOMPILER and file_exists(TEST_APK),
    "dex-decompiler or TestActivity.apk missing",
)
class DecompilerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = Application(TEST_APK)

    def test_decompile_method_selector(self):
        java = self.app.decompile_method_selector(
            "tests.androguard.TestActivity#onCreate"
        )
        self.assertIn("onCreate", java)
        self.assertIn("void", java)
        self.assertIn("setContentView", java)

    def test_decompile_by_regex_matches_selector(self):
        method = next(
            self.app.iter_methods(
                class_pattern=r"TestActivity",
                method_pattern=r"onCreate",
                with_code=True,
            )
        )
        via_regex = next(
            self.app.iter_decompiled_methods(
                class_pattern=r"TestActivity",
                method_pattern=r"onCreate",
            )
        )[1]
        via_direct = self.app.decompile_method(method)
        self.assertEqual(via_regex.strip(), via_direct.strip())

    def test_decompile_method_low_level(self):
        raw = self.app._dex_blobs()[0][1]
        java = decompile_method(
            raw,
            "Ltests/androguard/TestActivity;",
            "onCreate",
        )
        self.assertIn("onCreate", java)

    def test_decompile_apk_to_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            self.app.decompile_apk_to_dir(
                out, only_package="tests.androguard"
            )
            self.assertTrue(out.exists())
            sub = out / "classes"
            self.assertTrue(sub.is_dir() or (out / "Decompiled.java").exists())

    def test_invalid_selector_on_app(self):
        with self.assertRaises(ValueError):
            parse_method_selector("invalid")


if __name__ == "__main__":
    unittest.main()
