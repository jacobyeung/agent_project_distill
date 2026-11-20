import unittest
from funnel import stage, worse, outside_obb, synthetic_evidence, summarize, sample_indices


class FunnelTests(unittest.TestCase):
    def setUp(self):
        self.good = dict(visible=True, proposed=True, selected_correct=True,
                         selected_correct_frames=3, outside_box_m=.25)
        self.box = dict(center=[0,0,0], axes=[[1,0,0],[0,1,0],[0,0,1]], full_lengths=[2,2,2])

    def test_first_failure(self):
        cases = [('visible',False,'S0'),('proposed',False,'S1'),
                 ('selected_correct',False,'S2'),('selected_correct_frames',2,'S3'),
                 ('outside_box_m',.250001,'S4')]
        for key,val,want in cases:
            evidence = dict(self.good, **{key: val})
            self.assertEqual(stage(evidence)[0],want)
        self.assertEqual(stage(self.good)[0],'S5')
        self.assertEqual(stage(dict(visible=False))[0],'S0')
        self.assertEqual(stage(dict(visible=True,proposed=False))[0],'S1')

    def test_unknown_upstream_is_not_success(self):
        self.assertEqual(stage(dict(self.good,visible=None)),('U','visible'))
        self.assertEqual(stage(dict(self.good,proposed=None)),('U','proposed'))
        self.assertEqual(stage(dict(self.good,outside_box_m=None)),('U','outside_box_m'))

    def test_worse_order(self):
        self.assertEqual(worse(['S1','S4']),'S1')
        self.assertEqual(worse(['S5','S3']),'S3')
        self.assertEqual(worse(['S4','U']),'U')
        self.assertEqual(worse(['S0','U']),'S0')

    def test_null_with_target_proposal(self):
        gt={1:{1,2,3},2:{1,2,3},3:{1,2,3}}
        e=synthetic_evidence(gt,[gt],None)
        self.assertEqual(stage(e)[0],'S2')

    def test_early_lift_loss_preserves_raw_proposal_evidence(self):
        gt={1:{1,2,3}}
        e=synthetic_evidence(gt,[],None,raw_candidates=[gt])
        self.assertEqual(stage(e)[0],'S2')

    def test_synthetic_capture_all_stages(self):
        gt={1:{1,2},2:{1,2},3:{1,2}}
        wrong={1:{8,9},2:{8,9},3:{8,9}}
        self.assertEqual(stage(synthetic_evidence({},[gt],0))[0],'S0')
        self.assertEqual(stage(synthetic_evidence(gt,[wrong],0))[0],'S1')
        self.assertEqual(stage(synthetic_evidence(gt,[wrong,gt],0))[0],'S2')
        self.assertEqual(stage(synthetic_evidence(gt,[{1:{1,2}}],0))[0],'S3')
        self.assertEqual(stage(synthetic_evidence(gt,[gt],0,[2,0,0],self.box))[0],'S4')
        self.assertEqual(stage(synthetic_evidence(gt,[gt],0,[0,0,0],self.box))[0],'S5')

    def test_wrong_frames_do_not_count(self):
        gt={i:{1,2} for i in range(1,5)}
        track={1:{1,2},2:{1,2},3:{8,9},4:{8,9}}
        e=synthetic_evidence(gt,[track],0)
        self.assertEqual(e['selected_correct_frames'],2)
        self.assertEqual(stage(e)[0],'S3')

    def test_box_distance_boundary_and_rotation(self):
        self.assertEqual(outside_obb([1.25,0,0],**self.box),.25)
        self.assertAlmostEqual(outside_obb([2,2,0],**self.box),2**.5)
        b=dict(self.box,axes=[[0,1,0],[-1,0,0],[0,0,1]],full_lengths=[4,2,2])
        self.assertEqual(outside_obb([0,2.25,0],**b),.25)
        with self.assertRaises(ValueError):
            outside_obb([0,0,0],**dict(b,axes=[[1,0,0],[1,0,0],[0,0,1]]))

    def test_room_bootstrap_weights_items(self):
        rows=[dict(room='a',group='S5',score=100),dict(room='a',group='S5',score=100),
              dict(room='b',group='S1',score=0)]
        s=summarize(rows,draws=10000)
        self.assertAlmostEqual(s['groups']['S1']['association_points'],100/3)
        self.assertLess(s['groups']['S1']['association_points_defined_draws'],10000)
        self.assertEqual(s['groups']['S1']['score_ci95'],[0,0])

    def test_s5_absent_has_no_recovery_estimate(self):
        s=summarize([dict(room='r',group='U',score=50)],draws=100)
        self.assertIsNone(s['groups']['U']['association_points'])
        self.assertIsNone(s['groups']['U']['association_points_ci95'])

    def test_nested_sampling(self):
        original=[(2324*i)//31 for i in range(32)]
        a=sample_indices(2325,64,original);b=sample_indices(2325,96,original)
        self.assertEqual(len(set(a)),64)
        self.assertEqual(len(set(b)),96)
        self.assertTrue(set(original)<=set(a)<=set(b))
        self.assertEqual(original,[(2324*i)//31 for i in range(32)])
        self.assertEqual((b[0],b[-1]),(0,2324))


if __name__=='__main__':
    unittest.main()
