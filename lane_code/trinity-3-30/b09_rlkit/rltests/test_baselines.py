import unittest

from rlkit.baselines import collapse_table, constant_report, fit_constants, shuffle_videos


def p(pid, qtype, gt, options=None, scene=None, frames=32):
    return dict(prompt_id=pid, type=qtype, gt_answer=gt, options=options, scene_key=scene or 's' + pid,
                row=dict(student_input=dict(question='q', frame_indices=list(range(frames)), fps=24.,
                                            total_num_frames=frames, video_identity=dict(video_sha256='v' + pid))))


OPTS = ['A. x', 'B. y', 'C. z', 'D. w']


class Baselines(unittest.TestCase):
    def test_constants(self):
        fit = [p('f1', 'rel', 'B', OPTS), p('f2', 'rel', 'B', OPTS), p('f3', 'rel', 'C', OPTS),
               p('g1', 'size', '100'), p('g2', 'size', '110'), p('g3', 'size', '300')]
        k = fit_constants(fit)
        self.assertEqual(k['rel']['answer'], 'B')
        self.assertEqual(k['size']['answer'], 100.0)  # 100 earns MRA on 100 and 110; 110 too, the tie goes to the smaller
        rep = constant_report(k, [p('x1', 'rel', 'B', OPTS), p('x2', 'rel', 'A', OPTS), p('y1', 'size', '100')])
        self.assertEqual(rep['rel']['c'], 0.5)
        self.assertEqual(rep['rel']['r'], 0.0)
        self.assertEqual(rep['size']['c'], 1.0)

    def test_shuffle_is_seeded_and_scene_disjoint(self):
        pool = [p(f'q{i}', 'rel', 'A', OPTS, scene=f's{i % 3}') for i in range(9)] + [p('z1', 'rel', 'A', OPTS, frames=64),
                                                                                    p('z2', 'rel', 'A', OPTS, frames=64)]
        a, b = shuffle_videos(pool, 3), shuffle_videos(pool, 3)
        self.assertEqual(a, b)
        self.assertNotEqual([r['shuffled_from'] for r in a], [r['shuffled_from'] for r in shuffle_videos(pool, 4)])
        by = {x['prompt_id']: x for x in pool}
        for r in a:
            src = by[r['shuffled_from']['prompt_id']]
            orig = by[r['prompt_id'][:-5]]
            self.assertNotEqual(src['scene_key'], orig['scene_key'])
            self.assertEqual(r['row']['student_input']['video_identity'], src['row']['student_input']['video_identity'])
            self.assertEqual(len(r['row']['student_input']['frame_indices']), len(orig['row']['student_input']['frame_indices']))
        with self.assertRaises(ValueError):
            shuffle_videos([p('a', 'rel', 'A', OPTS, scene='s'), p('b', 'rel', 'A', OPTS, scene='s')])

    def test_collapse(self):
        pool = [p(f'r{i}', 'rel', 'ABCD'[i % 4], OPTS) for i in range(8)]
        kept = [(f'r{i}', 'direct', 'A') for i in range(4)]
        t = collapse_table(pool, kept)['types']['rel']
        self.assertEqual(t['kept_bins']['A'], 1.0)
        self.assertAlmostEqual(t['tv_distance'], 0.75)
        self.assertEqual(t['path_share'], {'direct': 1.0})


if __name__ == '__main__':
    unittest.main()
