import unittest

import sys

from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis


class AnalysisTest(unittest.TestCase):
    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.Analysis(d)
            self.assertTrue(dx)


if __name__ == '__main__':
    unittest.main()
