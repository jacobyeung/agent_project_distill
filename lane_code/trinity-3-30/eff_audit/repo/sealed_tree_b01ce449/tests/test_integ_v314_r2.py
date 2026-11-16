"""Exercise version and perception boundaries with production classes on CPU."""
import json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from student_pilot import ground_lifting as L, trace_format313 as F
from student_pilot.live_trace313 import LiveSession, parse_response
from student_pilot.live_instances314 import ExactFrames
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.trace_version import resolve,bind,metadata
from trace_format.program_errors import ProgramRefusal
from trace_format.ground_v313 import Session, MergedInstances, connected_components
from trace_format import box_v313 as B
from trace_format.instance_policy314 import min_mask_px,mask_floor
from tests.test_integ_v314 import P,Geometry,obj,raw,scene
from tests.test_ground_r2 import geometry
from ofs.hrp_reference import Candidate

class Versions(unittest.TestCase):
 def test_export_load_without_config_and_mismatch(self):
  export=metadata({'trace_program_version':'3.14'})
  # The export binding survives serialization, exactly as artifact.json does.
  model=NS();bind(model,json.loads(json.dumps(export)))
  @F.bind_generate
  def generate(model,processor,batch,**kw):return F._current.get()
  s=generate(model,None,{},ground_backend=NS(geometry=Geometry()))
  self.assertEqual(s.spec_version,'3.14')
  with self.assertRaisesRegex(ProgramRefusal,'mismatch'):generate(model,None,{},ground_backend=NS(geometry=Geometry()),trace_program_version='3.13')
 def test_adapter_reads_model_and_rejects_config_mismatch(self):
  import importlib.util
  from unittest.mock import patch
  path=Path(__file__).resolve().parents[1]/'scripts/acceptance_live_adapter.py'
  spec=importlib.util.spec_from_file_location('adapter_version_r2',path)
  adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
  model=NS(trace_program_version='3.14');adapter.base._inputs={}
  owner=NS(geometry=Geometry())
  with patch.object(adapter.base,'routed',side_effect=lambda *args: ({},None,dict(ground_backend=owner))):
   _,_,kwargs=adapter.routed({},model,None)
   self.assertEqual(kwargs['trace_session'].spec_version,'3.14')
   adapter.base._inputs={'trace_program_version':'3.13'}
   with self.assertRaisesRegex(ProgramRefusal,'mismatch'):adapter.routed({},model,None)
 def test_missing_and_explicit_legacy(self):
  with self.assertRaisesRegex(ProgramRefusal,'missing'):resolve({})
  with self.assertRaisesRegex(ProgramRefusal,'missing'):LiveSession(NS(geometry=Geometry()))
  with self.assertRaisesRegex(ProgramRefusal,'missing'):resolve({'trace_version_binding':1},{'trace_program_version':'3.14'})
  self.assertEqual(resolve({}, {'trace_program_version':'3.13'}),'3.13')
 def test_bidirectional_form_refusals(self):
  s=Session(L,Geometry(),None,instances=lambda _:[],program_version='3.13')
  for call in ['<gap a="table" b="chair" rule="box_grid_5cm">','<gap camera="3" b="chair" rule="box_grid_5cm">']:
   with self.assertRaisesRegex(ProgramRefusal,'requires_v3.14'):s.execute(call)
  with self.assertRaisesRegex(ProgramRefusal,'requires_v3.14'):parse_response('<ground obj="chair" mode="box">','chair: 2 instances\n',program_version='3.13')
  s=scene()
  for call in ['<gap a="table" b="chair" rule="sampled_box_512">','<gap a="table" b="chair">','<extent_ends obj="table" axis="longest_observed">']:
   with self.assertRaisesRegex(ProgramRefusal,'requires_v3.13'):s.execute(call)
 def test_dead_renderers_name_generator(self):
  from trace_format.ground_v313 import render
  for fn in (B.render,B.render_camera,render):
   with self.assertRaisesRegex(ValueError,'derivgen_v7'):fn({},scene(),len)

