import os
import unittest

from operator import itemgetter

from androguard.core.analysis import analysis
from androguard.core.dex import DEX, EncodedMethod, HiddenApiClassDataItem
from androguard.misc import AnalyzeAPK, AnalyzeDex
from androguard.util import set_log

test_dir = os.path.dirname(os.path.abspath(__file__))


class AnalysisTest(unittest.TestCase):
    def testDex(self):
        with open(os.path.join(test_dir, "data/APK/classes.dex"), "rb") as fd:
            d = DEX(fd.read())
            dx = analysis.Analysis(d)
            self.assertIsInstance(dx, analysis.Analysis)

    def testAPK(self):
        a, d, dx = AnalyzeAPK(os.path.join(test_dir, "data/APK/a2dp.Vol_137.apk"))

        self.assertEqual(len(list(dx.get_internal_classes())), 1353)    # dex header header->headerItem->classDefsSize
        self.assertEqual(len(list(dx.get_external_classes())), 388)     # difficult to check, cannot find using JADX
        self.assertEqual(len(list(dx.get_classes())), 1741)             # sum of internal and external classes

        self.assertEqual(len(dx.get_strings()), 13523)                  # dex header header->headerItem->stringsIdsSize

        # don't have a way to discern external vs internal fields currently,
        # header->headerItemFieldIdsSize is 4005, but there must be 573 more external added
        # so this is difficult to derive. Even JADX seems to disagree with 4005 number?
        self.assertEqual(len(list(dx.get_fields())), 4005 + 573)

        # internal+external methods should sum up to header->headerItem->methodIdsSize
        self.assertEqual(len(list(dx.get_internal_methods())), 9676)    # difficult to check, can use jadx-gui and see summary
        self.assertEqual(len(list(dx.get_external_methods())), 3116)    # difficult to check

        # TODO: the DEX header says 12795 here, but 9676 + 3116 adds up to 12792
        # JADX corroborates 9676, so I think 3116 is off, and a few unncessary
        # ExternalMethods are added somewhere
        self.assertEqual(len(list(dx.get_methods())), 12792)            # dex header header->headerItem->methodIdsSize
        
    

        for cls in dx.get_external_classes():
            self.assertEqual(cls.name[0], 'L')
            self.assertEqual(cls.name[-1], ';')

        # Filter all support libraries
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$"))), 512)
        self.assertEqual(len(list(dx.find_classes("^(?!Landroid/support).*;$", no_external=True))), 124)

        # Find all constructors by method name
        self.assertEqual(
            len(list(dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor=r"^\(.+\).*$"))),
            138)
        self.assertEqual(len(list(
            dx.find_methods(classname="^(?!Landroid).*;$", methodname="<init>", descriptor=r"^\(.+\).*$",
                            no_external=True))), 94)

        # Find url like strings
        self.assertEqual(len(list(dx.find_strings(r".*:\/\/.*"))), 16)

        # find String fields
        self.assertEqual(len(list(dx.find_fields(classname="^(?!Landroid).*;$", fieldtype=r"Ljava\/lang\/String;"))),
                        95)#63)

    def testAnalysis(self):
        import sys
        h, d, dx = AnalyzeDex(os.path.join(test_dir, "data/APK/AnalysisTest.dex"))

        self.assertEqual(len(list(dx.get_internal_classes())), 1)
        self.assertEqual(len(list(dx.get_internal_methods())), 4)
        self.assertEqual(len(list(dx.get_external_methods())), 4)
        self.assertEqual(len(list(dx.get_methods())), 8)
        self.assertEqual(len(dx.get_strings()), 21)
        self.assertEqual(len(list(dx.get_fields())), 0)

        self.assertEqual(h, "4595fc25104f3fcd709163eb70ca476edf116753607ec18f09548968c71910dc")
        self.assertIsInstance(d, DEX)
        self.assertIsInstance(dx, analysis.Analysis)

        cls = ["Ljava/io/PrintStream;", "Ljava/lang/Object;",
               "Ljava/math/BigDecimal;", "Ljava/math/BigInteger;"]

        for c in cls:
            self.assertIn(c, map(lambda x: x.orig_class.get_name(),
                                 dx.get_external_classes()))

    def testMultidex(self):
        a, d, dx = AnalyzeAPK(os.path.join(test_dir, "data/APK/multidex.apk"))

        cls = list(map(lambda x: x.get_vm_class().get_name(), dx.get_classes()))
        self.assertIn('Lcom/foobar/foo/Foobar;', cls)
        self.assertIn('Lcom/blafoo/bar/Blafoo;', cls)

    def testMultiDexExternal(self):
        """
        Test if classes are noted as external if not both zips are opened
        """
        from zipfile import ZipFile

        with ZipFile(os.path.join(test_dir, "data/APK/multidex.apk")) as myzip:
            c1 = myzip.read("classes.dex")
            c2 = myzip.read("classes2.dex")

        d1 = DEX(c1)
        d2 = DEX(c2)

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
        h, d, dx = AnalyzeDex(os.path.join(test_dir, "data/APK/InterfaceCls.dex"))

        cls = dx.classes['LInterfaceCls;']
        self.assertIn('Ljavax/net/ssl/X509TrustManager;', cls.implements)
        self.assertEqual(cls.name, 'LInterfaceCls;')

    def testExtends(self):
        h, d, dx = AnalyzeDex(os.path.join(test_dir, "data/APK/ExceptionHandling.dex"))

        cls = dx.classes['LSomeException;']
        self.assertEqual(cls.extends, 'Ljava/lang/Exception;')
        self.assertEqual(cls.name, 'LSomeException;')
        self.assertFalse(cls.is_external())

        cls = dx.classes['Ljava/lang/Exception;']
        self.assertEqual(cls.extends, 'Ljava/lang/Object;')
        self.assertEqual(cls.name, 'Ljava/lang/Exception;')
        self.assertEqual(cls.implements, [])
        self.assertTrue(cls.is_external())

    def testXrefs(self):
        """Test if XREFs produce the correct results"""
        with open(os.path.join(test_dir, "data/APK/classes.dex"), "rb") as fd:
            d = DEX(fd.read())
            dx = analysis.Analysis(d)

        dx.create_xref()

        testcls = dx.classes['Ltests/androguard/TestActivity;']
        self.assertIsInstance(testcls, analysis.ClassAnalysis)

        testmeth = list(filter(lambda x: x.name == 'onCreate', testcls.get_methods()))[0]

        self.assertEqual(len(list(dx.find_methods(testcls.name, '^onCreate$'))), 1)
        self.assertEqual(list(dx.find_methods(testcls.name, '^onCreate$'))[0], testmeth)

        self.assertIsInstance(testmeth, analysis.MethodAnalysis)
        self.assertFalse(testmeth.is_external())
        self.assertIsInstance(testmeth.method, EncodedMethod)
        self.assertEqual(testmeth.name, 'onCreate')

        xrefs = list(map(lambda x: x.full_name, map(itemgetter(1), sorted(testmeth.get_xref_to(), key=itemgetter(2)))))
        self.assertEqual(len(xrefs), 5)

        # First, super is called:
        self.assertEqual(xrefs.pop(0), 'Landroid/app/Activity; onCreate (Landroid/os/Bundle;)V')
        # then setContentView (which is in the current class but the method is external)
        self.assertEqual(xrefs.pop(0), 'Ltests/androguard/TestActivity; setContentView (I)V')
        # then getApplicationContext (inside the Toast)
        self.assertEqual(xrefs.pop(0),
                         'Ltests/androguard/TestActivity; getApplicationContext ()Landroid/content/Context;')
        # then Toast.makeText
        self.assertEqual(xrefs.pop(0),
                         'Landroid/widget/Toast; makeText (Landroid/content/Context; Ljava/lang/CharSequence; I)Landroid/widget/Toast;')
        # then show()
        self.assertEqual(xrefs.pop(0), 'Landroid/widget/Toast; show ()V')

        # Now, test if the reverse is true
        other = list(dx.find_methods('^Landroid/app/Activity;$', '^onCreate$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        # We have MethodAnalysis now stored in the xref!
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^setContentView$'))
        # External because not overwritten in class:
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^getApplicationContext$'))
        # External because not overwritten in class:
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Landroid/widget/Toast;$', '^makeText$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Landroid/widget/Toast;$', '^show$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        # Next test internal calls
        testmeth = list(filter(lambda x: x.name == 'testCalls', testcls.get_methods()))[0]

        self.assertEqual(len(list(dx.find_methods(testcls.name, '^testCalls$'))), 1)
        self.assertEqual(list(dx.find_methods(testcls.name, '^testCalls$'))[0], testmeth)

        self.assertIsInstance(testmeth, analysis.MethodAnalysis)
        self.assertFalse(testmeth.is_external())
        self.assertIsInstance(testmeth.method, EncodedMethod)
        self.assertEqual(testmeth.name, 'testCalls')

        xrefs = list(map(lambda x: x.full_name, map(itemgetter(1), sorted(testmeth.get_xref_to(), key=itemgetter(2)))))
        self.assertEqual(len(xrefs), 4)

        self.assertEqual(xrefs.pop(0), 'Ltests/androguard/TestActivity; testCall2 (J)V')
        self.assertEqual(xrefs.pop(0), 'Ltests/androguard/TestIfs; testIF (I)I')
        self.assertEqual(xrefs.pop(0), 'Ljava/lang/Object; getClass ()Ljava/lang/Class;')
        self.assertEqual(xrefs.pop(0), 'Ljava/io/PrintStream; println (Ljava/lang/Object;)V')

        other = list(dx.find_methods('^Ltests/androguard/TestActivity;$', '^testCall2$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertFalse(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ltests/androguard/TestIfs;$', '^testIF$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertFalse(other[0].is_external())
        self.assertFalse(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        other = list(dx.find_methods('^Ljava/lang/Object;$', '^getClass$'))
        self.assertEqual(len(other), 1)
        self.assertIsInstance(other[0], analysis.MethodAnalysis)
        self.assertTrue(other[0].is_external())
        self.assertTrue(other[0].is_android_api())
        self.assertIn(testmeth, map(itemgetter(1), other[0].get_xref_from()))

        # Testing new_instance
        testmeth = list(filter(lambda x: x.name == 'testString', testcls.get_methods()))[0]
        self.assertIsInstance(testmeth, analysis.MethodAnalysis)
        self.assertFalse(testmeth.is_external())
        self.assertIsInstance(testmeth.method, EncodedMethod)
        self.assertEqual(testmeth.name, 'testString')

        stringcls = dx.classes['Ljava/lang/String;']
        self.assertIsInstance(stringcls, analysis.ClassAnalysis)

        self.assertIn(stringcls, map(itemgetter(0), testmeth.get_xref_new_instance()))
        self.assertIn(testmeth, map(itemgetter(0), stringcls.get_xref_new_instance()))

        # Not testing println, as it has too many variants...

    def testXrefOffsets(self):
        """Tests if String offsets in bytecode are correctly stored"""
        _, _, dx = AnalyzeDex(os.path.join(test_dir, "data/APK/AnalysisTest.dex"))

        self.assertEqual(len(dx.get_strings()), 21)
        self.assertIsInstance(dx.strings['Hello world'], analysis.StringAnalysis)

        sa = dx.strings['Hello world']

        self.assertEqual(len(sa.get_xref_from()), 1)
        self.assertEqual(len(sa.get_xref_from(with_offset=True)), 1)
        self.assertEqual(next(iter(sa.get_xref_from(with_offset=True)))[2], 4)  # offset is 4

    def testXrefOffsetsFields(self):
        """Tests if Field offsets in bytecode are correctly stored"""
        _, _, dx = AnalyzeDex(os.path.join(test_dir, "data/APK/FieldsTest.dex"))

        self.assertEqual(len(dx.get_strings()), 20)
        self.assertIn('hello world', dx.strings.keys())
        self.assertIn('sdf', dx.strings.keys())
        self.assertIn('hello mars', dx.strings.keys())
        self.assertIn('i am static', dx.strings.keys())

        afield = next(dx.find_fields(fieldname='afield'))

        self.assertEqual(len(afield.get_xref_read()), 1)  # always same method
        self.assertEqual(len(afield.get_xref_read(with_offset=True)), 2)
        self.assertListEqual(list(sorted(map(itemgetter(2), afield.get_xref_read(with_offset=True)))), [4, 40])
        self.assertListEqual(list(map(lambda x: x.name, map(itemgetter(1),
                                                            afield.get_xref_read(with_offset=True)))),
                             ["foonbar", "foonbar"])

        self.assertEqual(len(afield.get_xref_write()), 2)
        self.assertEqual(len(afield.get_xref_write(with_offset=True)), 2)
        self.assertListEqual(list(sorted(map(itemgetter(2), afield.get_xref_write(with_offset=True)))), [10, 32])
        self.assertListEqual(list(sorted(map(lambda x: x.name, map(itemgetter(1),
                                                                   afield.get_xref_write(with_offset=True))))),
                             sorted(["<init>", "foonbar"]))

        cfield = next(dx.find_fields(fieldname='cfield'))
        # this one is static, hence it must have a write in <clinit>
        self.assertListEqual(list(sorted(map(lambda x: x.name, map(itemgetter(1),
                                                                   cfield.get_xref_write(with_offset=True))))),
                             sorted(["<clinit>"]))
        self.assertListEqual(list(sorted(map(lambda x: x.name, map(itemgetter(1),
                                                                   cfield.get_xref_read(with_offset=True))))),
                             sorted(["foonbar"]))

    def testPermissions(self):
        """Test the get_permissions and get_permission_usage methods"""
        a, _, dx = AnalyzeAPK(os.path.join(test_dir, "data/APK/TestActivity.apk"))

        api_level = a.get_effective_target_sdk_version()
        used_permissions = ['android.permission.BROADCAST_STICKY', 'android.permission.ACCESS_NETWORK_STATE']
        sticky_meths = ['onMenuItemSelected', 'navigateUpTo']
        network_meths = ['getNetworkInfo', 'getActiveNetworkInfo', 'isActiveNetworkMetered']

        for _, perm in dx.get_permissions(api_level):
            for p in perm:
                self.assertIn(p, used_permissions)
        meths = [x.name for x in dx.get_permission_usage('android.permission.BROADCAST_STICKY', api_level)]
        self.assertListEqual(sorted(meths), sorted(sticky_meths))
        meths = [x.name for x in dx.get_permission_usage('android.permission.ACCESS_NETWORK_STATE', api_level)]
        self.assertListEqual(sorted(meths), sorted(network_meths))

        # Should give same result if no API level is given
        for _, perm in dx.get_permissions():
            for p in perm:
                self.assertIn(p, used_permissions)
        meths = [x.name for x in dx.get_permission_usage('android.permission.BROADCAST_STICKY')]
        self.assertListEqual(sorted(meths), sorted(sticky_meths))
        meths = [x.name for x in dx.get_permission_usage('android.permission.ACCESS_NETWORK_STATE')]
        self.assertListEqual(sorted(meths), sorted(network_meths))

    def testHiddenAnnotation(self):
        a, d, dx = AnalyzeAPK(os.path.join(test_dir, "data/APK/OPCommonTelephony.jar"))

        class1 = dx.classes["Lvendor/mediatek/hardware/radio_op/V1_2/IRadioIndicationOp$Stub;"]
        self.assertEqual(class1.restriction_flag, HiddenApiClassDataItem.RestrictionApiFlag.WHITELIST)
        self.assertEqual(class1.domain_flag, HiddenApiClassDataItem.DomapiApiFlag.CORE_PLATFORM_API)

        class1 = dx.classes["Lcom/mediatek/opcommon/telephony/MtkRILConstantsOp;"]
        self.assertEqual(class1.restriction_flag, HiddenApiClassDataItem.RestrictionApiFlag.BLACKLIST)
        self.assertEqual(class1.domain_flag, HiddenApiClassDataItem.DomapiApiFlag.NONE)

if __name__ == '__main__':
    unittest.main()
