"""Native load_model with tiny native weights at the model-loader boundary."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import torch
from student_pilot import carrier_c1_run as R, full_ft
from student_pilot.r2_contract import INIT
from student_pilot.r2_openers import vocabulary
from student_pilot.p3_provenance import file_pin, write
from tests.test_carrier_c1 import fixture
from tests.test_r2_data_path import directory, LANE


class Loader(unittest.TestCase):
    def test_native_loader_opener_policy(self):
        from transformers import Qwen3_5ForConditionalGeneration
        root=directory()
        donor,_,_=fixture(training_mode='final',depth_enabled=False,trace_program_version='3.14')
        donor.frame_layout='duplicate'
        with torch.no_grad():
            donor.get_input_embeddings().weight[63].fill_(3)
            donor.get_output_embeddings().weight[63].fill_(5)
        state={n:p.detach().to(torch.bfloat16).clone() for n,p in full_ft.base_parameters(donor)}
        full_ft.save_export(state,root/'f',{}, {})
        torch.save({},root/'h.pt')
        write(root/'a.json',dict(schema='carrier-c1-artifact-v1',pose_backing='lm_final_norm',
            placement=donor.carrier_placement,frame_layout='duplicate',carrier_position_policy='native_v1',
            r2_identity=dict(init=INIT),full_weights=file_pin(root/'f/full_weights.json'),heads=file_pin(root/'h.pt')))
        processor=SimpleNamespace(tokenizer=SimpleNamespace(
            get_vocab=lambda:{str(i):i for i in range(64)},convert_tokens_to_ids=lambda token:5,
            encode=lambda token,**kwargs:[5]),
            _routing_tokens=dict(ids={'<move':63},constituents={'<move':[1,2]}))
        spec=dict(artifact=file_pin(root/'a.json'),lm='full',heads=[])
        write(root/'v.json',dict(artifact_sha256=spec['artifact']['sha256'],lineage_sha256=INIT['artifact_sha256'],
                                **vocabulary(processor)))
        receipt=dict(camera=dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
            weight_gravity=.05,weight_scale=.02,supervision={'path':'/fixture','sha256':'a'*64}),
            depth={},carrier_placement=donor.carrier_placement,training_mode='final',depth_enabled=False,
            recipe=donor.recipe,frame_layout='duplicate',depth_fov_source='pose_head',trace_program_version='3.14',
            init_artifact=spec,routing_vocabulary=file_pin(root/'v.json'))
        proofs=[]
        for policy in ('keep','reset'):
            base=Qwen3_5ForConditionalGeneration(deepcopy(donor.config)).float()
            with patch.object(Qwen3_5ForConditionalGeneration,'from_pretrained',return_value=base):
                model=R.load_model(dict(root=str(root),files={}),{**receipt,'routing_opener_init':policy},processor)
            for module,expected in ((model.get_input_embeddings(),3),(model.get_output_embeddings(),5)):
                if policy=='keep':self.assertTrue(torch.equal(module.weight[63],torch.full_like(module.weight[63],expected)))
                else:self.assertTrue(torch.equal(module.weight[63],module.weight[[1,2]].float().mean(0)))
            proofs.append(dict(policy=policy,real_loader=True,real_export_reader=True))
        (LANE/'out/B3_LOADER_PROOF.json').write_text(json.dumps(dict(proofs=proofs,
            stand_in='Qwen3_5ForConditionalGeneration.from_pretrained returns a randomly initialized tiny native Qwen; real export masters then load',
            rgb_forward=False),indent=2)+'\n')
