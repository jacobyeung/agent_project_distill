"""Close the remaining CPU guard branches without replacing producer functions."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from student_pilot import r2_mix as M, g3t_online as gx
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.p3_provenance import file_pin
from tests.test_r2_data_path import directory
from tests.test_r2_sampling import binding
from tests.test_gf1 import fixture, TinyEncoder


class FinalGuards(unittest.TestCase):
    def test_foreign_filtered_cell(self):
        root=directory();pins,_,_=binding(root)
        population=json.loads((root/'population.json').read_text())
        population['cells']['foreign']=1
        (root/'population.json').write_text(json.dumps(population))
        counts=json.loads((root/'c.json').read_text())
        counts['cells']['foreign']=1;counts['receipts']=[file_pin(root/'population.json')]
        (root/'c.json').write_text(json.dumps(counts))
        with self.assertRaisesRegex(ValueError,'foreign cells'):
            M.preflight(pins['mix'],file_pin(root/'c.json'))

    def test_legacy_camera_branch_remains_separate(self):
        fusion,_,cfg=fixture()
        from transformers import Qwen3_5ForConditionalGeneration
        base=Qwen3_5ForConditionalGeneration(deepcopy(fusion.config)).float()
        geometry={k:v for k,v in cfg['geometry_online'].items() if k!='gf1'}
        camera=dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
                    weight_gravity=.05,weight_scale=.02,supervision=dict(path='/fixture',sha256='a'*64))
        with patch.object(gx,'G3TEncoder',TinyEncoder):
            model=CarrierC1(base,camera,{},5,training_mode='final',depth_enabled=False,frame_layout='duplicate',
                depth_fov_source='pose_head',recipe=cfg['recipe'],geometry_online=geometry,
                geometry_runtime=dict(image_mean=[.5]*3,image_std=[.25]*3))
        self.assertIsNotNone(model.auxiliary_heads.pose.cam_token_connector)
