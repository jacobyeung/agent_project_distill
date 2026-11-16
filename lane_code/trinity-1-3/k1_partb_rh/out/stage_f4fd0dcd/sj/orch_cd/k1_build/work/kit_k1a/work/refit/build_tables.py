"""K1 I/O adapter around unchanged candidate/set-feature and GT label rules."""
import collections,importlib.util,itertools,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import gate
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'native_kit'))
import bindings as B
import numpy as np
def original_build():
 p=gate.ROOT/'grd_selector/work/setsel/build.py'
 spec=importlib.util.spec_from_file_location('b6_original_build',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def extract(c,raw,geometry):
 """Execute the runtime's unselected candidate and feature producers, without GT."""
 from types import SimpleNamespace as NS
 from student_pilot import routed_features as F
 from student_pilot.scene_state import FrameMap
 source=NS(cache=raw,reader=NS(phrase=B.kitlib.normalize_phrase,rle_decode=B.kitlib.decode),live=None,frame_indices=tuple(c['anchor_indices']))
 exact=F.Geometry(geometry);grids=F.candidates.lift_grid(geometry);pools={};frames={}
 for name in raw['phrases']:
  frames[name],origin=F.detections(source,name,FrameMap(tuple(c['anchor_indices'])))
  proposals,_=F.candidates.lift(F.cache_for(name,frames[name]),name,geometry,floor=.3,grids=grids,phrase=name)
  pools[name]=F.candidates.link(proposals,name)
 F.candidates.scene_candidates(pools,geometry)
 return {name:F.accept_features(pools[name],frames[name],exact) for name in pools},exact
def label(c,features,geometry,gt,*,fixture=False):
 if not fixture and not gate.eligible(*c['canonical'].split('/')):raise ValueError('Excluded table capture')
 from student_pilot import routed_features as F
 build=original_build();rows=[];pairs=[]
 if gt['frame_indices'].tolist()!=c['anchor_indices']:raise ValueError('GT anchor identity differs')
 truth=gt['instances'];allids=[int(i) for i in np.unique(truth) if i>=0]
 named=c['gt_name_ids']
 for name,group in features.items():
  if name not in named:raise ValueError('Missing named GT instance authority: '+name)
  build.set_features(group,None)
  identities={}
  for cand in group:
   mem=[]
   for frame,mask in cand['masks'].items():
    if mask.shape!=truth[frame-1].shape:raise ValueError('GT raster differs; no silent resize')
    score=[(build.iou(mask,truth[frame-1]==i),i) for i in named[name]]
    value,identity=max(score,default=(0.,-1))
    av,ai=max(((build.iou(mask,truth[frame-1]==i),i) for i in allids),default=(0.,-1))
    mem.append(dict(slot=frame-1,gid=identity if value>.5 else -1,iou=value,any_gid=ai,any_iou=av))
   hit=float(np.mean([m['gid']>=0 for m in mem]))
   ids=[m['any_gid'] for m in mem if m['any_iou']>.5 and m['any_gid']>=0]
   identities[cand['candidate_id']]=collections.Counter(ids).most_common(1)[0][0] if ids and len(ids)>=.5*len(mem) else None
   rows.append(dict(kind='candidate',scene=c['canonical'],object_id=c['canonical']+'::'+name,name=name,
      candidate_id=cand['candidate_id'],features=cand['features'],members=mem,y=int(hit>=.5),hit_frac=hit))
  ys={r['candidate_id']:r['y'] for r in rows if r['name']==name}
  for a,b in itertools.combinations(group,2):
   ai,bi=identities[a['candidate_id']],identities[b['candidate_id']]
   pairs.append(dict(scene=c['canonical'],object_id=c['canonical']+'::'+name,a=a['candidate_id'],b=b['candidate_id'],
      ya=ys[a['candidate_id']],yb=ys[b['candidate_id']],y=-1 if ai is None or bi is None else int(ai==bi),f=F.pair_features(a,b,geometry)))
 return rows,pairs
def build_capture(c,raw,geometry,gt,*,fixture=False):
 features,g=extract(c,raw,geometry)
 return label(c,features,g,gt,fixture=fixture)
