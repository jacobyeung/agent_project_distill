import copy
import os
from pathlib import Path
import unittest
import torch
from rl_on_n import provenance as P
ROOT=Path(os.environ.get('N_TREE','/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1'))
P.tree(ROOT)
from rl_on_n.reward import score,Weights
from rl_on_n.pool import build
from rl_on_n.loss import attach,group_advantages
from rl_on_n.grpo_math import token_terms,settings
from rl_on_n.adapters import install,reference,LowRank
from student_pilot.r1_rooms import Rooms,AUTHORITY
from student_pilot.r2_withheld import Withheld
from student_pilot.r0_exclusion import reserve

class Tokenizer:
    def encode(self,text,**kw): return text.split()

class Rewards(unittest.TestCase):
    def setUp(self):
        self.tok=Tokenizer(); self.routes={'camera_displacement':'route','room_size_estimation':'direct','object_abs_distance':'route'}
        self.prompt=dict(type='room_size_estimation',gt_answer='10',options=[])
    def rec(self,text,**kw):return dict(text=text,calls=[],finish='eos',**kw)
    def test_correct_incorrect_numeric(self):
        for answer,c in [('10',1.),('100',0.)]:
            r=score(self.prompt,self.rec('Locate: room in frame 1.\n</think>\n'+answer),self.tok,self.routes)
            self.assertEqual(r['correct'],c)
    def test_zero_mra_uses_native_scorer(self):
        self.prompt['gt_answer']='0'
        self.assertEqual(score(self.prompt,self.rec('</think>0'),self.tok,self.routes)['correct'],1)
    def test_choice_exact(self):
        self.prompt.update(gt_answer='A',options=['A. left','B. right'])
        for answer,c in [('A',1),('B',0)]:
            self.assertEqual(score(self.prompt,self.rec('Locate: room.\n</think>'+answer),self.tok,self.routes)['correct'],c)
    def test_short_long_and_response_free(self):
        a=score(self.prompt,self.rec('Locate: room.\n</think>10'),self.tok,self.routes)
        b=score(self.prompt,self.rec('room '*1100+'</think>10'),self.tok,self.routes)
        self.assertGreater(a['short'],b['short']);self.assertEqual(b['short'],0)
        r=self.rec('Locate: room.<tool_response>'+'x '*2000+'</tool_response></think>10')
        self.assertLess(score(self.prompt,r,self.tok,self.routes)['thought_tokens'],10)
    def test_budget_cannot_earn_short(self):
        r=self.rec('room</think>10',budget_hit=True)
        self.assertEqual(score(self.prompt,r,self.tok,self.routes)['short'],0)
    def test_routed_missing_spurious(self):
        call=dict(call='<move from=1 to=2>',response='distance=1',kind='move')
        r=self.rec('Call: <move from=1 to=2><tool_response>distance=1</tool_response>\n</think>10');r['calls']=[call]
        self.prompt['type']='camera_displacement'
        self.assertEqual(score(self.prompt,r,self.tok,self.routes)['route'],1)
        self.assertEqual(score(self.prompt,self.rec('Locate: camera.\n</think>10'),self.tok,self.routes)['route'],0)
        self.prompt['type']='room_size_estimation'
        self.assertEqual(score(self.prompt,r,self.tok,self.routes)['route'],0)
        self.assertEqual(score(self.prompt,self.rec('Locate: room.\n</think>10'),self.tok,self.routes)['route'],1)
    def test_call_after_answer_and_unforced_response_refuse(self):
        self.prompt['type']='camera_displacement'
        call=dict(call='<move from=1 to=2>',response='distance=1',kind='move')
        for text in ['</think>10<move from=1 to=2><tool_response>distance=1</tool_response>',
                     '<move from=1 to=2><tool_response>distance=999</tool_response></think>10']:
            r=self.rec(text);r['calls']=[call]
            self.assertEqual(score(self.prompt,r,self.tok,self.routes)['route'],0)
    def test_failed_or_wrong_head_no_credit(self):
        self.prompt['type']='camera_displacement'
        r=self.rec('<move from=1 to=2><tool_response>error: bad_frame</tool_response></think>10')
        r['calls']=[dict(call='<move from=1 to=2>',response='error: bad_frame',kind='error')]
        self.assertEqual(score(self.prompt,r,self.tok,self.routes)['route'],0)
    def test_ground_gap_sequence_and_failed_gap(self):
        self.prompt['type']='object_abs_distance'
        calls=[dict(call='<ground obj="chair">',response='P1',kind='ground'),
               dict(call='<ground obj="table">',response='P2',kind='ground'),
               dict(call='<gap a="chair" b="table" rule="sampled_box_512">',response='gap=1',kind='gap')]
        def record(calls):
            text=''.join(c['call']+'<tool_response>'+c['response']+'</tool_response>' for c in calls)
            return dict(text=text+'</think>10',calls=calls,finish='eos')
        self.assertEqual(score(self.prompt,record(calls),self.tok,self.routes)['route'],1)
        self.assertEqual(score(self.prompt,record(calls[:-1]),self.tok,self.routes)['route'],0)
        self.assertEqual(score(self.prompt,record([calls[2],*calls[:2]]),self.tok,self.routes)['route'],0)
        calls[-1].update(kind='error',response='error: unavailable')
        self.assertEqual(score(self.prompt,record(calls),self.tok,self.routes)['route'],0)
    def test_unclosed_thought_cannot_supply_answer(self):
        self.assertEqual(score(self.prompt,self.rec('10'),self.tok,self.routes)['correct'],0)
    def test_weights(self):
        r=score(self.prompt,self.rec('room</think>10'),self.tok,self.routes,Weights(2,0,0))
        self.assertEqual(r['total'],2)
        with self.assertRaises(ValueError):Weights(short=-1)

