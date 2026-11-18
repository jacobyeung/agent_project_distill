"""CPU decode diagnostics, strict fp32 hybrid state parity, and suffix-only gates."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import torch

from student_pilot import decode_parity as P
from student_pilot import carrier_c1_decode as D, carrier_c1_batch_decode as B
from tests.test_batched_routed_decode import fixture, varied, Script


def record():
    return dict(tokens=[7, 8, 9, 10, 11, 1],
        text='<ground obj="chair"><tool_response>chair: not seen</tool_response>\n</think>\nA<|im_end|>',
        calls=[dict(call='<ground obj="chair">', response='chair: not seen', at_token=1, forced_tokens=2)],
        finish='eos', errors=0)


class Diagnostics(unittest.TestCase):
    def test_suffix_noise_and_exact_answer_gate(self):
        a=record();b=deepcopy(a);b['tokens'][3]=12
        b['text']=b['text'].replace('</think>', 'extra reasoning\n</think>')
        row=P.compare([a],[b])[0]
        self.assertEqual(row['first_differing_token'],3)
        self.assertEqual(row['token_ids'],[10,12])
        self.assertTrue(row['acceptance_equal']);self.assertFalse(row['strict_equal'])
        self.assertEqual(P.noise_report([a],[a],[b])['repeatability']['strict_failures'],0)
        self.assertFalse(P.noise_report([a],[a],[b])['bf16_batch_arithmetic_floor_measured'])

    def test_each_semantic_mutation_fails_even_with_equal_tokens(self):
        a=record()
        changes=[lambda r:r['calls'][0].update(call='<gap obj="chair">'),
                 lambda r:r['calls'][0].update(call='<ground obj="table">'),
                 lambda r:r['calls'][0].update(response='chair: unresolved'),
                 lambda r:r.update(text=r['text'].replace('\nA','\nB')),
                 lambda r:r.update(finish='max_new_tokens'),lambda r:r.update(errors=1),
                 lambda r:r['calls'].clear()]
        for change in changes:
            b=deepcopy(a);change(b)
            self.assertFalse(P.compare([a],[b])[0]['acceptance_equal'])

    def test_prefix_or_response_divergence_fails(self):
        for index in range(3):
            a=record();b=deepcopy(a);b['tokens'][index]=100
            self.assertFalse(P.compare([a],[b])[0]['acceptance_equal'])

    def test_length_diff_missing_record_and_missing_answer(self):
        a=record();b=deepcopy(a);b['tokens'].append(12)
        self.assertEqual(P.compare([a],[b])[0]['token_ids'],[None,12])
        self.assertTrue(P.compare([a],[b])[0]['acceptance_equal'])
        self.assertFalse(P.compare([a],[])[0]['acceptance_equal'])
        a['text']=a['text'].split('</tool_response>')[0]+'</tool_response>'
        self.assertFalse(P.compare([a],[a])[0]['acceptance_equal'])

    def test_pooled_counts_cannot_dilute_one_semantic_failure(self):
        a=record();b=deepcopy(a);b['text']=b['text'].replace('\nA','\nB')
        rows=P.compare([a]*100,[a]*99+[b]);summary=P.pooled(rows)
        self.assertEqual(summary['semantic_failures'],1)
        self.assertEqual(summary['acceptance_failures'],1)

    def test_saves_both_arms_before_strict_failure(self):
        root=Path(tempfile.mkdtemp());a=record();b=deepcopy(a);b['tokens'][3]=12
        result=P.save_comparison(root,[a],[b])
        self.assertEqual(result['status'],'FAIL')
        for name in ('b1.json','b4.json','COMPARISON.json'):self.assertTrue((root/name).is_file())
        self.assertEqual(P.save_comparison(root,[a],[b],strict=False)['status'],'PASS')
        b['audit']='changed'
        self.assertEqual(P.save_comparison(root,[a],[b],full_records=True)['status'],'FAIL')

    def test_real_stage_saves_failure_and_runs_b1_twice(self):
        import importlib.util, sys
        root=Path(__file__).resolve().parents[3]
        sys.path.insert(0,str(root/'scripts'))
        spec=importlib.util.spec_from_file_location('r9_gpu_stage',root/'scripts/gpu_routed_batch.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        tmp=Path(tempfile.mkdtemp());inputs=tmp/'inputs.json'
        inputs.write_text(json.dumps(dict(call_mode='scripted',routed=[dict(id=str(i),row={}) for i in range(32)])))
        calls=[]
        def generate(model,processor,batch,**kw):
            calls.append(4 if isinstance(batch,list) else 1)
            r=record()
            if isinstance(batch,list):r['text']=r['text'].replace('\nA','\nB')
            return [deepcopy(r) for _ in batch] if isinstance(batch,list) else r
        base=NS(_batch=lambda *a:({},), _backend=lambda *a:NS(mask_source='svp_sam3'),document=lambda *a:{})
        adapter=NS(base=base,load=lambda *a:(torch.nn.Linear(1,1).bfloat16(),NS()))
        with patch.dict(sys.modules,acceptance_live_adapter=adapter), \
             patch.object(torch.cuda,'device_count',return_value=1), \
             patch.object(D,'generate',side_effect=generate), \
             patch('student_pilot.live_trace313.LiveSession',side_effect=lambda b:NS(memory_hits=[True])), \
             patch('student_pilot.live_trace313.check_record'), \
             patch.object(sys,'argv',['stage','--inputs',str(inputs),'--out',str(tmp/'out'),'--call-mode','scripted']):
            with self.assertRaisesRegex(AssertionError,'parity failed'):module.main()
        self.assertEqual(calls.count(1),64);self.assertEqual(calls.count(4),16)
        result=json.loads((tmp/'out/COMPARISON.json').read_text())
        self.assertEqual(result['pooled']['acceptance_failures'],32)
        for name in ('b1.json','b1_repeat.json','b4.json','RESULT.json','memory/0/COMPARISON.json'):
            self.assertTrue((tmp/'out'/name).is_file())


class NativeFP32(unittest.TestCase):
    def test_free_greedy_ragged_prompts_and_compaction_exact_records(self):
        for seed in (1,7,19,31):
            model,p,batch=fixture();rows=varied(batch)
            self.assertEqual(next(model.parameters()).dtype,torch.float32)
            torch.manual_seed(seed)
            with torch.no_grad():model.lm_head.weight.normal_(0,.04)
            def greedy(limit):
                def choose(ids,logits):
                    logits=logits.clone();logits[:,30:]=-float('inf');logits[:,1]=-float('inf')
                    if len(ids)>=limit:logits[:]=-float('inf');logits[:,1]=0
                    return logits
                return choose
            single=[D.generate(model,p,row,logits_processor=greedy(12+3*i)) for i,row in enumerate(rows)]
            batched=D.generate(model,p,rows,logits_processor=[greedy(12+3*i) for i in range(4)])
            self.assertEqual(single,batched,seed)

    def test_torch_fallback_positions_and_no_recurrent_padding(self):
        model,p,batch=fixture();rows=varied(batch)
        scripts=[[42,1],[42,40,41,49,1],[45,46,47,48,32,1],[42,42,40,37,36,1]]
        traces=[];sizes=[]
        original=D.consume_cache_tokens
        def consume(native,ids,mask,cache,**kw):
            self.assertTrue(bool(mask[:,-1].all()))
            position=native._prepare_position_ids_for_generation(ids,dict(attention_mask=mask,past_key_values=cache))
            expected=mask.long().sum(-1)-1+native.model.rope_deltas.flatten()
            self.assertTrue(torch.equal(position[:,:,-1],expected.expand_as(position[:,:,-1])))
            sizes.append(ids.shape[0])
            return original(native,ids,mask,cache,**kw)
        linear=model.model.language_model.layers[0].linear_attn
        # Explicitly execute the installed torch implementations, regardless of optional kernels.
        from transformers.models.qwen3_5 import modeling_qwen3_5 as Q
        def recurrent(*args,**kw):
            traces.append(args[0].shape[:2] if args else kw['query'].shape[:2])
            return Q.torch_recurrent_gated_delta_rule(*args,**kw)
        with patch.object(linear,'recurrent_gated_delta_rule',side_effect=recurrent), \
             patch.object(linear,'causal_conv1d_update',Q.torch_causal_conv1d_update), \
             patch.object(linear,'chunk_gated_delta_rule',Q.torch_chunk_gated_delta_rule), \
             patch.object(D,'consume_cache_tokens',side_effect=consume):
            single=[D.generate(model,p,row,logits_processor=Script(script)) for row,script in zip(rows,scripts)]
            batched=D.generate(model,p,rows,logits_processor=[Script(s) for s in scripts])
        self.assertEqual(single,batched)
        self.assertTrue(traces);self.assertTrue(all(s[1]==1 for s in traces))
        self.assertTrue({1,2,3,4}.issubset(set(sizes)))


if __name__=='__main__':
    torch.set_num_threads(1)
    unittest.main(verbosity=2)
