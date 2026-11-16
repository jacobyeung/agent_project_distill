"""Real native CPU forward with tiny random LM/tower weights at the GPU boundary."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import torch
from student_pilot.carrier_c1 import CarrierC1, parameter_groups
from student_pilot import r2_config as C
from student_pilot.p3_provenance import load
from tests.test_gf1 import fixture as fusion_fixture, logits, equal
from tests.test_r2_data_path import PROOFS, directory, LANE
from tests.test_r2_build import dense


class Models(unittest.TestCase):
    def test_arms_parent_parity_reload_and_trainables(self):
        root=directory(); dp=dense(root)
        parent_cfg=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        reports=[]
        for stage in (1,2):
            fusion,batch,native=fusion_fixture(stage)
            from transformers import Qwen3_5ForConditionalGeneration
            base=Qwen3_5ForConditionalGeneration(deepcopy(fusion.config)).float()
            camera=dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
                        weight_gravity=.05,weight_scale=.02,supervision=dict(path='/fixture',sha256='a'*64))
            parent=CarrierC1(base,camera,{},5,training_mode='final',depth_enabled=False,
                             frame_layout='duplicate',depth_fov_source='pose_head',recipe=native['recipe'])
            selected={k:v for k,v in fusion.state_dict().items() if k in parent.state_dict()}
            parent.load_state_dict(selected,strict=True)
            parent.eval();fusion.eval()
            with torch.no_grad():
                expected=logits(parent,deepcopy(batch)); actual=logits(fusion,deepcopy(batch))
            self.assertTrue(torch.equal(expected,actual))
            self.assertEqual(fusion.auxiliary_heads.geometry_encoder.calls,1)
            for connector,model in [('none',parent),('gf1',fusion)]:
                cfg=C.configure(parent_cfg,connector,dense_manifest=dp if connector=='gf1' else None,stage=stage)
                settings=C.apply_native(cfg,native['geometry_online'] if connector=='gf1' else None)
                self.assertEqual(settings['geometry_connector'],connector)
                names=[n for n,p in model.named_parameters() if p.requires_grad]
                self.assertIsNone(model.auxiliary_heads.pose.cam_token_connector)
                if connector=='gf1' and stage==1:
                    self.assertTrue(names and all(n.startswith('auxiliary_heads.gf1.') for n in names))
                else:
                    self.assertTrue(any(n.startswith('model.language_model.') for n in names))
                    self.assertTrue(any(n.startswith('auxiliary_heads.pose.') for n in names))
                self.assertFalse(any('geometry_encoder' in n for n in names))
                groups=parameter_groups(model,native['recipe'])
                if connector=='gf1':
                    self.assertEqual(next(g['lr'] for g in groups if g['name']=='gf1'),
                                     parent_cfg['recipe']['learning_rate'] if stage==1 else native['recipe']['lm_learning_rate'])
                path=root/(connector+str(stage)+'.pt');torch.save(model.state_dict(),path)
                restored=deepcopy(model);restored.load_state_dict(torch.load(path,weights_only=True))
                self.assertTrue(equal(model.state_dict(),restored.state_dict()))
                with torch.no_grad():
                    self.assertTrue(torch.equal(logits(model,deepcopy(batch)),logits(restored,deepcopy(batch))))
                model.train(); result=model(deepcopy(batch),stream='vqa');result['loss'].backward()
                self.assertTrue(torch.isfinite(result['loss']))
                reports.append(dict(connector=connector,stage=stage,parity_exact=True,reload_exact=True,trainables=names,
                                    finite_loss=True,synthetic=True))
        (PROOFS/'B2_MODEL_PROOF.json').write_text(json.dumps(reports,indent=2)+'\n')
