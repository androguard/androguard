import unittest

import sys
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
                self.assertTrue(ap)


if __name__ == '__main__':
    unittest.main()
