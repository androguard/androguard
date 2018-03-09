import unittest

import sys

from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis
from androguard.misc import AnalyzeAPK, AnalyzeDex


class AnalysisTest(unittest.TestCase):
    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.Analysis(d)
            self.assertTrue(dx)

    def testAPK(self):
        a, d, dx = AnalyzeAPK("examples/tests/a2dp.Vol_137.apk")

        dx.create_xref()

        self.assertEqual(len(list(dx.get_internal_classes())), 1353)  # checked by reading the dex header
        self.assertEqual(len(dx.get_strings()), 1564)
        self.assertEqual(len(list(dx.get_methods())), 11694)
        self.assertEqual(len(list(dx.get_fields())), 3033)
        self.assertEqual(len(list(dx.get_external_classes())), 394)

        # Filter all support libraries
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$"))), 516)
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$", no_external=True))), 124)

        # Find all constructors by method name
        self.assertEqual(len(list(dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor="^\(.+\).*$"))), 138)
        self.assertEqual(len(list(dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor="^\(.+\).*$", no_external=True))), 94)

        # Find url like strings
        self.assertEqual(len(list(dx.find_strings(".*:\/\/.*"))), 15)

        # find String fields
        self.assertEqual(len(list(dx.find_fields(classname="^(?!Landroid).*;$", fieldtype="Ljava\/lang\/String;"))), 63)

    def testAnalysis(self):
        h, d, dx = AnalyzeDex("examples/tests/AnalysisTest.dex")

        self.assertEqual(h, "4595fc25104f3fcd709163eb70ca476edf116753607ec18f09548968c71910dc")
        self.assertIsInstance(d, dvm.DalvikVMFormat)
        self.assertIsInstance(dx, analysis.Analysis)

        cls = ["Ljava/io/PrintStream;", "Ljava/lang/Object;",
                "Ljava/math/BigDecimal;", "Ljava/math/BigInteger;"]

        for c in cls:
            self.assertIn(c, map(lambda x: x.orig_class.get_name(),
                dx.get_external_classes()))



if __name__ == '__main__':
    unittest.main()
