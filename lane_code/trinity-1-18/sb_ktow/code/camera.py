"""Reader camera formatting and mandatory real-item parity gate."""
import re
import numpy as np
from common import *
from cpu_formatter import OwnGeometry

def response(raw_pose,scale,gravity,call):
 pose=np.asarray(raw_pose,float).copy();assert pose.shape==(32,9)
 pose[:,:3]*=scale
 m=re.fullmatch(r'<(move|turn) from=(\d+) to=(\d+)>',call)
 if not m:raise ValueError('Unsupported camera call: '+call)
 own=OwnGeometry(pose,np.asarray(gravity,float),None)
 return getattr(own,m[1]+'_text')(int(m[2]),int(m[3]))

def ratio_scale(stored,depth32,depth64):
 a,b=np.asarray(depth32,float),np.asarray(depth64,float)
 if a.shape!=b.shape:raise ValueError('Shared anchor depth grids differ')
 ok=np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
 if not ok.any():raise ValueError('No valid shared depth grid points')
 return float(stored*np.median(a[ok]/b[ok]))

def parity(items):
 results=[]
 for item in items:
  text=response(item['raw_pose32'],item['scale'],item['gravity'],item['call'])
  results.append(dict(id=item['id'],equal=text==item['stored_response'],recomputed=text,stored=item['stored_response']))
 matched=sum(r['equal'] for r in results)
 return dict(status='PASS' if len(results)==450 and matched>=440 else 'BLOCKER',matched=matched,total=len(results),required_matches=440,required_total=450,items=results)

def synthetic():
 # Known camera centres: frame 2 is one metre to the right; identity orientations.
 pose=np.zeros((32,9));pose[:,6]=1.;pose[:,7:]=1.;pose[1,0]=-1.
 outputs={call:response(pose,2.,[0.,-1.,0.],call) for call in ('<move from=1 to=2>','<turn from=1 to=2>')}
 expected={'<move from=1 to=2>':'dx = +2.00 m, dy = +0.00 m, dz = +0.00 m, distance = 2.00 m','<turn from=1 to=2>':'turn = +0 deg'}
 return dict(status='PASS' if outputs==expected else 'FAIL',mode='synthetic_only',outputs=outputs,expected=expected,real_parity_gate='MISSING: 450 routed step-544 records')

def da3_pose(c2w,intrinsics,hw,anchors):
 from student_pilot.camera_targets import encode_cameras
 raw,valid,_=encode_cameras(np.asarray(c2w)[anchors],np.asarray(intrinsics)[anchors],hw,all_frames=True)
 if not valid.all():raise ValueError('DA3 camera trajectory contains invalid anchors')
 return raw
