from dataclasses import replace
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
from student_pilot.svp_stages import SVPStages,RescuePass,NativePresence,footprint,propagate
from student_pilot.geometry_profiles import ProfileGeometry
from student_pilot.scene_state import FrameMap
from student_pilot.ground_context import GroundContext
from student_pilot.ground_sources import OwnProposals
from student_pilot.p3_printed_calculator import PrintedPointRegistry as Reg
from student_pilot import verify_pass as V,carrier_c1_decode as D
from tests.test_ground_r2 import geometry,svp,own_source
from tests.test_verify_r2 import frame_data,rgb_hash,integration_fixture,force


def fixture():
    frames=frame_data();hashes=tuple(rgb_hash(frames[k]) for k in range(1,33))
    mapping=FrameMap(tuple(range(0,64,2)),dense_indices=tuple(range(64)),anchor_slots=tuple(range(0,64,2)),rgb_sha256=hashes)
    c=geometry().contract
    C=np.repeat(c.camera_to_world[:1],32,0);K=np.repeat(c.K[:1],32,0)
    c=replace(c,frame_map=mapping,reference_source_frame=0,K=K,camera_to_world=C)
    g=ProfileGeometry(c,np.full((32,51,51),4.))
    secondary=FrameMap(tuple(range(1,64,2)),rgb_sha256=hashes)
    other=ProfileGeometry(replace(c,frame_map=secondary,reference_source_frame=1),np.full((32,51,51),4.))
    return g,other,frames


def context(b,frames):
    return GroundContext(NS(mdg_backend=b),b.geometry,None,None,b.scene.video_sha256,b.scene.frames,frames,
                         dict(hrp_frame_indices=b.scene.frames.source_indices),registry=Reg(),verify_identity='test')


