import unittest

import sys
import re
import os
from androguard.misc import AnalyzeAPK
from androguard.decompiler.decompiler import DecompilerJADX


def which(program):
    """
    Thankfully copied from https://stackoverflow.com/a/377028/446140
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class DecompilerTest(unittest.TestCase):

    @unittest.skipIf(which("jadx") is None, "Skipping JADX test as jadx "
                                            "executable is not in path")
    def testJadx(self):
        a, d, dx = AnalyzeAPK("examples/tests/hello-world.apk")

        decomp = DecompilerJADX(d, dx)
        self.assertIsNotNone(decomp)

        d.set_decompiler(decomp)

        for c in d.get_classes():
            self.assertIsNotNone(c.get_source())

if __name__ == '__main__':
    unittest.main()

