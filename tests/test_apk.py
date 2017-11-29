import unittest

import sys

from androguard.core.bytecodes import apk


class APKTest(unittest.TestCase):
    def testAPK(self):
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            a = apk.APK(fd.read(), True)
            self.assertTrue(a)

    def testAPKWrapper(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        a, d, dx = AnalyzeAPK("examples/android/TestsAndroguard/bin/TestActivity.apk")

        self.assertIsInstance(a, APK)
        self.assertIsInstance(d, DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

        self.assertEqual(a.get_signature_name(), "META-INF/CERT.RSA")
        self.assertEqual(a.get_signature_names(), ["META-INF/CERT.RSA"])

        self.assertIsNotNone(a.get_certificate(a.get_signature_name()))

    def testAPKCert(self):
        """
        Test if certificates are correctly unpacked from the SignatureBlock files
        :return:
        """
        from androguard.core.bytecodes.apk import APK
        import binascii
        a = APK("examples/android/TestsAndroguard/bin/TestActivity.apk", skip_analysis=True)

        cert = a.get_certificate_der(a.get_signature_name())
        expected = "308201E53082014EA00302010202045114FECF300D06092A864886F70D010105" \
                   "05003037310B30090603550406130255533110300E060355040A1307416E6472" \
                   "6F6964311630140603550403130D416E64726F6964204465627567301E170D31" \
                   "33303230383133333430375A170D3433303230313133333430375A3037310B30" \
                   "090603550406130255533110300E060355040A1307416E64726F696431163014" \
                   "0603550403130D416E64726F696420446562756730819F300D06092A864886F7" \
                   "0D010101050003818D00308189028181009903975EC93F0F3CCB54BD1A415ECF" \
                   "3505993715B8B9787F321104ACC7397D186F01201341BCC5771BB28695318E00" \
                   "6E47C888D3C7EE9D952FF04DF06EDAB1B511F51AACDCD02E0ECF5AA7EC6B51BA" \
                   "08C601074CF2DA579BD35054E4F77BAAAAF0AA67C33C1F1C3EEE05B5862952C0" \
                   "888D39179C0EDD785BA4F47FB7DF5D5F030203010001300D06092A864886F70D" \
                   "0101050500038181006B571D685D41E77744F5ED20822AE1A14199811CE649BB" \
                   "B29248EB2F3CC7FB70F184C2A3D17C4F86B884FCA57EEB289ECB5964A1DDBCBD" \
                   "FCFC60C6B7A33D189927845067C76ED29B42D7F2C7F6E2389A4BC009C01041A3" \
                   "6E666D76D1D66467416E68659D731DC7328CB4C2E989CF59BB6D2D2756FDE7F2" \
                   "B3FB733EBB4C00FD3B"

        self.assertEqual(binascii.hexlify(cert).decode("ascii").upper(), expected)

    def testAPKCertFingerprint(self):
        """
        Test if certificates are correctly unpacked from the SignatureBlock files
        Check if fingerprints matches
        :return:
        """
        from androguard.core.bytecodes.apk import APK
        import binascii
        from cryptography.hazmat.primitives import hashes
        from hashlib import md5, sha1, sha256
        a = APK("examples/android/TestsAndroguard/bin/TestActivity.apk", skip_analysis=True)

        self.assertEqual(a.get_signature_name(), "META-INF/CERT.RSA")

        cert = a.get_certificate(a.get_signature_name())
        cert_der = a.get_certificate_der(a.get_signature_name())

        # Keytool are the hashes collected by keytool -printcert -file CERT.RSA
        for h, h2, keytool in [(hashes.MD5, md5, "99:FF:FC:37:D3:64:87:DD:BA:AB:F1:7F:94:59:89:B5"),
                               (hashes.SHA1, sha1, "1E:0B:E4:01:F9:34:60:E0:8D:89:A3:EF:6E:27:25:55:6B:E1:D1:6B"),
                               (hashes.SHA256, sha256, "6F:5C:31:60:8F:1F:9E:28:5E:B6:34:3C:7C:8A:F0:7D:E8:1C:1F:B2:14:8B:53:49:BE:C9:06:44:41:44:57:6D")]:
            hash_x509 = binascii.hexlify(cert.fingerprint(h())).decode("ascii")
            x = h2()
            x.update(cert_der)
            hash_hashlib = x.hexdigest()

            self.assertEqual(hash_x509.lower(), hash_hashlib.lower())
            self.assertEqual(hash_x509.lower(), keytool.replace(":", "").lower())

    def testAPKWrapperUnsigned(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        a, d, dx = AnalyzeAPK("examples/android/TestsAndroguard/bin/TestActivity_unsigned.apk")

        self.assertIsInstance(a, APK)
        self.assertIsInstance(d, DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

        self.assertEqual(a.get_signature_name(), None)
        self.assertEqual(a.get_signature_names(), [])

    def testAPKManifest(self):
        from androguard.core.bytecodes.apk import APK
        a = APK("examples/android/TestsAndroguard/bin/TestActivity.apk", testzip=True)

        self.assertEqual(a.get_app_name(), "TestsAndroguardApplication")
        self.assertEqual(a.get_app_icon(), "res/drawable-hdpi/icon.png")
        self.assertEqual(a.get_app_icon(max_dpi=120), "res/drawable-ldpi/icon.png")
        self.assertEqual(a.get_app_icon(max_dpi=160), "res/drawable-mdpi/icon.png")
        self.assertEqual(a.get_app_icon(max_dpi=240), "res/drawable-hdpi/icon.png")
        self.assertIsNone(a.get_app_icon(max_dpi=1))
        self.assertEqual(a.get_main_activity(), "tests.androguard.TestActivity")
        self.assertEqual(a.get_package(), "tests.androguard")
        self.assertEqual(a.get_androidversion_code(), '1')
        self.assertEqual(a.get_androidversion_name(), "1.0")
        self.assertEqual(a.get_min_sdk_version(), "9")
        self.assertEqual(a.get_target_sdk_version(), "16")
        self.assertIsNone(a.get_max_sdk_version())
        self.assertEqual(a.get_permissions(), [])
        self.assertEqual(a.get_declared_permissions(), [])
        self.assertTrue(a.is_valid_APK())

    def testAPKPermissions(self):
        from androguard.core.bytecodes.apk import APK
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)

        self.assertEqual(a.get_package(), "a2dp.Vol")
        self.assertListEqual(sorted(a.get_permissions()), sorted(["android.permission.RECEIVE_BOOT_COMPLETED",
                                                                  "android.permission.CHANGE_WIFI_STATE",
                                                                  "android.permission.ACCESS_WIFI_STATE",
                                                                  "android.permission.KILL_BACKGROUND_PROCESSES",
                                                                  "android.permission.BLUETOOTH",
                                                                  "android.permission.BLUETOOTH_ADMIN",
                                                                  "com.android.launcher.permission.READ_SETTINGS",
                                                                  "android.permission.RECEIVE_SMS",
                                                                  "android.permission.MODIFY_AUDIO_SETTINGS",
                                                                  "android.permission.READ_CONTACTS",
                                                                  "android.permission.ACCESS_COARSE_LOCATION",
                                                                  "android.permission.ACCESS_FINE_LOCATION",
                                                                  "android.permission.ACCESS_LOCATION_EXTRA_COMMANDS",
                                                                  "android.permission.WRITE_EXTERNAL_STORAGE",
                                                                  "android.permission.READ_PHONE_STATE",
                                                                  "android.permission.BROADCAST_STICKY",
                                                                  "android.permission.GET_ACCOUNTS"]))

    def testAPKActivitiesAreString(self):
        from androguard.core.bytecodes.apk import APK
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)
        activities = a.get_activities()
        self.assertTrue(isinstance(activities[0], str), 'activities[0] is not of type str')

    def testAPKIntentFilters(self):
        from androguard.core.bytecodes.apk import APK
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)
        activities = a.get_activities()
        receivers = a.get_receivers()
        services = a.get_services()
        filter_list = []
        for i in activities:
            filters = a.get_intent_filters("activity", i)
            if len(filters) > 0:
                filter_list.append(filters)
        for i in receivers:
            filters = a.get_intent_filters("receiver", i)
            if len(filters) > 0:
                filter_list.append(filters)
        for i in services:
            filters = a.get_intent_filters("service", i)
            if len(filters) > 0:
                filter_list.append(filters)
        pairs = zip(filter_list, [{'action': ['android.intent.action.MAIN'], 'category': ['android.intent.category.LAUNCHER']},
                                                         {'action': ['android.service.notification.NotificationListenerService']},
                                                         {'action': ['android.intent.action.BOOT_COMPLETED', 'android.intent.action.MY_PACKAGE_REPLACED'], 'category': ['android.intent.category.HOME']},
                                                         {'action': ['android.appwidget.action.APPWIDGET_UPDATE']}])
        self.assertTrue(any(x != y for x, y in pairs))


if __name__ == '__main__':
    unittest.main()