class RealRoomGate:
    def __init__(self):
        base=ROOT.parents[1]/'work/build18/inputs'
        self.rooms=Rooms({k:P.pin(base/(v+'.json')) for k,v in AUTHORITY.items()})
        self.withheld=Withheld();self.reserve=reserve()
    def admit(self,row):
        self.rooms.admit(row);self.reserve.check(row,'test')
        canonical,_=self.rooms.canonical(row)
        if self.withheld.touches(row,{'names':[canonical]}):raise ValueError('RL_WITHHELD_ROOM_REFUSED')

class PoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate=RealRoomGate()
        data=P.load(ROOT.parents[1]/'work/build18/inputs'/ (AUTHORITY['split']+'.json'))
        cls.captures=data['teacher_k1']['captures']
    def row(self,canonical,qid='fixture'):
        ds,scene=canonical.split('/',1)
        return dict(qid=qid,dataset=ds,scene=scene,canonical=canonical,question_type='object_counting',answer='2',
                    target='<think>fixture only</think>2',student_input=dict(question='How many chairs?',frame_indices=list(range(32))))
    def training(self):
        for c in self.captures:
            # Read an existing canonical capture, never infer a native/alias mapping.
            canonical=c.get('canonical') or c.get('capture')
            if not canonical or '/' not in canonical:continue
            row=self.row(canonical)
            try:self.gate.admit(row)
            except ValueError:continue
            return row
        raise AssertionError('No supplied known training capture found')
    def test_heldout_pool_refuses(self):
        data=P.load(ROOT/'student_pilot/r2_withheld.json')
        name=data['rooms'][0]
        # Physical ScanNet room test uses its listed alias when available.
        aliases=data['aliases'].get(name,[])
        capture=next((v for v in [name,*aliases] if not v.startswith('scannet/') or '_' in v),name)
        with self.assertRaises(ValueError):build([('vqa',0,self.row(capture))],self.gate,{'object_counting':'direct'})
    def test_k1_and_r0_refuse(self):
        for room in (sorted(self.gate.rooms.k1)[0],sorted(self.gate.rooms.r0)[0]):
            with self.assertRaises(ValueError):self.gate.rooms.admit(self.row(room))
    def test_unknown_room_refuses(self):
        with self.assertRaises(ValueError):self.gate.admit(dict(dataset='unknown',scene='unresolved'))
    def test_pool_deterministic(self):
        row=self.training();rows=[]
        for i in range(5):r=copy.deepcopy(row);r['qid']=f'fixture-{i}';rows.append(('vqa',i,r))
        a=build(rows,self.gate,{'object_counting':'direct'})
        b=build(list(reversed(rows)),self.gate,{'object_counting':'direct'})
        self.assertEqual(P.canonical(a),P.canonical(b))
        self.assertNotIn('target',a[0]['row']);self.assertNotIn('answer',a[0]['row'])
    def test_duplicate_refuses(self):
        row=self.training()
        with self.assertRaises(ValueError):build([('vqa',0,row),('vqa',1,row)],self.gate,{'object_counting':'direct'})

class LossTests(unittest.TestCase):
    def test_masks(self):
        b=dict(input_ids=torch.tensor([[1,2]]),attention_mask=torch.ones(1,2,dtype=torch.long))
        r=dict(tokens=[3,4,5,6],kinds=['f','r','s','b'],logp_tempered=[0,None,-2,0])
        result=attach(b,r,[7]);self.assertEqual(result['pg_mask'].tolist(),[[False,False,False,False,True,False]])
    def test_kl_clip_and_backward(self):
        x=torch.tensor([-.5,-1.],requires_grad=True);old=torch.tensor([-1.,-1.]);ref=torch.tensor([-1.,-2.])
        terms,ratio,kl=token_terms(x,old,ref,torch.tensor([1.,-1.]),settings({}))
        terms.mean().backward();self.assertTrue(torch.isfinite(x.grad).all());self.assertTrue((kl>=0).all())
    def test_tied_group_zero(self):self.assertEqual(group_advantages([1,1]).tolist(),[0,0])
    def test_reference_is_immutable(self):
        layer=LowRank(torch.nn.Linear(3,4),2,4);x=torch.ones(1,3)
        a=layer(x).detach();layer.b.data.fill_(1)
        self.assertFalse(torch.equal(a,layer(x)))
        with reference(layer):self.assertTrue(torch.equal(a,layer(x)))

if __name__=='__main__':unittest.main()
