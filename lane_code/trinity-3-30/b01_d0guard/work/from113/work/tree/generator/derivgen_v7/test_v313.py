"""CPU contract, geometry, legacy replay, balancing and GT raster fixtures."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import unittest
from collections import Counter
import numpy as np
from derivgen import ground_v312 as old
from derivgen.ground_v313 import Session, render, witness_pair, selector_provider, balance_gap_positions, GTInstances
from derivgen.ground_v313_tokens import tokenizer_for_rows,gate_positions
from derivgen.ground_v313_pack import training_row
from derivgen.surface_rows_v313 import visible,pair_allowed
from test_v312_ground import Geometry,masks,item

ROOT=Path('/scratch/jjyeung/orch_cd/spec313_kp')
BACKEND='/scratch/jjyeung/orch_cd/ground_rows/work/backend_v3122/ground_lifting.py'
TOKENIZER='/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json'
backend=old.load_backend(BACKEND)
tokenizer=tokenizer_for_rows(TOKENIZER,keypoint_calls=True)
count=lambda s:len(tokenizer.encode(s,add_special_tokens=False).ids)

def instances(name):
    m,p=masks(name)
    return [dict(instance_id=name,masks=m,prob=p)] if m.any() else []

def session(**kwargs):
    kwargs.setdefault('distance_rule','visible_surface')
    return Session(backend,Geometry(),masks,instances=instances,**kwargs)

def raw_object(name,points,frame):
    return dict(name=name,seen=True,visible=[frame],areas={str(frame):1.},points={str(frame):np.asarray(points,float).tolist()})

class TinyGeometry(Geometry):
    def lift(self,k,uv,mode='center'):
        p=np.column_stack((uv[:,0]/100,2+uv[:,1]/100,np.ones(len(uv))))
        R,t=self.cam(k)
        return p,(p-t)@R,np.zeros(len(p))


def raster_fixture(seed):
    n=seed%7
    raster=np.full((32,8,40),-1,int)
    for j in range(n):
        frame=(seed*7+j*3)%32
        raster[frame,2:6,1+j*6:5+j*6]=100+j
    gt=len(set(raster[raster>=0].tolist()))
    def resolve(name):
        if name!='chair':return []
        return [dict(instance_id=int(i),masks=raster==i,prob=(raster==i).any(axis=(1,2)).astype(float))
                for i in np.unique(raster) if i>=0]
    s=Session(backend,TinyGeometry(),lambda _:None,instances=resolve)
    q=dict(qid=f'count-{seed}',type='object_counting',roles=dict(obj='chair'),question=f'How many chairs are observed in clip {seed}?',
           gt_answer=str(gt),gt_authority='synthetic native instance raster distinct IDs',options=[])
    return q,s,raster

class ContractTests(unittest.TestCase):
    def test_legacy_flag_equivalence(self):
        for typ in old.TYPES:
            q=item(typ)
            a=old.render(q,old.Session(backend,Geometry(),masks),count)
            b=render(q,session(enabled=False,keypoint_calls=True,witness_points=True),count)
            self.assertEqual(a,b)
            old.replay(a,session(enabled=False))
        for call in ['<surface_pair a="stand" b="face" mode="closest_visible">','<extent_ends obj="stand" axis="longest_observed">','<ground obj="stand" mode="instances">']:
            with self.assertRaises(ValueError):session(enabled=False).execute(call)

    def test_witnesses_and_rounded_registry(self):
        s=session();row=render(item(),s,count)
        self.assertEqual(row['spec_version'],'3.13');self.assertEqual(len(s.registry._points),4)
        pair=s.witness_audit[0]
        for name,point,frame in zip(['stand','face'],pair['positions'],pair['frames']):
            self.assertTrue(any(np.array_equal(point,p) for p in s.objects[name]['points'][str(frame)]))
        gap=float(row['answer'])
        self.assertAlmostEqual(np.linalg.norm(np.subtract(*pair['positions'])),pair['distance_m'],places=9)
        rounded=[np.array(s.registry._points[p]['f1'],float) for p in ['P3','P4']]
        self.assertEqual(f'{np.linalg.norm(rounded[0]-rounded[1]):.2f}', row['answer'])
        self.assertEqual(s.execute('<dist P3 P4>'),row['answer']+' m')
        old.validate_evidence(row);old.replay(row,session())

    def test_multicandidate_witness_order(self):
        s=session();r=render(item('object_rel_distance'),s,count)
        b=r['events'][-1]['response'];self.assertIn('min "face"',b)
        self.assertEqual(len(s.registry._points),7)
        self.assertEqual([p.split(': ',1)[1].split(' nearest')[0] for p in b.splitlines() if 'nearest point' in p],['stand','face','stand','far'])
        old.replay(r,session())

    def test_disjoint_frames_one_world(self):
        a=raw_object('a',[[0,3,1]],2);b=raw_object('b',[[2,3,1]],19)
        result=witness_pair(backend,a,b)
        self.assertEqual(result['frames'],[2,19]);self.assertEqual(result['distance_m'],2.)
        from derivgen.ground_v313 import point_line
        s=session()
        for name,p,f in zip(['a','b'],result['positions'],result['frames']):
            point_line(backend,s.geometry,s.registry,name,'nearest point',f,p)
        self.assertEqual(s.registry.execute('<dist P1 P2>')['text'],'2.00 m')
        self.assertNotEqual(s.registry._points['P1']['camera'][0],s.registry._points['P1']['f1'][0])

    def test_concavity_defeats_facing_support(self):
        # U's arms extend past the small object nestled inside its concavity.
        A=np.array([[0,0,0],[0,4,0],[5,0,0],[5,4,0],[1,2,0]],float)
        B=np.array([[2,2,0],[2,2.2,0]],float)
        direction=B.mean(0)-A.mean(0)
        support_a=A[np.argmax(A@direction)];support_b=B[np.argmin(B@direction)]
        exact=witness_pair(backend,raw_object('a',A,1),raw_object('b',B,1))['distance_m']
        self.assertEqual(exact,1.)
        self.assertGreater(np.linalg.norm(support_a-support_b),exact)

    def test_unresolved_and_no_allocations(self):
        def ambiguous(name):return [dict(e,instance_id=i) for i in [1,2] for e in instances('stand')]
        s=Session(backend,Geometry(),masks,instances=ambiguous)
        self.assertEqual(s.execute('<ground obj="chair">'),'chair: unresolved')
        self.assertEqual(s.execute('<gap a="chair" b="face">'),'unresolved')
        self.assertEqual(len(s.registry._points),0)
        self.assertEqual(s.execute('<ground obj="chair" mode="instances">').splitlines()[0],'chair: 2 found')
        self.assertEqual(len(s.registry._points),2)
        self.assertNotIn('chair',s.objects)

    def test_counting_500_native_raster_rows(self):
        rows=[]
        for i in range(500):
            q,s,raster=raster_fixture(i)
            row=render(q,s,count)
            self.assertEqual(int(row['answer']),len(np.unique(raster[raster>=0])))
            self.assertLess(row['suffix_tokens'],5000)
            old.validate_evidence(row)
            rows.append(row)
        (Path(__file__).resolve().parents[2]/'out/counting_500_v6.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))

    def test_appearance_order_and_ties(self):
        def resolver(name):
            m,p=masks('stand');m[:]=False;m[1 if name=='chair' else 9,20:28,20:28]=True
            return [dict(instance_id=name,masks=m,prob=m.any(axis=(1,2)).astype(float))]
        q=dict(qid='appearance',type='object_appearance_order',question='Which appears first?',roles=dict(cands=['chair','table']),
               options=['A. chair','B. table'],gt_answer='A',gt_authority='fixture first-frame raster')
        row=render(q,Session(backend,Geometry(),masks,instances=resolver),count)
        self.assertEqual(row['answer'],'A');self.assertEqual(row['program_audit']['first_frames'],{'chair':2,'table':10})
        q['gt_answer']='B'
        with self.assertRaisesRegex(ValueError,'independent_gt'):render(q,Session(backend,Geometry(),masks,instances=resolver),count)
        q['gt_answer']='A'
        with self.assertRaisesRegex(ValueError,'tied_first'):render(q,Session(backend,Geometry(),masks,instances=lambda _: instances('stand')),count)

    def test_selector_api_and_feature_gate(self):
        spec=importlib.util.spec_from_file_location('selector_owner','/scratch/jjyeung/orch_cd/hrp_infer/hrp/selector.py')
        selector=importlib.util.module_from_spec(spec);sys.modules[spec.name]=selector;spec.loader.exec_module(selector)
        rows=[dict(object_id='stand',keypoint='nearest_surface',toward='face',frame=2,point_2d=[250,300]),
              dict(object_id='face',keypoint='nearest_surface',toward='stand',frame=19,point_2d=[650,300]),
              dict(object_id='stand',keypoint='extent_start',axis='longest_observed',frame=2,point_2d=[250,300]),
              dict(object_id='stand',keypoint='extent_end',axis='longest_observed',frame=19,point_2d=[650,300])]
        provider=selector_provider(selector,rows,Geometry())
        s=session(keypoint_calls=True,keypoint_provider=provider)
        for n in ['stand','face']:s.execute(f'<ground obj="{n}">')
        body=s.execute('<surface_pair a="stand" b="face" mode="closest_visible">')
        self.assertEqual(provider('surface_pair',['stand','face'])['frames'],[2,19])
        self.assertEqual(body,'unavailable')  # Selector points lack these objects' supporting surfaces.
        self.assertIn('observed endpoint distance',s.execute('<extent_ends obj="stand" axis="longest_observed">'))
        with self.assertRaisesRegex(ValueError,'disabled'):session().execute('<surface_pair a="stand" b="face" mode="closest_visible">')

    def test_zbuffer_hidden_silhouette_and_joint_ties(self):
        class Geo:
            K=np.repeat(np.eye(3)[None],32,axis=0)
            depth=np.ones((32,8,8))*2
            def cam(self,k):return np.eye(3),np.zeros(3)
            def lift(self,k,uv,patch=False):
                xy=np.floor(np.asarray(uv)*8/1000)+.5
                p=np.column_stack((xy,np.ones(len(xy))))*2
                return p,p,np.zeros(len(p))
        g=Geo();mask=np.ones((32,8,8),bool)
        self.assertTrue(visible(g,[3,3,2],1,mask)['visible'])
        self.assertEqual(visible(g,[6,6,4],1,mask)['reason'],'occluded_or_invalid_depth')
        mask[:,1,1]=False
        self.assertEqual(visible(g,[3,3,2],1,mask)['reason'],'wrong_instance_or_silhouette')
        self.assertTrue(pair_allowed([[0,0,0],[1,0,0]],1))
        self.assertTrue(pair_allowed([[0,2,0],[1,2,0]],1))
        self.assertFalse(pair_allowed([[0,0,0],[1,2,0]],1))
        s=session(keypoint_calls=True)
        s.keypoint_provider=lambda *_:dict(status='ok',observed_surface_points=True,
            **witness_pair(backend,s.objects['stand'],s.objects['face']),
            full_surface_distance_m=.5,true_closest_visible=False)
        for n in ['stand','face']:s.execute(f'<ground obj="{n}">')
        self.assertTrue(s.execute('<surface_pair a="stand" b="face" mode="closest_visible">').endswith('full surface gap unavailable'))

    def test_position_balance_and_tokens(self):
        from derivgen.ground_v312_quality import shuffled_item
        rows=[]
        for i in range(80):
            q=item('object_rel_distance');q.update(qid=f'bal-{i}',question=f'Which is closest in clip {i}?',gt_answer='A')
            q=shuffled_item(q);r=render(q,session(),count);r.update(roles=q['roles'],scene=f'clip-{i}');rows.append(r)
        selected,report=balance_gap_positions(rows,80)
        self.assertGreater(len(selected),40)
        self.assertEqual(len(set(Counter(r['answer'] for r in selected).values())),1)
        minimum_positions=[]
        for r in selected:
            minimum_positions.append(r['roles']['cands'].index(r['answer_content']))
            r['gt_agrees']=True;packed=training_row(r)
            self.assertTrue(all(s['target_loss']==0 for s in packed['tool_output_spans']))
            self.assertTrue(gate_positions(tokenizer,r['suffix']))
            self.assertLess(r['suffix_tokens'],5000)
        self.assertEqual(len(set(Counter(minimum_positions).values())),1)
        (Path(__file__).resolve().parents[2]/'out/BALANCE_v6.json').write_text(json.dumps(dict(rows=len(selected),**report),indent=2)+'\n')
        plain=tokenizer_for_rows(TOKENIZER)
        for token,tid in plain.get_vocab().items():self.assertEqual(tokenizer.token_to_id(token),tid)

    def test_overflow_refuses(self):
        with self.assertRaisesRegex(ValueError,'suffix_cap'):render(item(),session(),lambda _:5001)
        q,s,_=raster_fixture(3)
        with self.assertRaisesRegex(ValueError,'suffix_cap'):render(q,s,lambda _:5001)

if __name__=='__main__':unittest.main(verbosity=2)
