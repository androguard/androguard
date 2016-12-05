import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis


class AnalysisTest(unittest.TestCase):

    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "r") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.newVMAnalysis(d)
            self.assertTrue(dx)


if __name__ == '__main__':
    unittest.main()
