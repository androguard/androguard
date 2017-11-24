import unittest

import sys
from xml.dom import minidom

from androguard.core.bytecodes import axml


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
                ap = axml.AXMLPrinter(fd.read())
                self.assertIsNotNone(ap)

                e = minidom.parseString(ap.get_buff())
                self.assertIsNotNone(e)

    def testNonZeroStyleOffset(self):
        """
        Test if a nonzero style offset in the string section causes problems
        if the counter is 0
        """
        filename = "examples/axml/AndroidManifestNonZeroStyle.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testExtraNamespace(self):
        """
        Test if extra namespaces cause problems
        """
        filename = "examples/axml/AndroidManifestExtraNamespace.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testTextChunksWithXML(self):
        """
        Test for Text chunks containing XML
        """
        filename = "examples/axml/AndroidManifestTextChunksXML.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testWrongFilesize(self):
        """
        Assert that files with a broken filesize are not parsed
        """
        filename = "examples/axml/AndroidManifestWrongFilesize.xml"

        with self.assertRaises(AssertionError) as cnx:
            with open(filename, "rb") as f:
                axml.AXMLPrinter(f.read())
        self.assertTrue("Declared filesize does not match" in str(cnx.exception))

    def testNullbytes(self):
        """
        Assert that Strings with nullbytes are handled correctly
        """
        filename = "examples/axml/AndroidManifestNullbytes.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testMaskingNamespace(self):
        """
        Assert that Namespaces which are used in a tag and the tag is closed
        are actually correctly parsed.
        """
        filename = "examples/axml/AndroidManifestMaskingNamespace.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testDoubleNamespace(self):
        """
        Test if weird namespace constelations cause problems
        """
        filename = "examples/axml/AndroidManifestDoubleNamespace.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        e = minidom.parseString(ap.get_buff())
        self.assertIsNotNone(e)

    def testPackers(self):
        """
        Assert that Packed files are read
        """
        filename = "examples/axml/AndroidManifestLiapp.xml"

        with open(filename, "rb") as f:
            ap = axml.AXMLPrinter(f.read())
        self.assertIsInstance(ap, axml.AXMLPrinter)

        self.assertTrue(ap.is_packed())


if __name__ == '__main__':
    unittest.main()
