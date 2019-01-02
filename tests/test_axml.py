import unittest

import sys
from xml.dom import minidom

from androguard.core.bytecodes import axml

def is_valid_manifest(tree):
    # We can not really check much more...
    print(tree.tag, tree.attrib)
    if tree.tag == "manifest" and "package" in tree.attrib:
        return True
    return False


class AXMLTest(unittest.TestCase):
    def testAndroidManifest(self):
        filenames = [
            "examples/axml/AndroidManifest-Chinese.xml",
            "examples/axml/AndroidManifestDoubleNamespace.xml",
            "examples/axml/AndroidManifestExtraNamespace.xml",
            "examples/axml/AndroidManifest_InvalidCharsInAttribute.xml",
            "examples/axml/AndroidManifestLiapp.xml",
            "examples/axml/AndroidManifestMaskingNamespace.xml",
            "examples/axml/AndroidManifest_NamespaceInAttributeName.xml",
            "examples/axml/AndroidManifestNonZeroStyle.xml",
            "examples/axml/AndroidManifestNullbytes.xml",
            "examples/axml/AndroidManifestTextChunksXML.xml",
            "examples/axml/AndroidManifestUTF8Strings.xml",
            "examples/axml/AndroidManifestWithComment.xml",
            "examples/axml/AndroidManifest_WrongChunkStart.xml",
            "examples/axml/AndroidManifest-xmlns.xml",
        ]

        for filename in filenames:
            with open(filename, "rb") as fd:
                ap = axml.AXMLPrinter(fd.read())
                self.assertIsNotNone(ap)

                self.assertTrue(is_valid_manifest(ap.get_xml_obj()))

                e = minidom.parseString(ap.get_buff())
                self.assertIsNotNone(e)

    def testNonManifest(self):
        filenames = [
            "examples/axml/test.xml",
            "examples/axml/test1.xml",
            "examples/axml/test2.xml",
            "examples/axml/test3.xml",
        ]

        for filename in filenames:
            with open(filename, "rb") as fp:
                ap = axml.AXMLPrinter(fp.read())

            self.assertEqual(ap.get_xml_obj().tag, "LinearLayout")

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

    def testNonTerminatedString(self):
        """
        Test if non-null terminated strings are detected.
        This sample even segfaults aapt...
        """
        filename = "examples/axml/AndroidManifest_StringNotTerminated.xml"

        with self.assertRaises(AssertionError) as cnx:
            with open(filename, "rb") as f:
                ap = axml.AXMLPrinter(f.read())
        self.assertTrue("not null terminated" in str(cnx.exception))

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
