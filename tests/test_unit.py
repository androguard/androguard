# -*- coding: utf-8 -*-
"""Unit tests (no APK fixtures required)."""

from __future__ import annotations

import tempfile
import unittest

from androguard.core.decompiler import (
    DecompilerNotAvailable,
    descriptor_to_java,
    ensure_loaded,
    java_class_from_method,
    parse_method_selector,
)
from androguard.misc import AnalyzeDex, clean_file_name

from tests.helpers import HAS_DECOMPILER, TEST_DEX, file_exists


class DescriptorTest(unittest.TestCase):
    def test_descriptor_to_java(self):
        self.assertEqual(
            descriptor_to_java("Ltests/androguard/TestActivity;"),
            "tests.androguard.TestActivity",
        )
        self.assertEqual(
            descriptor_to_java("Ljava/lang/String;"),
            "java.lang.String",
        )

    def test_java_class_from_method(self):
        self.assertEqual(
            java_class_from_method("Lcom/foo/Bar;"),
            "com.foo.Bar",
        )
        self.assertEqual(
            java_class_from_method("com.foo.Bar"),
            "com.foo.Bar",
        )


class ParseMethodSelectorTest(unittest.TestCase):
    def test_valid_selector(self):
        cls, meth = parse_method_selector("com.example.Main#onCreate")
        self.assertEqual(cls, "com.example.Main")
        self.assertEqual(meth, "onCreate")

    def test_selector_strips_whitespace(self):
        cls, meth = parse_method_selector("  com.Foo # bar  ")
        self.assertEqual(cls, "com.Foo")
        self.assertEqual(meth, "bar")

    def test_invalid_selector_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_method_selector("no-hash-here")
        self.assertIn("CLASS#METHOD", str(ctx.exception))


class CleanFileNameTest(unittest.TestCase):
    def test_sanitize_and_truncate(self):
        self.assertEqual(
            "foobarfoo_", clean_file_name("foobarfoo ", unique=False)
        )
        self.assertEqual(
            "foobarsdf.", clean_file_name("foobarsdf.", unique=False)
        )
        self.assertEqual("_init_", clean_file_name("<init>", unique=False))
        self.assertEqual("a" * 230, clean_file_name("a" * 999, unique=False))

    def test_unique_prefix(self):
        result = clean_file_name("my_export", unique=True)
        self.assertNotEqual(result, "my_export")
        self.assertTrue(result.startswith("my_export"))


@unittest.skipUnless(HAS_DECOMPILER, "dex-decompiler not installed")
class DecompilerModuleTest(unittest.TestCase):
    def test_ensure_loaded(self):
        mod = ensure_loaded()
        self.assertTrue(hasattr(mod, "parse_dex"))

    def test_parse_dex_class_names(self):
        if not file_exists(TEST_DEX):
            self.skipTest("Test.dex not present")
        from androguard.core.decompiler import parse_dex

        dex = parse_dex(TEST_DEX.read_bytes())
        names = dex.class_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)


class DecompilerNotAvailableTest(unittest.TestCase):
    @unittest.skipIf(HAS_DECOMPILER, "dex-decompiler is installed")
    def test_ensure_loaded_raises(self):
        with self.assertRaises(DecompilerNotAvailable):
            ensure_loaded()


@unittest.skipUnless(file_exists(TEST_DEX), "Test.dex not present")
class AnalyzeDexTest(unittest.TestCase):
    def test_analyze_dex_path(self):
        dh = AnalyzeDex(str(TEST_DEX))
        classes = list(dh.get_classes())
        methods = list(dh.get_methods())
        self.assertEqual(len(classes), 1)
        self.assertEqual(len(methods), 2)

    def test_analyze_dex_bytes(self):
        dh = AnalyzeDex(TEST_DEX.read_bytes())
        self.assertGreater(len(list(dh.get_strings())), 0)


if __name__ == "__main__":
    unittest.main()
