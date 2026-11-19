import copy
import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import torch
from rl_on_n import provenance as P
from test_kit import ROOT, Tokenizer
from rl_on_n.pool import RoomGate,build,clean_row
from rl_on_n.reward import score
from rl_on_n.rollout import native_kwargs,sample,refused
from rl_on_n.train import backward_draw,zero_gradients,average_gradients,checkpoint_due,save_checkpoint
from rl_on_n.grpo_math import group_advantages
from rl_on_n.loss import Objective
from evalpath.run import score_item
from parity_cases import cases as review_cases

BASE=ROOT.parents[1]/'work/build18/inputs'

class Parity(unittest.TestCase):
    def test_official_formats(self):
        routes=P.load(BASE/'config.json')['route_table']
        own=[]
        for typ,gt,opts in [('room_size_estimation','12.19',[]),('camera_movement_direction','B',[]),
                             ('object_rel_direction_easy','B',['A. left','B. right'])]:
            for ans in ('', '  B  ', 'b)', 'B\nextra','12.19e0','nan','inf','-12.19','0','12.19\nB',
                        '<answer>12.19</answer>','１２.１９'):
                own.append((typ,gt,opts,ans))
        mismatches=[]
        for i,(typ,gt,opts,ans) in enumerate([*review_cases,*own]):
            text='I look at the frames.\n</think>\n\n'+ans+'<|im_end|>'
            record=dict(text=text,calls=[],finish='eos')
            actual=score(dict(type=typ,gt_answer=gt,options=opts),record,Tokenizer(),routes)['correct']
            expected=score_item(dict(question_type=typ,ground_truth=gt,options=opts),record)['score']
            if actual!=expected:mismatches.append(dict(index=i,actual=actual,expected=expected))
        P.sha('/scratch/jjyeung/orch_n30/sb_rlrev/runs/parity.py')
        P.write('out/PARITY.json',dict(review_cases=len(review_cases),additional_cases=len(own),
                mismatches=mismatches,command='bash scripts/run_tests.sh'))
        self.assertEqual(len(review_cases),74);self.assertEqual(mismatches,[])

    def test_no_wrong_or_duplicate_close_auxiliaries(self):
        prompt=dict(type='room_size_estimation',gt_answer='10')
        for text in ('short</think>100','short</think>'+'long '*1500+'</think>10',
                     'short</think>long</THINK>10','short</think>long</think >10'):
            r=score(prompt,dict(text=text,finish='eos',calls=[]),Tokenizer(),{prompt['type']:'direct'})
            self.assertEqual((r['short'],r['route']),(0.,0.))
        self.assertEqual(group_advantages([0,0,0,0],scale_std=False).tolist(),[0]*4)
        self.assertTrue(torch.allclose(group_advantages([1.2,0,0,0],scale_std=False),torch.tensor([.9,-.3,-.3,-.3],dtype=torch.float64)))

    def test_exact_kinds(self):
        calls=[dict(call='<move from=1 to=2>',response='distance=1',kind='move'),
               dict(call='<pose frame=1>',response='pose',kind='pose')]
        text=''.join(c['call']+'<tool_response>'+c['response']+'</tool_response>' for c in calls)+'</think>10'
        r=score(dict(type='camera_displacement',gt_answer='10'),dict(text=text,calls=calls,finish='eos'),
                Tokenizer(),{'camera_displacement':'route'})
        self.assertEqual(r['route'],0)

class ProductionGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=P.load(BASE/'config.json');cls.gate=RoomGate(cls.cfg)
        cls.split=P.load(BASE/'27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390.json')
    def row(self,name,qid='probe'):
        ds,scene=name.split('/',1)
        return dict(qid=qid,dataset=ds,scene=scene,question_type='object_counting',answer='2',
                    student_input=dict(question='How many chairs?',frame_indices=list(range(32))))
    def test_all_pinned_lists(self):
        dev=P.load(self.cfg['dev_scene_exclusions']['path']);bench=P.load(self.cfg['benchmark_scene_exclusions']['path'])
        withheld=P.load(ROOT/'student_pilot/r2_withheld.json')
        reserve=BASE/'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3.json'
        P.sha(reserve)
        groups=dict(
            k1_heldout=[c['canonical'] for c in self.split['teacher_k1']['captures'] if c['k1_split']=='heldout'],
            r0_dev=[k for k,v in self.split['r0_scenes']['captures'].items() if v['r0_split']=='R0-dev'],
            r0_rl=[k for k,v in self.split['r0_scenes']['captures'].items() if v['r0_split']=='R0-rl'],
            reserve_rooms=reserve.read_text().splitlines(),
            withheld80=list(withheld['rooms'])+[a for v in withheld['aliases'].values() for a in v],
            dev_s1=list(dev['natives'])+list(dev['rooms'])+[a for v in dev['aliases'].values() for a in v]+[a for v in dev['canonical'].values() for a in v],
            bench_v2=list(bench['scenes'])+[f'{d}/{t}' for d,t in bench['rung1_tokens']])
        counts={}
        for label,names in groups.items():
            names=set(n.strip() for n in names if n.strip());admitted=[]
            for i,name in enumerate(sorted(names)):
                try:build([('vqa',i,self.row(name))],self.gate,{'object_counting':'direct'},prompt_encoder=lambda row:dict(input_ids=[[1]]))
                except ValueError:continue
                admitted.append(name)
            counts[label]=dict(checked=len(names),admitted=len(admitted))
            self.assertEqual(admitted,[],label)
        controls=[c['canonical'] for c in self.split['teacher_k1']['captures'] if c['k1_split']=='train']
        for name in controls:self.gate.admit(self.row(name))
        physical=set(bench['physical_groups'])|set(dev['physical_groups'])|set(dev['rooms'])
        physical={n.replace('d1/','scannet/').replace('d2/','scannetpp/').replace('d3/','arkitscenes/') for n in physical}
        hits=[c for c in controls if self.gate.rooms.room(c) in physical]
        self.assertEqual(hits,[])
        P.write('out/GATE_CHECK.json',dict(groups=counts,admitted_controls=len(controls),physical_overlap=len(hits),
            reserve_policy='Refuse the entire pinned R0 reserve; deliberately stricter than heldout-only exclusion',
            command='bash scripts/run_tests.sh'))
    def test_remove_lists(self):
        control=next(c['canonical'] for c in self.split['teacher_k1']['captures'] if c['k1_split']=='train')
        count=0
        for keys in self.gate.removals.keys:
            for key in keys:
                row=self.row(control);row['row_key']=key
                with self.assertRaisesRegex(ValueError,'REMOVE-listed'):self.gate.admit(row)
                count+=1
        self.assertGreater(count,0)
        P.write('out/REMOVE_CHECK.json',dict(checked=count,command='bash scripts/run_tests.sh'))
    def test_nested_allowlist(self):
        row=self.row(next(c['canonical'] for c in self.split['teacher_k1']['captures'] if c['k1_split']=='train'))
        for key in ('gt_answer','source_gt_answer','answer_content','tool_output_spans','unknown_future_label'):
            row[key]='SECRET';row['student_input'][key]='SECRET'
        row['routing']=dict(question_type='object_counting',answer='SECRET',tool_output_spans='SECRET')
        row['student_input']['frames']=[dict(path='/scratch/frame',sha256='a'*64,answer='SECRET')]
        result=build([('vqa',0,row)],self.gate,{'object_counting':'direct'},prompt_encoder=lambda row:dict(input_ids=[[1]]))[0]
        self.assertNotIn('SECRET',P.canonical(result['row']))
        self.assertEqual(result['gt_answer'],'2');self.assertEqual(result['row'],clean_row(row))

