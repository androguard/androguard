import os
import unittest

from androguard.core.dex import DEX

test_dir = os.path.dirname(os.path.abspath(__file__))


class AnnotationTest(unittest.TestCase):
    def testAnnotation(self):
        with open(
            os.path.join(test_dir, 'data/APK/Annotation_classes.dex'), "rb"
        ) as f:
            d = DEX(f.read())

        clazz = d.get_class(
            'Landroid/support/v4/widget/SlidingPaneLayout$SlidingPanelLayoutImplJB;'
        )
        annotations = clazz._get_annotation_type_ids()
        self.assertIn(
            'Landroid/support/annotation/RequiresApi;',
            [
                clazz.CM.get_type(annotation.type_idx)
                for annotation in annotations
            ],
        )

        self.assertIn(
            'Landroid/support/annotation/RequiresApi;', clazz.get_annotations()
        )
