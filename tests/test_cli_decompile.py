import os
import shutil
import unittest

from androguard import session
from androguard.cli.main import export_apps_to_format

test_dir = os.path.dirname(os.path.abspath(__file__))


class TestCLIDecompile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_testactivity_apk_path = os.path.join(
            test_dir, 'data/APK/TestActivity.apk'
        )
        cls.s = session.Session()
        with open(test_testactivity_apk_path, "rb") as fd:
            cls.s.add(test_testactivity_apk_path, fd.read())

    def testDecompileDefaults(self):
        """test decompile command using default cli settings"""
        export_apps_to_format(
            None,
            self.s,
            os.path.join(test_dir, 'tmp_TestActivity_decompilation'),
            None,
            False,
            None,
            None,
        )

    @classmethod
    def tearDownClass(cls):
        decomp_dir = os.path.join(test_dir, 'tmp_TestActivity_decompilation')
        if os.path.exists(decomp_dir):
            shutil.rmtree(decomp_dir)


if __name__ == '__main__':
    unittest.main()
