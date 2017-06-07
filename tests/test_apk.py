import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


class APKTest(unittest.TestCase):

    def testAPK(self):
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            a = apk.APK(fd.read(), True)
            self.assertTrue(a)


if __name__ == '__main__':
    unittest.main()
