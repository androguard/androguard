# -*- coding: utf-8 -*-
"""Coverage for every public androguard submodule."""

from __future__ import annotations

import importlib
import io
import json
import unittest
from pathlib import Path

import androguard
from androguard import Application, LazyProperty
from androguard.core import apk as core_apk
from androguard.core import arm as core_arm
from androguard.core import axml as core_axml
from androguard.core import bytecode as core_bc
from androguard.core import decompiler as core_dec
from androguard.core import dex as core_dex
from androguard.core import patch as core_patch
from androguard.helper.logging import LOGGER
from androguard.main import app as module_app
from androguard.misc import AnalyzeAPK, AnalyzeDex, clean_file_name

from tests.helpers import (
    APK_DIR,
    HAS_ARM,
    HAS_BYTECODE,
    HAS_DECOMPILER,
    HAS_PATCH,
    TEST_APK,
    TEST_DEX,
    UNSIGNED_APK,
    file_exists,
    read_apk_bytes,
)

FIELDS_DEX = APK_DIR / "FieldsTest.dex"
MULTIDEX_APK = APK_DIR / "multidex.apk"
EXPECTED_MODULES = (
    "androguard",
    "androguard.application",
    "androguard.misc",
    "androguard.main",
    "androguard.cli.main",
    "androguard.core",
    "androguard.core.apk",
    "androguard.core.dex",
    "androguard.core.axml",
    "androguard.core.bytecode",
    "androguard.core.decompiler",
    "androguard.core.arm",
    "androguard.core.patch",
    "androguard.helper",
    "androguard.helper.logging",
)


class PackageSurfaceTest(unittest.TestCase):
    def test_every_submodule_imports(self):
        for name in EXPECTED_MODULES:
            mod = importlib.import_module(name)
            self.assertIsNotNone(mod, name)

    def test_public_exports(self):
        self.assertEqual(androguard.__version__, "5.0.0")
        for name in androguard.__all__:
            self.assertTrue(hasattr(androguard, name), name)
        self.assertIs(module_app, importlib.import_module("androguard.cli.main").app)

    def test_core_all_lists(self):
        self.assertIn("APK", core_apk.__all__)
        self.assertIn("FileNotPresent", core_apk.__all__)
        self.assertIn("is_dex", core_dex.__all__)
        self.assertIn("AXMLPrinter", core_axml.__all__)
        self.assertIn("ARSCParser", core_axml.__all__)

    def test_logger_name(self):
        self.assertEqual(LOGGER.name, "androguard")


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class CoreApkTest(unittest.TestCase):
    def setUp(self):
        self.raw = read_apk_bytes(TEST_APK)
        self.apk = core_apk.APK(
            io.BytesIO(self.raw),
            {
                core_apk.OPTION_AXML: True,
                core_apk.OPTION_SIGNATURE: True,
                core_apk.OPTION_PERMISSION: True,
            },
        )

    def test_manifest_identity(self):
        self.assertEqual(self.apk.get_app_name(), "TestsAndroguardApplication")
        self.assertEqual(
            self.apk.get_main_activity(), "tests.androguard.TestActivity"
        )
        self.assertIn(
            "tests.androguard.TestActivity", self.apk.get_activities()
        )
        self.assertFalse(self.apk.is_multidex())
        self.assertTrue(self.apk.signature.is_signed())

    def test_archive_entries(self):
        names = list(self.apk.get_files())
        self.assertIn("classes.dex", names)
        self.assertIn("AndroidManifest.xml", names)
        self.assertIn("resources.arsc", names)
        crc = dict(self.apk.get_files_crc32())
        self.assertIn("classes.dex", crc)
        self.assertIsNone(self.apk.get_file("does-not-exist"))
        self.assertTrue(self.apk.get_app_icon())

    def test_unsigned_apk(self):
        if not file_exists(UNSIGNED_APK):
            self.skipTest("unsigned apk missing")
        apk = core_apk.APK(
            io.BytesIO(read_apk_bytes(UNSIGNED_APK)),
            {core_apk.OPTION_SIGNATURE: True, core_apk.OPTION_AXML: True},
        )
        self.assertFalse(apk.signature and apk.signature.is_signed())

    def test_multidex_flag(self):
        if not file_exists(MULTIDEX_APK):
            self.skipTest("multidex.apk missing")
        apk = core_apk.APK(
            io.BytesIO(read_apk_bytes(MULTIDEX_APK)),
            {core_apk.OPTION_AXML: True},
        )
        names = list(apk.get_dex_names())
        self.assertGreaterEqual(len(names), 2)
        self.assertTrue(apk.is_multidex())


