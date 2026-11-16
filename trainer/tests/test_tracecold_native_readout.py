import unittest

from scripts.tracecold_read_native import contains_sha, score_projection
from student_pilot.trace_readout import firing_report


class NativeProjectionTests(unittest.TestCase):
    def test_primary_parse_rates_use_frozen_lenient_scores(self):
        members = [{'qid': '1', 'category': 'object_counting', 'physical_scene': 'synthetic'}]
        raw = [{'qid': '1', 'status': 'ok', 'raw_generation': 'chair newly visible: <0.0 seconds> +1; count: 1\n</think>\n\n1',
                'generated_tokens': 25, 'finish_reason': 'eos', 'parsed_answer': None}]
        scores = [{'qid': '1', 'category': 'object_counting', 'status': 'ok', 'parsed_answer': 1, 'credit': 1.0}]
        projected = score_projection(raw, scores, members)
        self.assertIsNone(projected[0]['strict_parsed_answer'])
        self.assertIsNone(raw[0]['parsed_answer'])
        self.assertEqual(projected[0]['raw_generation'], raw[0]['raw_generation'])
        report = firing_report(projected, members, ['object_counting'])
        self.assertEqual(report['by_type']['object_counting']['parse_rate'], 1.0)
        self.assertEqual(report['by_type']['object_counting']['trained_line_rate'], 1.0)

    def test_projection_refuses_changed_status_or_membership(self):
        members = [{'qid': '1', 'category': 'object_counting'}]
        raw = [{'qid': '1', 'status': 'error'}]
        scores = [{'qid': '1', 'category': 'object_counting', 'status': 'error', 'parsed_answer': None}]
        self.assertEqual(score_projection(raw, scores, members)[0]['status'], 'error')
        for changed in ([{**scores[0], 'status': 'ok'}], [{**scores[0], 'qid': '2'}], [scores[0], scores[0]]):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                score_projection(raw, changed, members)

    def test_adapter_identity_requires_a_bound_weight_hash(self):
        core = {'adapter': {'weights': {'sha256': 'a' * 64}}}
        self.assertTrue(contains_sha(core, 'a' * 64))
        self.assertFalse(contains_sha(core, 'b' * 64))


if __name__ == '__main__':
    unittest.main()
