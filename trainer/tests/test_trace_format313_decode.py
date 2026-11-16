"""Decoder-format parity with the pinned v3.13 generator, including B4 routing."""
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import json,re,copy
from pathlib import Path
import numpy as np
import torch
from transformers.cache_utils import DynamicCache
from student_pilot import carrier_c1_decode as D, ground_lifting
from trace_format.ground_v313 import Session
from tests.test_carrier_c1_final import FakeTokenizer
from test_v312_ground import Geometry,masks

class FormatTests(unittest.TestCase):
    @staticmethod
    def session(keypoints=False):
        def instances(name):
            m,p=masks(name)
            return [dict(instance_id=name,masks=m,prob=p)] if m.any() else []
        return Session(ground_lifting,Geometry(),masks,instances=instances,keypoint_calls=keypoints)

    def run_rows(self,scripts,sessions=None,extra_words=None):
        class Tok(FakeTokenizer):
            words={**FakeTokenizer.words,30:'<ground obj="stand">',31:'<ground obj="face">',
                32:'<gap a="stand" b="face">',33:'<ground obj="stand" mode="instances">',
                34:'<surface_pair a="stand" b="face" mode="closest_visible">',
                35:'<extent_ends obj="stand" axis="longest_observed">'}
        Tok.words.update(extra_words or {})
        p=NS(tokenizer=Tok(),_routing_tokens={'ids':{}})
        model=NS(training=False,carrier_id=5,model=NS(rope_deltas=None));logits=torch.zeros(1,1,64)
        def prepare(model,p,batch,**kwargs):
            n=batch['input_ids'].shape[1];model.model.rope_deltas=torch.zeros(1,1,dtype=torch.long)
            cache=DynamicCache([(torch.zeros(1,1,n,1),torch.zeros(1,1,n,1))])
            heads=NS(pose9=np.zeros((32,9)),gravity=None,queries=[],grounding_head=None,mdg_backend=None,
                     ground=lambda *a: (_ for _ in ()).throw(AssertionError('legacy ground invoked')))
            return NS(native=NS(generation_config=NS(eos_token_id=1)),output=NS(logits=logits,past_key_values=cache),
                heads=heads,geometry=None,geometry_error=None,prompt_length=n,cap=5000,tokenizer=p.tokenizer,
                openers=set(),mdg=None,stream=None,ground_backend=None,verify_session=None,rereader=None)
        shapes=[]
        def consume(native,ids,mask,cache,**kw):
            shapes.append(len(ids));n=ids.shape[1]-cache.get_seq_length();v=torch.zeros(len(ids),1,n,1)
            cache.update(v,v.clone(),0);return NS(logits=logits.expand(len(ids),-1,-1)),cache
        def force(script):
            it=iter(script)
            return lambda ids,logits:NS(argmax=lambda dim:torch.tensor(next(it)))
        batches=[dict(input_ids=torch.ones(1,4+i,dtype=torch.long),attention_mask=torch.ones(1,4+i,dtype=torch.long)) for i in range(len(scripts))]
        sessions=sessions or [self.session(keypoints=True) for _ in scripts]
        references=copy.deepcopy(sessions,{id(s.backend):s.backend for s in sessions})
        with patch.object(D,'_prepare_decode',side_effect=prepare),patch.object(D,'consume_cache_tokens',side_effect=consume):
            records=D.generate(model,p,batches,trace_session=sessions,logits_processor=[force(s) for s in scripts])
        self.assertIsNone(D.trace313._current.get());self.assertIsNone(D.trace313._rows.get())
        for script,record,reference in zip(scripts,records,references):
            expected=[reference.execute(p.tokenizer.words[t]) for t in script if t!=1]
            self.assertEqual([c['response'] for c in record['calls']],expected)
            self.assertEqual(record['finish'],'eos')
            for c in record['calls']:
                self.assertEqual(c['forced_tokens'],len(p.tokenizer.encode('\n<tool_response>\n'+c['response']+'\n</tool_response>')))
        return records,shapes

    def test_b4_two_ground_gap_witness_and_independent_registries(self):
        rows,shapes=self.run_rows([[30,31,32,1]]*4)
        self.assertIn(4,shapes)
        self.assertTrue(all('P3: stand nearest point' in r['calls'][-1]['response'] for r in rows))
        self.assertTrue(all('P4: face nearest point' in r['calls'][-1]['response'] for r in rows))

    def test_instance_and_keypoint_tags_use_trained_response_layout(self):
        rows,_=self.run_rows([[33,1],[30,31,34,1],[30,35,1],[34,1]])
        self.assertIn('stand: 1 found',rows[0]['calls'][0]['response'])
        self.assertEqual(rows[1]['calls'][-1]['response'],'unavailable')
        self.assertEqual(rows[2]['calls'][-1]['response'],'unavailable')
        self.assertEqual(rows[3]['calls'][-1]['response'],'not seen')

    def test_r4_fixture_roundtrip_with_private_measurement_audit(self):
        from trace_format import box_v313 as boxes
        root=Path(__file__).resolve().parents[3]
        fixture=root/'inputs/spec313_kp/fixtures_r4/absolute_sampled_box.jsonl'
        with fixture.open() as stream:row=json.loads(next(stream))
        events=row['events'];objects={};private={}
        for event in events[:-1]:
            name=re.search(r'obj="([^"]+)"',event['call'])[1]
            match=re.search(r'frames ([0-9,]+) \(best ([0-9]+)\)',event['response'])
            frames=list(map(int,match[1].split(',')));best=int(match[2])
            objects[name]=[dict(frames=frames,visible=frames,areas={str(k):2 if k==best else 1 for k in frames})]
            private[name]=event['audit']['full_precision_box']
        class Provider:
            provider_id=events[0]['audit']['box_provider']
            def __call__(self,name,obj,geometry,best):return private[name]
        session=self.session();session.box_provider=Provider();session.box_provider_id=Provider.provider_id
        session._instances=lambda name:objects[name]
        words={50+i:event['call'] for i,event in enumerate(events)}
        records,_=self.run_rows([[*words,1]],sessions=[session],extra_words=words)
        actual=records[0]['calls']
        for event,call in zip(events,actual):
            self.assertEqual('<tool_response>\n'+call['response']+'\n</tool_response>',event['response'])
            expected=copy.deepcopy(event['audit']);expected['numpy_version']=np.__version__
            self.assertEqual(call['audit'],expected);self.assertEqual(call['spec_revision'],5)
        self.assertEqual(session.registry._points,{})
        replay=[dict(call=c['call'],response='<tool_response>\n'+c['response']+'\n</tool_response>',audit=c['audit']) for c in actual]
        np.testing.assert_allclose(boxes.replay_audit(replay),row['program_audit']['unrounded_replay_m'],rtol=0,atol=1e-14)
        self.assertEqual(boxes.number(boxes.replay_audit(replay)[0],2),row['answer'])
        (root/'out/TRACE_R4_ROUNDTRIP.json').write_text(json.dumps(dict(status='PASS',qid=row['qid'],calls=actual,unrounded_m=boxes.replay_audit(replay)))+'\n')

    def test_sessions_cannot_be_shared_across_rows(self):
        session=self.session()
        with self.assertRaisesRegex(ValueError,'distinct'):
            D.generate(None,None,[{},{}],trace_session=[session,session])

    def test_hrp_and_trace_producers_cannot_silently_override(self):
        with self.assertRaisesRegex(ValueError,'separate calls'):
            D.generate(None,None,{},trace_session=self.session(),reread=object())

if __name__=='__main__':unittest.main()
