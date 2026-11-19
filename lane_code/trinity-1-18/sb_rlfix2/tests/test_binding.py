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
    def test_replay_selects_only_recorded_four_per_type(self):
        from collections import Counter
        from rl_on_n.replay import selection,TYPES
        rows=selection()
        self.assertEqual(Counter(r['item']['question_type'] for r in rows),dict.fromkeys(TYPES,4))
        self.assertTrue(all(r['expected']['tokens'] for r in rows))
        P.write('out/REPLAY_SELECTION.json',dict(status='SELECTED_NOT_RUN',
                counts=dict(Counter(r['item']['question_type'] for r in rows)),
                items=[dict(id=r['item']['id'],journal=r['journal'],journal_sha256=r['journal_sha256']) for r in rows],
                command='bash scripts/run_tests.sh'))
