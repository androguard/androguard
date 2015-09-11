import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.analysis import auto
from androguard.core.androconf import set_debug

class DexTest(unittest.TestCase):
    def testDex(self):
        pass

    def testMultiDex(self):
        pass

if __name__ == '__main__':
    unittest.main()
