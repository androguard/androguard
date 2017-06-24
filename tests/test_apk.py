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



if __name__ == '__main__':
    unittest.main()