@unittest.skipUnless(file_exists(TEST_DEX), "Test.dex not present")
class CoreDexTest(unittest.TestCase):
    def test_is_dex_magic(self):
        raw = TEST_DEX.read_bytes()
        self.assertTrue(core_dex.is_dex(raw))
        self.assertFalse(core_dex.is_dex(b"PK\x03\x04not-dex"))
        self.assertFalse(core_dex.is_dex(b""))

    def test_helpers_on_test_dex(self):
        dh = core_dex.DEXHelper.from_string(TEST_DEX.read_bytes())
        classes = list(dh.get_classes())
        self.assertEqual(len(classes), 1)
        self.assertTrue(classes[0].name.endswith("Test;"))
        methods = list(dh.get_methods())
        names = {m.name for m in methods}
        self.assertIn("<init>", names)
        self.assertIn("aTestMethod", names)
        coded = [m for m in methods if m.get_code()]
        self.assertEqual(len(coded), len(methods))

    def test_dex_header_and_path(self):
        d = core_dex.DEX.from_path(str(TEST_DEX))
        header = d["header"]
        self.assertGreater(header["class_defs_size"], 0)
        self.assertGreater(header["method_ids_size"], 0)
        dh = core_dex.DEXHelper.from_rawdex(
            core_dex.DEX_from_source(str(TEST_DEX))
        )
        self.assertGreater(len(list(dh.get_strings())), 0)

    def test_fields(self):
        if not file_exists(FIELDS_DEX):
            self.skipTest("FieldsTest.dex missing")
        dh = core_dex.DEXHelper.from_string(FIELDS_DEX.read_bytes())
        fields = {(f.name, f.type_field) for f in dh.get_fields()}
        self.assertIn(("afield", "I"), fields)
        self.assertIn(("cfield", "S"), fields)
        cls = next(iter(dh.get_classes()))
        self.assertIn("FieldsTest", cls.name)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class CoreAxmlTest(unittest.TestCase):
    def test_manifest_printer(self):
        apk = core_apk.APK(
            io.BytesIO(read_apk_bytes(TEST_APK)),
            {core_apk.OPTION_AXML: True},
        )
        xml = core_axml.AXMLPrinter(
            apk.get_file("AndroidManifest.xml")
        ).get_xml()
        text = xml.decode("utf-8") if isinstance(xml, bytes) else str(xml)
        self.assertIn("tests.androguard", text)
        self.assertIn("manifest", text)
        self.assertTrue(core_axml.namespace)

    def test_arsc_packages(self):
        apk = core_apk.APK(
            io.BytesIO(read_apk_bytes(TEST_APK)),
            {core_apk.OPTION_AXML: True},
        )
        parser = core_axml.ARSCParser(apk.get_file("resources.arsc"))
        self.assertIn("tests.androguard", parser.get_packages_names())
        self.assertIsInstance(core_axml.ARSCResTableConfig, type)


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class ApplicationModuleTest(unittest.TestCase):
    def test_constructors(self):
        from_path = Application(TEST_APK)
        from_bytes = Application(read_apk_bytes(TEST_APK))
        from_stream = Application(io.BytesIO(read_apk_bytes(TEST_APK)))
        self.assertEqual(
            from_path.summary()["package"], from_bytes.summary()["package"]
        )
        self.assertEqual(len(from_stream.dex), 1)
        self.assertIsInstance(Application.class_names, LazyProperty)

    def test_flags_without_axml(self):
        app = Application(
            TEST_APK, axml=False, signature=False, permissions=False
        )
        self.assertEqual(app.summary()["package"], "")
        self.assertFalse(app.summary()["signed"])
        self.assertGreater(app.summary()["methods"], 0)

    def test_filters_and_cache(self):
        app = Application(TEST_APK)
        self.assertEqual(
            list(app.iter_methods(class_pattern=r"NoSuchClassXYZ")), []
        )
        first = app.strings
        self.assertIs(first, app.strings)
        self.assertTrue(any("this is a test" in s for s in first))

    def test_analyze_apk_compat(self):
        apk, helpers, app = AnalyzeAPK(
            read_apk_bytes(TEST_APK), raw=True, session=object()
        )
        self.assertEqual(apk.get_app_name(), "TestsAndroguardApplication")
        self.assertEqual(len(helpers), 1)
        self.assertIsInstance(app, Application)

    def test_analyze_dex_rejects_garbage(self):
        with self.assertRaises(Exception):
            AnalyzeDex(b"not a dex file")

    def test_clean_file_name_keeps_safe_chars(self):
        self.assertEqual(
            clean_file_name("A-b_c.1", unique=False), "A-b_c.1"
        )


