"""CPU proofs against the fixed programs and the production v3.14 rows."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
from student_pilot import ground_lifting as L
from student_pilot.live_trace313 import LiveSession, AuditSession, entries, parse_response, replay
from student_pilot.live_instances314 import ExactFrames
from trace_format import box_v313 as B
from trace_format.ground_v313 import Session, GTInstances, MergedInstances
from trace_format.category_vocab import vocabulary

ROOT=Path(__file__).resolve().parents[3]
REF=Path('/scratch/jjyeung/orch_cd/gt_ceiling/work')
sys.path.insert(0,str(REF/'tp'))
import prog_v2 as P

class Geometry:
    def has(self,k):return 1<=k<=32
    def cam(self,k):
        return np.array([[1.,0,0],[0,0,1],[0,-1,0]]),np.array([.1*(k-1),0.,0.])
    def lift(self,k,uv,mode='center'):
        world=np.c_[uv[:,0]/100,uv[:,1]/100,np.ones(len(uv))]
        r,t=self.cam(k)
        return world,(world-t)@r,np.zeros(len(uv))

def raw(box):
    return dict(centroid=box['centre'],axesLengths=box['lengths'],normalizedAxes=np.array(box['axes']).ravel())

def obj(iid,frame=1):
    return dict(instance_id=iid,seen=True,frames=[frame],visible=[frame],best=frame,
                areas={str(frame):1.},points={str(frame):[[0,2,1]]*4},first=frame)

BOXES={'table':[B.box([0,0,2],[1,1,1],np.eye(3))],
       'chair':[B.box([4,0,2],[1,1,1],np.eye(3)),B.box([1.5,0,2],[1,1,1],np.eye(3))],
       'lamp':[B.box([0,0,6],[1,1,1],np.eye(3))]}

def scene(boxes=BOXES):
    class Provider:
        provider_id='synthetic_known_geometry'
        def __call__(self,name,item,geo,best):return boxes[name][int(item['instance_id'])]
    s=Session(L,Geometry(),None,instances=lambda n:[],box_provider=Provider(),multi_instance=True,program_version='3.14')
    s._instances=lambda n:[obj(str(i)) for i,_ in enumerate(boxes.get(n,[]))]
    return s

def execute(s,call):
    body=s.execute(call);parse_response(call,body);return body

class Forms(unittest.TestCase):
    def test_grid_absolute_matches_prog_v2(self):
        s=scene()
        for n in ('table','chair'):execute(s,f'<ground obj="{n}" mode="box">')
        value=P.bdist(NS(fixes=set()),[raw(b) for b in BOXES['table']],[raw(b) for b in BOXES['chair']])
        self.assertAlmostEqual(value,.5)
        self.assertEqual(execute(s,'<gap a="table" b="chair" rule="box_grid_5cm">'),f'distance {value:.2f} m')

    def test_multi_instance_entries_and_header(self):
        query=dict(instances=[dict(instance_id=str(i),result=obj(str(i))) for i in range(2)])
        self.assertEqual([x['instance_id'] for x in entries(query)],['0','1'])
        s=scene();body=execute(s,'<ground obj="chair" mode="box">')
        self.assertTrue(body.startswith('chair: 2 instances\n'))
        self.assertEqual(len(B.split_instances(body)),2)
        for bad in (body.replace('2 instances','3 instances'),body.replace('B2:','B1:'),body.replace('chair: frames','desk: frames',1)):
            with self.assertRaises(ValueError):parse_response('<ground obj="chair" mode="box">',bad)
        s=scene(dict(chair=[BOXES['chair'][0]]*9))
        self.assertEqual(execute(s,'<ground obj="chair" mode="box">'),'chair: unresolved')

    def test_relative_minimum_matches_prog_v2_answer(self):
        s=scene()
        for n in BOXES:execute(s,f'<ground obj="{n}" mode="box">')
        ctx=NS(fixes={'extent'},ids=lambda n:list(range(len(BOXES[n]))),
            fused=NS(seen=lambda i:True,box=lambda i:None))
        q=dict(question_type='object_rel_distance',question='which of these objects (chair, lamp) is the closest to the table?',options=['A. chair','B. lamp'])
        with patch.object(P,'boxes_of',side_effect=lambda ctx,n:[raw(b) for b in BOXES[n]]):
            expected=P.run_vsi(q,ctx)[0]
        got=execute(s,'<gap a="table" b="chair" b="lamp" rule="box_grid_5cm">')
        winner=re.findall(r'min "([^"]+)"',got)[0]
        self.assertEqual(P.T.letter_of(q['options'],winner),expected)
        self.assertEqual(expected,'A')

    def test_camera_gap_asked_frame_and_unavailable(self):
        s=scene();s._instances=lambda n:[obj(str(i),3 if i==0 else 1) for i in range(len(BOXES[n]))]
        execute(s,'<ground obj="chair" mode="box">')
        centre=B.camera_centre_f1(s.geometry,3)
        # prog_v2 camera program uses its shared benchmark grid and Euclidean norm.
        want=np.linalg.norm(P.C.box_grid(raw(BOXES['chair'][0]))-centre,axis=1).min()
        self.assertEqual(execute(s,'<gap camera="3" b="chair" rule="box_grid_5cm">'),f'distance {want:.2f} m')
        self.assertEqual(execute(s,'<gap camera="33" b="chair" rule="box_grid_5cm">'),'frame unavailable')
        self.assertAlmostEqual(B.replay_audit(s.events)[0],want)

    def test_fused_default_full_height_matches_prog_v2(self):
        rng=np.random.default_rng(3)
        points=np.c_[rng.uniform(0,1,(500,2)),rng.uniform(0,1,500)]
        points[0,2]=-1;points[1,2]=2
        data=obj('0');data.update(frames=[1,2],visible=[1,2],areas={'1':2.,'2':1.},points={'1':points[:250].tolist(),'2':(points[250:]+[2,0,0]).tolist()})
        allpoints=np.concatenate([data['points']['1'],data['points']['2']])
        want=P.gbox_full(allpoints)
        s=Session(L,Geometry(),None,instances=lambda _:[],multi_instance=True)
        s._instances=lambda n:[data]
        execute(s,'<ground obj="table" mode="box">')
        got=s.events[0]['audit']['full_precision_box']
        expected=B.in_f1(s.geometry,want['centroid'],want['axesLengths'],want['normalizedAxes'])
        np.testing.assert_allclose(got['centre'],expected['centre'],atol=1e-10)
        np.testing.assert_allclose(sorted(got['lengths']),sorted(expected['lengths']),atol=1e-10)
        self.assertAlmostEqual(got['lengths'][2],3.)
        self.assertEqual(s.box_provider_id,'fit_gbox_fused_full_v1')

    def test_tilted_box_envelope_keeps_private_measurement(self):
        theta=np.pi/6;c,t=np.cos(theta),np.sin(theta)
        tilted=B.box([0,0,2],[2,1,.5],[[c,t,0],[-t,c,0],[0,0,1]])
        s=scene({'table':[tilted],'lamp':BOXES['lamp']})
        for n in ('table','lamp'):execute(s,f'<ground obj="{n}" mode="box">')
        want=P.bdist(NS(fixes=set()),[raw(tilted)],[raw(BOXES['lamp'][0])])
        self.assertEqual(execute(s,'<gap a="table" b="lamp" rule="box_grid_5cm">'),f'distance {want:.2f} m')
        self.assertEqual(s.events[0]['audit']['full_precision_box']['axes'],tilted['axes'].tolist())

    def test_counting_merge_matches_prog_v2(self):
        frames=[[] for _ in range(32)]
        def mask(x,y):
            m=np.zeros((40,40),bool);m[y:y+5,x:x+5]=True;return m
        frames[0]=[mask(5,5),mask(9,5)];frames[1]=[mask(5,9)];frames[2]=[mask(30,30)]
        geo=Geometry()
        detector=lambda _:frames
        resolver=MergedInstances(L,geo,detector)
        s=Session(L,geo,None,instances=resolver,multi_instance=True)
        def clicks(n,k,mode):
            return [np.mean(L.mask_pixels(m),axis=0) for m in frames[k-1]]
        gt=NS(valid=[True]*32,has=geo.has,lift=geo.lift)
        ctx=NS(gt=gt,ground=NS(get=clicks),fixes={'merge'})
        q=dict(question_type='object_counting',question='How many chair(s) are in this room?')
        want=P.run_vsi(q,ctx)[0]
        self.assertEqual(want,3)
        body=execute(s,'<ground obj="chair" mode="instances">')
        self.assertEqual(body.splitlines()[0],f'chair: {want} found')

    def test_vocab_pools_raw_labels(self):
        geo=NS(ids=[1,2,3],labels=['table','desk','chair'],inst=np.stack([np.full((8,8),i) for i in (1,2,3)]*11)[:32])
        resolver=GTInstances(NS(geo=geo),vocab=vocabulary())
        ground=NS(by_label={'table':[1],'desk':[2],'chair':[3]},instances=lambda name:[])
        P.use_vocab(ground)
        self.assertEqual([e['instance_id'] for e in resolver('table')],ground.instances('table'))
        self.assertEqual(ground.instances('table'),[1,2])
        s=Session(L,Geometry(),None,instances=resolver,program_version='3.14')
        body=execute(s,'<ground obj="table" mode="instances">')
        self.assertEqual(body.splitlines()[0],f'table: {len(ground.instances("table"))} found')

    def test_exact_frame_gate_skips_paired_depth(self):
        class Paired(Geometry):
            def frame_of(self,k):return k if k%2==0 else k+1
            def lift(self,k,*args,**kw):
                self_outer.assertEqual(k%2,0);return super().lift(k,*args,**kw)
        self_outer=self;geo=ExactFrames(Paired())
        m=np.zeros((32,40,40),bool);m[:2,5:10,5:10]=True
        s=Session(L,geo,None,instances=lambda n:[dict(instance_id='one',masks=m,prob=np.ones(32))],multi_instance=True)
        body=execute(s,'<ground obj="table" mode="box">')
        self.assertIn('frames 2 (best 2)',body)
        self.assertEqual(execute(s,'<gap camera="3" b="table" rule="box_grid_5cm">'),'frame unavailable')

class Live(unittest.TestCase):
    def geometry(self):
        from student_pilot.geometry_profiles import GeometryContract, ProfileGeometry
        from student_pilot.scene_state import FrameMap
        fm=FrameMap(tuple(range(32)),rgb_sha256=tuple(['a'*64]*32))
        K=np.repeat(np.array([[20.,0,20],[0,20,20],[0,0,1.]])[None],32,axis=0)
        C=np.repeat(np.eye(4)[None],32,axis=0);C[:,:3,:3]=Geometry().cam(1)[0]
        contract=GeometryContract('legacy_v3122',fm,0,K,np.repeat(np.diag([.04,.04,1.])[None],32,axis=0),C,1.,'vc','metric','metric',0,1)
        return ProfileGeometry(contract,np.broadcast_to(3.+.2*(np.arange(40)[:,None]/40)**2,(32,40,40)).copy())
    def test_live_all_candidates_replay_and_cache(self):
        geo=self.geometry();calls=[]
        m=np.zeros((40,40),bool);m[5:12,5:12]=True
        n=np.zeros_like(m);n[25:32,25:32]=True
        def candidates(name):
            calls.append(name)
            return [NS(frame=k,mask=a) for k,a in [(1,m),(1,n),(2,m)]]
        owner=NS(geometry=geo,source=NS(selector_candidates=candidates),scene=NS(frames=geo.frame_map))
        s=LiveSession(owner,program_version='3.14',multi_instance=True);state=NS(verify_session=None);s.bind_state(state)
        first=execute(s,'<ground obj="chair" mode="box">')
        self.assertTrue(first.startswith('chair: 2 instances'))
        execute(s,'<ground obj="chair" mode="instances">')
        self.assertEqual(calls,['chair']);self.assertEqual(s.memory_hits,[False,True])
        record=dict(heads=dict(ground_queries=s.queries,trace_program_version='3.14'),calls=[])
        record['calls']=[dict(call=e['call'],response=e['response'].removeprefix('<tool_response>\n').removesuffix('\n</tool_response>')) for e in s.events]
        self.assertTrue(replay(record)['byte_equal'])
        record['heads']['ground_queries'][0]['instances'][0]['result']={'seen':False}
        self.assertTrue(replay(record)['byte_equal'],'Stored results are not replay evidence')

    def test_v313_bytes_equal_base_live_on_multi_frame_masks(self):
        base=Path('/scratch/jjyeung/orch_cd/integ_v3/work/tree')
        spec=importlib.util.spec_from_file_location('legacy_trace_format',base/'trace_format/__init__.py',submodule_search_locations=[str(base/'trace_format')])
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        namespace={'__name__':'student_pilot._base_live_trace313','__package__':'student_pilot'}
        code=(base/'student_pilot/live_trace313.py').read_text().replace('from trace_format','from legacy_trace_format')
        exec(compile(code,str(base/'student_pilot/live_trace313.py'),'exec'),namespace)
        geo=self.geometry();m=np.zeros((32,40,40),bool);m[0,5:12,5:12]=True;m[1,5:12,8:15]=True
        from student_pilot.ground_replay import record_mask
        result=L.lift_object('table',m,np.ones(32),geo,tau=.5)
        q=dict(name='table',state='resolved',result=result,**record_mask(m,np.ones(32),.5,geo))
        old=namespace['AuditSession']([deepcopy(q)]);new=AuditSession([deepcopy(q)])
        for call in ['<ground obj="table" mode="box">','<gap a="table" b="chair" rule="sampled_box_512">']:
            self.assertEqual(new.execute(call),old.execute(call))
        self.assertEqual(new.events,old.events)

    def test_v313_all_existing_forms_match_base(self):
        base=Path('/scratch/jjyeung/orch_cd/integ_v3/work/tree/trace_format')
        spec=importlib.util.spec_from_file_location('baseline313',base/'__init__.py',submodule_search_locations=[str(base)])
        mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        from baseline313.ground_v313 import Session as OldSession
        geo=self.geometry()
        def instances(name):
            if name=='missing':return []
            mask=np.zeros((32,40,40),bool)
            x={'table':5,'chair':20,'lamp':30}.get(name,5)
            mask[0,5:12,x:x+7]=True;mask[1,8:15,x:x+7]=True
            ids=['a','b'] if name=='many' else ['a']
            return [dict(instance_id=i,masks=mask,prob=np.ones(32)) for i in ids]
        old=OldSession(L,geo,None,instances=instances,keypoint_calls=True)
        new=Session(L,geo,None,instances=instances,keypoint_calls=True)
        calls=[f'<ground obj="{n}" mode="box">' for n in ('table','chair','lamp','many','missing')]
        calls+=['<gap a="table" b="chair" rule="sampled_box_512">',
                '<gap a="table" b="chair" b="lamp" rule="sampled_box_512">',
                '<ground obj="table">','<ground obj="chair">','<gap a="table" b="chair">',
                '<ground obj="many" mode="instances">','<ground obj="many">',
                '<surface_pair a="table" b="chair" mode="closest_visible">',
                '<extent_ends obj="table" axis="longest_observed">']
        for call in calls:
            with self.subTest(call=call):self.assertEqual(new.execute(call),old.execute(call))
        self.assertEqual(new.events,old.events)
        self.assertEqual(new.box_provider_id,'fit_gbox_best_v1')
        theta=.3;c,t=np.cos(theta),np.sin(theta)
        value=B.box([0,0,2],[2,1,.5],[[c,t,0],[-t,c,0],[0,0,1]])
        class Tilt:
            provider_id='test_tilt'
            def __call__(self,*args):return value
        for s in (old,new):s.box_provider=Tilt();s.box_provider_id=Tilt.provider_id
        call='<ground obj="table" mode="box">'
        self.assertEqual(new.execute(call),old.execute(call))
        self.assertEqual(new.events[-1],old.events[-1])
        self.assertIn('box unavailable',new.events[-1]['response'])

class Decode(unittest.TestCase):
    def test_explicit_version_binds_live_sessions_before_first_call(self):
        from student_pilot import trace_format313 as F
        geometry=Geometry();geometry.kind='gt'
        owner=NS(geometry=geometry)
        @F.bind_generate
        def generate(model,processor,batch,**kwargs):
            return F._current.get(),F._rows.get()
        self.assertEqual(generate(None,None,{}),(None,None))
        one,_=generate(None,None,{},ground_backend=owner,trace_program_version='3.14')
        self.assertEqual(one.spec_version,'3.14');self.assertTrue(one.multi_instance)
        self.assertEqual(one.box_provider_id,'fit_gbox_fused_full_v1')
        _,many=generate(None,None,[{},{}],ground_backend=[owner,owner],trace_program_version='3.14')
        self.assertEqual(len({id(s) for s in many}),2)
        old,_=generate(None,None,{},ground_backend=owner,trace_program_version='3.13')
        self.assertEqual(old.box_provider_id,'fit_gbox_best_v1');self.assertFalse(old.multi_instance)
        self.assertIsNone(F._current.get());self.assertIsNone(F._rows.get())
        self.assertTrue(Session(L,Geometry(),None,program_version='3.14').multi_instance)
        with self.assertRaisesRegex(ValueError,'instance_mode_mismatch'):
            Session(L,Geometry(),None,program_version='3.13',multi_instance=True)

    def test_v314_forms_through_generate_b4(self):
        from tests.test_trace_format313_decode import FormatTests
        words={50:'<ground obj="table" mode="box">',51:'<ground obj="chair" mode="box">',
               52:'<gap a="table" b="chair" rule="box_grid_5cm">',
               53:'<gap camera="1" b="chair" rule="box_grid_5cm">'}
        records,shapes=FormatTests().run_rows([[50,51,52,53,1]]*4,
            sessions=[scene() for _ in range(4)],extra_words=words)
        self.assertIn(4,shapes)
        for r in records:
            self.assertEqual(r['calls'][2]['response'],'distance 0.50 m')
            self.assertEqual(r['calls'][0]['spec_version'],'3.14')
            for c in r['calls']:parse_response(c['call'],c['response'])

    def test_live_verifies_every_merged_instance(self):
        geo=Live().geometry()
        m=np.zeros((40,40),bool);m[5:12,5:12]=True
        n=np.zeros_like(m);n[25:32,25:32]=True
        owner=NS(geometry=geo,source=NS(selector_candidates=lambda name:[NS(frame=1,mask=m),NS(frame=1,mask=n)]),
                 scene=NS(frames=geo.frame_map),config={'verify_threshold':.5})
        verifier=NS(model=None,native=object(),processor=None,budget=None)
        context=NS(frame_map=geo.frame_map,frames=[None]*32)
        s=LiveSession(owner,program_version='3.14',multi_instance=True);s.bind_state(NS(verify_session=verifier,tool_context=context))
        def verify(model,processor,request,**kw):
            self.assertEqual(len(request['candidates']),2)
            return dict(status='ok',rows=[dict(candidate_id=c['candidate_id'],form='V1',p_yes=p)
                for c,p in zip(request['candidates'],[.8,.2])])
        with patch('student_pilot.verify_pass.verify_pass',side_effect=verify):
            body=execute(s,'<ground obj="chair" mode="instances">')
        self.assertTrue(body.startswith('chair: 1 found'))

    def test_own_head_geometry_records_replay_inputs(self):
        from student_pilot.carrier_c1_routing import OwnGeometry
        from student_pilot.live_instances314 import record_geometry,restore_recorded_geometry
        p=np.zeros((32,9));p[:,6]=1.;p[:,7:9]=1.
        p[1,0]=-.5
        geo=L.OwnGeometryAdapter(OwnGeometry(p,[0,-1,0],lambda k,uv:3.+.2*(uv[:,1]/1000)**2))
        uv=np.array([[250.,250.],[300.,300.]])
        want=geo.lift(2,uv)
        record=record_geometry(geo);restored=restore_recorded_geometry(record)
        for a,b in zip(want,restored.lift(2,uv)):np.testing.assert_array_equal(a,b)
        with self.assertRaisesRegex(ValueError,'missing_depth_grid'):restored.lift(3,uv)

if __name__=='__main__':unittest.main()
