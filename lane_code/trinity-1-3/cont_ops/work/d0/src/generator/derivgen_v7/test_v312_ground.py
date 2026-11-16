"""CPU-only tests; no temporary-directory cleanup or network access."""
import os
from pathlib import Path
import sys
import unittest

import numpy as np

from derivgen.ground_v312 import (Session, RowRefusal, load_backend, render,
                                  replay, select_balanced, parse_roles, validate_evidence)
from derivgen.ground_v312_io import reference, agrees, CalibratedGTSource
from derivgen.ground_v312_tokens import tokenizer_for_rows, gate_positions
from derivgen.ground_v312_input import normalize
from derivgen.ground_v312_pack import training_row

BACKEND = os.environ.get('V312_BACKEND', '/scratch/jjyeung/orch_cd/ground_backend/work/c1mix_sb/student_pilot/ground_lifting.py')
RKIT = '/scratch/jjyeung/orch_cd/mdg_next/work/rkit'


class Geometry:
    def has(self, k): return 1 <= k <= 32
    def frame_of(self, k): return k
    def cam(self, k):
        return np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]]), np.array([.1*(k-1), 0., .2])
    def lift(self, k, uv, mode='center'):
        assert mode == 'center'
        p = np.column_stack((uv[:, 0]/100, uv[:, 1]/100, .5+uv[:, 0]/2000))
        R, t = self.cam(k)
        return p, (p-t)@R, np.zeros(len(p))


def masks(name):
    x = np.zeros((32, 80, 112), bool)
    locations = {'stand': (20, 20), 'face': (20, 55), 'query': (45, 55), 'far': (65, 90)}
    if name in locations:
        y, col = locations[name]
        x[2, y:y+7, col:col+7] = True
        x[3, y:y+9, col:col+9] = True
    return x, x.any(axis=(1, 2)).astype(float)


def item(typ='object_abs_distance'):
    value = dict(qid='fixture', type=typ, question='fixture', options=[])
    if typ == 'object_abs_distance': value['roles'] = dict(a='stand', b='face')
    elif typ == 'object_rel_distance':
        value.update(roles=dict(target='stand', cands=['face', 'far']), options=['A. face','B. far'])
    else:
        value.update(roles=dict(stand='stand', face='face', query='query'),
                     options=['A. front-left','B. front-right','C. back-left','D. back-right'] if typ.endswith('hard')
                     else ['A. left','B. right','C. back'])
    return value


class GroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = load_backend(BACKEND)
        cls.programs, cls.MaskGround, cls.Scene = reference(RKIT)
    def session(self): return Session(self.backend, Geometry(), masks)
    def test_exact_ground_text_and_named_frame(self):
        s = self.session()
        text = s.execute('<ground obj="stand">')
        self.assertEqual(text.splitlines()[0], 'stand: frames 3,4 (best 4)')
        self.assertIn('P1: cam4 ', text)
        self.assertEqual(len(text.splitlines()), 3)
        self.assertIn('; f1 ', text)
        self.assertNotIn('-0.00', text)
    def test_shared_registry(self):
        s = self.session()
        s.registry.register(camera=[0.,0.,1.], f1=[0.,0.,1.], spread=0., requested_frame=1)
        self.assertIn('P2:', s.execute('<ground obj="stand">'))
        self.assertIn('P3:', s.execute('<ground obj="stand">'))
    def test_null_does_not_allocate(self):
        s = self.session()
        self.assertEqual(s.execute('<ground obj="missing">'), 'missing: not seen')
        self.assertIn('P1:', s.execute('<ground obj="stand">'))
    def test_gap_requires_grounded_names(self):
        s = self.session()
        self.assertEqual(s.execute('<gap a="stand" b="face">'), 'not seen')
        for n in ['stand', 'face']: s.execute(f'<ground obj="{n}">')
        self.assertRegex(s.execute('<gap a="stand" b="face">'), r'^\d+\.\d{2} m$')
    def test_rkit_mask_and_gap_parity(self):
        names = ['stand', 'face']
        Base = self.MaskGround
        class Ground(Base):
            def __init__(self):
                self.names = names
                self.values = dict(mask=np.stack([masks(n)[0] for n in names]), prob=np.stack([masks(n)[1] for n in names]))
                self.geo, self.tau, self.cache = Geometry(), .5, {}
            def index(self, name): return self.names.index(name)
        g = Ground()
        s = self.session()
        for n in names:
            s.execute(f'<ground obj="{n}">')
            for k in [3, 4]: np.testing.assert_array_equal(s.objects[n]['points'][str(k)], g.lifted(n,k)[1])
        sc = self.Scene(g.geo, g)
        self.assertEqual(s.execute('<gap a="stand" b="face">'), f'{sc.distance(*names):.2f} m')
    def test_all_types_replay(self):
        for typ in ['object_abs_distance','object_rel_distance','object_rel_direction_medium','object_rel_direction_hard']:
            row = render(item(typ), self.session(), len)
            self.assertTrue(replay(row, self.session()))
            self.assertFalse(row['not_seen'])
    def test_absent_without_direct_trace_refuses(self):
        q = item(); q['roles']['a']='missing'
        with self.assertRaisesRegex(RowRefusal,'missing_direct_canonical'):render(q,self.session(),len)
    def test_simulated_miss_uses_direct_canonical(self):
        q=item('object_rel_direction_medium');q['gt_answer']='A'
        body='Step 1: locate the stand, face and query in the video.\nStep 2: facing the face from the stand, the query is on the left.'
        q.update(scene='fixture',frame_indices=list(range(32)))
        q['direct_canonical']=dict(body=body,answer='A',form='vqa_canonical',source_sha256='fixture',
            scene=q['scene'],frame_indices=q['frame_indices'],question=q['question'],options=q['options'])
        s=Session(self.backend,Geometry(),masks,simulated_misses=['stand'])
        row=render(q,s,len)
        self.assertIn('stand: not seen',row['suffix'])
        self.assertIn('The tool did not find stand, so I estimate from the frames.\n'+body,row['suffix'])
        self.assertTrue(row['suffix'].endswith('<answer>A</answer>'))
        self.assertNotIn('<angle',row['suffix'])
        self.assertTrue(replay(row,Session(self.backend,Geometry(),masks,simulated_misses=['stand'])))
    def test_miss_cannot_mask_invisible_object(self):
        s=Session(self.backend,Geometry(),masks,simulated_misses=['missing'])
        with self.assertRaisesRegex(RowRefusal,'requires_visible'):s.execute('<ground obj="missing">')
    def test_cap_counts_complete_suffix(self):
        seen=[]
        def counter(text): seen.append(text); return 5001
        with self.assertRaisesRegex(RowRefusal,'suffix_cap'):render(item(),self.session(),counter)
        self.assertTrue(seen[0].startswith('<think>\n'))
        self.assertTrue(seen[0].endswith('</answer>'))
        self.assertEqual(render(item(),self.session(),lambda _:5000)['suffix_tokens'],5000)
    def test_invalid_names_and_calls(self):
        for call in ['<ground obj="">','<ground obj="a\nb">','<ground obj="a" frame=2>','<gap b="face" a="stand">']:
            with self.assertRaises(ValueError):self.session().execute(call)
    def test_invalid_prob_and_tau(self):
        m,p=masks('stand')
        for tau in [-1,float('nan'),2]:
            with self.assertRaises(ValueError):self.backend.lift_object('stand',m,p,Geometry(),tau=tau)
        p[0]=float('nan')
        with self.assertRaises(ValueError):self.backend.lift_object('stand',m,p,Geometry(),tau=.5)
    def test_threshold_and_erosion(self):
        m,p=masks('stand');p[:]=.49
        self.assertFalse(self.backend.lift_object('stand',m,p,Geometry(),tau=.5)['seen'])
        p[:]=.5
        self.assertTrue(self.backend.lift_object('stand',m,p,Geometry(),tau=.5)['seen'])
        m[:]=False;m[0,5,5]=True
        self.assertFalse(self.backend.lift_object('stand',m,p,Geometry(),tau=.5)['seen'])
    def test_common_unclickable_falls_back_to_disjoint(self):
        a=dict(seen=True,visible=[1,2],areas={'1':1,'2':1},points={'2':[[1,0,0]]})
        b=dict(seen=True,visible=[1,3],areas={'1':1,'3':1},points={'3':[[0,0,0]]})
        self.assertEqual(self.backend.gap_objects(a,b),1.)
    def test_multi_gap_prints_minimum(self):
        s=self.session()
        for n in ['stand','face','far']:s.execute(f'<ground obj="{n}">')
        result=s.execute('<gap a="stand" b="face" b="far">')
        self.assertEqual(len(result.splitlines()),3)
        self.assertTrue(result.splitlines()[-1].startswith('min "face" '))
    def test_size_failure_is_not_missing(self):
        class Flat(Geometry):
            def lift(self,k,uv,mode='center'):
                p,pc,spread=super().lift(k,uv,mode)
                p[:,1]=2
                return p,pc,spread
        s=Session(self.backend,Flat(),masks)
        body=s.execute('<ground obj="stand">')
        self.assertIn('P1:',body)
        self.assertTrue(body.endswith('size unavailable'))
    def test_pair_nearest_frame_tie(self):
        a=dict(seen=True,visible=[2,8],areas={'2':1,'8':1},points={'2':[[1,0,0]],'8':[[8,0,0]]})
        b=dict(seen=True,visible=[4,6],areas={'4':1,'6':1},points={'4':[[0,0,0]],'6':[[0,0,0]]})
        self.assertEqual(self.backend.gap_objects(a,b),1.)
    def test_corrupted_replay_fails(self):
        row=render(item(),self.session(),len)
        row['events'][0]['response']+=' invented'
        with self.assertRaisesRegex(RowRefusal,'mismatch'):replay(row,self.session())
    def test_invented_point_in_prose_fails(self):
        row=render(item(),self.session(),len)
        row['suffix']=row['suffix'].replace('</think>', 'P999 is the closest point.\n</think>')
        with self.assertRaisesRegex(RowRefusal,'unprinted_point'):validate_evidence(row)
    def test_detached_event_log_fails(self):
        row=render(item(),self.session(),len)
        row['suffix']=row['suffix'].replace('best 4', 'best 9')
        with self.assertRaisesRegex(RowRefusal,'suffix_event'):validate_evidence(row)
    def test_benchmark_quota_prevents_one_dominating(self):
        rows=[dict(qid=str(i),type='count',answer_content='1' if i<90 else '2') for i in range(100)]
        selected,report=select_balanced(rows,{'count':{'content':{'1':1,'2':1}}},20)
        self.assertEqual(sum(r['answer_content']=='1' for r in selected),10)
        self.assertEqual(len(selected),20)
    def test_shortages_do_not_duplicate(self):
        rows=[dict(qid='one',type='count',answer_content='1')]
        selected,report=select_balanced(rows,{'count':{'content':{'1':1,'2':1}}},10)
        self.assertEqual(len(selected),1)
        self.assertEqual(report['count']['shortage'],{'1':4,'2':5})
    def test_missing_distribution_is_pending(self):
        rows=[dict(qid='one',type='count',answer_content='1')]
        selected,report=select_balanced(rows,{},10)
        self.assertEqual(selected,[])
        self.assertIn('PENDING-INPUT',report['count']['status'])
    def test_numeric_five_percent_gate(self):
        self.assertTrue(agrees('1.04',1.,'object_abs_distance'))
        self.assertFalse(agrees('1.06',1.,'object_abs_distance'))
        self.assertTrue(agrees('0.00',0.,'object_abs_distance'))
        self.assertFalse(agrees('0.01',0.,'object_abs_distance'))
    def test_per_frame_intrinsics_use_exact_frame(self):
        class Raw:
            K=np.eye(3);Kinv=np.eye(3)
            def lift(self,k,uv,mode='center'):return np.asarray(uv)@self.Kinv[:2,:2]
        matrices=np.tile(np.eye(3),(32,1,1));matrices[4,0,0]=2
        source=CalibratedGTSource(Raw(),matrices)
        np.testing.assert_equal(source.lift(1,[[2,1]]),[[2,1]])
        np.testing.assert_equal(source.lift(5,[[2,1]]),[[1,1]])
        np.testing.assert_equal(source.lift(1,[[2,1]]),[[2,1]])
    def test_delivered_row_adapter_binds_provenance(self):
        row=dict(qid='q',question_type='object_abs_distance',question='What is the distance between the stand and the face (in meters)?',
                 options=[],gt_answer='1.00',provenance=dict(alias='d1/s',gt_sha256='pin',frame_indices=list(range(32)),canonical='scannet/s'))
        scenes={'s':dict(gt={'sha256':'pin'},frame_indices=list(range(32)),canonical='scannet/s')}
        result=normalize(row,scenes,self.programs.T)
        self.assertEqual(result['scene'],'s')
        self.assertEqual(result['roles'],dict(a='stand',b='face'))
        row['provenance']['gt_sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'GT pin'):normalize(row,scenes,self.programs.T)
    def test_relative_balance_uses_letters(self):
        rows=[dict(qid=str(i),type='object_rel_distance',answer='A' if i<9 else 'B',answer_content='chair') for i in range(10)]
        selected,report=select_balanced(rows,{'object_rel_distance':{'letters':{'A':1,'B':1}}},4)
        self.assertEqual([r['answer'] for r in selected],['A','A','B'])
        self.assertEqual(report['object_rel_distance']['shortage']['B'],1)
    def test_atomic_tokenizer_gate_positions(self):
        tokenizer=tokenizer_for_rows('/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json')
        suffix='ordinary prose\n<ground obj="stand">\n<tool_response>stand: not seen</tool_response>'
        ids=tokenizer.encode(suffix,add_special_tokens=False).ids
        positions=gate_positions(tokenizer,suffix)
        self.assertEqual(ids[positions[0]],tokenizer.token_to_id('<ground'))
        self.assertEqual(tokenizer.encode('<gap',add_special_tokens=False).ids,[tokenizer.token_to_id('<gap')])
    def test_no_direct_type_routing(self):
        q=item();q['type']='object_counting'
        with self.assertRaisesRegex(RowRefusal,'direct_type'):render(q,self.session(),len)
    def test_training_pack_masks_only_forced_responses(self):
        row=render(item(),self.session(),len);row['gt_agrees']=True
        packed=training_row(row)
        self.assertEqual(packed['target'],row['suffix'])
        spans=packed['loss_spans']
        self.assertEqual(spans[0]['start'],0)
        self.assertEqual(spans[-1]['end'],len(packed['target']))
        for a,b in zip(spans,spans[1:]):self.assertEqual(a['end'],b['start'])
        outputs=[packed['target'][s['start']:s['end']] for s in spans if s['target_loss']==0]
        self.assertEqual(outputs,[e['response'] for e in row['events']])


if __name__=='__main__':unittest.main(verbosity=2)
