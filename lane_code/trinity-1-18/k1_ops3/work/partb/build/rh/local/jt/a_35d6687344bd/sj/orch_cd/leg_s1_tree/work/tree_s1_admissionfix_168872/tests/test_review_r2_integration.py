"""Regression checks for integration findings in the independent r2 review."""
from types import SimpleNamespace as NS
import unittest
import numpy as np
import torch
from tests.test_ground_r2 import backend,geometry,batch,svp,own_source
from tests.test_svp_stages_r2 import fixture,context
from student_pilot.ground_sources import MaskProvider,OwnProposals,CachedSAM3
from student_pilot.object_memory import ClipMemory
from student_pilot.svp_stages import SVPStages,RescuePass,footprint
from student_pilot.geometry_profiles import ProfileGeometry
from student_pilot.p3_printed_calculator import PrintedPointRegistry as Reg
from rk.sam3mask import tower

class ReviewIntegration(unittest.TestCase):
    def test_rescue_requires_propagation(self):
        g,other,frames=fixture();rescue=RescuePass(other,own_source(other),other.frame_map,frames,'world')
        with self.assertRaisesRegex(ValueError,'rescue_requires_propagation'):
            svp(g,stages=SVPStages(rescue=rescue,world_reference='world',propagation=False))

    def test_rescue_does_not_replace_primary_memory(self):
        g,other,frames=fixture();rescue=RescuePass(other,own_source(other),other.frame_map,frames,'world')
        empty=OwnProposals(lambda *a:([],[]),g.frame_map,'empty_primary')
        b=svp(g,empty,stages=SVPStages(rescue=rescue,world_reference='world'));b.begin_question()
        ctx=context(b,frames);primary=b._resolve('chair');b.memory.put('chair',b.config_hash,primary,scene=b.scene)
        req=b.retry_verify('chair',dict(status='empty'),ctx)
        receipt=dict(status='ok',rows=[dict(form='V1',candidate_id=c['candidate_id'],p_yes=1.) for c in req['candidates']])
        text=b.accept_verify('chair',receipt,ctx)
        self.assertIn('frames',text)
        stored=b.memory.get('chair',b.config_hash,scene=b.scene)
        self.assertFalse(stored.get('rescue'));self.assertEqual(stored['candidates'],[])

    def test_shared_memory_separates_videos_with_identical_source_geometry(self):
        g=geometry();calls=[]
        source=MaskProvider(lambda n:calls.append(n) or batch(g.frame_map.source_indices),'same_source')
        memory=ClipMemory();a=backend(g,source,memory=memory,video='a'*64);b=backend(g,source,memory=memory,video='b'*64)
        self.assertEqual(a.config_hash,b.config_hash)
        a.ground('chair',Reg());b.ground('chair',Reg());self.assertEqual(calls,['chair','chair'])

    def test_verify_rejects_a_different_clip_key(self):
        b=backend()
        with self.assertRaisesRegex(ValueError,'verify_clip_key_mismatch'):
            b.verify_request('chair',NS(clip_key='b'*64))

    def test_rescue_rejects_overlap_even_with_valid_geometry(self):
        g,other,frames=fixture();rescue=RescuePass(g,own_source(g),g.frame_map,frames,'world')
        with self.assertRaisesRegex(ValueError,'other_32_source_frames'):rescue.validate(g.frame_map,'world')

    def test_oom_from_ground_source_is_not_an_observation(self):
        g=geometry()
        def fail(name):raise torch.cuda.OutOfMemoryError('synthetic test')
        b=backend(g,MaskProvider(fail,'oom_fixture'))
        with self.assertRaises(torch.cuda.OutOfMemoryError):b.ground('chair',Reg())
        self.assertFalse(b.memory.slots);self.assertFalse(b.queries)

    def test_native_sam_mask_uses_non_top_index(self):
        s=CachedSAM3.__new__(CachedSAM3);s.reader=tower();s.live=None
        first=np.zeros((80,112),bool);first[10:25,10:25]=True
        second=np.zeros_like(first);second[40:65,60:90]=True
        s.cache=dict(phrases=['chair'],frames={'0':dict(phrases={'chair':dict(instances=[
            dict(score=.9,mask=s.reader.rle_encode(first)),dict(score=.8,mask=s.reader.rle_encode(second))])})})
        np.testing.assert_array_equal(s.native_mask('chair',NS(frame=1,index=1)),second)

    def test_depth_agreement_uses_larger_absolute_or_relative_tolerance(self):
        g,other,frames=fixture()
        for source_depth,target_depth in [(4.,4.1),(.2,.22)]:
            source=ProfileGeometry(g.contract,np.full((32,51,51),source_depth))
            target=ProfileGeometry(g.contract,np.full((32,51,51),target_depth))
            points=source.lift(1,np.array([[500.,500.]]))[0]
            self.assertTrue(footprint(points,target,1).any())

if __name__=='__main__':unittest.main()
