import unittest

from androguard.misc import AnalyzeDex
import sys
import re
from androguard.misc import AnalyzeAPK
from androguard.decompiler.dad.decompile import DvMethod, DvClass


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


def dvmethod(c, dx, doAST=False):
    for m in c.get_methods():
        mx = dx.get_method(m)
        ms = DvMethod(mx)
        ms.process(doAST=doAST)
        assert ms.get_source() is not None

def dvclass(c, dx):
    dc = DvClass(c, dx)
    dc.process()

    assert dc.get_source() is not None

def test_all_decompiler():
    # Generate test cases for this APK:
    a, d, dx = AnalyzeAPK("examples/tests/hello-world.apk")
    for c in d.get_classes():
        test_name = re.sub("[^a-zA-Z0-9_]", "_", c.get_name()[1:-1])
        # Test the decompilation of a single class
        yield dvclass, c, dx

        # Test the decompilation of all single methods in the class
        # if methods are in the class
        if len(c.get_methods()) == 0:
            continue

        yield dvmethod, c, dx, False
        # Disable tests for doAST=True for now...
        # yield dvmethod, c, dx, True

if __name__ == '__main__':
    unittest.main()
