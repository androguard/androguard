import unittest
import sys
from androguard.core.bytecodes import dvm


class AnnotationTest(unittest.TestCase):
    def testAnnotation(self):
        with open("examples/android/TestsAnnotation/classes.dex", "rb") as f:
            d = dvm.DalvikVMFormat(f.read())

        clazz = d.get_class('Landroid/support/v4/widget/SlidingPaneLayout$SlidingPanelLayoutImplJB;')
        annotations = clazz._get_annotation_type_ids()
        self.assertIn('Landroid/support/annotation/RequiresApi;', [clazz.CM.get_type(annotation.type_idx) for annotation in annotations])

        self.assertIn('Landroid/support/annotation/RequiresApi;', clazz.get_annotations())

