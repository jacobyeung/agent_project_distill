"""Synthetic geometry controls and authenticated T1 printed-gap parity."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import unittest
import json
import math
from collections import Counter
import devpose as d
import numpy as np


class DevPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = d.arguments([])
        d.dependencies(cls.args.gbuild)

    def fixture(self, center):
        return d.corners(dict(center=center, axes=np.eye(3), full_lengths=[1., 1., 1.]))

    def test_identical_cameras_zero_pose_term(self):
        a, b = self.fixture([2, 0, 0]), self.fixture([5, 0, 0])
        camera = np.eye(4); camera[:3, 3] = [7, 9, 1]
        l2 = d.gap(d.refit(a), d.refit(b))
        l1 = d.gap(*[d.refit(d.transport(p, camera, camera)) for p in (a, b)])
        self.assertAlmostEqual(l1, l2, places=12)
        self.assertEqual(d.metrics_row(l2, l1, l2, l2)['pose_term'], 0)
        self.assertEqual(d.metrics_row(l2, l1, l2, l2)['label_free_term'], 0)

    def test_one_anchor_known_rotation_changes_gap(self):
        a, b = self.fixture([2, 0, 0]), self.fixture([5, 0, 0])
        turn = np.eye(4); turn[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        l2 = d.gap(d.refit(a), d.refit(b))
        l1 = d.gap(d.refit(a), d.refit(d.transport(b, np.eye(4), turn)))
        self.assertAlmostEqual(l2, 2.)
        self.assertAlmostEqual(l1, np.sqrt(17))
        self.assertEqual(d.metrics_row(l2, l1, l2, l2)['pose_term'], 100)

    def test_similarity_scale_and_translation_only(self):
        c = np.repeat(np.eye(4)[None], 4, axis=0)
        c[:, :3, 3] = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
        gt = c.copy(); gt[:, :3, 3] = 3*c[:, :3, 3]+[4, 5, 6]
        fit = d.similarity(c, gt)
        self.assertAlmostEqual(fit['factor'], 3.)
        self.assertLess(fit['rms_m'], 1e-12)
        p = self.fixture([2, 0, 0])
        out = d.transport(p, np.eye(4), c[1], 3)
        np.testing.assert_allclose(out, p+[3, 0, 0])
        np.testing.assert_allclose(np.ptp(out, axis=0), [1, 1, 1])

    def test_bootstrap_empty_cells_and_paired_difference(self):
        boot = d.Bootstrap({'a': {'task': {'room': 'a'}}, 'b': {'task': {'room': 'b'}}})
        empty = boot.metric([], 'value')
        self.assertEqual(empty['undefined_draws'], 10000)
        rows = [dict(room='a', value=10.), dict(room='b', value=20.)]
        self.assertEqual(boot.contrast(rows, rows, 'value')['ci95'], [0., 0.])

    def test_registered_parity_gate(self):
        metric = lambda value: dict(mean=value, ci95=[value, value])
        ladder = [dict(dataset='all', pair_class='same', metrics=dict(pose_term=metric(0.), label_free_term=metric(20.))),
                  dict(dataset='all', pair_class='all', metrics=dict(L2_within_10pct=metric(.95)))]
        audit = [dict(dataset='all', pair_class='same', metrics=dict(label_free_term=metric(20.)))]
        weighted = [dict(dataset=ds, weighted_term=metric(1.), ladder_different_minus_same=metric(0.)) for ds in ('all', 'ARKit')]
        self.assertTrue(d.verdicts(ladder, audit, weighted)['parity_pass'])
        ladder[1]['metrics']['L2_within_10pct'] = metric(.949)
        self.assertFalse(d.verdicts(ladder, audit, weighted)['parity_pass'])

    def test_exact_search_bound_matches_unmodified_reader(self):
        rng = np.random.default_rng(20261120)
        for k in range(16):
            p = self.fixture([0, 0, 0])*rng.uniform(1., 2.5, size=3)
            a = d.refit(p)
            b = d.refit(p+rng.uniform(-3, 3, size=3))
            if k == 0:
                b = a  # A zero minimum must survive a strict search bound.
            expected = d.boxes.box_grid_5cm(a, b)
            self.assertEqual(d.gap(a, b), expected)
            self.assertEqual(d.gap(b, a), d.boxes.box_grid_5cm(b, a))
        outer = d.refit(self.fixture([0, 0, 0])*2)
        inner = d.refit(self.fixture([0, 0, 0])*.2)
        self.assertEqual(d.gap(outer, inner), d.boxes.box_grid_5cm(outer, inner))
        self.assertEqual(d.gap(inner, outer), d.boxes.box_grid_5cm(inner, outer))

    def test_T1_at_least_twenty_real_printed_gaps(self):
        refs = {r['item_id']: r for r in d.read(self.args.manifest, {})['items']}
        records, _ = d.load_capture(self.args, refs)
        checks = d.reproduce_printed(records, refs)
        self.assertGreaterEqual(len(checks), 20)
        self.assertTrue(all(r['matches'] for r in checks))
        self.assertLess(max(r['world_f1_difference_m'] for r in checks), 1e-10)
        print(f'Exact T1 printed gaps reproduced: {len(checks)}', flush=True)

    @unittest.skipUnless((Path(__file__).resolve().parent/'out/DEVPOSE.json').exists(), 'full-run artifact not yet present')
    def test_full_run_population_and_pair_accounting(self):
        result = json.loads((self.args.out/'DEVPOSE.json').read_text())
        self.assertEqual(len(result['items']), 150)
        bound = [r for r in result['items'] if all(o['instance_id'] is not None for o in r['operands'])]
        self.assertEqual(len(bound), 66)
        self.assertTrue(all('exclusion' not in r for r in bound))
        self.assertEqual(result['counts']['all_zero_mask_operands'], 1)
        self.assertEqual(len(result['GT_inventory']), 38)
        counts = Counter(r['capture'] for r in result['pairs'])
        seen = set()
        for inventory in result['GT_inventory']:
            self.assertEqual(counts[inventory['capture']], math.comb(len(inventory['eligible_instance_ids']), 2))
        for r in result['pairs']:
            key = (r['capture'], *sorted(r['instance_ids']))
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertTrue(math.isfinite(r['L2_gap_m']) and r['L2_gap_m'] >= 0)
        for mode in ('raw', 'rescaled'):
            for table in ('ladder_cells', 'audit_cells'):
                source = bound if table == 'ladder_cells' else result['pairs']
                for cell in result['statistics'][mode][table]:
                    rr = [r for r in source if (cell['dataset'] == 'all' or r['dataset_group'] == cell['dataset'])
                          and (cell['pair_class'] == 'all' or r['pair_class'] == cell['pair_class'])]
                    self.assertEqual(cell['n'], len(rr))
                    for metric in cell['metrics'].values():
                        self.assertEqual(metric['defined_draws']+metric['undefined_draws'], 10000)
        self.assertAlmostEqual(result['printed_anchor_census_by_dataset'][0]['L0_score']['mean'], 58.6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
