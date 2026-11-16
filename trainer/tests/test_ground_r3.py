"""Regression probes for shared memory, native selection, and review survivors."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace as NS
import json
import unittest
from unittest.mock import patch
import numpy as np
import torch
import ofs
from student_pilot import carrier_c1_decode as D, verify_pass as V
from student_pilot.ground_sources import CachedSAM3, TowerSAM3, MaskProvider, OwnProposals
from student_pilot.object_memory import ClipMemory
from student_pilot.scene_state import FrameMap
from student_pilot.geometry_profiles import ProfileGeometry
from student_pilot.svp_stages import SVPStages, RescuePass, footprint
from tests.test_ground_r2 import backend, svp, own_source, batch, Reg, TMP
from tests.test_svp_stages_r2 import fixture, context
from tests.test_verify_r2 import integration_fixture, force


def accept(b, frames, name='chair'):
    b.begin_question();ctx=context(b,frames);req=b.verify_request(name,ctx)
    receipt=dict(status='ok',rows=[dict(form='V1',candidate_id=c['candidate_id'],p_yes=.9) for c in req['candidates']])
    return b.accept_verify(name,receipt,ctx)


class GroundR3(unittest.TestCase):
    def test_verified_sam_two_questions_fresh_backend(self):
        g,other,frames=fixture()
        for rule in ('seed_excl_fwd','native_selector'):
            memory=ClipMemory()
            def make():return backend(g,own_source(g),mask_source='svp_sam3',memory=memory,
                                     selector=ofs,selector_identity='ofs',rule=rule)
            a=make();first=accept(a,frames)
            self.assertIn('frames',first)
            a.begin_question();self.assertEqual(a.ground('chair',Reg()),first)
            b=make();b.begin_question()
            self.assertFalse(b.candidate_cache)
            self.assertIsNone(b.verify_request('chair',context(b,frames)))
            self.assertEqual(b.ground('chair',Reg()),first)
            self.assertTrue(memory.get('chair',a.config_hash,scene=a.scene)['primary_proposals'])

    def test_two_identical_rows_share_sam_memory(self):
        for rule in ('seed_excl_fwd','native_selector'):
            model,p,row=integration_fixture();memory=ClipMemory()
            from tests.test_ground_r2 import geometry
            g=geometry()
            bs=[backend(g,own_source(g),mask_source='svp_sam3',memory=memory,selector=ofs,
                        selector_identity='ofs',verify_threshold=0.,rule=rule) for _ in range(2)]
            records=D.generate(model,p,[deepcopy(row),deepcopy(row)],mask_source='svp_sam3',ground_backend=bs,
                verify=[V.Config(b) for b in bs],logits_processor=[force([40,1]),force([40,1])])
            self.assertIn('frames',records[0]['calls'][0]['response'])
            self.assertEqual(records[0]['text'],records[1]['text'])
            self.assertTrue(all(D.replay(r)['byte_equal'] for r in records))

    def test_clip_key_includes_video_with_identical_source_geometry_config(self):
        g,_,_=fixture();memory=ClipMemory();calls=[]
        source=MaskProvider(lambda n:calls.append(n) or batch(g.frame_map.source_indices),'same_source')
        a=backend(g,source,memory=memory,video='a'*64);b=backend(g,source,memory=memory,video='b'*64)
        self.assertEqual(a.config_hash,b.config_hash)
        self.assertNotEqual(memory.key('chair',a.config_hash,a.scene),memory.key('chair',b.config_hash,b.scene))
        a.ground('chair',Reg());b.ground('chair',Reg())
        self.assertEqual(calls,['chair','chair'])

    def test_verify_rejects_foreign_clip_even_when_frames_match(self):
        g,_,frames=fixture();b=svp(g);b.begin_question()
        ctx=replace(context(b,frames),clip_key='b'*64)
        with self.assertRaisesRegex(ValueError,'verify_clip_key_mismatch'):b.verify_request('chair',ctx)

    def test_rescue_rejects_overlap_and_propagation_off(self):
        g,other,frames=fixture()
        rescue=RescuePass(other,own_source(other),other.frame_map,frames,'same')
        with self.assertRaisesRegex(ValueError,'rescue_requires_propagation'):
            svp(g,stages=SVPStages(rescue=rescue,world_reference='same',propagation=False))
        # Do not set dense_indices: its completeness check cannot hide overlap.
        primary=replace(g.frame_map,dense_indices=(),anchor_slots=())
        overlap=RescuePass(g,own_source(g),g.frame_map,frames,'same')
        with self.assertRaisesRegex(ValueError,'other_32_source_frames'):overlap.validate(primary,'same')

    def test_rescue_preserves_primary_and_reuses_separate_memory(self):
        g,other,frames=fixture()
        C=np.array(other.contract.camera_to_world);C[:,0,3]+=1.
        other=ProfileGeometry(replace(other.contract,camera_to_world=C),np.full((32,51,51),4.))
        rescue=RescuePass(other,own_source(other),other.frame_map,frames,'same')
        source=OwnProposals(lambda *a:([],[]),g.frame_map,'empty_primary');memory=ClipMemory()
        def make():return svp(g,source,memory=memory,stages=SVPStages(rescue=rescue,world_reference='same'))
        b=make();b.begin_question();ctx=context(b,frames);b.verify_request('chair',ctx)
        primary=b.pending_verify['chair'];memory.put('chair',b.config_hash,primary,scene=b.scene)
        request=b.retry_verify('chair',dict(status='empty'),ctx)
        receipt=dict(status='ok',rows=[dict(form='V1',candidate_id=c['candidate_id'],p_yes=.9) for c in request['candidates']])
        first=b.accept_verify('chair',receipt,ctx)
        self.assertIn('frames',first)
        self.assertEqual(memory.get('chair',b.config_hash,scene=b.scene)['candidates'],[])
        self.assertTrue(memory.get('chair',b.config_hash+':rescue',scene=b.scene)['rescue'])
        later=make();later.begin_question()
        self.assertIsNone(later.verify_request('chair',context(later,frames)))
        self.assertEqual(later.ground('chair',Reg()),first)
        expected=other.lift(1,[[250.,500.]])[0][0]
        observed=np.concatenate([np.asarray(p) for p in b.results['chair']['points'].values()])
        self.assertLess(abs(np.median(observed,axis=0)[0]-expected[0]),.5)

    def test_ground_oom_reaches_decoder_boundary(self):
        model,p,row=integration_fixture()
        from tests.test_ground_r2 import geometry
        g=geometry()
        def oom(name):raise torch.cuda.OutOfMemoryError('ground provider OOM')
        b=backend(g,MaskProvider(oom,'oom'))
        with self.assertRaises(torch.cuda.OutOfMemoryError):b.ground('chair',Reg())
        b.verify_request=lambda *a:None
        good=backend(g)
        records=D.generate(model,p,[deepcopy(row),deepcopy(row)],mask_source='gt',ground_backend=[b,good],
            verify=[V.Config(b),V.Config(good)],logits_processor=[force([40,1]),force([40,1])])
        self.assertEqual(records[0]['calls'][0]['response'],'error: verify_out_of_memory')
        self.assertEqual(records[0]['errors'],1);self.assertIn('frames',records[1]['text'])
        self.assertFalse(b.memory.slots)

    def test_native_rescue_matches_unselected_primary_proposal(self):
        g,other,frames=fixture()
        primary=own_source(g,lambda n:[(1,0,2,7,.9),(3,0,2,7,.9),(1,1,12,18,.8),(3,1,12,18,.8)])
        secondary=own_source(other,lambda n:[(1,0,12,18,.9),(3,0,12,18,.9)])
        stages=SVPStages(rescue=RescuePass(other,secondary,other.frame_map,frames,'same'),world_reference='same')
        memory=ClipMemory()
        def make():return backend(g,primary,mask_source='svp_sam3',memory=memory,selector=ofs,
                                  selector_identity='ofs',stages=stages)
        b=make();b.begin_question();ctx=context(b,frames);request=b.verify_request('chair',ctx)
        self.assertEqual(len(b.pending_verify['chair']['primary_proposals']),4)
        rejected=dict(status='ok',rows=[dict(form='V1',candidate_id=c['candidate_id'],p_yes=.1) for c in request['candidates']])
        self.assertEqual(b.accept_verify('chair',rejected,ctx),'chair: not seen')
        request=b.retry_verify('chair',rejected,ctx)
        accepted=dict(status='ok',rows=[dict(form='V1',candidate_id=c['candidate_id'],p_yes=.9) for c in request['candidates']])
        text=b.accept_verify('chair',accepted,ctx)
        self.assertIn('frames 1,3',text)
        self.assertGreater(np.nonzero(b.question_slots['chair'].masks[0])[1].mean(),60)
        later=make();later.begin_question()
        self.assertIsNone(later.verify_request('chair',context(later,frames)))
        self.assertEqual(later.ground('chair',Reg()),text)

    def test_non_top_native_sam_mask_and_cached_live_gate(self):
        from rk.sam3mask import tower
        codec=tower();g,_,_=fixture()
        masks=[]
        for x in (40,180,320,460):
            m=np.zeros((480,640),bool);m[100:300,x:x+100]=True;masks.append(m)
        scores=[.99,.8,.625,.6];presence=.8
        record=dict(presence=presence,instances=[dict(score=s,mask=codec.rle_encode(m)) for s,m in zip(scores,masks)])
        cache=CachedSAM3.__new__(CachedSAM3);cache.reader=codec;cache.live=None
        cache.cache=dict(phrases=['chair'],frames={str(k):dict(phrases={'chair':record}) for k in range(32)})
        np.testing.assert_array_equal(cache.native_mask('chair',NS(frame=1,index=1)),masks[1])
        self.assertFalse(np.array_equal(cache.native_mask('chair',NS(frame=1,index=1)),masks[0]))
        live=TowerSAM3(NS(encode=lambda frames:None,detect=lambda encoded,name:[NS(scores=scores,masks=masks,presence=presence)]*32),
                      [None]*32,g.frame_map,'live',codec)
        a=cache.selector_candidates('chair');b=live.selector_candidates('chair')
        self.assertEqual([(c.frame,c.instance) for c in a],[(k,j) for k in range(1,33) for j in (0,1)])
        self.assertEqual([(c.frame,c.instance,c.confidence) for c in a],[(c.frame,c.instance,c.confidence) for c in b])
        for x,y in zip(a,b):np.testing.assert_array_equal(x.mask,y.mask)
        grids=ofs.core.lift_grid(g)
        pa,_=cache.proposals_for('chair',g,ofs,grids);pb,_=live.proposals_for('chair',g,ofs,grids)
        self.assertEqual([(p.frame,p.index) for p in pa],[(p.frame,p.index) for p in pb])
        self.assertEqual({p.index for p in pa},{0,1})

    def test_propagation_uses_max_absolute_or_relative_depth(self):
        g,_,_=fixture();uv=np.array([[500.,500.]])
        for depth,offset in ((4.,.1),(.2,.02)):
            source=ProfileGeometry(g.contract,np.full((32,51,51),depth))
            target=ProfileGeometry(g.contract,np.full((32,51,51),depth+offset))
            self.assertTrue(footprint(source.lift(1,uv)[0],target,1).any())
            bad=ProfileGeometry(g.contract,np.full((32,51,51),depth+.4))
            self.assertFalse(footprint(source.lift(1,uv)[0],bad,1).any())

    def test_rules_control_claims_in_ground_and_accept(self):
        g,_,frames=fixture()
        for rule in ('seed','native_selector','seed_excl_fwd'):
            for verified in (False,True):
                b=svp(g,rule=rule)
                if verified:accept(b,frames)
                else:b.ground('chair',Reg())
                text=b.ground('seat',Reg())
                self.assertEqual(bool(b.claims),rule=='seed_excl_fwd')
                self.assertEqual('frames' in text,rule!='seed_excl_fwd')

    def test_native_default_strict_joint_and_no_margin(self):
        g,_,_=fixture();source=own_source(g,lambda n:[(1,0,2,8,.5),(3,0,2,8,.50001)])
        b=backend(g,source,mask_source='svp_own',selector=ofs,selector_identity='ofs')
        self.assertEqual(b.config['rule'],'native_selector');b.ground('chair',Reg())
        self.assertEqual(b.question_slots['chair'].frames,(3,));self.assertFalse(b.claims)
        pieces=own_source(g,lambda n:[(1,0,2,7,.9),(1,1,9,14,.9),(3,0,2,14,.9)])
        for rule in ('native_selector','seed','seed_excl_fwd'):
            with self.assertRaisesRegex(ValueError,'ambiguity_margin_removed'):
                svp(g,pieces,rule=rule,ambiguity_margin=.05)


if __name__=='__main__':unittest.main()
