"""Reviewer refute tests, adapted to this candidate and its local main contract."""
import offline_guard
import json, sys, unittest
from pathlib import Path
C = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(C), str(C/'readk')]
import h1pair as P

def row(fam, i, room, score, task='object_counting'):
    return dict(family=fam, id=f'{fam}{i}', room=room, scene=room, task_type=task, level=None,
                score=score, budget=2048, step=200, scoring_basis='answer', pair_id=None, count_kind=None)

class Refute(unittest.TestCase):
    def test_unpaired_family_silently_dropped(self):
        # D0 side carries main + r0dev, H1 side lost its main family: pairing must refuse, it does not.
        d0 = [row('main', i, f'r{i%5}', 1.0) for i in range(20)] + [row('a7', i, f'q{i%5}', 0.5) for i in range(20)]
        h1 = [row('a7', i, f'q{i%5}', 0.5) for i in range(20)]
        with self.assertRaises(ValueError):
            P.compare(d0, h1, 200)

    def test_partial_item_loss_silently_pairs_subset(self):
        d0 = [row('main', i, f'r{i%5}', 1.0) for i in range(20)]
        h1 = [row('main', i, f'r{i%5}', 0.0) for i in range(10)]
        with self.assertRaises(ValueError):
            P.compare(d0, h1, 200)

    def test_harm_flag_reaches_non_main_families(self):
        # D0's registered F1 (readk f1f2.evaluate) selects family 'main' only.
        d0 = [row('away', i, f'r{i%10}', 1.0, 'object_rel_direction_easy') for i in range(40)]
        h1 = [row('away', i, f'r{i%10}', 0.0, 'object_rel_direction_easy') for i in range(40)]
        out = P.compare(d0, h1, 200)
        self.assertEqual(out['harm'], [], 'away-family type flagged as F1 harm')

class Layout(unittest.TestCase):
    def test_r0dev_uses_trained_32_duplicate_layout(self):
        cfg = json.loads((C/'kit/reader/e193_contract.json').read_text())['main']['cells'][0]
        self.assertEqual(cfg['layout'], 'duplicate')
        self.assertEqual(cfg['frames'], 32)
        src = (C/'kit/reader/x7.py').read_text()
        self.assertFalse("cell['layout']='spread'" in src, 'r0dev feeds 32 spread frames; H1-1/D0 train on 32 duplicate')

if __name__ == '__main__':
    unittest.main()
