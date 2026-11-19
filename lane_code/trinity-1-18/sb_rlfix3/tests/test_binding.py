"""CPU regressions for the deployed reader contract."""
from types import SimpleNamespace
import unittest
import torch
from rl_on_n import provenance as P
from rl_on_n.serving import load_binding, budget, call_caps
from rl_on_n.rollout import SamplingProcessor, capped_hook, MaxCalls
from rl_on_n.pool import build
from rl_on_n.reward import score
from test_kit import Tokenizer

class BudgetTokenizer:
    eos_token_id=0
    def encode(self,text,**kw):
        return {'</think>':[2],'\n</think>\n\n':[3,2,3]}.get(text,[1])
    def decode(self,ids,**kw):return ''.join({0:'EOS',1:'x',2:'</think>',3:'\n'}.get(i,'x') for i in ids)
    def convert_ids_to_tokens(self,i):return self.decode([i])
    def convert_tokens_to_ids(self,t):return {'<tool_response>':4,'</tool_response>':5}[t]

class Binding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):load_binding()
    def test_deployed_budget_and_sampling_order(self):
        processor=SimpleNamespace(tokenizer=BudgetTokenizer(),_routing_tokens={'ids':{}})
        b=budget(processor);s=SamplingProcessor(b,seed=17,greedy=True)
        ids=[];logits=torch.tensor([[0.,10.,0.,0.,0.,0.]])
        for _ in range(2048+3+64+1):ids.append(int(s(ids,logits).argmax()))
        self.assertEqual(ids[:2048],[1]*2048)
        self.assertEqual(ids[2048:2051],[3,2,3])
        self.assertEqual(ids[2051:-1],[1]*64);self.assertEqual(ids[-1],0)
        self.assertEqual(s.kinds[2048:2051],['b']*3);self.assertEqual(s.kinds[-1],'b')
        self.assertEqual(s.kinds.count('s'),2112)
        self.assertEqual(b.receipt(len(ids))['forced_budget_tokens'],4)
    def test_cap_reaching_call_is_not_served(self):
        processor=SimpleNamespace(tokenizer=BudgetTokenizer(),_routing_tokens={'ids':{}})
        self.assertEqual(call_caps(),{'object_abs_distance':6,'room_size_estimation':2})
        for typ,n in call_caps().items():
            hook=capped_hook(processor,typ);hook.begin({})
            for _ in range(n-1):hook.respond('<pose frame=1>')
            with self.assertRaises(MaxCalls):hook.respond('<pose frame=1>')
            self.assertEqual(sum(hook.counts.values()),n)
            self.assertEqual(len(hook.records),n);self.assertFalse(hook.records[-1]['served'])
            self.assertNotIn('forced_tokens',hook.records[-1])
    def test_partial_correctness_scales_both_auxiliaries(self):
        r=score(dict(type='room_size_estimation',gt_answer='12.19'),
                dict(text='room</think>7',calls=[],finish='eos'),Tokenizer(),{'room_size_estimation':'direct'})
        self.assertAlmostEqual(r['correct'],.2);self.assertAlmostEqual(r['short'],.2)
        self.assertAlmostEqual(r['route'],.2);self.assertAlmostEqual(r['total'],.24)
    def test_pool_checks_raw_and_clean_prompt_ids(self):
        seen=[]
        def encode(row):
            seen.append(row)
            return dict(input_ids=[[1,int(bool(row.get('pose_sample')))]] )
        row=dict(qid='fixture',question_type='room_size_estimation',answer='1',pose_sample=True,
                 student_input=dict(frame_indices=list(range(32))))
        with self.assertRaisesRegex(ValueError,'changes native prompt ids'):
            build([('vqa',0,row)],SimpleNamespace(admit=lambda r:None),{'room_size_estimation':'direct'},prompt_encoder=encode)
        self.assertEqual(len(seen),2);self.assertNotIn('answer',seen[1])
    def test_sealed_native_geometry_and_namespace_restore(self):
        import sys
        from rl_on_n.serving import reader_runtime,PAYLOAD
        from student_pilot import geometry_profiles as original
        with reader_runtime():
            from student_pilot import geometry_profiles as sealed
            from e2e_reader.geometry import reader_contract
            self.assertTrue(str(sealed.__file__).startswith(str(PAYLOAD)))
            self.assertIsNot(sealed,original)
            self.assertTrue(issubclass(reader_contract(sealed),sealed.GeometryContract))
        self.assertIs(sys.modules['student_pilot.geometry_profiles'],original)
    def test_replay_selects_types_gap_calls_and_forced_close(self):
        from collections import Counter
        from rl_on_n.replay import selection,TYPES,REQUIRED,COUNTS,exercises,call_records
        rows=selection()
        self.assertEqual(Counter(r['group'] for r in rows),COUNTS)
        self.assertEqual(len(rows),26)
        for typ in TYPES:
            self.assertEqual([r['item']['question_type'] for r in rows if r['group']==typ],[typ]*4)
        for group,ids in REQUIRED.items():
            self.assertEqual(tuple(r['item']['id'] for r in rows if r['group']==group),ids)
        for r in rows:
            self.assertTrue(r['expected']['tokens'])
            self.assertTrue(exercises(r['group'],r['expected']))
        gap=[r for r in rows if r['group']=='gap']
        self.assertTrue(all('gap' in [c['family'] for c in call_records(r['expected'])] for r in gap))
        fired=[r for r in rows if r['group']=='budget_fired']
        self.assertTrue(all(r['expected']['decode_budget']['fired'] for r in fired))
        self.assertFalse(exercises('gap',dict(calls=[dict(family='ground')])))
        self.assertFalse(exercises('budget_fired',dict(decode_budget=dict(fired=False))))
        P.write('out/REPLAY_SELECTION.json',dict(status='SELECTED_NOT_RUN',counts=dict(Counter(r['group'] for r in rows)),
                items=[dict(id=r['item']['id'],group=r['group'],type=r['item']['question_type'],
                            journal=r['journal'],journal_sha256=r['journal_sha256']) for r in rows],
                command='bash scripts/run_tests.sh'))
    def test_replay_refuses_staged_m544_as_m200(self):
        from rl_on_n.replay import check_export
        settings=load_binding()
        with self.assertRaisesRegex(ValueError,'MISSING A4 m200 export'):
            check_export(settings['export_dir'],settings['config'])
    def test_replay_native_mapping_uses_recorded_items(self):
        from rl_on_n.replay import selection
        from rl_on_n.serving import reader_runtime
        selected=selection();items=[r['item'] for r in selected]
        settings=load_binding()
        with reader_runtime():
            from h1eval.h10.parity_adapter import map_items
            mapped,receipt=map_items(items,settings)
        self.assertEqual(set(mapped),{r['id'] for r in items})
        self.assertEqual(len(receipt['items']),26)
