"""Check censoring precedence and real-data audit invariants."""
from round7_common import *
import unittest
from funnel_round7 import item_stage, dense_stage
from gpkg.runtime.c import rle

class StageRules(unittest.TestCase):
    def test_missing_gt_does_not_hide_observed_failure(self):
        for s in LABELS[:5]:
            self.assertEqual(item_stage([dict(stage='no-GT'),dict(stage=s)]),s)
        self.assertEqual(item_stage([dict(stage='no-GT'),dict(stage='S5')]),'no-GT')

    def test_censoring_has_an_upstream_boundary(self):
        self.assertEqual(item_stage([dict(stage='S3'),dict(stage='censored',censored_from='S4')]),'S3')
        self.assertEqual(item_stage([dict(stage='S3'),dict(stage='censored',censored_from='S0')]),'censored')
        self.assertEqual(item_stage([dict(stage='S5'),dict(stage='censored',censored_from='S4')]),'censored')

    def test_dense_unannotated_identity_is_not_a_failure_or_recovery(self):
        row=dict(ground_frame_count=64,anchor_slots=list(range(0,64,2)))
        obj=dict(selected_masks={'2':rle(np.ones((2,2),bool))},proposals=[])
        anchor=dict(stage='S3',reason=None,evidence=dict(visible=True,proposed=True,outside_box_m=0.),
                    nonempty_selected_frames=2,selected_matched_frames=[1])
        actual=dense_stage(row,obj,anchor,dict(alignment=dict(accepted=True)))
        self.assertEqual(actual['stage'],'censored')
        self.assertEqual(actual['censored_from'],'S2')

    def test_dense_lower_bound_can_prove_stage_pass(self):
        row=dict(ground_frame_count=64,anchor_slots=list(range(0,64,2)))
        obj=dict(selected_masks={'2':rle(np.ones((2,2),bool))},proposals=[])
        anchor=dict(stage='S5',reason=None,evidence=dict(visible=True,proposed=True,outside_box_m=0.),
                    nonempty_selected_frames=3,selected_matched_frames=[1,2,3])
        actual=dense_stage(row,obj,anchor,dict(alignment=dict(accepted=True)))
        self.assertEqual(actual['stage'],'S5')
        actual=dense_stage(row,obj,anchor,dict(alignment=dict(accepted=False)))
        self.assertEqual(actual['stage'],'censored')
        self.assertEqual(actual['censored_from'],'S4')

    def test_real_partitions_and_migrations(self):
        f=read(OUT/'FUNNEL_T1.json')
        for arm in ('t1','points','dense64'):
            self.assertEqual(sum(x['objects'] for x in f['tables'][arm]),300)
            self.assertEqual(sum(x['items'] for x in f['tables'][arm]),150)
            self.assertEqual(len({x['key'] for x in f['objects'][arm]}),300)
        for arm,units in f['migrations'].items():
            for unit,m in units.items():
                matrix=np.array(m['matrix']); n=300 if unit=='objects' else 150
                self.assertEqual(int(matrix.sum()),n)
                np.testing.assert_array_equal(matrix.sum(1),[r[unit] for r in f['tables']['t1']])
                np.testing.assert_array_equal(matrix.sum(0),[r[unit] for r in f['tables'][arm]])
        for o in f['objects']['t1']:
            if o['stage']=='S2': self.assertTrue(o['evidence']['proposed'])
            if o['stage'] in ('S4','S5'): self.assertTrue(o['alignment_accepted'])

    def test_real_bootstrap_matches_existing_scorer(self):
        f=read(OUT/'FUNNEL_T1.json')
        for filename,arm,key in [('SCORE_POINT_T1.json','points','points'),('SCORE_DENSE_T1.json','dense64','dense64')]:
            s=read(OUT/filename)['statistics']['groups']['all']['metrics']
            np.testing.assert_allclose(f['overall'][arm]['ci95'],s[key]['ci95'])
            self.assertAlmostEqual(f['overall'][arm]['mean'],s[key]['mean'])

    def test_camera_and_s2_integrity(self):
        c=read(OUT/'CAMERA_SPLIT.json');s=read(OUT/'S2_T1.json');f=read(OUT/'FUNNEL_T1.json')
        self.assertEqual(len(c['captures']),38)
        self.assertEqual(sum(x['alignment_pass'] for x in c['captures']),6)
        self.assertEqual(sum(x['items'] for x in c['captures']),76)
        self.assertEqual(sum(x['count'] for x in f['migrations']['points']['objects']['cells']),300)
        self.assertEqual(len(s['objects']),sum(o['stage']=='S2' for o in f['objects']['t1']))
        self.assertEqual(sum(r['objects'] for r in s['class_x_pool']),len(s['objects']))
        self.assertTrue(all(len(o['frames'])==32 and o['pool_had_target'] for o in s['objects']))

if __name__=='__main__': unittest.main(verbosity=2)
