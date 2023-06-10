import unittest

import sys
from androguard.core.apk import APK

from androguard import session


class SessionTest(unittest.TestCase):
    def testSessionDex(self):
        s = session.Session()
        s.add("examples/android/TestsAndroguard/bin/classes.dex")

        self.assertEqual(len(s.analyzed_apk), 0)
        self.assertEqual(len(s.analyzed_files), 1)
        self.assertEqual(len(s.analyzed_digest), 1)
        self.assertEqual(len(s.analyzed_vms), 1)
        self.assertEqual(len(s.analyzed_dex), 1)

    def testSessionDexIPython(self):
        """ Test if exporting ipython works"""
        s = session.Session(export_ipython=True)
        s.add("examples/android/TestsAndroguard/bin/classes.dex")

        self.assertEqual(len(s.analyzed_apk), 0)
        self.assertEqual(len(s.analyzed_files), 1)
        self.assertEqual(len(s.analyzed_digest), 1)
        self.assertEqual(len(s.analyzed_vms), 1)
        self.assertEqual(len(s.analyzed_dex), 1)

    def testSessionAPK(self):
        s = session.Session()
        s.add("examples/android/TestsAndroguard/bin/TestActivity.apk")

        self.assertEqual(len(s.analyzed_apk), 1)
        self.assertEqual(len(s.analyzed_files), 1)
        self.assertEqual(len(s.analyzed_files['examples/android/TestsAndroguard/bin/TestActivity.apk']), 2)
        self.assertEqual(len(s.analyzed_digest), 2)
        # Two VMs analyzed: one at the APK level, one at the dex level
        self.assertEqual(len(s.analyzed_vms), 2)
        self.assertEqual(len(s.analyzed_dex), 1)

    def testSessionAPKIP(self):
        """Test if exporting to ipython works with APKs"""
        s = session.Session(export_ipython=True)
        s.add("examples/android/TestsAndroguard/bin/TestActivity.apk")

        self.assertEqual(len(s.analyzed_apk), 1)
        self.assertEqual(len(s.analyzed_files), 1)
        self.assertEqual(len(s.analyzed_files['examples/android/TestsAndroguard/bin/TestActivity.apk']), 2)
        self.assertEqual(len(s.analyzed_digest), 2)
        # Two VMs analyzed: one at the APK level, one at the dex level
        self.assertEqual(len(s.analyzed_vms), 2)
        self.assertEqual(len(s.analyzed_dex), 1)

    def testSessionSave(self):
        s = session.Session()
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            s.add("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  fd.read())
            session.Save(s, "test_session")

    def testSessionLoad(self):
        s = session.Session()
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            s.add("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  fd.read())
            session.Save(s, "test_session")

        self.assertIn('2f24538b3064f1f88d3eb29ee7fbd2146779a4c9144aefa766d18965be8775c7', s.analyzed_dex.keys())
        self.assertIn('3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb', s.analyzed_apk.keys())
        x = s.analyzed_apk['3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb'][0]
        self.assertIsInstance(x, APK)

        nsession = session.Load("test_session")
        self.assertIn('2f24538b3064f1f88d3eb29ee7fbd2146779a4c9144aefa766d18965be8775c7', nsession.analyzed_dex.keys())
        self.assertIn('3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb', nsession.analyzed_apk.keys())
        y = nsession.analyzed_apk['3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb'][0]
        self.assertIsInstance(y, APK)

    def testSessionClassesDex(self):
        """Test if all classes.dex are added into the session"""
        from androguard.core.bytecodes.dvm import DEX
        from androguard.core.analysis.analysis import Analysis

        s = session.Session()

        # 0e1aa10d9ecfb1cb3781a3f885195f61505e0a4557026a07bd07bf5bd876c951
        x = s.add("examples/tests/Test.dex")
        self.assertEqual(x, "0e1aa10d9ecfb1cb3781a3f885195f61505e0a4557026a07bd07bf5bd876c951")
        self.assertIn('0e1aa10d9ecfb1cb3781a3f885195f61505e0a4557026a07bd07bf5bd876c951', s.analyzed_dex)

        dexfiles = list(s.get_objects_dex())

        self.assertEqual(len(dexfiles), 1)
        df = dexfiles[0]
        self.assertEqual(df[0], "0e1aa10d9ecfb1cb3781a3f885195f61505e0a4557026a07bd07bf5bd876c951")
        self.assertIsInstance(df[1], DEX)
        self.assertIsInstance(df[2], Analysis)
        self.assertIn(df[1], df[2].vms)

        x = s.add("examples/android/TestsAndroguard/bin/TestActivity.apk")
        self.assertEqual(x, '3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb')
        self.assertIn('2f24538b3064f1f88d3eb29ee7fbd2146779a4c9144aefa766d18965be8775c7', s.analyzed_dex)

        dexfiles = list(s.get_objects_dex())
        self.assertEqual(len(dexfiles), 2)
        self.assertEqual(sorted(['0e1aa10d9ecfb1cb3781a3f885195f61505e0a4557026a07bd07bf5bd876c951',
            '2f24538b3064f1f88d3eb29ee7fbd2146779a4c9144aefa766d18965be8775c7']),
            sorted(map(lambda x: x[0], dexfiles)))


if __name__ == '__main__':
    unittest.main()
