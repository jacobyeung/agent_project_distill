from dataclasses import replace
import unittest

import numpy as np
import torch

from scripts.sam3_validate import compare, compare_noise_aware, prediction, rle_decode, rle_encode
from student_pilot.sam3_tower import postprocess
from tests.test_sam3_tower import StubModel


class ValidationTests(unittest.TestCase):
    def result(self):
        raw = StubModel().forward_grounding(backbone_out={'backbone_fpn': [torch.zeros(1, 1, 1, 1)]})
        result = postprocess(raw, (9, 13), legacy=True)
        return prediction(result), result

    def test_reference_masks_and_recache_payload_roundtrip(self):
        reference, result = self.result()
        check = compare(reference, result)
        self.assertTrue(check['ok'])
        self.assertEqual(check['masks_compared'], 5)
        self.assertEqual(check['mask_min_iou'], 1.)
        for mask in (np.zeros((3, 7), bool), np.ones((3, 7), bool), np.eye(5, dtype=bool)):
            np.testing.assert_array_equal(rle_decode(rle_encode(mask)), mask)
        with self.assertRaises(ValueError):
            rle_decode({'size': [2, 2], 'counts': [3]})

    def test_score_presence_query_and_mask_drift_fail(self):
        ref, result = self.result()
        for changed in (
            replace(result, all_scores=result.all_scores-.002),
            replace(result, presence=result.presence-.002),
            replace(result, query_ids=result.query_ids.flip(0)),
            replace(result, masks=~result.masks),
        ):
            self.assertFalse(compare(ref, changed)['ok'])

    def test_no_masks_does_not_hide_score_drift(self):
        ref, result = self.result()
        ref['instances'] = []
        result = replace(result, query_ids=result.query_ids[:0], masks=result.masks[:0])
        self.assertTrue(compare(ref, result)['ok'])
        self.assertFalse(compare(ref, replace(result, all_scores=result.all_scores-.1))['ok'])

    def test_noise_rule_keeps_strict_and_accepts_small_score_noise(self):
        ref, result = self.result()
        changed = replace(result, all_scores=result.all_scores-.005, presence=result.presence-.005)
        self.assertFalse(compare(ref, changed)['ok'])
        self.assertTrue(compare_noise_aware(ref, changed)['ok'])
        for changed in (replace(result, all_scores=result.all_scores-.03),
                        replace(result, presence=result.presence-.02),
                        replace(result, masks=~result.masks)):
            self.assertFalse(compare_noise_aware(ref, changed)['ok'])

    def test_reordering_compares_masks_by_query(self):
        ref, result = self.result()
        # Use distinct masks so matching positions instead of IDs would fail.
        result = replace(result, masks=torch.stack([torch.eye(9, 13, dtype=torch.bool).roll(i, 0)
                                                   for i in range(5)]))
        ref = prediction(result)
        changed = replace(result, query_ids=result.query_ids.flip(0), masks=result.masks.flip(0),
                          scores=result.scores.flip(0), joint_scores=result.joint_scores.flip(0),
                          boxes=result.boxes.flip(0))
        self.assertFalse(compare(ref, changed)['ok'])
        self.assertTrue(compare_noise_aware(ref, changed)['ok'])
        self.assertFalse(compare_noise_aware(ref, replace(changed, masks=result.masks))['ok'])

    def test_confident_query_changes_and_score_permutations_fail(self):
        ref, result = self.result()
        ids = result.query_ids.clone()
        ids[-1] = 5  # An above-gate exchange at the proposal cap must fail.
        self.assertFalse(compare_noise_aware(ref, replace(result, query_ids=ids))['ok'])
        permuted = result.all_scores.clone()
        permuted[:2] = permuted[:2].flip(0)
        changed = replace(result, all_scores=permuted)
        self.assertTrue(compare(ref, changed)['ok'])  # Sorted top-five alone hides this.
        self.assertFalse(compare_noise_aware(ref, changed)['ok'])

    def test_gate_ambiguity_is_explicit_and_symmetric(self):
        raw = StubModel().forward_grounding(backbone_out={'backbone_fpn': [torch.zeros(1, 1, 1, 1)]})
        raw['pred_logits'] = torch.logit(torch.tensor([.8, .305, .1])).view(1, 3, 1)
        raw['pred_boxes'] = raw['pred_boxes'][:, :3]
        raw['pred_masks'] = raw['pred_masks'][:, :3]
        old = postprocess(raw, (9, 13), legacy=True)
        raw['pred_logits'][0, 1, 0] = torch.logit(torch.tensor(.295))
        new = postprocess(raw, (9, 13), legacy=True)
        for a, b in ((old, new), (new, old)):
            check = compare_noise_aware(prediction(a), b)
            self.assertTrue(check['ok'])
            self.assertEqual(check['status'], 'pass_with_gate_ambiguity')
            self.assertEqual(check['gate_ambiguous_query_ids'], [1])
            self.assertEqual(check['masks_compared'], 1)
            self.assertFalse(compare(prediction(a), b)['ok'])

    def test_joint_gate_and_invalid_inputs(self):
        ref, result = self.result()
        self.assertTrue(compare_noise_aware(ref, result, gate=.2, joint_gate=True)['ok'])
        for scores in (result.all_scores[:2], result.all_scores*float('nan')):
            self.assertFalse(compare_noise_aware(ref, replace(result, all_scores=scores))['ok'])
        ids = result.query_ids.clone()
        ids[-1] = ids[0]
        self.assertFalse(compare_noise_aware(ref, replace(result, query_ids=ids))['ok'])

    def test_unretained_scores_and_empty_predictions_are_still_checked(self):
        ref, result = self.result()
        scores = result.all_scores.clone()
        scores[6] += .03  # Outside the retained cap and outside the gate band.
        self.assertFalse(compare_noise_aware(ref, replace(result, all_scores=scores))['ok'])
        empty = replace(result, all_scores=torch.zeros_like(result.all_scores),
                        query_ids=result.query_ids[:0], masks=result.masks[:0], scores=result.scores[:0],
                        joint_scores=result.joint_scores[:0], boxes=result.boxes[:0])
        self.assertTrue(compare_noise_aware(prediction(empty), empty)['ok'])
        self.assertFalse(compare_noise_aware(prediction(empty), replace(empty, presence=empty.presence-.02))['ok'])


if __name__ == '__main__':
    unittest.main()
