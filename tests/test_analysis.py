import unittest

import sys
from operator import itemgetter

from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis
from androguard.misc import AnalyzeAPK, AnalyzeDex


class AnalysisTest(unittest.TestCase):
    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.Analysis(d)
            self.assertIsInstance(dx, analysis.Analysis)

    def testAPK(self):
        a, d, dx = AnalyzeAPK("examples/tests/a2dp.Vol_137.apk")

        dx.create_xref()

        self.assertEqual(len(list(dx.get_internal_classes())), 1353)  # checked by reading the dex header
        self.assertEqual(len(dx.get_strings()), 1564)
        self.assertEqual(len(list(dx.get_methods())), 11694)
        self.assertEqual(len(list(dx.get_fields())), 3033)
        self.assertEqual(len(list(dx.get_external_classes())), 394)

        # Filter all support libraries
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$"))), 516)
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$", no_external=True))), 124)

        # Find all constructors by method name
        self.assertEqual(len(list(dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor=r"^\(.+\).*$"))), 138)
        self.assertEqual(len(list(dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor=r"^\(.+\).*$", no_external=True))), 94)

        # Find url like strings
        self.assertEqual(len(list(dx.find_strings(r".*:\/\/.*"))), 15)

        # find String fields
        self.assertEqual(len(list(dx.find_fields(classname="^(?!Landroid).*;$", fieldtype=r"Ljava\/lang\/String;"))), 63)

    def testAnalysis(self):
        h, d, dx = AnalyzeDex("examples/tests/AnalysisTest.dex")

        self.assertEqual(h, "4595fc25104f3fcd709163eb70ca476edf116753607ec18f09548968c71910dc")
        self.assertIsInstance(d, dvm.DalvikVMFormat)
        self.assertIsInstance(dx, analysis.Analysis)

        cls = ["Ljava/io/PrintStream;", "Ljava/lang/Object;",
                "Ljava/math/BigDecimal;", "Ljava/math/BigInteger;"]

        for c in cls:
            self.assertIn(c, map(lambda x: x.orig_class.get_name(),
                dx.get_external_classes()))


    def testMultidex(self):
        a, d, dx = AnalyzeAPK("examples/tests/multidex/multidex.apk")

        cls = list(map(lambda x: x.get_vm_class().get_name(), dx.get_classes()))
        self.assertIn('Lcom/foobar/foo/Foobar;', cls)
        self.assertIn('Lcom/blafoo/bar/Blafoo;', cls)


    def testMultiDexExternal(self):
        """
        Test if classes are noted as external if not both zips are opened
        """
        from zipfile import ZipFile

        with ZipFile("examples/tests/multidex/multidex.apk") as myzip:
            c1 = myzip.read("classes.dex")
            c2 = myzip.read("classes2.dex")

        d1 = dvm.DalvikVMFormat(c1)
        d2 = dvm.DalvikVMFormat(c2)

        dx = analysis.Analysis()

        dx.add(d1)

        # Both classes should be in the analysis, but only the fist is internal
        self.assertIn("Lcom/foobar/foo/Foobar;", dx.classes)
        self.assertFalse(dx.classes["Lcom/foobar/foo/Foobar;"].is_external())
        self.assertNotIn("Lcom/blafoo/bar/Blafoo;", dx.classes)

        dx = analysis.Analysis()
        dx.add(d2)
        self.assertIn("Lcom/blafoo/bar/Blafoo;", dx.classes)
        self.assertFalse(dx.classes["Lcom/blafoo/bar/Blafoo;"].is_external())
        self.assertNotIn("Lcom/foobar/foo/Foobar;", dx.classes)

        # Now we "see" the reference to Foobar
        dx.create_xref()
        self.assertIn("Lcom/foobar/foo/Foobar;", dx.classes)
        self.assertTrue(dx.classes["Lcom/foobar/foo/Foobar;"].is_external())

        dx = analysis.Analysis()
        dx.add(d1)
        dx.add(d2)

        self.assertIn("Lcom/blafoo/bar/Blafoo;", dx.classes)
        self.assertFalse(dx.classes["Lcom/blafoo/bar/Blafoo;"].is_external())
        self.assertIn("Lcom/foobar/foo/Foobar;", dx.classes)
        self.assertFalse(dx.classes["Lcom/foobar/foo/Foobar;"].is_external())


    def testInterfaces(self):
        h, d, dx = AnalyzeDex('examples/tests/InterfaceCls.dex')

        cls = dx.classes['LInterfaceCls;']
        self.assertIn('Ljavax/net/ssl/X509TrustManager;', cls.implements)
        self.assertEquals(cls.name, 'LInterfaceCls;')

    def testExtends(self):
        h, d, dx = AnalyzeDex('examples/tests/ExceptionHandling.dex')

        cls = dx.classes['LSomeException;']
        self.assertEquals(cls.extends, 'Ljava/lang/Exception;')
        self.assertEquals(cls.name, 'LSomeException;')
        self.assertFalse(cls.is_external())

        cls = dx.classes['Ljava/lang/Exception;']
        self.assertEquals(cls.extends, 'Ljava/lang/Object;')
        self.assertEquals(cls.name, 'Ljava/lang/Exception;')
        self.assertEquals(cls.implements, [])
        self.assertTrue(cls.is_external())

    def testXrefs(self):
        """Test if XREFs produce the correct results"""
        with open("examples/android/TestsAndroguard/bin/classes.dex", "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            dx = analysis.Analysis(d)

        dx.create_xref()

        testcls = dx.classes['Ltests/androguard/TestActivity;']
        self.assertIsInstance(testcls, analysis.ClassAnalysis)

        testmeth = list(filter(lambda x: x.name == 'onCreate', testcls.get_methods()))[0]

        self.assertEqual(len(list(dx.find_methods(testcls.name, '^onCreate$'))), 1)
        self.assertEqual(list(dx.find_methods(testcls.name, '^onCreate$'))[0], testmeth)

        self.assertIsInstance(testmeth, analysis.MethodClassAnalysis)
        self.assertFalse(testmeth.is_external())
        self.assertIsInstance(testmeth.method, dvm.EncodedMethod)
        self.assertEquals(testmeth.name, 'onCreate')

        xrefs = list(map(lambda x: x.full_name, map(itemgetter(1), sorted(testmeth.get_xref_to(), key=itemgetter(2)))))
        self.assertEqual(len(xrefs), 5)

        # First, super is called:
        self.assertEquals(xrefs.pop(0), 'Landroid/app/Activity; onCreate (Landroid/os/Bundle;)V')
        # then setContentView (which is in the current class but the method is external)
        self.assertEquals(xrefs.pop(0), 'Ltests/androguard/TestActivity; setContentView (I)V')
        # then getApplicationContext (inside the Toast)
        self.assertEquals(xrefs.pop(0), 'Ltests/androguard/TestActivity; getApplicationContext ()Landroid/content/Context;')
        # then Toast.makeText
        self.assertEquals(xrefs.pop(0), 'Landroid/widget/Toast; makeText (Landroid/content/Context; Ljava/lang/CharSequence; I)Landroid/widget/Toast;')
        # then show()
        self.assertEquals(xrefs.pop(0), 'Landroid/widget/Toast; show ()V')

        # Now, test if the reverse is true
        other = list(dx.find_methods('^Landroid/app/Activity;$', '^onCreate$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^setContentView$'))
        # External because not overwritten in class:
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^getApplicationContext$'))
        # External because not overwritten in class:
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Landroid/widget/Toast;$', '^makeText$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Landroid/widget/Toast;$', '^show$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        # Next test internal calls
        testmeth = list(filter(lambda x: x.name == 'testCalls', testcls.get_methods()))[0]

        self.assertEqual(len(list(dx.find_methods(testcls.name, '^testCalls$'))), 1)
        self.assertEqual(list(dx.find_methods(testcls.name, '^testCalls$'))[0], testmeth)

        self.assertIsInstance(testmeth, analysis.MethodClassAnalysis)
        self.assertFalse(testmeth.is_external())
        self.assertIsInstance(testmeth.method, dvm.EncodedMethod)
        self.assertEquals(testmeth.name, 'testCalls')

        xrefs = list(map(lambda x: x.full_name, map(itemgetter(1), sorted(testmeth.get_xref_to(), key=itemgetter(2)))))
        self.assertEqual(len(xrefs), 4)

        self.assertEquals(xrefs.pop(0), 'Ltests/androguard/TestActivity; testCall2 (J)V')
        self.assertEquals(xrefs.pop(0), 'Ltests/androguard/TestIfs; testIF (I)I')
        self.assertEquals(xrefs.pop(0), 'Ljava/lang/Object; getClass ()Ljava/lang/Class;')
        self.assertEquals(xrefs.pop(0), 'Ljava/io/PrintStream; println (Ljava/lang/Object;)V')

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^testCall2$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertFalse(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestIfs;$', '^testIF$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertFalse(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ljava/lang/Object;$', '^getClass$'))
        self.assertEquals(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodClassAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth.method, map(itemgetter(1), other[0].get_xref_from()))

        # Not testing println, as it has too many variants...


if __name__ == '__main__':
    unittest.main()
