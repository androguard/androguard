# -*- coding: utf8- -*-
import unittest
import os

from androguard.misc import clean_file_name
import tempfile

class MiscTest(unittest.TestCase):
    def testCleanPath(self):
        self.assertEqual("foobarfoo_", clean_file_name("foobarfoo ", unique=False))
        self.assertEqual("foobarsdf_", clean_file_name("foobarsdf.", unique=False))
        self.assertEqual("_init_", clean_file_name("<init>", unique=False))
        if os.name == "nt":
            self.assertEqual("C:\\" + "a" * 230, clean_file_name("C:\\" + "a" * 999, unique=False, force_nt=True))
            self.assertEqual("C:\\" + "a" * 226 + ".foo", clean_file_name("C:\\" + "a" * 999 + ".foo", unique=False, force_nt=True))
        else:
            self.assertEqual("/some/path/" + "a" * 230, clean_file_name("/some/path/" + "a" * 999, unique=False, force_nt=True))
            self.assertEqual("/some/path/" + "a" * 226 + ".foo", clean_file_name("/some/path/" + "a" * 999 + ".foo", unique=False, force_nt=True))

        with tempfile.NamedTemporaryFile() as fp:
            self.assertEqual(fp.name + "_0", clean_file_name(fp.name, unique=True))


if __name__ == '__main__':
    unittest.main()
