"""Behavioral checks for merge safety, voting, scoring, and train folds."""
import unittest
from types import SimpleNamespace as NS
import numpy as np
import serving_reference as R
import math_v2 as M

class Tests(unittest.TestCase):
    def proposal(self,frame,index,pixels,vox,score=.8):
        mask=np.zeros((80,112),bool)
        for y,x in pixels:mask[y,x]=True
        return NS(frame=frame,index=index,mask=mask,voxels=frozenset(vox),score=score,joint=score)
    def candidate(self,*ps):return NS(proposals=list(ps),voxels=frozenset().union(*(p.voxels for p in ps)))
    def test_shared_frame_conflict_prevents_merge(self):
        a=self.proposal(1,0,[(1,1)],{1,2});b=self.proposal(1,1,[(9,9)],{1,2})
        self.assertEqual(len(M.merge([self.candidate(a),self.candidate(b)],.15)),2)
    def test_overlap_uses_smaller_voxel_set_and_keeps_larger_mask(self):
        a=self.proposal(1,0,[(1,1)],{1});b=self.proposal(1,1,[(1,1),(1,2)],{1,2,3,4})
        result=M.merge([self.candidate(a),self.candidate(b)],1.)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['members'][1].index,1)
        self.assertEqual(result[0]['voxels'],frozenset({1,2,3,4}))
    def test_no_merge_threshold(self):
        a=self.proposal(1,0,[(1,1)],{1});b=self.proposal(2,0,[(1,1)],{1})
        self.assertEqual(len(M.merge([self.candidate(a),self.candidate(b)],1.01)),2)
    def test_votes_count_frames_and_fallback(self):
        # Repeated points of one view never supply a second supporting frame.
        p=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.],[0.,0.,.01]])
        far=p+1
        seen=[]
        def recorder(points):seen.append(points.copy());return R.G.min_area_box(points)
        with self.assertRaises(ValueError):M.fusion_box({1:p,2:far},1,'vote_5_2',recorder)
        self.assertEqual(len(seen[-1]),0)
        M.fusion_box({1:p,2:far},1,'vote_5_3',recorder)
        np.testing.assert_array_equal(seen[-1],p)
    def test_harness_scorer(self):
        original=R.declarations(R.ROOT/'vendor/agg.py',['mra'],dict(np=np)).mra
        for pred in [None,0.,.5,.55,.8,1.,1.05,1.5]:self.assertEqual(M.mra(pred,1.),original(pred,1.))
    def test_folds(self):
        rooms=[f'room{i}' for i in range(192)];fold=M.folds(rooms)
        self.assertEqual(fold,M.folds(list(reversed(rooms))))
        self.assertLessEqual(max(list(fold.values()).count(k) for k in range(5))-min(list(fold.values()).count(k) for k in range(5)),1)

if __name__=='__main__':unittest.main()
