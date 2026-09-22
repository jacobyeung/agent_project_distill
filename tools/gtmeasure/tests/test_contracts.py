import copy
import unittest

from tools.gtmeasure.blocking import refuse_blocked, scene_key
from tools.gtmeasure.formats import format_value, harvest, render_question
from tools.gtmeasure.split import SplitPolicy, hash_side
from tools.gtmeasure.targets import render_target, validate_target


def authorities():
    suffix = '\nPlease answer the question using a single word or phrase.'
    samples = {
        'absolute_count': [{'line': 1, 'question': 'How many chair(s) are here?' + suffix, 'answer': '2'}],
        'absolute_size_object': [
            {'line': 2, 'question': 'What is the longest dimension of the chair in feet?' + suffix, 'answer': '3.2'},
            {'line': 3, 'question': 'What is the longest dimension of the chair in meters?' + suffix, 'answer': '0.98'},
            {'line': 4, 'question': 'What is the longest dimension of the chair in meters?' + suffix, 'answer': '1.0'}],
        'absolute_distance_object': [{'line': 5, 'question': 'What is the distance between the chair and table at their closest points in centimeters?' + suffix, 'answer': '15.0'},
                                     {'line': 6, 'question': 'What is the distance between the chair and table at their closest points in meters?' + suffix, 'answer': '0.2'}],
        'absolute_size_room': [{'line': 7, 'question': 'What is the room area in square meters?' + suffix, 'answer': '16.3'}],
        'relative_count': [{'line': 8, 'question': 'Are there more chair(s) than table(s)?\nOptions:\nA. more\nB. fewer', 'answer': 'A'}],
        'relative_size_object': [{'line': 9, 'question': 'Is the chair or table longer?\nOptions:\nA. table\nB. chair', 'answer': 'B'}],
        'relative_distance_object': [{'line': 10, 'question': 'Which (chair, table, lamp, desk) is closest to the door, at their closest points?\nOptions:\nA. chair\nB. table\nC. lamp\nD. desk', 'answer': 'C'}],
    }
    camera = {'line': 11, 'question': 'What is the approximate distance (in meters) between the camera (or the person filming) and the nearest point of the table in frame 3 of 32?', 'answer': '1.9'}
    pin = {'path': '/fixture', 'sha256': 'a' * 64}
    return {'vsi': {'samples': samples, 'sampling': {}, 'authority': pin},
            'vsti': {'samples': [camera], 'authority': pin},
            'vsibench': {'authority': pin, 'mc_question_types': {'object_rel_distance': 4}}}


class ConventionTests(unittest.TestCase):
    def setUp(self):
        self.conventions = harvest(authorities())

    def test_units_precision_and_midpoint_refusal(self):
        self.assertEqual(format_value(.3048, 'absolute_size_object', 'feet', self.conventions), '1.0')
        self.assertEqual(format_value(.987, 'absolute_size_object', 'meters', self.conventions), '0.99')
        self.assertEqual(format_value(1., 'absolute_size_object', 'meters', self.conventions), '1.0')
        self.assertEqual(format_value(.1264, 'absolute_distance_object', 'centimeters', self.conventions), '12.6')
        with self.assertRaisesRegex(ValueError, 'midpoint'):
            format_value(.125, 'absolute_size_object', 'meters', self.conventions)
        with self.assertRaises(KeyError):
            format_value(1., 'absolute_size_room', 'feet', self.conventions)

    def test_templates_keep_source_lines_and_pool_option_order(self):
        spec = self.conventions['templates']['relative_distance_object'][0]
        question, options = render_question(spec, reference='sofa', option_0='stool', option_1='window', option_2='cabinet', option_3='bed')
        self.assertEqual(options, ['stool', 'window', 'cabinet', 'bed'])
        self.assertIn('A. stool\nB. window\nC. cabinet\nD. bed', question)
        self.assertEqual(spec['source_line'], 10)
        self.assertEqual(self.conventions['emitted_mc_types'], ['relative_distance_object'])
        self.assertEqual(self.conventions['non_emitted_mc_types'], ['relative_count', 'relative_size_object'])

    def test_compact_numeric_token_and_layout_discipline(self):
        target = render_target(['The closest-point distance is 1.9 meters.'], '1.9')
        self.assertEqual(target, 'Observations (1)\n1. The closest-point distance is 1.9 meters.\nEnd of reasoning.\n1.9')
        self.assertTrue(validate_target(target)['numeric_tokens'])
        with self.assertRaisesRegex(ValueError, 'ungrounded'):
            render_target(['The closest-point distance is 1.9 meters.'], '2.0')
        with self.assertRaises(ValueError):
            validate_target(target + '\n')


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.original = {'seed': 17, 'heldout_fraction_of_groups': .1,
                         'heldout_scenes': ['scannet/scene0010_01', 'scannetppv2/held'],
                         'train_scenes': ['scannet/scene0000_00', 'scannetppv2/train']}
        self.published = {'seed': 17, 'validation_fraction': .1,
                          'heldout_scenes': ['scannet/scene0010', 'scannetppv2/held', 'scannet/scene0420'],
                          'train_scenes': ['scannet/scene0000', 'scannetppv2/train']}
        self.policy = SplitPolicy(self.published, self.original, {'path': '/arm', 'sha256': 'b' * 64})

    def test_benchmark_group_refusal(self):
        blocked = {('scannet', 'scene0123'), ('scannetpp', 'same')}
        self.assertEqual(scene_key('scannetpp2', 'same'), ('scannetpp', 'same'))
        for dataset, scene in [('scannet', 'scene0123_99'), ('scannetppv2', 'same')]:
            with self.assertRaisesRegex(ValueError, 'blocked'):
                refuse_blocked(dataset, scene, blocked)
        refuse_blocked('scannet', 'scene0124_00', blocked)

    def test_split_inherits_physical_groups_and_hashes_new_scenes(self):
        self.assertEqual(self.policy.side('scannet', 'scene0010_02'), 'heldout')
        self.assertEqual(self.policy.side('scannetpp2', 'held'), 'heldout')
        self.assertEqual(self.policy.side('scannet', 'scene0000_09'), 'train')
        self.assertEqual(hash_side('scannet/scene0581'), 'heldout')
        self.assertEqual(self.policy.side('scannet', 'scene0581_00'), 'heldout')
        rows = [{'qid': 'held', 'dataset': 'scannet', 'scene': 'scene0010_02'},
                {'qid': 'new', 'dataset': 'scannet', 'scene': 'scene0581_00'},
                {'qid': 'train', 'dataset': 'scannet', 'scene': 'scene0000_09'}]
        train, held = self.policy.partition(rows)
        self.assertEqual([row['qid'] for row in train], ['train'])
        result = self.policy.record(train, held)
        self.assertEqual(result['heldout_scenes'], self.published['heldout_scenes'])
        self.assertEqual(result['inherited_split'], {'path': '/arm', 'sha256': 'b' * 64})
        self.assertEqual(result['new_heldout_scenes'], ['scannet/scene0581'])
        with self.assertRaisesRegex(ValueError, 'heldout'):
            self.policy.assert_train(held)

    def test_split_refuses_published_side_changes(self):
        bad = copy.deepcopy(self.published)
        bad['train_scenes'].append('scannet/scene0010_03')
        with self.assertRaisesRegex(ValueError, 'changes'):
            SplitPolicy(bad, self.original)


if __name__ == '__main__':
    unittest.main()
