"""Exercise SAM, memory, verification, own ViT rereading and B4 together."""
from copy import deepcopy
from pathlib import Path
import json,os,unittest
from unittest.mock import patch
import numpy as np
import torch
from transformers import Qwen2VLImageProcessorPil
from tests.test_verify_r2 import integration_fixture,force
from tests.test_ground_r2 import geometry
from tests.test_sam3_tower import StubBackend,StubModel
from student_pilot import carrier_c1_decode as D,verify_pass as V
from student_pilot.sam3_tower import attach_sam3_tower
from student_pilot.ground_sources import TowerSAM3
from student_pilot.ground_v3 import GroundV3
from student_pilot.scene_state import SceneState
from student_pilot.reread import Config,ReRead
from student_pilot.hrp_reread import Config as HRPConfig
from student_pilot.object_memory import ClipMemory
from rk.sam3mask import tower as codec
import ofs

ROOT=Path(os.environ.get('GV_FIX_ROOT',Path.cwd()))
class NamedSAM(StubModel):
    def forward_grounding(self,*,backbone_out,**kwargs):
        mask=torch.full((1,1,12,20),-10.)
        left=2 if self.phrases[-1]=='chair' else 12
        mask[:,:,2:10,left:left+6]=10.
        return dict(pred_logits=torch.tensor([[[5.]]]),presence_logit_dec=torch.tensor([5.]),
                    pred_boxes=torch.tensor([[[.5,.5,.5,.5]]]),pred_masks=mask)

class Combined(unittest.TestCase):
    def run_all_features(self,batched):
        model,p,row=integration_fixture()
        p.image_processor=Qwen2VLImageProcessorPil(patch_size=2,temporal_patch_size=2,merge_size=2)
        stub=StubBackend();stub.model=NamedSAM()
        tower=attach_sam3_tower(model,{'device':'cpu'},enabled=True,backend=stub)
        before=set(model.state_dict());g=geometry();memory=ClipMemory()
        own=Config(frames=row['ground_frames'],frame_indices=tuple(row['frame_indices']),clip_key=row['video_sha256'],
                   layers=(1,2,3),size_hw=(8,8),preload_ids=(),max_cache_bytes=100000)
        rows=[dict(row,own_vit_reread=own) for _ in range(4)]
        backends=[];readers=[];shapes=[];consumed=[]
        for i in range(4):
            source=TowerSAM3(tower,[row['ground_frames'][k] for k in range(1,33)],g.frame_map,'sam_fixture',codec())
            b=GroundV3(SceneState('a'*64,g.frame_map,g.identity),g,source,mask_source='svp_sam3',memory=memory,
                       selector=ofs,selector_identity='fixture',audit_dir=ROOT/'out/e2e_r2_audits'/str(i),verify_threshold=0.)
            original=b.verify_request
            def request(name,context,original=original):
                reader=context.heads.own_rereader
                taps=reader.features((1,3),(8,8))
                consumed.append(dict(name=name,slots=[1,3],shapes={k:list(v.shape) for k,v in taps.items()}))
                readers.append(reader)
                return original(name,context)
            b.verify_request=request;backends.append(b)
        original_consume=D.consume_cache_tokens
        def observe(native,ids,*args,**kwargs):
            shapes.append(len(ids));return original_consume(native,ids,*args,**kwargs)
        hrps=[HRPConfig(row['ground_frames'],tuple(row['frame_indices'])) for _ in rows]
        with patch.object(D,'consume_cache_tokens',side_effect=observe):
            if batched:
                records=D.generate(model,p,rows,mask_source='svp_sam3',ground_backend=backends,
                    verify=[V.Config(b) for b in backends],reread=hrps,
                    logits_processor=[force([40,43,44,1]) for _ in rows])
            else:
                records=[D.generate(model,p,row,mask_source='svp_sam3',ground_backend=b,
                    verify=V.Config(b),reread=h,logits_processor=force([40,43,44,1]))
                    for row,b,h in zip(rows,backends,hrps)]
        (ROOT/'out/CPU_E2E_R2_DIAGNOSTIC.json').write_text(json.dumps(records,indent=1)+'\n')
        self.assertIn(4 if batched else 1,shapes);self.assertEqual(len({id(r) for r in readers}),4)
        self.assertTrue(all(r.forward_calls==2 for r in readers))
        self.assertEqual(set(model.state_dict()),before)
        for rec in records:
            self.assertEqual([c['kind'] for c in rec['calls']],['ground','ground','gap'])
            self.assertEqual(rec['errors'],0);self.assertEqual(rec['finish'],'eos')
            self.assertNotEqual(rec['calls'][2]['response'],'not seen')
            self.assertTrue(D.replay(rec)['byte_equal'])
            self.assertTrue(all(c.get('verify_memory_hit') or c.get('verify',{}).get('status')=='ok' for c in rec['calls'][:2]))
        self.assertGreater(memory.hits,0)
        # Inspect one row through its own cache after the joint decode.
        result=dict(status='PASS',batch=4,calls_per_row=['ground','ground','gap'],records=records,
            batched_forward_sizes=sorted(set(shapes)),own_readers=4,own_feature_calls=consumed,
            own_resolution=[8,8],scope='Native tiny student and ViT; stub SAM weights; real scheduler, memory, verify, reread and lifting.',
            memory_hits=memory.hits,sam_encode_batches=stub.batch_sizes,sam_names=stub.model.phrases,
            hrp='Enabled; verification has priority, so no HRP point query is expected',replay=True)
        return result

    def test_b4_equals_four_singles_all_features(self):
        batched=self.run_all_features(True);single=self.run_all_features(False)
        self.assertEqual(batched['records'],single['records'])
        (ROOT/'out/CPU_E2E_R3.json').write_text(json.dumps(dict(status='PASS',records_equal=True,
            batched=batched,single=single),indent=1)+'\n')

if __name__=='__main__':unittest.main()
