import os
import unittest

from androguard.core import dex
from androguard.core.analysis import analysis

test_dir = os.path.dirname(os.path.abspath(__file__))


class RenameTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RenameTest, self).__init__(*args, **kwargs)
        with open(os.path.join(test_dir, 'data/APK/classes.dex'), "rb") as fd:
            self.d = dex.DEX(fd.read())
            self.dx = analysis.Analysis(self.d)
            # self.d.set_vmanalysis(self.dx)

    def testMethodRename(self):
        (meth,) = self.d.get_encoded_method("testDouble")
        clas = self.d.get_class(meth.get_class_name())
        self.assertEqual(meth.get_name(), "testDouble")
        self.assertIn(meth.get_name(), [i.name for i in clas.get_methods()])
        meth.set_name("blablaMyMethod")
        self.assertEqual(meth.get_name(), "blablaMyMethod")
        self.assertIn(meth.get_name(), [i.name for i in clas.get_methods()])
        self.assertNotIn("testDouble", [i.name for i in clas.get_methods()])

    def testFieldRename(self):
        (field,) = self.d.get_encoded_field("FLAG_REGISTER_CONTENT_OBSERVER")
        self.assertEqual(field.get_name(), "FLAG_REGISTER_CONTENT_OBSERVER")
        field.set_name("FLAG_REGISTER_CONTENT_OBSERVER_RENAMED")
        self.assertEqual(
            field.get_name(), "FLAG_REGISTER_CONTENT_OBSERVER_RENAMED"
        )

    def testClassRename(self):
        clazz = self.d.get_class("LTestDefaultPackage;")
        self.assertEqual(clazz.get_name(), "LTestDefaultPackage;")
        clazz.set_name("LMySuperDefaultPackage;")
        self.assertEqual(clazz.get_name(), "LMySuperDefaultPackage;")


if __name__ == '__main__':
    unittest.main()
