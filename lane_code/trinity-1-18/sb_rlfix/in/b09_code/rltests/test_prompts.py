import unittest

from rlkit.prompts import build
from rlkit.sampler import check_prompts


def row(qid, scene, n=32, **kw):
    return dict(dict(qid=qid, scene=scene, question_type='object_abs_distance', answer='1.2', target='<think>x',
                     roles={'a': 'table', 'b': 'stove'},
                     student_input=dict(question='How far?', options=[], frame_indices=list(range(n)))), **kw)


class Pool(unittest.TestCase):
    def test_build(self):
        rows = [row('a', 's1'), row('b', 's2'), row('c', 'bench'), row('d', 's1', n=64), row('a', 's1')]
        out, refused = build(rows, ['s1', 's2'], 32)
        self.assertEqual([p['prompt_id'] for p in out], ['a', 'b'])
        self.assertEqual(len(refused), 3)
        self.assertEqual(out[0]['objects'], ['table', 'stove'])
        self.assertNotIn('target', out[0]['row'])
        self.assertTrue(check_prompts(out, {}))
        out64, _ = build(rows, ['s1', 's2'], 64)
        self.assertEqual([p['prompt_id'] for p in out64], ['d'])

    def test_limit_is_seeded(self):
        rows = [row(f'q{i}', 's1') for i in range(50)]
        a, _ = build(rows, ['s1'], 32, limit=10, seed=1)
        b, _ = build(rows, ['s1'], 32, limit=10, seed=1)
        c, _ = build(rows, ['s1'], 32, limit=10, seed=2)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == '__main__':
    unittest.main()
