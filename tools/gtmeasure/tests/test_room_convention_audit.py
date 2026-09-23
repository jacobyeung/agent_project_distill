import unittest

import numpy as np

from tools.gtmeasure.room_convention_audit import alpha_areas, area_label, reference_summary, scene_identity


class RoomConventionAuditTests(unittest.TestCase):
    def test_square_feet_use_area_conversion(self):
        value = area_label('100', 'How large is the room in square feet?')
        self.assertAlmostEqual(value['area_m2'], 9.290304)
        self.assertEqual(value['units'], 'square feet')

    def test_invalid_or_ambiguous_area_labels_are_refused(self):
        for answer, question in (('nan', 'square meters'), ('-1', 'square meters'),
                                 ('4', 'feet'), ('4', 'square feet or square meters')):
            with self.subTest(answer=answer, question=question), self.assertRaises(ValueError):
                area_label(answer, question)

    def test_exact_scan_identity_is_not_a_repeat_scan_alias(self):
        self.assertEqual(scene_identity('scannetppv2', 'abc'), scene_identity('scannetpp', 'abc'))
        self.assertNotEqual(scene_identity('scannet', 'scene0001_00'), scene_identity('scannet', 'scene0001_01'))

    def test_missing_reference_stays_missing(self):
        self.assertIsNone(reference_summary([]))

    def test_reference_prefers_the_published_square_meter_label(self):
        labels = [area_label('100', 'square feet'), area_label('9.3', 'square meters')]
        value = reference_summary(labels)
        self.assertEqual(value['area_m2'], 9.3)
        self.assertEqual(value['label_count'], 2)
        self.assertFalse(value['conflicting_labels'])

    def test_conflicting_references_are_not_averaged_into_truth(self):
        labels = [area_label('10', 'square meters'), area_label('30', 'square meters')]
        value = reference_summary(labels)
        self.assertTrue(value['conflicting_labels'])
        self.assertIsNone(value['area_m2'])

    def test_alpha_radius_controls_diagnostic_triangle_admission(self):
        points = np.array([[0., 0.], [2., 0.], [0., 2.], [2., 2.], [2., 2.]])
        original = points.copy()
        value = alpha_areas(points, radius_limits=(0.1, 2.0))
        self.assertAlmostEqual(value['convex_hull_m2'], 4.)
        self.assertAlmostEqual(value['by_circumradius_cutoff_m']['0.1'], 0.)
        self.assertAlmostEqual(value['by_circumradius_cutoff_m']['2.0'], 4.)
        self.assertFalse(value['is_official_benchmark_ground_truth'])
        np.testing.assert_array_equal(points, original)

    def test_nonfinite_geometry_is_refused(self):
        with self.assertRaises(ValueError):
            alpha_areas(np.array([[0., 0.], [1., 0.], [0., np.nan]]))


if __name__ == '__main__':
    unittest.main()
