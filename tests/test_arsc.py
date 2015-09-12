import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


TEST_APP_NAME = "TestsAndroguardApplication"
TEST_ICONS = {
    120: "res/drawable-ldpi/icon.png",
    160: "res/drawable-mdpi/icon.png",
    240: "res/drawable-hdpi/icon.png",
    65536: "res/drawable-hdpi/icon.png"
}


class ARSCTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk", "r") as fd:
            cls.apk = apk.APK(fd.read(), True)

    def testARSC(self):
        arsc = self.apk.get_android_resources()
        self.assertTrue(arsc)

    def testAppName(self):
        app_name = self.apk.get_app_name()
        self.assertEqual(app_name, TEST_APP_NAME, "Couldn't deduce application/activity label")

    def testAppIcon(self):
        for wanted_density, correct_path in TEST_ICONS.iteritems():
            app_icon_path = self.apk.get_app_icon(wanted_density)
            self.assertEqual(app_icon_path, correct_path, "Incorrect icon path for requested density")

if __name__ == '__main__':
    unittest.main()
