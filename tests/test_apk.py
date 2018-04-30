# -*- coding: utf-8 -*-

import unittest
import inspect
import os
import sys
import glob
import hashlib

# ensure that androguard is loaded from this source code
localmodule = os.path.realpath(
    os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), '..'))
if localmodule not in sys.path:
    sys.path.insert(0, localmodule)

from androguard.core.bytecodes import apk
print('loaded from', apk.__file__)


class APKTest(unittest.TestCase):
    def testAPK(self):
        for f in ["examples/android/TestsAndroguard/bin/TestActivity.apk"] \
            + glob.glob('examples/tests/*.apk'):
            with open(f, "rb") as fd:
                a = apk.APK(fd.read(), True)
                self.assertTrue(a)

    def testAPKWrapper(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        a, d, dx = AnalyzeAPK("examples/android/TestsAndroguard/bin/TestActivity.apk")

        self.assertIsInstance(a, APK)
        self.assertIsInstance(d[0], DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

        self.assertEqual(a.get_signature_name(), "META-INF/CERT.RSA")
        self.assertEqual(a.get_signature_names(), ["META-INF/CERT.RSA"])

        self.assertIsNotNone(a.get_certificate(a.get_signature_name()))

    def testAPKWrapperRaw(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        with open(
            "examples/android/TestsAndroguard/bin/TestActivity.apk", 'rb') \
                as file_obj:
            file_contents = file_obj.read()
        a, d, dx = AnalyzeAPK(file_contents, raw=True)
        self.assertIsInstance(a, APK)
        self.assertIsInstance(d[0], DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

        self.assertEqual(a.get_signature_name(), "META-INF/CERT.RSA")
        self.assertEqual(a.get_signature_names(), ["META-INF/CERT.RSA"])

        self.assertIsNotNone(a.get_certificate(a.get_signature_name()))

    def testMultiDexAPK(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        a, d, dx = AnalyzeAPK('examples/android/abcore/app-prod-debug.apk')
        self.assertIsInstance(a, APK)
        self.assertIsInstance(d[0], DalvikVMFormat)
        self.assertIsInstance(d[1], DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

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
        from hashlib import md5, sha1, sha256
        a = APK("examples/android/TestsAndroguard/bin/TestActivity.apk", skip_analysis=True)

        # this one is not signed v2, it is v1 only
        self.assertTrue(a.is_signed_v1())
        self.assertFalse(a.is_signed_v2())
        self.assertTrue(a.is_signed())
        self.assertEqual(a.get_certificates_der_v2(), [])
        self.assertEqual(a.get_certificates_v2(), [])

        self.assertEqual(a.get_signature_name(), "META-INF/CERT.RSA")
        self.assertEqual(a.get_signature_names(), ["META-INF/CERT.RSA"])

        cert = a.get_certificate(a.get_signature_name())
        cert_der = a.get_certificate_der(a.get_signature_name())

        # Keytool are the hashes collected by keytool -printcert -file CERT.RSA
        for h2, keytool in [(md5, "99:FF:FC:37:D3:64:87:DD:BA:AB:F1:7F:94:59:89:B5"),
                               (sha1, "1E:0B:E4:01:F9:34:60:E0:8D:89:A3:EF:6E:27:25:55:6B:E1:D1:6B"),
                               (sha256, "6F:5C:31:60:8F:1F:9E:28:5E:B6:34:3C:7C:8A:F0:7D:E8:1C:1F:B2:14:8B:53:49:BE:C9:06:44:41:44:57:6D")]:
            x = h2()
            x.update(cert_der)
            hash_hashlib = x.hexdigest()

            self.assertEqual(hash_hashlib.lower(), keytool.replace(":", "").lower())

    def testAPKv2Signature(self):
        from androguard.core.bytecodes.apk import APK

        a = APK("examples/signing/TestActivity_signed_both.apk")

        self.assertTrue(a.is_signed_v1())
        self.assertTrue(a.is_signed_v2())
        self.assertTrue(a.is_signed())

        # Signing name is maximal 8 chars...
        self.assertEqual(a.get_signature_name(), "META-INF/ANDROGUA.RSA")
        self.assertEqual(len(a.get_certificates_der_v2()), 1)
        # As we signed with the same certificate, both methods should return the
        # same content
        self.assertEqual(a.get_certificate_der(a.get_signature_name()),
                a.get_certificates_der_v2()[0])

        from asn1crypto import x509
        self.assertIsInstance(a.get_certificates_v2()[0], x509.Certificate)

        # Test if the certificate is also the same as on disk
        with open("examples/signing/certificate.der", "rb") as f:
            cert = f.read()
        cert_der_v1 = a.get_certificate_der(a.get_signature_name())
        cert_der_v2 = a.get_certificates_der_v2()[0]

        for fun in [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.sha512]:
            h1 = fun(cert).hexdigest()
            h2 = fun(cert_der_v1).hexdigest()
            h3 = fun(cert_der_v2).hexdigest()

            self.assertEqual(h1, h2)
            self.assertEqual(h1, h3)
            self.assertEqual(h2, h3)

    def testApksignAPKs(self):
        # These APKs are from the apksign testcases and cover
        # all different signature algorithms as well as some error cases
        from androguard.core.bytecodes.apk import APK
        import zipfile
        from asn1crypto import x509, pem
        import binascii
        root = "examples/signing/apksig"
        
        # Correct values generated with openssl:
        certfp = {
            "dsa-1024.x509.pem": "fee7c19ff9bfb4197b3727b9fd92d95406b1bd96db99ea642f5faac019a389d7",
            "dsa-2048.x509.pem": "97cce0bab292c2d5afb9de90e1810b41a5d25c006a10d10982896aa12ab35a9e",
            "dsa-3072.x509.pem": "966a4537058d24098ea213f12d4b24e37ff5a1d8f68deb8a753374881f23e474",
            "ec-p256.x509.pem": "6a8b96e278e58f62cfe3584022cec1d0527fcb85a9e5d2e1694eb0405be5b599",
            "ec-p384.x509.pem": "5e7777ada7ee7ce8f9c4d1b07094876e5604617b7988b4c5d5b764a23431afbe",
            "ec-p521.x509.pem": "69b50381d98bebcd27df6d7df8af8c8b38d0e51e9168a95ab992d1a9da6082da",
            "rsa-1024.x509.pem": "bc5e64eab1c4b5137c0fbc5ed05850b3a148d1c41775cffa4d96eea90bdd0eb8",
            "rsa-16384.x509.pem": "f3c6b37909f6df310652fbd7c55ec27d3079dcf695dc6e75e22ba7c4e1c95601",
            "rsa-2048.x509.pem": "fb5dbd3c669af9fc236c6991e6387b7f11ff0590997f22d0f5c74ff40e04fca8",
            "rsa-3072.x509.pem": "483934461229a780010bc07cd6eeb0b67025fc4fe255757abbf5c3f2ed249e89",
            "rsa-4096.x509.pem": "6a46158f87753395a807edcc7640ac99c9125f6b6e025bdbf461ff281e64e685",
            "rsa-8192.x509.pem": "060d0a24fea9b60d857225873f78838e081795f7ef2d1ea401262bbd75a58234",
        }

        will_not_validate_correctly = [
            "targetSandboxVersion-2.apk",
            "targetSandboxVersion-2.apk",
            "v1-only-with-cr-in-entry-name.apk",
            "v1-only-with-lf-in-entry-name.apk",
            "v1-only-with-nul-in-entry-name.apk",
            "v1-only-with-rsa-1024-cert-not-der2.apk",
            "v2-only-cert-and-public-key-mismatch.apk",
            "v2-only-with-dsa-sha256-1024-sig-does-not-verify.apk",
        ]

        # Collect possible hashes for certificates
        # Unfortunately, not all certificates are supplied...
        for apath in os.listdir(root):
            if apath in certfp:
                with open(os.path.join(root, apath), "rb") as fp:
                    cert = x509.Certificate.load(pem.unarmor(fp.read())[2])
                    h = cert.sha256_fingerprint.replace(" ","").lower()
                    self.assertEqual(h, certfp[apath])
                    self.assertIn(h, certfp.values())

        for apath in os.listdir(root):
            if apath.endswith(".apk"):
                if apath == "v2-only-garbage-between-cd-and-eocd.apk" or \
                   apath == "v2-only-truncated-cd.apk":
                    # Can not load as APK
                    if sys.version_info.major == 2:
                        # Different name in python2...
                        with self.assertRaises(zipfile.BadZipfile):
                            APK(os.path.join(root, apath))
                    else:
                        with self.assertRaises(zipfile.BadZipFile):
                            APK(os.path.join(root, apath))
                    continue
                elif apath in will_not_validate_correctly:
                    # These APKs are faulty (by design) and will return a not correct fingerprint.
                    # TODO: we need to check if we can prevent such errors...
                    continue

                a = APK(os.path.join(root, apath))

                self.assertIsInstance(a, APK)

                # Special error cases
                if apath == "v2-only-apk-sig-block-size-mismatch.apk":
                    with self.assertRaises(AssertionError):
                        a.is_signed_v2()
                    continue
                elif apath == "v2-only-empty.apk":
                    with self.assertRaises(AssertionError):
                        a.is_signed_v2()
                    continue

                if a.is_signed_v1():
                    if apath == "weird-compression-method.apk":
                        with self.assertRaises(NotImplementedError):
                            for c in a.get_signature_names():
                                a.get_certificate(c)

                    elif apath == "v1-only-with-rsa-1024-cert-not-der.apk":
                        for sig in a.get_signature_names():
                            c = a.get_certificate(sig)
                            h = c.sha256_fingerprint.replace(" ","").lower()
                            self.assertNotIn(h, certfp.values())
                            # print([apath, h]) # I do not know, why put this file?
                            der = a.get_certificate_der(sig)
                            apk.show_Certificate(c, True)
                            apk.show_Certificate(c, False)
                            self.assertEqual(hashlib.sha256(der).hexdigest(), h)
                        pass
                    else:
                        for sig in a.get_signature_names():
                            c = a.get_certificate(sig)
                            h = c.sha256_fingerprint.replace(" ","").lower()
                            self.assertIn(h, certfp.values())

                            # Check that we get the same signature if we take the DER
                            der = a.get_certificate_der(sig)
                            self.assertEqual(hashlib.sha256(der).hexdigest(), h)

                if a.is_signed_v2():
                    if apath == "weird-compression-method.apk":
                        with self.assertRaises(NotImplementedError):
                            a.get_certificates_der_v2()
                    elif apath == "v2-only-with-rsa-pkcs1-sha256-1024-cert-not-der.apk":
                        # FIXME
                        # Not sure what this one should do... but the certificate fingerprint is weird
                        # as the hash over the DER is not the same when using the certificate
                        continue
                    else:
                        for c in a.get_certificates_der_v2():
                            cert = x509.Certificate.load(c)
                            h = cert.sha256_fingerprint.replace(" ","").lower()
                            self.assertIn(h, certfp.values())
                            # Check that we get the same signature if we take the DER
                            self.assertEqual(hashlib.sha256(c).hexdigest(), h)

    def testAPKWrapperUnsigned(self):
        from androguard.misc import AnalyzeAPK
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        a, d, dx = AnalyzeAPK("examples/android/TestsAndroguard/bin/TestActivity_unsigned.apk")

        self.assertIsInstance(a, APK)
        self.assertIsInstance(d[0], DalvikVMFormat)
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

    def testEffectiveTargetSdkVersion(self):
        from androguard.core.bytecodes.apk import APK

        a = APK('examples/android/abcore/app-prod-debug.apk')
        self.assertEqual(27, a.get_effective_target_sdk_version())

        a = APK('examples/android/Invalid/Invalid.apk')
        self.assertEqual(15, a.get_effective_target_sdk_version())

        a = APK('examples/android/TC/bin/TC-debug.apk')
        self.assertEqual(1, a.get_effective_target_sdk_version())

        a = APK('examples/android/TCDiff/bin/TCDiff-debug.apk')
        self.assertEqual(1, a.get_effective_target_sdk_version())

        a = APK('examples/android/TestsAndroguard/bin/TestActivity.apk')
        self.assertEqual(16, a.get_effective_target_sdk_version())

        a = APK('examples/android/TestsAndroguard/bin/TestActivity_unsigned.apk')
        self.assertEqual(16, a.get_effective_target_sdk_version())

        a = APK('examples/dalvik/test/bin/Test-debug.apk')
        self.assertEqual(1, a.get_effective_target_sdk_version())

        a = APK('examples/dalvik/test/bin/Test-debug-unaligned.apk')
        self.assertEqual(1, a.get_effective_target_sdk_version())

        a = APK('examples/tests/a2dp.Vol_137.apk')
        self.assertEqual(25, a.get_effective_target_sdk_version())

        a = APK('examples/tests/hello-world.apk')
        self.assertEqual(25, a.get_effective_target_sdk_version())

        a = APK('examples/tests/duplicate.permisssions_9999999.apk')
        self.assertEqual(27, a.get_effective_target_sdk_version())

        a = APK('examples/tests/com.politedroid_4.apk')
        self.assertEqual(3, a.get_effective_target_sdk_version())

    def testUsesImpliedPermissions(self):
        from androguard.core.bytecodes.apk import APK

        a = APK('examples/android/abcore/app-prod-debug.apk')
        self.assertEqual([['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/android/Invalid/Invalid.apk')
        self.assertEqual([],
                         a.get_uses_implied_permission_list())
        a = APK('examples/android/TC/bin/TC-debug.apk')
        self.assertEqual([['android.permission.WRITE_EXTERNAL_STORAGE', None],
                          ['android.permission.READ_PHONE_STATE', None],
                          ['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/android/TCDiff/bin/TCDiff-debug.apk')
        self.assertEqual([['android.permission.WRITE_EXTERNAL_STORAGE', None],
                          ['android.permission.READ_PHONE_STATE', None],
                          ['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/android/TestsAndroguard/bin/TestActivity.apk')
        self.assertEqual([],
                         a.get_uses_implied_permission_list())
        a = APK('examples/android/TestsAndroguard/bin/TestActivity_unsigned.apk')
        self.assertEqual([],
                         a.get_uses_implied_permission_list())
        a = APK('examples/dalvik/test/bin/Test-debug.apk')
        self.assertEqual([['android.permission.WRITE_EXTERNAL_STORAGE', None],
                          ['android.permission.READ_PHONE_STATE', None],
                          ['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/dalvik/test/bin/Test-debug-unaligned.apk')
        self.assertEqual([['android.permission.WRITE_EXTERNAL_STORAGE', None],
                          ['android.permission.READ_PHONE_STATE', None],
                          ['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/tests/a2dp.Vol_137.apk')
        self.assertEqual([['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/tests/com.politedroid_4.apk')
        self.assertEqual([['android.permission.WRITE_EXTERNAL_STORAGE', None],
                          ['android.permission.READ_PHONE_STATE', None],
                          ['android.permission.READ_EXTERNAL_STORAGE', None],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/tests/duplicate.permisssions_9999999.apk')
        self.assertEqual([['android.permission.READ_EXTERNAL_STORAGE', 18],],
                         a.get_uses_implied_permission_list())
        a = APK('examples/tests/hello-world.apk')
        self.assertEqual([],
                         a.get_uses_implied_permission_list())
        a = APK('examples/tests/urzip-πÇÇπÇÇ现代汉语通用字-български-عربي1234.apk')
        self.assertEqual([],
                         a.get_uses_implied_permission_list())

    def testNewZipWithoutModification(self):
        from androguard.core.bytecodes.apk import APK
        try:
            from unittest.mock import patch, MagicMock
        except:
            from mock import patch, MagicMock
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)
        with patch('zipfile.ZipFile') as zipFile:
            mockZip = MagicMock()
            zipFile.return_value=mockZip
            a.new_zip("testout.apk")
            self.assertTrue(mockZip.writestr.call_count == 48)
            self.assertTrue(mockZip.close.called)

    def testNewZipWithDeletedFile(self):
        from androguard.core.bytecodes.apk import APK
        try:
            from unittest.mock import patch, MagicMock
        except:
            from mock import patch, MagicMock
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)
        with patch('zipfile.ZipFile') as zipFile:
            mockZip = MagicMock()
            zipFile.return_value=mockZip
            a.new_zip("testout.apk", deleted_files="res/menu/menu.xml")
            self.assertTrue(mockZip.writestr.call_count == 47)
            self.assertTrue(mockZip.close.called)

    def testNewZipWithNewFile(self):
        from androguard.core.bytecodes.apk import APK
        try:
            from unittest.mock import patch, MagicMock
        except:
            from mock import patch, MagicMock
        a = APK("examples/tests/a2dp.Vol_137.apk", testzip=True)
        with patch('zipfile.ZipFile') as zipFile:
            mockZip = MagicMock()
            zipFile.return_value=mockZip
            a.new_zip("testout.apk", new_files={'res/menu/menu.xml': 'content'})
            self.assertTrue(mockZip.writestr.call_count == 48)
            self.assertTrue(mockZip.close.called)

    def testFeatures(self):
        from androguard.core.bytecodes.apk import APK

        # First Demo App
        a = APK("examples/tests/com.example.android.tvleanback.apk")
        self.assertListEqual(list(a.get_features()), ["android.hardware.microphone",
                                                      "android.hardware.touchscreen",
                                                      "android.software.leanback"])
        self.assertTrue(a.is_androidtv())
        self.assertFalse(a.is_wearable())
        self.assertTrue(a.is_leanback())

        # Second Demo App
        a = APK("examples/tests/com.example.android.wearable.wear.weardrawers.apk")
        self.assertListEqual(list(a.get_features()), ["android.hardware.type.watch"])
        self.assertTrue(a.is_wearable())
        self.assertFalse(a.is_leanback())
        self.assertFalse(a.is_androidtv())
        self.assertListEqual(list(a.get_libraries()), ["com.google.android.wearable"])

    def testAdaptiveIcon(self):
        # See https://developer.android.com/guide/practices/ui_guidelines/icon_design_adaptive.html
        from androguard.core.bytecodes.apk import APK
        from androguard.core.bytecodes.axml import AXMLPrinter

        a = APK("examples/tests/com.android.example.text.styling.apk")

        self.assertEqual(a.get_app_icon(), "res/mipmap-anydpi-v26/ic_launcher.xml")
        x = AXMLPrinter(a.get_file(a.get_app_icon())).get_xml().decode("UTF-8")
        self.assertIn("adaptive-icon", x)

        # * ldpi (low) ~120dpi
        # * mdpi (medium) ~160dpi
        # * hdpi (high) ~240dpi
        # * xhdpi (extra-high) ~320dpi
        # * xxhdpi (extra-extra-high) ~480dpi
        # * xxxhdpi (extra-extra-extra-high) ~640dpi
        self.assertIsNone(a.get_app_icon(max_dpi=120))  # No LDPI icon
        self.assertIn("mdpi", a.get_app_icon(max_dpi=160))
        self.assertIn("hdpi", a.get_app_icon(max_dpi=240))
        self.assertIn("xhdpi", a.get_app_icon(max_dpi=320))
        self.assertIn("xxhdpi", a.get_app_icon(max_dpi=480))
        self.assertIn("xxxhdpi", a.get_app_icon(max_dpi=640))

        self.assertIn(".png", a.get_app_icon(max_dpi=65533))
        self.assertIn(".xml", a.get_app_icon(max_dpi=65534))

if __name__ == '__main__':
    unittest.main(failfast=True)
