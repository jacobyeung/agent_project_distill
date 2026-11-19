import unittest

from student_pilot.trace_readout import decision, firing_report, validity
from student_pilot.trace_statistics import paired_scene_interval


class StatisticsTests(unittest.TestCase):
    def test_two_seeds_stay_paired_by_scene(self):
        membership = [{'qid': str(index), 'category': 'object_counting', 'physical_scene': 'scene' + str(index // 2)} for index in range(4)]
        control = {seed: [{'qid': row['qid'], 'category': row['category'], 'credit': 0.0, 'status': 'ok'} for row in membership]
                   for seed in ('17', '18')}
        treatment = {seed: [{**row, 'credit': credit} for row in control[seed]] for seed, credit in [('17', .1), ('18', .2)]}
        result = paired_scene_interval(control, treatment, membership)
        self.assertEqual(result['n'], 4)
        self.assertEqual(result['physical_scene_clusters'], 2)
        self.assertEqual(result['seed_deltas_percentage_points'], {'17': 10.0, '18': 20.0})
        self.assertAlmostEqual(result['point_delta_percentage_points'], 15.0)
        for endpoint in result['interval_95_percentage_points']:
            self.assertAlmostEqual(endpoint, 15.0)
        treatment['17'][0]['status'] = 'generation_error'
        with self.assertRaises(ValueError):
            paired_scene_interval(control, treatment, membership)
        treatment['17'][0]['status'] = 'ok'
        treatment['18'].reverse()
        with self.assertRaises(ValueError):
            paired_scene_interval(control, treatment, membership)

    def test_preregistered_verdict_precedence(self):
        self.assertEqual(decision({'17': 2, '18': 3}, [1, 4], []), 'TRACE_HELPS')
        self.assertEqual(decision({'17': -2, '18': -3}, [-4, -1], []), 'TRACE_HURTS')
        self.assertEqual(decision({'17': 2, '18': 3}, [-1, 4], []), 'NOT_DISTINGUISHABLE')
        self.assertEqual(decision({'17': 2, '18': 3}, [1, 4], ['firing']), 'INVALID_READOUT')
        self.assertEqual(decision({'17': -1, '18': 3}, [0.1, 4], []), 'SEED_DISCORDANT_NO_DECISION')

    def test_cap_and_parse_thresholds_are_inclusive(self):
        left = {'status': 'VALID_READOUT', 'by_type': {'object_counting': {'expected': 100, 'parse_rate': .98, 'cap_rate': .02}}}
        right = {'status': 'VALID_READOUT', 'by_type': {'object_counting': {'expected': 100, 'parse_rate': 1.0, 'cap_rate': 0}}}
        self.assertEqual(validity(left, right, 'object_counting'), [])
        left['by_type']['object_counting']['cap_rate'] = .021
        self.assertIn('cap_rate_exceeds_2_percent', validity(left, right, 'object_counting'))
        left['by_type']['object_counting']['parse_rate'] = .979
        self.assertIn('parse_rate_gap_exceeds_2_points', validity(left, right, 'object_counting'))


if __name__ == '__main__':
    unittest.main()
