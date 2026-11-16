"""CPU pass/fail proofs for all three numerical gates and the real image paths."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from student_pilot.precision_parity import probability_parity, feature_parity, record_parity

ROOT = Path(__file__).resolve().parents[3]
PROVENANCE = dict(parameter_dtype='torch.bfloat16', device='cpu')


def crop(inside=.7, reference=.702, repeat=.704):
    audit=dict(crop_rgb_sha256='rgb',prompt_tokens_sha256='prompt',processed_pixels_sha256='pixels',
        image_grid_thw=[1,2,2],attention_implementation={'text_config':'sdpa','vision_config':'sdpa'},padding_side='left',
        batch_shape={'input_ids':[1,3]},padding_tokens=0,padded_tokens_sha256='padded')
    return dict(inside=inside, reference=reference, reference_grouped=repeat,
        reference_inputs=deepcopy(audit), inside_inputs=deepcopy(audit), grouped_inputs=deepcopy(audit),
        reference_token_groups=[[1,2],[3,4]], inside_token_groups=[[1,2],[3,4]])


class ProbabilityGate(unittest.TestCase):
    def test_save_before_asserting(self):
        from student_pilot.precision_parity import check_probabilities
        root=Path(tempfile.mkdtemp())
        self.assertTrue(check_probabilities(root/'pass',[crop()],PROVENANCE,PROVENANCE,threshold=.5)['ok'])
        with self.assertRaisesRegex(AssertionError,'P\\(yes\\) parity failed'):
            check_probabilities(root/'fail',[crop(.1)],PROVENANCE,PROVENANCE,threshold=.5)
        saved=json.loads((root/'fail/P_YES_PARITY.json').read_text())
        self.assertFalse(saved['ok']);self.assertEqual(len(saved['rows']),1)
        self.assertIn('inside_yes',saved['rows'][0]);self.assertIn('reference_inputs',saved['rows'][0])
        self.assertTrue((root/'fail/crops.json').is_file())

    def test_measured_floor_pass_and_numeric_fail(self):
        row=crop()
        result=probability_parity([row],PROVENANCE,PROVENANCE)
        self.assertTrue(result['ok']);self.assertEqual(result['strict_failures'],1)
        self.assertAlmostEqual(result['floor'],.002)
        row['inside']=.69
        result=probability_parity([row],PROVENANCE,PROVENANCE)
        self.assertFalse(result['ok']);self.assertEqual(result['acceptance_failures'],1)

    def test_pooled_floor_boundaries_and_one_outlier(self):
        rows=[crop(.75,.75,.78125),crop(.65625,.75,.75)]
        result=probability_parity(rows,PROVENANCE,PROVENANCE)
        self.assertTrue(result['ok']);self.assertEqual(result['tolerance'],.09375)
        rows[-1]['inside']-=1e-7
        self.assertFalse(probability_parity(rows,PROVENANCE,PROVENANCE)['ok'])
        # A disagreement exactly at 3*floor is within the decision band.
        rows=[crop(.5,.40625,.4375)]
        self.assertTrue(probability_parity(rows,PROVENANCE,PROVENANCE)['ok'])

    def test_decision_guard_uses_floor_not_minimum_numeric_tolerance(self):
        row=crop(.4998,.5002,.5002)
        result=probability_parity([row],PROVENANCE,PROVENANCE)
        self.assertEqual(result['acceptance_failures'],0);self.assertEqual(result['decision_failures'],1)
        self.assertFalse(result['ok'])
        row['reference_grouped']=.5004
        self.assertTrue(probability_parity([row],PROVENANCE,PROVENANCE)['ok'])
        # Use the caller's actual threshold and its inclusive comparison.
        row=crop(.1999,.2001,.2001)
        self.assertFalse(probability_parity([row],PROVENANCE,PROVENANCE,threshold=.2)['ok'])
        self.assertTrue(probability_parity([crop(.2,.2,.2)],PROVENANCE,PROVENANCE,threshold=.2)['rows'][0]['inside_yes'])

    def test_bad_input_token_attention_and_nan_cannot_use_floor(self):
        for key in ('crop_rgb_sha256','prompt_tokens_sha256','processed_pixels_sha256','padding_side','attention_implementation'):
            row=crop();row['inside_inputs'][key]='bad'
            self.assertFalse(probability_parity([row],PROVENANCE,PROVENANCE)['ok'])
        row=crop();row['inside_token_groups']=[[3],[1]]
        self.assertFalse(probability_parity([row],PROVENANCE,PROVENANCE)['ok'])
        for key in ('inside','reference','reference_grouped'):
            row=crop();row[key]=float('nan')
            self.assertFalse(probability_parity([row],PROVENANCE,PROVENANCE)['ok'])
        self.assertFalse(probability_parity([crop()],PROVENANCE,dict(PROVENANCE,device='other'))['ok'])
        row=crop();row.pop('reference_grouped')
        self.assertFalse(probability_parity([row],PROVENANCE,PROVENANCE)['ok'])

    def test_cpu_fp32_cannot_borrow_half_precision_floor(self):
        provenance=dict(PROVENANCE,parameter_dtype='torch.float32')
        self.assertTrue(probability_parity([crop(.7,.7,.8)],provenance,provenance)['ok'])
        self.assertFalse(probability_parity([crop(.700002,.7,.8)],provenance,provenance)['ok'])

    def test_cpu_path_comparison_matches_reference_batch_shape(self):
        from student_pilot.run_live_parity import cpu_matched_rows
        provenance=dict(PROVENANCE,parameter_dtype='torch.float32')
        rows=cpu_matched_rows([crop(.700002,.7,.700002)])
        result=probability_parity(rows,provenance,provenance)
        self.assertTrue(result['ok']);self.assertEqual(result['rows'][0]['absolute_error'],0)
        self.assertGreater(result['rows'][0]['mixed_absolute_error'],1e-6)
        rows[0]['inside']+=2e-6
        self.assertFalse(probability_parity(rows,provenance,provenance)['ok'])

    def test_real_hfbackend_and_routed_native_fp32_same_crops(self):
        from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration, AutoModelForImageTextToText
        from verifykit.model import HFBackend
        from student_pilot.run_live_parity import images_for, reference_predictions, routed_predictions
        from student_pilot.verify_pass import native_view
        checkpoint=ROOT/'out/acceptance_inputs/REAL_T0_R6_2/bound/hf'
        manifest=json.loads((checkpoint.parent/'PARITY_CROPS_20.json').read_text())
        crops=manifest['crops'][:4];images=images_for(crops)
        config=Qwen3_5Config.from_pretrained(checkpoint,local_files_only=True)
        text=config.text_config
        text.hidden_size=32;text.intermediate_size=64;text.num_hidden_layers=2
        text.num_attention_heads=4;text.num_key_value_heads=2;text.head_dim=8
        text.layer_types=['linear_attention','full_attention'];text.linear_key_head_dim=4
        text.linear_value_head_dim=4;text.linear_num_key_heads=4;text.linear_num_value_heads=4
        text.rope_parameters=dict(rope_type='default',rope_theta=10000.,mrope_section=[1,1,2],partial_rotary_factor=1.)
        visual=config.vision_config
        visual.depth=2;visual.hidden_size=32;visual.intermediate_size=64;visual.num_heads=4
        visual.out_hidden_size=32;visual.num_position_embeddings=16
        for item in (config,text,visual):item._attn_implementation='sdpa'
        torch.manual_seed(12)
        model=Qwen3_5ForConditionalGeneration(config).float().eval()
        with patch.object(AutoModelForImageTextToText,'from_pretrained',return_value=model):
            reference=HFBackend(str(checkpoint),device='cpu')
        mixed,grouped=reference_predictions(reference,crops,images)
        class Wrapper(torch.nn.Module):
            def __init__(self,base):
                super().__init__();self.config=base.config;self.model=base.model;self.lm_head=base.lm_head
                self.generation_config=base.generation_config
            def forward(self,batch):raise AssertionError('Carrier forward is not the image path')
        native=native_view(Wrapper(deepcopy(model)).eval())
        rows=routed_predictions(native,deepcopy(reference.processor),crops,images,dict(rows=mixed,grouped_rows=grouped))
        provenance=dict(parameter_dtype='torch.float32',device='cpu')
        result=probability_parity(rows,provenance,provenance)
        self.assertTrue(result['ok'], result)
        self.assertLessEqual(max(r['absolute_error'] for r in result['rows']),1e-6)
        rows[0]['inside']+=.01
        self.assertFalse(probability_parity(rows,provenance,provenance)['ok'])


class FeatureGate(unittest.TestCase):
    def test_bf16_floor_pass_and_planted_fail(self):
        a={1:torch.zeros(2,3,dtype=torch.bfloat16)}
        b={1:a[1]+.03125};c={1:a[1]+.0625}
        report=feature_parity(a,b,c)
        self.assertTrue(report['passed']);self.assertEqual(report['strict_failures'],6)
        c[1][0,0]=.125
        self.assertFalse(feature_parity(a,b,c)['passed'])
        self.assertFalse(feature_parity(a,b,{2:c[1]})['passed'])
        c[1][0,0]=float('nan')
        self.assertFalse(feature_parity(a,b,c)['passed'])

    def test_real_native_fp32_and_saved_failure(self):
        from tests.test_own_vit_reread import fixture, bind
        spec=importlib.util.spec_from_file_location('r12_vision',ROOT/'work/tree/scripts/benchmark_own_vit_reread.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        model,processor,frames=fixture();frames[4]=frames[1].copy()
        reader=bind(model,processor,frames,chunk_size=1)
        report=dict(status='running',rows=[])
        out=Path(tempfile.mkdtemp())
        module.check_feature_parity(reader,report,out)
        self.assertTrue(report['bf16_parity']['passed'])
        original=reader.features
        def corrupted(*a):
            values=original(*a);values[1][0,0,0,0]+=.1;return values
        with patch.object(reader,'features',side_effect=corrupted):
            with self.assertRaisesRegex(AssertionError,'ViT parity failed'):
                module.check_feature_parity(reader,report,out/'fail')
        saved=json.loads((out/'fail/LATENCY.json').read_text())
        self.assertFalse(saved['bf16_parity']['passed'])
        self.assertEqual(saved['bf16_parity']['acceptance_failures'],1)


class RecordGate(unittest.TestCase):
    def records(self):
        from tests.test_decode_parity_r9 import record
        a=[record()];a[0]['heads']={'scores':[.7],'ids':[7]};return a

    def test_numeric_floor_pass_and_fail(self):
        a=self.records();b=deepcopy(a);c=deepcopy(a)
        b[0]['heads']['scores'][0]+=.002;c[0]['heads']['scores'][0]+=.004
        report=record_parity(a,b,c)
        self.assertTrue(report['ok']);self.assertEqual(report['strict_failures'],1)
        c[0]['heads']['scores'][0]+=.01
        self.assertFalse(record_parity(a,b,c)['ok'])
        self.assertFalse(record_parity(a,b,b,half=False)['ok'])

    def test_every_decision_and_structure_stays_exact(self):
        a=self.records()
        changes=[lambda r:r[0]['tokens'].__setitem__(0,9),lambda r:r[0].update(text='B'),
            lambda r:r[0]['calls'][0].update(response='changed'),lambda r:r[0]['calls'][0].update(call='<ground obj="desk">'),
            lambda r:r[0]['heads']['ids'].__setitem__(0,8),lambda r:r[0].update(finish='length'),
            lambda r:r[0].update(extra=1),lambda r:r.clear()]
        for change in changes:
            b=deepcopy(a);change(b)
            self.assertFalse(record_parity(a,a,b)['ok'])
            self.assertFalse(record_parity(a,b,a)['ok'])
        b=deepcopy(a);b[0]['heads']['scores'][0]=float('nan')
        self.assertFalse(record_parity(a,a,b)['ok'])

    def test_native_b4_preload_decisions_fp32(self):
        from tests.test_own_vit_reread import DecodeTests
        case=DecodeTests();model,processor,batch,config=case.prepare()
        batches=[deepcopy(batch) for _ in range(4)]
        reference=case.run_decode(model,processor,batches)
        repeat=case.run_decode(model,processor,batches)
        actual=case.run_decode(model,processor,[dict(b,own_vit_reread=config) for b in batches])
        self.assertTrue(record_parity(reference,repeat,actual,half=False)['ok'])
        actual[0]['tokens'][0]+=1
        self.assertFalse(record_parity(reference,repeat,actual,half=False)['ok'])


if __name__=='__main__':unittest.main()
