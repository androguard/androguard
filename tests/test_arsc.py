import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk
import collections


TEST_APP_NAME = "TestsAndroguardApplication"
TEST_ICONS = {
    120: "res/drawable-ldpi/icon.png",
    160: "res/drawable-mdpi/icon.png",
    240: "res/drawable-hdpi/icon.png",
    65536: "res/drawable-hdpi/icon.png"
}
TEST_CONFIGS = {
    "layout": [apk.ARSCResTableConfig.default_config()],
    "string": [apk.ARSCResTableConfig.default_config()],
    "drawable": [
        apk.ARSCResTableConfig(sdkVersion=4, density=120),
        apk.ARSCResTableConfig(sdkVersion=4, density=160),
        apk.ARSCResTableConfig(sdkVersion=4, density=240)
    ]
}


class ARSCTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            cls.apk = apk.APK(fd.read(), True)

    def testARSC(self):
        arsc = self.apk.get_android_resources()
        self.assertTrue(arsc)

    def testAppName(self):
        app_name = self.apk.get_app_name()
        self.assertEqual(app_name, TEST_APP_NAME, "Couldn't deduce application/activity label")

    def testAppIcon(self):
        for wanted_density, correct_path in TEST_ICONS.items():
            app_icon_path = self.apk.get_app_icon(wanted_density)
            self.assertEqual(app_icon_path, correct_path,
                             "Incorrect icon path for requested density")

    def testTypeConfigs(self):
        arsc = self.apk.get_android_resources()
        configs = arsc.get_type_configs(None)

        for res_type, test_configs in list(TEST_CONFIGS.items()):
            config_set = set(test_configs)
            self.assertIn(res_type, configs,
                          "resource type %s was not found" % res_type)
            for config in configs[res_type]:
                self.assertIn(config, config_set,
                              "config %r was not expected" % config)
                config_set.remove(config)

            self.assertEqual(len(config_set), 0,
                             "configs were not found: %s" % config_set)

        unexpected_types = set(TEST_CONFIGS.keys()) - set(configs.keys())
        self.assertEqual(len(unexpected_types), 0,
                         "received unexpected resource types: %s" % unexpected_types)


if __name__ == '__main__':
    unittest.main()
