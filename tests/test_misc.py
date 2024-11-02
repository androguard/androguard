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
            self.assertEqual("C:\\" + "a" * 230, clean_file_name("C:\\" + "a" * 999, unique=False))
            self.assertEqual("C:\\" + "a" * 226 + ".foo", clean_file_name("C:\\" + "a" * 999 + ".foo", unique=False))
        else:
            self.assertEqual("/some/path/" + "a" * 230, clean_file_name("/some/path/" + "a" * 999, unique=False))
            self.assertEqual("/some/path/" + "a" * 226 + ".foo", clean_file_name("/some/path/" + "a" * 999 + ".foo", unique=False))

        with tempfile.NamedTemporaryFile() as fp:
            self.assertEqual(fp.name + "_0", clean_file_name(fp.name, unique=True))

    def testClassNameFormatting(self):
        from androguard.core.bytecode import get_package_class_name

        self.assertEqual(get_package_class_name('Ljava/lang/Object;'), ('java.lang', 'Object'))
        self.assertEqual(get_package_class_name('[Ljava/lang/Object;'), ('java.lang', 'Object'))
        self.assertEqual(get_package_class_name('[[Ljava/lang/Object;'), ('java.lang', 'Object'))
        self.assertEqual(get_package_class_name('[[[[[[[[[[[[[[[[[[[[[[[Ljava/lang/Object;'), ('java.lang', 'Object'))
        self.assertEqual(get_package_class_name('[[[[[[[[[[[[[[[[[[[[[[[LObject;'), ('', 'Object'))
        self.assertEqual(get_package_class_name('LFoobar;'), ('', 'Foobar'))
        self.assertEqual(get_package_class_name('Lsdflkjdsklfjsdkjfklsdjfkljsdkflsd/shdfjksdhkjfhsdkjfsh;'),
                         ('sdflkjdsklfjsdkjfklsdjfkljsdkflsd', 'shdfjksdhkjfhsdkjfsh'))
        self.assertEqual(get_package_class_name('L;'), ('', ''))

        with self.assertRaises(ValueError):
            get_package_class_name('Foobar')

        with self.assertRaises(ValueError):
            get_package_class_name('java.lang.Object')

        with self.assertRaises(ValueError):
            get_package_class_name('LOLjava.lang.Object')

        with self.assertRaises(ValueError):
            get_package_class_name('[[LOLjava.lang.Object')

        with self.assertRaises(ValueError):
            get_package_class_name('java.lang.Object;')

        with self.assertRaises(ValueError):
            get_package_class_name('[java.lang.Object;')


if __name__ == '__main__':
    unittest.main()
