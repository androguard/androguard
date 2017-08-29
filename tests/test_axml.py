import unittest

import sys
from lxml import etree

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


class AXMLTest(unittest.TestCase):
    def testAXML(self):
        filenames = [
            "examples/axml/AndroidManifest-Chinese.xml",
            "examples/axml/AndroidManifest-xmlns.xml",
            "examples/axml/AndroidManifest.xml", "examples/axml/test.xml",
            "examples/axml/test1.xml", "examples/axml/test2.xml",
            "examples/axml/test3.xml"
        ]

        for filename in filenames:
            with open(filename, "rb") as fd:
                ap = apk.AXMLPrinter(fd.read())
                self.assertIsNotNone(ap)

    def testNonZeroStyleOffset(self):
        """
        Test if a nonzero style offset in the string section causes problems
        if the counter is 0
        """
        filename = "examples/axml/AndroidManifestNonZeroStyle.xml"

        ap = apk.AXMLPrinter(open(filename, "rb").read())
        self.assertIsInstance(ap, apk.AXMLPrinter)

        # Try to load in etree
        e = etree.fromstring(ap.get_buff())
        self.assertIsNotNone(e)

    def testExtraNamespace(self):
        """
        Test if extra namespaces cause problems
        """
        filename = "examples/axml/AndroidManifestExtraNamespace.xml"

        ap = apk.AXMLPrinter(open(filename, "rb").read())
        self.assertIsInstance(ap, apk.AXMLPrinter)

        # Try to load in etree
        e = etree.fromstring(ap.get_buff())
        self.assertIsNotNone(e)

    def testExtraNamespace(self):
        """
        Assert that files with a broken filesize are not parsed
        """
        filename = "examples/axml/AndroidManifestWrongFilesize.xml"

        with self.assertRaises(AssertionError) as cnx:
            apk.AXMLPrinter(open(filename, "rb").read())
        self.assertTrue("Declared filesize does not match" in str(cnx.exception))


if __name__ == '__main__':
    unittest.main()
