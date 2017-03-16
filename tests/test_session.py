import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

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


if __name__ == '__main__':
    unittest.main()
