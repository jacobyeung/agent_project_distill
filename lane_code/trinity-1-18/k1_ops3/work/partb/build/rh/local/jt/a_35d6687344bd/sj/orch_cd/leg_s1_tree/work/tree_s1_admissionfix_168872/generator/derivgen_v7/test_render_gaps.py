"""CPU regressions for the added programs and fixed-runtime byte compatibility."""
import copy
import unittest
import numpy as np
from derivgen import ground_v312 as G,ground_v313 as I,programs_v314 as P
from derivgen.gaps_v314 import printed_count,question,validate_computation,rotation_sense
from derivgen.ground_v312_quality import shuffled_item
from test_v312_ground import Geometry,masks,item
from test_v313 import backend,count
from trace_format.ground_v313 import Session as Runtime
from student_pilot.live_trace313 import parse_response


def resolver(name):
    n={'chair':2,'table':1}.get(name,1)
    return [dict(instance_id=str(i),masks=masks('stand' if name in ('chair','table') else name)[0],
        prob=masks('stand' if name in ('chair','table') else name)[1]) for i in range(n)]


def sess(typ,runtime=False,resolve=resolver):
    if runtime:return Runtime(backend,Geometry(),masks,instances=resolve,program_version='3.14')
    return I.Session(backend,Geometry(),masks,instances=resolve) if typ in ('object_counting','relative_count') else G.Session(backend,Geometry(),masks)


def fixture(typ):
    q=item(typ);q.update(qid='test-'+typ,scene='fixture',frame_indices=list(range(32)),gt_authority='synthetic geometry')
    if typ=='object_rel_direction_easy':q.update(options=['A. left','B. right'],gt_answer='A')
    elif typ=='object_counting':q.update(roles={'obj':'chair'},options=[],gt_answer='2',expected_instance_ids={'chair':['0','1']})
    elif typ=='relative_count':q.update(roles={'a':'chair','b':'table'},options=['A. more','B. fewer','C. equal number'],gt_answer='A',expected_instance_ids={'chair':['0','1'],'table':['0']})
    else:
        q.update(roles=dict(stand='stand',face='face',query='query',ccw=False),options=[],
            question='At the stand facing the face, how many degrees clockwise to face the query?',gt_answer='315')
        # Derive the fixture's reference from native fixture centres, not the rendered answer.
        s=G.Session(backend,Geometry(),masks)
        for n in ('stand','face','query'):s.execute(f'<ground obj="{n}">')
        S,F,Q=[s.objects[n]['f1'] for n in ('stand','face','query')]
        u,v=[np.asarray(p)[[0,2]]-np.asarray(S)[[0,2]] for p in (F,Q)]
        q['gt_answer']=str((-np.degrees(np.arctan2(np.linalg.det(np.stack([u,v])),np.dot(u,v))))%360)
    q['question']=question(q)
    return q


