import unittest
from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis
import sys

class RenameTest(unittest.TestCase):

    def testMethodRename(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.Analysis(d)
            d.set_vmanalysis(dx)

            meth, = d.get_method("testDouble")
            self.assertEqual(meth.get_name(), "testDouble")
            meth.set_name("blablaMyMethod")
            self.assertEqual(meth.get_name(), "blablaMyMethod")


if __name__ == '__main__':
    unittest.main()
