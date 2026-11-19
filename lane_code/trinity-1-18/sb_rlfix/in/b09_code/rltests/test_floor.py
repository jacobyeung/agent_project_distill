import unittest

import numpy as np

from rlkit.floor import FloorError, budget_curve, check_heldout, fit_floor, render, sweep_length


def rows_of(qtype, path, spec, forced_tokens=8):
    """spec: list of (prompt_id, n, base); every third draw is forced on `path`."""
    out = []
    for i, (pid, n, base) in enumerate(spec):
        out.append(dict(type=qtype, path=path, prompt_id=pid, n=n, c=base, g=1.0,
                        forced=path if i % 3 == 0 else 'free', forced_prefix_tokens=forced_tokens if i % 3 == 0 else 0))
    return out


class FloorTest(unittest.TestCase):
    def test_budget_curve_is_monotone_with_fixed_denominator(self):
        cur = budget_curve([10, 40, 40, 100], [1, 0, 1, 1])
        self.assertEqual(cur['L'].tolist(), [10, 40, 100])
        np.testing.assert_allclose(cur['acc'], [0.25, 0.5, 0.75])
        np.testing.assert_allclose(cur['cond'], [1.0, 2 / 3, 0.75])

    def test_sweep_picks_shortest_budget_within_delta(self):
        # right answers need about 60 tokens; a few short right ones do not set the floor
        n = [5, 60, 62, 65, 70, 200]
        b = [1, 1, 1, 1, 1, 0]
        self.assertEqual(sweep_length(n, b, 0.0), 70)
        self.assertEqual(sweep_length(n, b, 0.2), 65)
        self.assertIsNone(sweep_length([5, 6], [0, 0], 0.02))

    def test_short_easy_prompts_cannot_pull_the_floor_down(self):
        # 20 easy prompts right at 10 tokens; 20 hard prompts right only at 80 tokens
        spec = [(f'e{i}', 10, 1.0) for i in range(20)] + [(f'h{i}', 80, 1.0) for i in range(20)] + \
               [(f'h{i}', 15, 0.0) for i in range(20)]
        res = fit_floor(rows_of('counting', 'direct', spec), delta=0.02, min_prompts=10, bootstrap=20)
        self.assertEqual(res['n_min']['counting']['direct'], 80)
        self.assertEqual(res['cells']['counting']['direct']['set_by'], 'sweep')

    def test_hard_minimum_wins_for_head_path(self):
        spec = [(f'p{i}', 14, 1.0) for i in range(30)]
        res = fit_floor(rows_of('abs_distance', 'head', spec, forced_tokens=20), delta=0.02, min_prompts=10,
                        bootstrap=0, required_calls={'abs_distance': 2})
        cell = res['cells']['abs_distance']['head']
        self.assertEqual(cell['hard_min'], 40)
        self.assertEqual(res['n_min']['abs_distance']['head'], 40)
        self.assertEqual(cell['set_by'], 'hard_min')

    def test_thin_cell_gets_no_floor(self):
        res = fit_floor(rows_of('room', 'direct', [('a', 30, 1.0), ('b', 30, 1.0)]), min_prompts=20, bootstrap=0)
        self.assertNotIn('room', res['n_min'])
        self.assertTrue(res['cells']['room']['direct']['set_by'].startswith('insufficient'))
        self.assertIn('| room | direct |', render(res))

    def test_heldout_must_not_touch_pool(self):
        pool = [dict(prompt_id='x', scene_key='s1')]
        with self.assertRaises(FloorError):
            check_heldout([dict(prompt_id='y', scene_key='s1')], pool)
        check_heldout([dict(prompt_id='y', scene_key='s2')], pool)

    def test_reward_reads_the_fitted_table(self):
        spec = [(f'p{i}', 50, 1.0) for i in range(25)]
        res = fit_floor(rows_of('object_size', 'direct', spec), min_prompts=10, bootstrap=0)
        self.assertEqual(res['n_min'], {'object_size': {'direct': 50}})
        self.assertEqual(res['n_ref'], {'object_size': 50})


if __name__ == '__main__':
    unittest.main()