class Perception(unittest.TestCase):
 def live(self,masks,geo=None):
  geo=geo or geometry()
  owner=NS(geometry=geo,source=NS(selector_candidates=lambda n:[Candidate(frame=k,uv=[500,500],mask=m,source='sam3') for k,m in masks] if n=='chair' else []),scene=NS(frames=getattr(geo,'frame_map',None)))
  s=LiveSession(owner,program_version='3.14');s.bind_state(NS(verify_session=None));return s
 def mask(self):
  m=np.zeros((80,112),bool);m[20:36,30:48]=True;return m
 def test_fragment_floor_count_and_unresolved(self):
  self.assertEqual(min_mask_px,P.MIN_PX);self.assertEqual(mask_floor((240,320)),154)
  valid=self.mask();fragments=[]
  for i in range(12):
   m=np.zeros_like(valid);m[2+i*4,2]=1;fragments.append((1,m))
  s=self.live([(1,valid),*fragments])
  self.assertEqual(s.execute('<ground obj="chair" mode="instances">').splitlines()[0],'chair: 1 found')
  self.assertIn('chair: frames',s.execute('<ground obj="chair" mode="box">'))
  self.assertNotIn('unresolved',s.events[-1]['response'])
  # Category-mask and pre-separated detection branches obey the same floor.
  stack=np.zeros((32,*valid.shape),bool);stack[0]=valid
  for _,m in fragments:stack[0]|=m
  self.assertEqual(len(connected_components(lambda n:(stack,np.ones(32)))('chair')[0]),1)
 def test_missing_box_and_unlifted_largest_skip(self):
  s=scene();good=obj('good');bad=obj('bad');unlifted=dict(obj('bad2'),visible=[1,2],areas={'1':1.,'2':2.})
  value=B.box([0,0,3],[1,1,1],np.eye(3))
  s._instances=lambda n:[bad,unlifted,good]
  s.box_provider=lambda n,o,g,k:None if o['instance_id']=='bad' else value
  text=s.execute('<ground obj="chair" mode="box">')
  self.assertIn('chair: frames',text);self.assertNotIn('instances',text)
  ctx=NS(ids=lambda n:['bad','good'],fixes=set(),fused=NS(seen=lambda i:True,box=lambda i:None if i=='bad' else raw(value)))
  self.assertEqual(len(P.boxes_of(ctx,'chair')),1)
  s._instances=lambda n:[bad]*9+[good]
  self.assertNotIn('unresolved',s.execute('<ground obj="chair" mode="box">'))
  s._instances=lambda n:[bad]*9
  self.assertEqual(s.execute('<ground obj="chair" mode="box">'),'chair: box unavailable')
 def test_paired_production_geometry_never_borrows_depth(self):
  from student_pilot.p3_geometry import Geometry as Paired
  calls=[]
  rawgeo=Paired(np.repeat(np.eye(3)[None],16,0),np.zeros((16,3)),np.ones((16,2)),lambda k,p:calls.append(k) or np.ones(len(p)))
  gate=ExactFrames(rawgeo)
  self.assertFalse(gate.has(3));self.assertTrue(gate.has(4))
  with self.assertRaisesRegex(ProgramRefusal,'exact_depth_frame_unavailable'):gate.lift(3,np.array([[500,500]]))
  self.assertEqual(calls,[])
 def test_own_production_odd_frame_uses_own_depth_and_pose(self):
  p=np.zeros((32,9));p[:,6]=1;p[:,7:]=1;seen=[]
  rawgeo=OwnGeometry(p,[0,-1,0],lambda k,uv:seen.append(k) or np.full(len(uv),2+k*.1))
  geo=ExactFrames(L.OwnGeometryAdapter(rawgeo));self.assertTrue(geo.has(3));self.assertTrue(geo.has_pose(3))
  world,pc,spread=geo.lift(3,np.array([[500,500]]));self.assertEqual(seen,[3]);self.assertAlmostEqual(pc[0,2],2.3,places=5)
 def test_defect_roundtrip_reference_or_direct_fallback(self):
  good=self.mask();fragment=np.zeros_like(good);fragment[1,1]=True
  for defect,masks,name in [('missing_instance',[(1,good)],'chair'),('fragment',[(1,good),(1,fragment)],'chair'),('empty_mask',[(1,np.zeros_like(good))],'chair'),('unknown_category',[(1,good)],'unlisted')]:
   with self.subTest(defect=defect):
    s=self.live(masks);text=s.execute(f'<ground obj="{name}" mode="instances">')
    # Reference merge_count sees precisely the same detections and metric depth.
    from trace_format.instance_policy314 import valid_mask
    def clicks(n,k,mode):return [np.mean(L.mask_pixels(m),axis=0) for f,m in masks if n=='chair' and f==k and valid_mask(m)]
    ctx=NS(gt=NS(valid=[True]*32,has=s.geometry.has,lift=s.geometry.lift),ground=NS(get=clicks),fixes={'merge'})
    q=dict(question_type='object_counting',question=f'How many {name}(s) are in this room?')
    self.assertEqual(text.splitlines()[0],f'{name}: {P.run_vsi(q,ctx)[0]} found')
  # A real own-depth grid with a NaN refuses through the actual response caller.
  p=np.zeros((32,9));p[:,6]=1;p[:,7:]=1
  def depth(k,uv):
   d=np.full(len(uv),2.);d[len(d)//2]=np.nan;return d
  geo=L.OwnGeometryAdapter(OwnGeometry(p,[0,-1,0],depth))
  s=self.live([(1,good)],geo);token=F._current.set(s)
  try:
   text,info=F.respond('<ground obj="chair" mode="box">',s.registry)
   self.assertTrue(info['direct_answer_fallback']);self.assertEqual(info['code'],'nonfinite_depth_grid');self.assertIn('answer directly',text)
  finally:F._current.reset(token)
  # Production paired layout with an odd-frame sighting is rejected before lifting.
  from student_pilot.p3_geometry import Geometry as Paired
  paired=Paired(np.repeat(np.eye(3)[None],16,0),np.zeros((16,3)),np.ones((16,2)),lambda k,p:np.ones(len(p)))
  s=self.live([(3,good)],paired);token=F._current.set(s)
  try:
   text,info=F.respond('<ground obj="chair" mode="box">',s.registry)
   self.assertTrue(info['direct_answer_fallback']);self.assertEqual(info['code'],'exact_depth_frame_unavailable')
  finally:F._current.reset(token)
 def test_camera_largest_matches_unmocked_prog_v2(self):
  s=scene({'chair':[B.box([0,0,1.5],[.5,.5,.5],np.eye(3)),B.box([0,0,6],[2,2,2],np.eye(3))]})
  near=dict(obj('0',3),areas={'3':50.});far=dict(obj('1',3),areas={'3':900.})
  s._instances=lambda n:[near,far];s.execute('<ground obj="chair" mode="box">')
  vals=[r['value'] for r in s.box_registry.records.values()]
  centre=B.camera_centre_f1(s.geometry,3)
  ctx=NS(gt=NS(has=lambda k:True,cam=lambda k:(np.eye(3),centre)),fixes={'extent'},ground=NS(masks=lambda n,k:[(1,np.ones((30,30))),(0,np.ones((5,10)))]),fused=NS(box=lambda i:raw(vals[i])))
  q=dict(question_type='camera_obj_abs_dist',question='What is the distance from the camera to the nearest point of the chair in frame 3 of 32?',options=[])
  expected=P.run_vsti(q,ctx)[0]
  self.assertEqual(s.execute('<gap camera="3" b="chair" rule="box_grid_5cm">'),f'distance {expected:.2f} m')
  self.assertGreater(expected,4.)

if __name__=='__main__':unittest.main()
