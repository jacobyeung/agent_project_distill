import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import assign as A
import mask_match as M
from tests.test_assign import resp as make_resp


def raster():
    inst = -np.ones((2, 8, 8), int)
    inst[:, 0:4, 0:4] = 3      # chair 3
    inst[:, 4:8, 4:8] = 5      # chair 5
    inst[0, 0:2, 6:8] = 7      # table 7
    return dict(inst=inst, ids=np.array([3, 5, 7]), labels=np.array(['Chair', 'chair ', 'table']),
                frame_indices=np.array([10, 20]))


def box(r0, r1, c0, c1):
    m = np.zeros((8, 8), bool)
    m[r0:r1, c0:c1] = True
    return m


class MaskMatch(unittest.TestCase):
    def test_gt_instances_by_normalised_label(self):
        self.assertEqual(M.gt_instances(raster(), ['chair', 'table', 'sofa']),
                         {'chair': ['chair:3', 'chair:5'], 'table': ['table:7'], 'sofa': []})

    def test_match_and_threshold(self):
        r = raster()
        self.assertEqual(M.match_candidate(r, {10: box(0, 4, 0, 4), 20: box(0, 4, 0, 4)})[0], 3)
        self.assertEqual(M.match_candidate(r, {10: box(0, 4, 0, 2)})[0], 3)          # IoU 0.5
        self.assertIsNone(M.match_candidate(r, {10: box(0, 4, 0, 1)})[0])          # IoU 0.25
        self.assertIsNone(M.match_candidate(r, {10: box(0, 8, 0, 8)})[0])          # covers everything
        with self.assertRaises(ValueError):
            M.match_candidate(r, {11: box(0, 4, 0, 4)})

    def test_feeds_assign(self):
        r = raster()
        acc = {'chair': [{10: box(0, 4, 0, 4)}, {20: box(4, 8, 4, 8)}]}
        sel = M.selected_ids(r, acc)
        self.assertEqual(sel, {'chair': ['chair:3', 'chair:5']})
        item = dict(qid='q', type='object_counting', answer='2', dataset='scannet', scene='scannet/scene0232_02',
                    room='d1/scene0232', gt_instances=M.gt_instances(r, ['chair']))
        resp = make_resp(qid='q', pred='2', sel=sel, gt_answer='2')
        self.assertEqual(A.decide(item, resp, A.Eligibility())[0], 'head')
        resp['selected'] = M.selected_ids(r, {'chair': [{10: box(0, 4, 0, 4)}, {10: box(0, 2, 6, 8)}]})
        self.assertEqual(A.decide(item, resp, A.Eligibility()), ('direct', 'mask_mismatch:chair'))


if __name__ == '__main__':
    unittest.main()
