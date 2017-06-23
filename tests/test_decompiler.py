import unittest

from androguard.misc import AnalyzeDex
import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


class DecompilerTest(unittest.TestCase):
    def testSimplification(self):
        h, d, dx = AnalyzeDex("examples/tests/Test.dex")

        z, = d.get_classes()

        self.assertIn("return ((23 - p3) | ((p3 + 66) & 26));", z.get_source())

if __name__ == '__main__':
    unittest.main()