@unittest.skipUnless(HAS_BYTECODE, "dex-bytecode not installed")
class CoreBytecodeTest(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        nop = core_bc.encode_nop()
        ret = core_bc.encode_return_void()
        goto = core_bc.encode_goto(1)
        data = nop + goto + ret
        mnemonics = [i["mnemonic"] for i in core_bc.disassemble(data)]
        self.assertEqual(mnemonics, ["nop", "goto", "return-void"])
        self.assertEqual(core_bc.opcode_of("nop"), 0)
        self.assertIsNone(core_bc.opcode_of("not-an-opcode"))
        self.assertEqual(
            core_bc.encode_instruction("const/4", "v0, 1")[0], 0x12
        )

    def test_cfg_patch_and_labels(self):
        data = core_bc.encode_nop() + core_bc.encode_goto(1) + core_bc.encode_return_void()
        targets = core_bc.branch_targets(data)
        self.assertIn(4, targets)
        edges = core_bc.cfg_edges(data)
        self.assertTrue(any(e["to"] == 4 for e in edges))
        lines = list(core_bc.disassemble_lines(data, labels=True))
        self.assertTrue(any(line.startswith(":L") for line in lines))
        patched = core_bc.patch_branch(data, 2, 0)
        self.assertEqual(len(patched), len(data))
        self.assertNotEqual(patched, data)
        self.assertEqual(
            core_bc.exception_edges(data, []),
            [],
        )
        self.assertEqual(core_bc.method_basic_blocks(None), [])
        self.assertEqual(core_bc.method_cfg_edges(None), [])

    def test_bad_offset(self):
        with self.assertRaises(ValueError):
            core_bc.disassemble(b"\x00\x00", offset=8)
        plain = core_bc.format_instruction(
            {
                "offset": 0,
                "opcode": 0,
                "mnemonic": "nop",
                "operands": "",
            },
            show_address=False,
        )
        self.assertEqual(plain, "nop")


@unittest.skipUnless(HAS_DECOMPILER and file_exists(TEST_DEX), "decompiler or Test.dex missing")
class CoreDecompilerTest(unittest.TestCase):
    def setUp(self):
        self.raw = TEST_DEX.read_bytes()

    def test_names_and_slice(self):
        self.assertEqual(core_dec.to_dalvik("com.foo.Bar"), "Lcom/foo/Bar;")
        self.assertEqual(core_dec.to_dalvik("Lcom/foo/Bar;"), "Lcom/foo/Bar;")
        sliced = core_dec.slice_class(self.raw, "Test")
        self.assertTrue(sliced.startswith(b"dex\n"))
        self.assertTrue(core_dex.is_dex(sliced))
        java = core_dec.decompile_method(self.raw, "Test", "aTestMethod")
        self.assertIn("aTestMethod", java)

    def test_analysis_helpers(self):
        findings = core_dec.scan_vulns(self.raw)
        self.assertIsInstance(findings, list)
        report = json.loads(core_dec.export_json(self.raw))
        self.assertIn("classes", report)
        taint = json.loads(
            core_dec.taint_solve(self.raw, max_iterations=1)
        )
        self.assertIsInstance(taint, (dict, list))
        emu = core_dec.emulate_method(
            self.raw, "Test", "aTestMethod", max_steps=16
        )
        self.assertIn("registers", emu)
        rows, nodes, edges = core_dec.method_cfg(
            self.raw, "Test", "aTestMethod"
        )
        self.assertGreater(len(rows), 0)
        self.assertGreater(len(nodes), 0)
        self.assertIsInstance(edges, list)

    def test_bad_kind_and_missing_method(self):
        with self.assertRaises(ValueError):
            core_dec.findrefs(self.raw, "nope", "x")
        with self.assertRaises(ValueError):
            core_dec.decompile_method(self.raw, "Test", "noSuchMethod")

    def test_apk_string_xref(self):
        if not file_exists(TEST_APK):
            self.skipTest("apk missing")
        sites = core_dec.findrefs(
            read_apk_bytes(TEST_APK), "string", "this is a test"
        )
        self.assertGreaterEqual(len(sites), 1)
        self.assertEqual(sites[0]["kind"], "string")
        app = Application(TEST_APK)
        self.assertGreaterEqual(
            len(app.findrefs("string", "this is a test")), 1
        )
        with self.assertRaises(ValueError):
            app.decompile_method_selector("missing.Class#nope")
        with self.assertRaises(ValueError):
            app.emulate("missing.Class", "nope")


@unittest.skipUnless(HAS_ARM, "arm bindings not installed")
class CoreArmTest(unittest.TestCase):
    def test_disasm_and_decompile(self):
        word = core_arm.decode_one(0xD503201F)
        self.assertEqual(word["mnemonic"], "nop")
        via_bytes = core_arm.decode_bytes(bytes.fromhex("1f2003d5"), 0x1000)
        self.assertEqual(via_bytes["mnemonic"], "nop")
        self.assertEqual(via_bytes["vaddr"], 0x1000)
        code = bytes.fromhex("1f2003d5c0035fd6")
        insns = core_arm.disassemble(code, base_vaddr=0x4000)
        self.assertEqual(len(insns), 2)
        self.assertEqual(insns[0]["vaddr"], 0x4000)
        out = core_arm.decompile(code, name="entry", symbols={0: "entry"})
        self.assertIn("source", out)
        self.assertEqual(out["name"], "entry")
        self.assertGreater(out["end_vaddr"], out["start_vaddr"])

    def test_short_buffer(self):
        with self.assertRaises(ValueError):
            core_arm.decode_bytes(b"\x00\x01")


@unittest.skipUnless(HAS_PATCH and file_exists(TEST_APK), "apk-patch or apk missing")
class CorePatchTest(unittest.TestCase):
    def test_decode_file_and_build(self):
        project = core_patch.decode_file(
            TEST_APK, only_manifest=True, no_res=True
        )
        self.assertEqual(project["project_root"], "project")
        self.assertGreater(project["entry_count"], 0)
        rebuilt = core_patch.build(
            project["files"],
            project_root=project["project_root"],
            sign=False,
        )
        self.assertEqual(rebuilt[:2], b"PK")
        app = Application(TEST_APK)
        again = app.rebuild(sign=False, only_manifest=True, no_res=True)
        self.assertEqual(again[:2], b"PK")

    def test_rejects_garbage(self):
        with self.assertRaises(Exception):
            core_patch.decode(b"this is not an apk")
        with self.assertRaises(Exception):
            core_patch.inject_goauld(b"not-apk", b"\x00" * 16)


class OptionalMissingTest(unittest.TestCase):
    @unittest.skipIf(HAS_BYTECODE, "dex-bytecode is installed")
    def test_bytecode_missing(self):
        with self.assertRaises(core_bc.BytecodeNotAvailable):
            core_bc.encode_nop()

    @unittest.skipIf(HAS_DECOMPILER, "dex-decompiler is installed")
    def test_decompiler_missing(self):
        with self.assertRaises(core_dec.DecompilerNotAvailable):
            core_dec.to_dalvik("com.foo.Bar")

    @unittest.skipIf(HAS_ARM, "arm bindings are installed")
    def test_arm_missing(self):
        with self.assertRaises(core_arm.ArmDisasmNotAvailable):
            core_arm.decode_one(0)
        with self.assertRaises(core_arm.ArmDecompilerNotAvailable):
            core_arm.decompile(b"\x00" * 4)

    @unittest.skipIf(HAS_PATCH, "apk-patch is installed")
    def test_patch_missing(self):
        with self.assertRaises(core_patch.PatchNotAvailable):
            core_patch.decode(b"PK")


if __name__ == "__main__":
    unittest.main()
