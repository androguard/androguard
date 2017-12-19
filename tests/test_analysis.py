import unittest

import sys

from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis
from androguard.misc import AnalyzeAPK


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

        self.assertEqual(len(dx.get_classes()), 1745)
        self.assertEqual(len(dx.get_strings()), 1564)
        self.assertEqual(len(list(dx.get_methods())), 11694)
        self.assertEqual(len(list(dx.get_fields())), 3033)
        self.assertEqual(len(list(dx.get_external_classes())), 392)

if __name__ == '__main__':
    unittest.main()
