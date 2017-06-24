import unittest

from androguard.misc import AnalyzeDex
import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)


class DecompilerTest(unittest.TestCase):
    def testSimplification(self):
        h, d, dx = AnalyzeDex("examples/tests/Test.dex")

        z, = d.get_classes()

        self.assertIn("return ((23 - p3) | ((p3 + 66) & 26));", z.get_source())

    def testArrays(self):
        h, d, dx = AnalyzeDex("examples/tests/FillArrays.dex")

        z, = d.get_classes()

        self.assertIn("{20, 30, 40, 50};", z.get_source())
        self.assertIn("{1, 2, 3, 4, 5, 999, 10324234};", z.get_source())
        self.assertIn("{97, 98, 120, 122, 99};", z.get_source())
        self.assertIn("{5, 10, 15, 20};", z.get_source())
        # Failed version of char array
        self.assertNotIn("{97, 0, 98, 0, 120};", z.get_source())
        # Failed version of short array
        self.assertNotIn("{5, 0, 10, 0};", z.get_source())

if __name__ == '__main__':
    unittest.main()