class FailureHandling(unittest.TestCase):
    def test_native_signature(self):
        from rl_on_n.serving import load_binding
        load_binding()
        from e2e_reader.real import generate_real
        processor=SimpleNamespace(tokenizer=Mock(),_routing_tokens={'ids':{}})
        with patch('rl_on_n.rollout.reader_frames',return_value={}):
            kw=native_kwargs(processor,dict(row={},type='room_size_estimation',prompt_id='fixture'),{},
                             dict(artifact=None,perception=Mock()))
        inspect.signature(inspect.unwrap(generate_real)).bind(1,2,3,budget=None,max_new_tokens=16384,**kw)
        self.assertNotIn('pose_source',kw)
    def test_missing_serving_binding_refuses(self):
        from rl_on_n.serving import load_binding
        with self.assertRaisesRegex(ValueError,'MISSING grounding.serving_table'):load_binding({})
    def test_refusals_do_not_align_or_backward(self):
        from rl_on_n.serving import load_binding
        load_binding()
        from student_pilot.carrier_c1_batch_decode import RowRefusal
        from student_pilot.tower_errors import TowerError
        tok=SimpleNamespace(encode=lambda *a,**k:[],eos_token_id=1)
        for failure in (RowRefusal('max calls'),TowerError('bad pose')):
            with patch('e2e_reader.real.generate_real',side_effect=failure), \
                 patch('rl_on_n.serving.budget',return_value=Mock()), \
                 patch('rl_on_n.rollout.align') as aligned:
                record=sample(Mock(),SimpleNamespace(tokenizer=tok),{},decode={})
                aligned.assert_not_called()
            self.assertTrue(record['refusal'])
            self.assertEqual(score({},record,tok,{})['total'],0)
            objective=Mock()
            self.assertIsNone(backward_draw(None,objective,None,record,0,[],.7,4))
            objective.assert_not_called()
    def test_dense_preparation_errors_are_typed(self):
        from rl_on_n.rollout import reader_frames
        from student_pilot.tower_errors import TowerError
        with self.assertRaises(TowerError):
            reader_frames(dict(student_input=dict(frames=[],frame_indices=[])),{})
    def test_zero_local_gradients_participate(self):
        parameters=[torch.nn.Parameter(torch.ones(2)),torch.nn.Parameter(torch.ones(3))]
        zero_gradients(parameters)
        with patch('torch.distributed.all_reduce',side_effect=lambda g:g.add_(2)) as reduce:
            average_gradients(parameters,4)
        self.assertEqual(reduce.call_count,2)
        for p in parameters:self.assertTrue(torch.equal(p.grad,torch.full_like(p,.5)))
    def test_checkpoint_cadence_and_content(self):
        from rl_on_n.adapters import LowRank
        self.assertEqual([s for s in range(1,62) if checkpoint_due(s,61)],[25,50,61])
        model=LowRank(torch.nn.Linear(2,2),1,2)
        opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad])
        model(torch.ones(1,2)).sum().backward();opt.step()
        output=Path('out/checkpoint_test');output.mkdir(exist_ok=True)
        save_checkpoint(model,opt,output,25)
        saved=torch.load(output/'checkpoint_000025.pt',weights_only=True)
        self.assertEqual(saved['step'],25);self.assertTrue(saved['adapters']);self.assertTrue(saved['optimizer']['state'])
    def test_diagnostic_arm_cannot_score(self):
        with self.assertRaisesRegex(ValueError,'Diagnostic'):
            score({},dict(diagnostic_arm='own_heads'),None,{})
    def test_norm_is_enforced(self):
        with self.assertRaisesRegex(ValueError,'norm=seq'):Objective(torch.nn.Linear(1,1),{'norm':'token'})
