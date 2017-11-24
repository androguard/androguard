import unittest

import sys
from androguard.core.bytecodes.apk import APK

from androguard import session


class SessionTest(unittest.TestCase):
    def testSessionDex(self):
        s = session.Session()
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            s.add("examples/android/TestsAndroguard/bin/classes.dex", fd.read())
            self.assertEqual(len(s.analyzed_apk), 0)
            self.assertEqual(len(s.analyzed_files), 1)
            self.assertEqual(len(s.analyzed_digest), 1)
            self.assertEqual(len(s.analyzed_dex), 1)

    def testSessionAPK(self):
        s = session.Session()
        with open("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  "rb") as fd:
            s.add("examples/android/TestsAndroguard/bin/TestActivity.apk",
                  fd.read())
            self.assertEqual(len(s.analyzed_apk), 1)
            self.assertEqual(len(s.analyzed_files), 1)
            self.assertEqual(len(s.analyzed_digest), 2)
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


if __name__ == '__main__':
    unittest.main()