class SVPStagesTest(unittest.TestCase):
    def test_transient_failure_then_same_name_replays_in_call_order(self):
        from tests.test_verify_r2 import make_backend
        for fallback in (False,True):
            model,p,row=integration_fixture();b=make_backend('gt');calls=[];original=b.verify_request
            def request(name,ctx):
                calls.append(name)
                if len(calls)==1:raise RuntimeError('transient reader failure')
                return None if fallback else original(name,ctx)
            b.verify_request=request
            record=D.generate(model,p,row,mask_source='gt',ground_backend=b,verify=V.Config(b),logits_processor=force([40,40,1]))
            self.assertEqual(record['calls'][0]['response'],'chair: not seen')
            self.assertIn('frames',record['calls'][1]['response']);self.assertTrue(D.replay(record)['byte_equal'],D.replay(record))

    def test_native_bindings_are_row_owned_and_unknown_cache_uses_live_crop(self):
        from student_pilot.ground_sources import NativeMDG,CachedSAM3
        g,other,frames=fixture();stages=SVPStages(presence=NativePresence('shared_artifact'))
        a,b=svp(g,stages=stages),svp(g,stages=stages)
        a.stages.presence.bind_native_backend('row_a');b.stages.presence.bind_native_backend('row_b')
        self.assertEqual(a.stages.presence.backend,'row_a');self.assertIsNone(stages.presence.backend)
        source=NativeMDG(g.frame_map,'shared_mdg')
        from tests.test_ground_r2 import backend
        a,b=backend(g,source,mask_source='mdg'),backend(g,source,mask_source='mdg')
        a.source.bind_native_backend('row_a');b.source.bind_native_backend('row_b')
        self.assertEqual(a.source.backend,'row_a');self.assertIsNone(source.backend)
        cache=CachedSAM3.__new__(CachedSAM3);cache.reader=NS(phrase=lambda n:n);cache.cache={'phrases':['chair']}
        calls=[];mask=np.ones((480,640),bool)
        cache.live=NS(native_mask=lambda name,p:calls.append(name) or mask)
        self.assertIs(cache.native_mask('new name',None),mask);self.assertEqual(calls,['new name'])

    def test_depth_test_pose_direction_and_sam_iou(self):
        g,other,frames=fixture()
        uv=np.array([[300.,400.],[400.,400.],[300.,500.],[400.,500.]])
        points=g.lift(1,uv)[0]
        mask=footprint(points,g,1)
        self.assertTrue(mask[32,33]);self.assertTrue(mask[40,44])
        depth=np.full((32,51,51),4.);depth[1]=2.;depth[2]=6.
        blocked=ProfileGeometry(g.contract,depth)
        self.assertFalse(footprint(points,blocked,2).any())
        self.assertFalse(footprint(points,blocked,3).any())
        C=np.array(g.contract.camera_to_world);C[3,:3,3]=[1.,0.,0.]
        moved=ProfileGeometry(replace(g.contract,camera_to_world=C),np.full((32,51,51),4.))
        self.assertLess(np.where(footprint(points,moved,4))[1].mean(),np.where(mask)[1].mean())
        p=NS(points=points,frame=1,index=0,joint=.8,mask=mask)
        c=NS(proposals=[p])
        masks,prob=propagate(c,blocked,[p],sam=True)
        np.testing.assert_array_equal(masks[0],mask);self.assertEqual(prob.sum(),1.)
        bad=NS(points=points,frame=1,index=0,joint=.8,mask=np.roll(mask,40,axis=1))
        self.assertFalse(propagate(c,blocked,[bad],sam=True)[0].any())
        masks,prob=propagate(c,blocked,[],sam=False)
        self.assertTrue(prob[31]);self.assertFalse(prob[1]);self.assertFalse(prob[2])

    def test_native_presence_and_best_visible_view(self):
        g,other,frames=fixture()
        calls=[];native=NativePresence('fixture_head')
        native.bind_native_backend(NS(batch=dict(frame_indices=g.frame_map.source_indices),memory=None,
            head=None,prefix=None,query=lambda name,**kw:calls.append((name,kw)) or 'states'))
        prior=np.zeros((1,32));prior[0,2]=.9
        with patch('student_pilot.mdg_decode.predict',return_value=({'frame_prob':prior},'encoded')):
            b=svp(g,own_source(g),stages=SVPStages(presence=native));b.begin_question()
            request=b.verify_request('lamp shade',context(b,frames))
        self.assertEqual(calls,[('lamp shade',dict(allow_unknown=True))])
        self.assertEqual(request['candidates'][0]['slot'],3)
        self.assertEqual(request['candidates'][0]['source_index'],4)
        self.assertEqual(request['candidates'][0]['rgb_sha256'],g.frame_map.rgb_sha256[2])
        self.assertEqual(b.pending_verify['lamp shade']['candidates'][0].features['presence'],.9)

    def test_rescue_runs_once_only_after_miss_and_replays(self):
        g,other,frames=fixture();model,p,row=integration_fixture();calls=[]
        source=own_source(other);original=source.fetch
        source.fetch=lambda *args:calls.append(args[0]) or original(*args)
        rescue=RescuePass(other,source,other.frame_map,frames,'same_64_export')
        empty=OwnProposals(lambda *args:([],[]),g.frame_map,'empty_primary')
        b=svp(g,empty,stages=SVPStages(rescue=rescue,world_reference='same_64_export'),verify_threshold=0.)
        row.update(frame_indices=list(g.frame_map.source_indices),hrp_frame_indices=list(g.frame_map.source_indices),
                   frame_rgb_sha256=list(g.frame_map.rgb_sha256),ground_frames=frames)
        record=D.generate(model,p,row,mask_source='svp_own',ground_backend=b,verify=V.Config(b),logits_processor=force([40,40,1]))
        self.assertEqual(calls,['chair'],record['calls']);self.assertTrue(b.results['chair']['seen'])
        self.assertEqual(len(record['calls'][0]['verify']['attempts']),2)
        self.assertIn('P2',record['calls'][1]['response']);self.assertTrue(D.replay(record)['byte_equal'])
        self.assertTrue(all(1<=k<=32 for k in b.results['chair']['frames']))
        b2=svp(g,own_source(g),stages=SVPStages(rescue=rescue,world_reference='same_64_export'),verify_threshold=0.)
        D.generate(model,p,row,mask_source='svp_own',ground_backend=b2,verify=V.Config(b2),logits_processor=force([40,1]))
        self.assertEqual(calls,['chair'])
        with self.assertRaisesRegex(ValueError,'world_reference'):
            svp(g,empty,stages=SVPStages(rescue=rescue,world_reference='wrong'))

    def test_unverified_candidate_cannot_win_at_zero_threshold(self):
        g,other,frames=fixture()
        source=own_source(g,lambda name:[(1,0,1,5,.95),(1,1,14,19,.6)])
        b=svp(g,source,verify_threshold=0.);b.begin_question();ctx=context(b,frames)
        request=b.verify_request('chair',ctx);low=request['candidates'][-1]['candidate_id']
        b.accept_verify('chair',dict(status='ok',rows=[dict(form='V1',candidate_id=low,p_yes=.9)],dropped=[{'candidate_id':'other'}]),ctx)
        self.assertEqual(b.question_slots['chair'].candidate.id,low)
        self.assertFalse(b.memory.slots)


if __name__=='__main__':unittest.main()
