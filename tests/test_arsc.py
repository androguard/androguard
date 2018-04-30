import sys
import unittest

from androguard.core.bytecodes import apk, axml
from androguard.core.bytecodes.apk import APK
from operator import itemgetter

TEST_APP_NAME = "TestsAndroguardApplication"
TEST_ICONS = {
    120: "res/drawable-ldpi/icon.png",
    160: "res/drawable-mdpi/icon.png",
    240: "res/drawable-hdpi/icon.png",
    65536: "res/drawable-hdpi/icon.png"
}
TEST_CONFIGS = {
    "layout": [axml.ARSCResTableConfig.default_config()],
    "string": [axml.ARSCResTableConfig.default_config()],
    "drawable": [
        axml.ARSCResTableConfig(sdkVersion=4, density=120),
        axml.ARSCResTableConfig(sdkVersion=4, density=160),
        axml.ARSCResTableConfig(sdkVersion=4, density=240)
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
                print(config.get_config_name_friendly())
                self.assertIn(config, config_set,
                              "config %r was not expected" % config)
                config_set.remove(config)

            self.assertEqual(len(config_set), 0,
                             "configs were not found: %s" % config_set)

        unexpected_types = set(TEST_CONFIGS.keys()) - set(configs.keys())
        self.assertEqual(len(unexpected_types), 0,
                         "received unexpected resource types: %s" % unexpected_types)

    def testFallback(self):
        a = APK("examples/tests/com.teleca.jamendo_35.apk")

        # Should use the fallback
        self.assertEqual(a.get_app_name(), "Jamendo")
        res_parser = a.get_android_resources()

        res_id = int(a.get_element('application', 'label')[1:], 16)

        # Default Mode, no config
        self.assertEqual(len(res_parser.get_res_configs(res_id)), 2)
        # With default config, but fallback
        self.assertEqual(len(res_parser.get_res_configs(res_id, axml.ARSCResTableConfig.default_config())), 1)
        # With default config but no fallback
        self.assertEqual(len(res_parser.get_res_configs(res_id, axml.ARSCResTableConfig.default_config(), fallback=False)), 0)

        # Also test on resolver:
        self.assertListEqual(list(map(itemgetter(1), res_parser.get_resolved_res_configs(res_id))), ["Jamendo", "Jamendo"])
        self.assertListEqual(list(map(itemgetter(1), res_parser.get_resolved_res_configs(res_id, axml.ARSCResTableConfig.default_config()))), ["Jamendo"])

if __name__ == '__main__':
    unittest.main()
