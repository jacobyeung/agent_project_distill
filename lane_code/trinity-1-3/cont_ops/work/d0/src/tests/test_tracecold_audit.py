import tempfile
import unittest
from pathlib import Path

from student_pilot.trace_io import OUT, pin, save_rows
from tools.dist9.replay_text_audit import audit, counted_object, scene_key, text_key


class ReplayAuditTests(unittest.TestCase):
    def test_dist9_normalization_preserves_words_case_and_punctuation(self):
        self.assertEqual(text_key('<image>\n How many  chairs?'), text_key('How many chairs?'))
        self.assertNotEqual(text_key('how many chairs?'), text_key('How many chairs?'))
        self.assertNotEqual(text_key('How many chairs'), text_key('How many chairs?'))

    def test_scene_aliases_and_count_objects(self):
        self.assertEqual(scene_key('scannet', 'scene0000_02.mp4'), 'scannet/scene0000')
        self.assertEqual(scene_key('scannetppv2', 'abc.mp4'), 'scannetpp/abc')
        self.assertEqual(counted_object('These are frames. How many chair(s) are in this room?'), 'chair(s)')
        self.assertEqual(counted_object('How many chairs can you see?'), 'chairs')
        self.assertIsNone(counted_object('Which direction is the chair?'))

    def test_answer_overlap_is_report_only_and_preserves_targets(self):
        root = Path(tempfile.mkdtemp(prefix='tracecold_audit_', dir=OUT))
        row = {'qid': 'gt1', 'category': 'object_counting', 'dataset': 'scannet', 'scene': 'scene0000_00',
               'student_input': {'question': 'How many chair(s) are in this room?'},
               'primitives': {'name': 'chair'}, 'answer': '3', 'target': 'our GT target stays unchanged'}
        mix = save_rows(root / 'mix.jsonl', [row])
        for source_answer, expected in [('3', 1), ('4', 0)]:
            source_row = {'video': 'scannet/scene0000_02.mp4', 'question_type': 'absolute_count',
                          'conversations': [{'from': 'human', 'value': '<image>\nHow many chairs can you see?'},
                                            {'from': 'gpt', 'value': source_answer}]}
            source = save_rows(root / ('source_' + source_answer + '.jsonl'), [source_row])
            result = audit({'TR': mix['path'], 'AO': mix['path']}, source)
            self.assertEqual(result['status'], 'REPORT_ONLY')
            self.assertFalse(result['source_answers_affect_admission'])
            self.assertFalse(result['source_answers_affect_targets'])
            self.assertEqual(result['counts']['TR']['scene_object_matches'], 1)
            self.assertEqual(result['counts']['TR']['scene_object_answer_matches'], expected)
            self.assertEqual(result['counts']['TR'], result['counts']['AO'])
            self.assertEqual(pin(mix['path']), mix)
            with self.assertRaises(ValueError):
                audit({'TR': mix['path']}, {**source, 'sha256': '0' * 64})


if __name__ == '__main__':
    unittest.main()
