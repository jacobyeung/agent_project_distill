"""Exercise the video-address adapter against the native decoder's cap gate."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
from student_pilot import carrier_c1_decode as D
from tests.test_batched_routed_decode import fixture

ROOT=Path(__file__).resolve().parents[3]

class VideoAddressCap(unittest.TestCase):
    def test_video_address_reaches_native_prefill_and_eos_with_legal_cap(self):
        spec=importlib.util.spec_from_file_location('r13_adapter',ROOT/'inputs/gv_fix/live_parity_adapter.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        model,processor,batch=fixture()
        original=D.generate
        def generate(*args,**kwargs):
            def eos(ids,logits):
                result=torch.full_like(logits,-float('inf'));result[:,1]=0;return result
            return original(*args,**kwargs,logits_processor=eos)
        with patch.object(adapter,'_batch',return_value=(batch,{})), \
             patch.object(D,'generate',side_effect=generate) as call, \
             patch.object(D,'_prepare_decode',wraps=D._prepare_decode) as prepare:
            result=adapter.video_address(dict(name='chair',anchor_slot=1),model,processor,batch)
        self.assertEqual(call.call_args.kwargs['max_new_tokens'],16384)
        self.assertEqual(prepare.call_count,1)
        self.assertEqual(result['record']['finish'],'eos')
        self.assertEqual(len(result['record']['tokens']),1)
        with self.assertRaisesRegex(ValueError,'Explicit caps must be at least 16384'):
            original(model,processor,batch,max_new_tokens=48)

if __name__=='__main__':unittest.main()
