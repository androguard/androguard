import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


class ARSCTest(unittest.TestCase):

    def testARSC(self):
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "r") as fd:
            a = apk.APK(fd.read(), True)
            arsc = a.get_android_resources()
            self.assertTrue(arsc)


if __name__ == '__main__':
    unittest.main()
