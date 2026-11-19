"""Numerical and leakage-boundary tests that do not need model dependencies."""
import unittest
from types import SimpleNamespace as NS
import numpy as np
from box_math import fused_points, gather, paired_bootstrap, first_seen, mra


class MathTests(unittest.TestCase):
    def test_votes_count_frames_not_points(self):
        a=np.array([[.01,.01,.01],[.02,.02,.02],[1.,1.,1.]])
        b=np.array([[1.01,1.01,1.01],[2.,2.,2.]])
        got=fused_points({1:a,2:b},1,'vote2')
        np.testing.assert_array_equal(got,np.array([[1.,1.,1.],[1.01,1.01,1.01]]))

    def test_no_vote_fallback_with_multiple_frames(self):
        p={1:np.ones((4,3)),2:np.ones((4,3))*3}
        self.assertEqual(len(fused_points(p,1,'vote2')),0)
        np.testing.assert_array_equal(fused_points(p,1,'vote2_best'),p[1])

    def test_gather_uses_candidate_fraction_and_score_floor(self):
        def p(f,i,v,s=.8):return NS(frame=f,index=i,voxels=frozenset(v),score=s)
        seed=p(1,0,[0])
        got=gather([seed],[p(2,0,range(5)),p(3,0,[0],.299),p(4,0,range(4))])
        self.assertEqual([x.frame for x in got],[1,2,4])
        # The five-voxel proposal joins in round two after frame 4 grows the union.

    def test_bootstrap_pairs_only_shared_rows_and_weights_items(self):
        def row(i,room,p):return dict(row_id=i,room=room,prediction=p,label=1.)
        a=[row('x','A',1),row('y','A',1),row('z','B',None),row('unpaired','C',1)]
        b=[row('x','A',None),row('y','A',None),row('z','B',1)]
        result=paired_bootstrap(a,b)
        self.assertEqual(result['n'],3)
        self.assertEqual(result['rooms'],2)
        self.assertAlmostEqual(result['estimate'],100/3)
        self.assertEqual(result['ci95'],[-100.,100.])
        self.assertEqual(result,paired_bootstrap(a,b))

    def test_refusal_and_strict_mra_boundaries(self):
        self.assertEqual(mra(None,1.),0.)
        self.assertEqual(mra(1.5,1.),0.)
        self.assertEqual(mra(1.,1.),1.)

    def test_appearance_threshold_and_first_printed(self):
        masks=np.zeros((3,10,100),bool)
        masks[0,0,0]=1;masks[1,0,:2]=1
        result=first_seen(masks,[3,2])
        self.assertTrue(result['exact'])
        self.assertEqual(result['first_gt'],2)
        self.assertFalse(first_seen(masks,[])['within_one'])

    def test_heldout_evidence_cannot_change_decisions(self):
        from decisions import judge
        train=dict(rule_train_gain=3.5,rule_train_lo=.2,nonull_oof_train_lo=.1,train_scannetpp_size_mra=64.)
        negative=dict(train,rule_heldout_gain=-100.,nonull_heldout_gain=-100.,heldout_scannetpp_size_mra=0.)
        positive=dict(train,rule_heldout_gain=100.,nonull_heldout_gain=100.,heldout_scannetpp_size_mra=100.)
        self.assertEqual(judge(negative),judge(positive))
        for name in ['replace_box','selector_adopt','size_screen']:
            self.assertEqual(judge(negative)[name]['verdict'],'PASS')

    def test_seed_instance_requires_authority_and_accepts_zero(self):
        from predicted_dry import seed_instance
        seed=[NS(frame=1,mask=np.ones((2,2),bool))]
        gt={'inst':np.zeros((1,2,2),int)}
        self.assertIsNone(seed_instance(seed,gt,[]))
        self.assertEqual(seed_instance(seed,gt,[0]),0)


if __name__=='__main__':unittest.main()
