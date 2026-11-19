"""Lane-local harness R0 adapter. No harness module or its global write hook is imported."""
import ast,sys
from common import *
import numpy as np
sys.path.insert(0,str(TREE));sys.path.insert(0,str(W/'vendor'))
import k1_convert as kc
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format import room_v314 as room
# Extract only reviewed function definitions. The unused R1 binding permits the original
# areas() body to execute unchanged; only its R0 result is ever exposed or consumed.
source=W/'vendor/harness.py'
assert sha(source)=='0edcd58616a4d9b6ec884be4e99f2932250b9f9b950ab7e12e085334151fe3d4'
nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('attempt','areas')]
assert len(nodes)==2
ns={'np':np,'room':room,'r1':room.from_points}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
def areas(geo,mode='predicted'): return {'R0':ns['areas'](geo,mode)['R0']}
def trim(sample,geo,pct=90):
 pts=[]
 for k,P in zip(sample['frames'],sample['points']):
  r=np.linalg.norm(P-np.asarray(geo.cam(k)[1],float),axis=1)
  pts.append(P[r<=np.percentile(r,pct)] if len(r) else P)
 return dict(sample,points=pts)
def arrays(path):
 with np.load(path,allow_pickle=False) as z: p={k:z[k] for k in z.files}
 if 'depth_grid' not in p:p['depth_grid']=p['depth_grid64']
 if 'item_slots' not in p:p['item_slots']=p['anchor_slots']
 n=len(p['frame_indices']);slots=p['item_slots'].astype(int)
 assert len(slots)==32 and len(set(slots))==32 and min(slots)>=0 and max(slots)<n
 assert p['depth_grid'].shape==(n,51,51) and p['c2w'].shape==(n,4,4) and p['intrinsics'].shape==(n,3,3)
 return p
def convert(path,dest):
 p=arrays(path);slots=p['item_slots'].astype(int);anchors=p['frame_indices'][slots].astype(int).tolist()
 C,up=kc.native_cameras(p['c2w'][slots],ct)
 kc.write(Path(dest),anchors,p['intrinsics'][slots].copy(),kc.canvas_affine(p['source_hw']),C,p['depth_grid'][slots].astype(np.float64),np.linspace(0,1000,51),1.,load_geometry,FrameMap)
 geo=load_geometry(dest,FrameMap(tuple(anchors)),'tower_scaled')
 assert geo.depth_scale_count==geo.pose_scale_count==1
 return geo
def price(geo,rule='R0'):
 try:
  sample=room.sample(geo,'predicted');sample=trim(sample,geo) if rule=='T10' else sample
  result=room.from_points(**sample);response=room.format_result(result);parsed=room.parse_response(response)
  area=float(parsed['area_m2'])
  if rule=='R0':
   harness_area,refusal=areas(geo)['R0'];assert (area,None)==(harness_area,refusal)
  return dict(area_m2=area,refusal=None,response=response,**{k:v for k,v in result.items() if k in ('floor_cells','supported_cells','floor_height_m')})
 except (ValueError,KeyError,FloatingPointError,np.linalg.LinAlgError) as e:
  return dict(area_m2=None,refusal=getattr(e,'code',str(e)),response=None)
def pipeline(path,dest,rule='R0'):
 try:geo=convert(path,dest)
 except ValueError as e:
  if str(e)!='reference_camera_up_opposes_gravity':raise
  return dict(area_m2=None,refusal=str(e),response=None)
 return price(geo,rule)
def input_code():
 modules=[ct,room,sys.modules[load_geometry.__module__],sys.modules[FrameMap.__module__]]
 return {**code_hashes(),**{str(Path(m.__file__)):sha(m.__file__) for m in modules}}
