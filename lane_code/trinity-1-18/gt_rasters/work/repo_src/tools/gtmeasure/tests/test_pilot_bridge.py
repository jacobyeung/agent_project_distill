import copy
import unittest

from tools.gtmeasure.pilot_bridge import validate_membership
from tools.gtmeasure.swarm import AdmissionError


class PilotBridgeTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            {'qid': 'gt_train', 'dataset': 'scannet', 'scene': 'scene0000_02'},
            {'qid': 'a0__source_train', 'h5_source_qid': 'source_train', 'dataset': 'scannet', 'scene': 'scene0001_00'},
        ]
        self.split = {'train_candidate_qids': ['gt_train', 'a0__source_train'], 'heldout_qids': ['held'],
                      'heldout_group_ids': ['scannet/scene0010']}
        self.protocol = {'split': {**self.split, 'hashed_group_count': 0}}
        self.training = {'rows': [{'qid': entry['qid']} for entry in self.entries],
                         'pre_evaluation_drops': [], 'training_ready': True}
        self.forbidden = {'eval'}
        self.blocked = {('scannet', 'scene0099')}

    def check(self):
        return validate_membership(self.entries, self.split, self.protocol, self.training, self.forbidden, self.blocked)

    def test_native_membership_keeps_training_and_holdout_separate(self):
        self.assertEqual(self.check(), {'training_rows': 2, 'heldout_context_rows': 1, 'heldout_in_train': 0,
                                       'evaluation_subset_qids_in_train': 0, 'hashed_group_count': 0, 'token_limit_drops': 0})

    def test_alias_cannot_hide_evaluation_source(self):
        self.entries[1]['h5_source_qid'] = 'eval'
        with self.assertRaisesRegex(AdmissionError, 'evaluation_qid'):
            self.check()

    def test_alias_cannot_hide_heldout_source(self):
        self.entries[1]['h5_source_qid'] = 'held'
        with self.assertRaisesRegex(AdmissionError, 'heldout_qid'):
            self.check()

    def test_repeat_scan_cannot_cross_evaluation_or_holdout_groups(self):
        for scene, reason in (('scene0099_09', 'evaluation_scene'), ('scene0010_04', 'heldout_scene')):
            self.entries[0]['scene'] = scene
            with self.assertRaisesRegex(AdmissionError, reason):
                self.check()

    def test_token_drops_and_unready_manifests_are_refused(self):
        self.training['pre_evaluation_drops'] = [{'qid': 'gt_train'}]
        with self.assertRaisesRegex(AdmissionError, 'training_drops'):
            self.check()
        self.training['pre_evaluation_drops'] = []
        self.training['training_ready'] = False
        with self.assertRaisesRegex(AdmissionError, 'training_drops'):
            self.check()

    def test_missing_or_duplicated_training_rows_are_refused(self):
        self.training['rows'] = [{'qid': 'gt_train'}] * 2
        with self.assertRaisesRegex(AdmissionError, 'training_membership'):
            self.check()

    def test_rehashed_or_moved_split_is_refused(self):
        self.protocol['split']['hashed_group_count'] = 1
        with self.assertRaisesRegex(AdmissionError, 'inherited_split'):
            self.check()
        self.protocol['split'] = copy.deepcopy(self.split)
        self.protocol['split'].update(hashed_group_count=0, heldout_qids=['another'])
        with self.assertRaisesRegex(AdmissionError, 'inherited_split'):
            self.check()

    def test_unfrozen_candidate_is_refused(self):
        self.entries.append({'qid': 'extra', 'dataset': 'scannet', 'scene': 'scene0000_02'})
        with self.assertRaisesRegex(AdmissionError, 'candidate_membership'):
            self.check()


if __name__ == '__main__':
    unittest.main()