class RenderGapsTests(unittest.TestCase):
    def check(self,typ):
        q=shuffled_item(fixture(typ));row=P.render(q,sess(typ),count)
        G.replay(row,sess(typ));validate_computation(row)
        runtime=sess(typ,True)
        for event in row['events']:
            expected=event['response'][len('<tool_response>\n'):-len('\n</tool_response>')]
            parse_response(event['call'],expected,program_version='3.14')
            self.assertEqual(runtime.execute(event['call']),expected)
        self.assertNotRegex(row['suffix'].lower(),r'benchmark|dataset|label|release')
        return row
    def test_easy_runtime(self):self.check('object_rel_direction_easy')
    def test_count_runtime(self):self.check('object_counting')
    def test_relative_count_runtime(self):self.check('relative_count')
    def test_absolute_direction_runtime(self):self.check('absolute_direction_object')
    def test_unseen_native_identity_refused(self):
        q=fixture('object_counting');q['expected_instance_ids']['chair'].append('hidden')
        with self.assertRaisesRegex(G.RowRefusal,'instance_not_visible'):P.render(q,sess(q['type']),count)
    def test_relative_count_unseen_even_when_relation_unchanged(self):
        q=fixture('relative_count');q['expected_instance_ids']['chair'].append('hidden')
        with self.assertRaisesRegex(G.RowRefusal,'instance_not_visible'):P.render(q,sess(q['type']),count)
    def test_count_list_mutation(self):
        row=self.check('object_counting');body=row['events'][0]['response'][len('<tool_response>\n'):-len('\n</tool_response>')]
        with self.assertRaisesRegex(G.RowRefusal,'instance_list_count_mismatch'):printed_count(body.replace(': 2 found',': 3 found'))
    def test_answer_mutation(self):
        for t in ('object_rel_direction_easy','object_counting','relative_count','absolute_direction_object'):
            r=self.check(t);r['answer']='wrong'
            with self.assertRaises(G.RowRefusal):validate_computation(r)
    def test_rotation_sense(self):
        self.assertTrue(rotation_sense('turn counter-clockwise'))
        self.assertFalse(rotation_sense('turn clockwise'))
        for s in ('turn','clockwise or counterclockwise'):
            with self.assertRaisesRegex(G.RowRefusal,'rotation_sense_ambiguous'):rotation_sense(s)
        q=fixture('absolute_direction_object');q['roles']['ccw']=True
        with self.assertRaisesRegex(G.RowRefusal,'rotation_sense_mismatch'):P.render(q,sess(q['type']),count)
    def test_rotation_computation_mutation(self):
        r=self.check('absolute_direction_object');r['suffix']=r['suffix'].replace('mod 360','mod 180')
        with self.assertRaisesRegex(G.RowRefusal,'rotation_computation_mismatch'):validate_computation(r)
    def test_equal_relative_count(self):
        q=fixture('relative_count');q.update(gt_answer='C',expected_instance_ids={'chair':['0'],'table':['0']})
        resolve=lambda n:resolver(n)[:1]
        r=P.render(q,sess(q['type'],resolve=resolve),count)
        self.assertEqual(r['answer'],'C');self.assertIn('1 = 1',r['suffix'])
    def test_template_easy_no_back(self):
        q=fixture('object_rel_direction_easy')
        self.assertEqual(q['question'],'If I am standing by the stand and facing the face, is the query to the left or the right of the face?')
        r=self.check(q['type']);self.assertIn('rule=easy>',r['suffix']);self.assertNotIn('back',r['suffix'])
    def test_token_cap(self):
        for t in ('object_rel_direction_easy','object_counting','relative_count','absolute_direction_object'):
            with self.assertRaisesRegex(G.RowRefusal,'suffix_cap'):P.render(fixture(t),sess(t),lambda _:5001)
    def angle_session(self,theta):
        from types import SimpleNamespace as NS
        radians=np.radians(theta)
        coords={'stand':[0.,0.,0.], 'face':[2.,0.,0.],
                'query':[2*np.cos(radians),0.,2*np.sin(radians)]}
        def lift(name,*args,**kwargs):
            return dict(name=name,seen=True,frames=[1],best=1,camera=[0.,0.,2.],
                f1=coords[name],spread=0.,size=None)
        fake=NS(lift_object=lift,render_ground=backend.render_ground)
        return G.Session(fake,Geometry(),masks)
    def test_easy_five_degree_boundaries_and_back_half_plane(self):
        for theta in (6,174,-6,-174):
            q=fixture('object_rel_direction_easy')
            r=P.render(q,self.angle_session(theta),count)
            self.assertEqual(r['answer_content'],'left' if theta>0 else 'right')
        for theta in (4,176,-4,-176):
            with self.assertRaisesRegex(G.RowRefusal,'boundary|margin'):
                P.render(fixture('object_rel_direction_easy'),self.angle_session(theta),count)
    def test_absolute_both_senses_and_wrap(self):
        for theta in (30,-30,150,-150):
            for ccw in (False,True):
                q=fixture('absolute_direction_object');q['roles']['ccw']=ccw
                q['question']='Turn '+('counterclockwise' if ccw else 'clockwise')+' to face the query.'
                q['gt_answer']=str((theta if ccw else -theta)%360)
                r=P.render(q,self.angle_session(theta),count)
                self.assertEqual(r['answer'],q['gt_answer']);validate_computation(r)
        for theta in (1,-1,2,-2):
            q=fixture('absolute_direction_object');q['gt_answer']=str((-theta)%360)
            with self.assertRaisesRegex(G.RowRefusal,'rotation_wrap_margin'):
                P.render(q,self.angle_session(theta),count)
    def test_all_row_validator_mutations(self):
        from unittest.mock import patch
        from types import SimpleNamespace as NS
        from render_gaps_v314 import check_row
        from derivgen.ground_v313_tokens import tokenizer_for_rows,gate_positions
        from test_v312_benchmark import benchmark_templates
        from orchard_ground_adapter import pack,validate
        tok=tokenizer_for_rows('/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json')
        for t in ('object_rel_direction_easy','object_counting','relative_count','absolute_direction_object'):
            q=shuffled_item(fixture(t));q['source_provenance']={'canonical':'synthetic/room_00'}
            r=P.render(q,sess(t),count)
            r.update(roles=q['roles'],frame_indices=q['frame_indices'],gt_answer=q['gt_answer'],option_letter_map=q.get('option_letter_map',{}),
                spec_version='3.14',training_admitted=False,gt_accepted=True,gt_agrees=True,
                not_seen=False,simulated_misses=[])
            r['mdg_gate_token_positions']=gate_positions(tok,r['suffix'])
            def check(row,dev=set(),rooms=set()):
                with patch('render_gaps_v314.session',side_effect=lambda *args:sess(t)):
                    return check_row(row,q,None,None,tok,benchmark_templates(),dev,rooms)
            self.assertEqual(check(r)['exact_replay'],1)
            packed=pack(r,q['source_provenance']);self.assertEqual(validate(packed)[0],r['suffix'])
            for key,value in [('gt_agrees',False),('suffix_tokens',0),('mdg_gate_token_positions',[]),
                              ('question','wrong question'),('answer','wrong'),('frame_indices',[999])]:
                bad=dict(r,**{key:value})
                with self.assertRaises((ValueError,KeyError,AttributeError),msg=(t,key)):check(bad)
            with self.assertRaisesRegex(ValueError,'dev'):check(r,{'synthetic/room_00'})
            with self.assertRaisesRegex(ValueError,'dev'):check(r,set(),{'synthetic/room'})
            if r['options']:
                bad=dict(r,options=list(reversed(r['options'])))
                with self.assertRaises(ValueError):check(bad)
            bad=copy.deepcopy(packed);bad['tool_output_spans'][0]['start']+=1
            with self.assertRaises(ValueError):validate(bad)
    def test_no_signed_grammar(self):
        with self.assertRaises(ValueError):sess('absolute_direction_object',True).execute('<angle S=P1 F=P2 Q=P3 rule=signed>')

if __name__=='__main__':unittest.main()
