"""Reader grounding for proposals, GT-mask checks, and video track candidates."""
import numpy as np
import re
from common import *
from box_hook import load as box_hook
from e2e_reader import grounding as G
from trace_format import box_v313 as B


def decode(rle):
 h,w=rle['size'];counts=np.asarray(rle['counts'],int)
 if (counts<0).any() or counts.sum()!=h*w:raise ValueError('invalid RLE')
 return np.repeat(np.arange(len(counts))%2,counts).reshape((h,w),order='F').astype(bool)

def cached(cache,name):
 from student_pilot.routed_features import resize,SHAPE
 if name not in cache['phrases']:raise Missing('proposal prompt '+name)
 out=[]
 for i in range(len(cache['frames'])):
  r=cache['frames'][str(i)]['phrases'][name];pr=float(r['presence'])
  kept=[e for e in sorted(r['instances'],key=lambda e:-e['score']) if e['score']*pr>=.05][:30]
  out.append([dict(mask=resize(decode(e.get('reader_mask',e['mask'])),SHAPE),score=e['score'],presence=pr) for e in kept])
 return out

def selector():
 from selector_head import load_head
 p=Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso')
 sha(p/'selector_head.json');h=sha(p/'selector_head.safetensors')
 if not h.startswith('6d97c524'):raise ValueError('selector checkpoint differs from registered head')
 return load_head(p)[0]

class PredictedSource:
 def __init__(self,cache,geo,rule):
  from e2e_reader.stage1 import StageOne
  self.stage=StageOne(lambda n:cached(cache,n),selector(),geo,rule='candidates_argmax',n_frames=len(geo.C));self.rule=rule
 def __call__(self,name):
  import torch
  F=self.stage.F;accepted,x=self.stage.features(name)
  if not accepted:return dict(entries=[],count=0 if self.rule=='object' else None)
  with torch.no_grad():choice=self.stage.select(dict(x=torch.tensor(x,dtype=torch.float64),name=name))
  raw=self.stage.raw[name];proposals,_=F.candidates.lift(F.cache_for(name,raw),name,self.stage.geometry,floor=.3,grids=self.stage.grids,phrase=name,n_frames=self.stage.n_frames)
  linked={c.id:c for c in F.candidates.link(proposals,name)};track=linked[accepted[choice]['candidate_id']];members=track.proposals
  count=None
  if self.rule=='object':
   hook,gate=box_hook(True);members=hook.gather(members,proposals)
   if hasattr(hook,'count_objects'):count=hook.count_objects(list(linked.values()),proposals)
  masks=np.zeros((self.stage.n_frames,240,320),bool)
  for p in members:masks[p.frame-1]=F.resize(raw[p.frame-1][p.index]['mask'],(240,320))
  return dict(entries=[dict(instance_id=track.id,masks=masks,tie_index=min((p.frame,p.index) for p in members))],count=count)

class TrackSource:
 def __init__(self,tracks,geo,head=None,probe=False):self.tracks=tracks;self.geo=geo;self.head=head;self.selection=[];self.probe=probe
 def __call__(self,name):
  from student_pilot import routed_features as F
  from student_pilot import routed_candidates as RC
  tracks=[t for t in self.tracks[name] if max((f['score'] for f in t['frames']),default=0)>=.3 and any(decode(f['mask']).mean()>=.002 for f in t['frames'])]
  if not tracks:return dict(entries=[],count=0)
  raw=[[] for _ in range(len(self.geo.C))];membership={};masks={};first={}
  for t in tracks:
   arr=np.zeros((len(raw),240,320),bool);eligible=[]
   for f in t['frames']:
    slot=f['frame']-1;mask=decode(f['mask']);arr[slot]=F.resize(mask,(240,320))
    if mask.mean()>=.002:eligible.append(f['frame'])
    membership[(slot,len(raw[slot]))]=t['id'];raw[slot].append(dict(mask=F.resize(mask,F.SHAPE),score=f['score'],presence=1.))
   masks[t['id']]=arr;first[t['id']]=min(eligible) if eligible else None
  # Build linked candidates directly, without the geometric linker or gather.
  # Lift each track alone so score sorting cannot change track ownership.
  candidates=[]
  for t in tracks:
   one=[[] for _ in raw]
   for f in t['frames']:one[f['frame']-1]=[dict(mask=F.resize(decode(f['mask']),F.SHAPE),score=f['score'],presence=1.)]
   pp,_=RC.lift(F.cache_for(name,one),name,self.geo,floor=0.,phrase=name,n_frames=len(raw))
   for proposal in pp:proposal.index=next(i for (slot,i),iid in membership.items() if slot==proposal.frame-1 and iid==t['id'])
   if pp:candidates.append(RC.Candidate(name,str(t['id']),pp))
  reason=None
  policy='candidates_argmax' if self.probe else js(ROOT/'out/TRACK_SELECTION.json')['selection']
  try:
   if policy=='peak_score':raise ValueError('CPU-fixed peak-score track policy')
   import torch,selector_inputs as SI
   RC.scene_candidates({name:candidates},self.geo,len(raw));exact=F.Geometry(self.geo,len(raw))
   accepted=F.accept_features(candidates,raw,exact)
   if len(accepted)!=len(tracks):raise ValueError('track not accepted by selector featuriser')
   x=SI.candidate_vectors(candidates,raw,exact,accepted)
   head=self.head if self.head is not None else selector()
   with torch.no_grad():i=int(torch.argmax(head(torch.tensor(x,dtype=torch.float64),None,name)))
   winner=accepted[i]['candidate_id'];chosen=next(t for t in tracks if str(t['id'])==str(winner))
  except (ValueError,KeyError,IndexError,TypeError) as e:
   if not self.probe and policy!='peak_score':raise Missing('Frozen track selector cannot featurise this track: '+str(e))
   chosen=max(tracks,key=lambda t:max(f['score'] for f in t['frames']));reason=str(e)
  self.selection.append(dict(name=name,selection='peak_score' if reason else 'candidates_argmax',reason=reason))
  t=chosen;arr=masks[t['id']];start=first[t['id']]
  return dict(entries=[dict(instance_id=str(t['id']),masks=arr,first_override=start,tie_index=(start or 10**9,next((i for (slot,i),iid in membership.items() if slot==(start or 0)-1 and iid==t['id']),0)))],count=len(tracks),count_conf=sum(max(f['score'] for f in t['frames'])>=.5 for t in tracks),selection=self.selection[-1])

class Grounder:
 def __init__(self,geometry,source,rule='today',anchor_slots=None):
  self.geometry=geometry;self.source=source;self.rule=rule;self.anchor_slots=anchor_slots;self.cache={};self.registry=B.BoxRegistry()
  self.mapping={int(s)+1:i+1 for i,s in enumerate(anchor_slots)} if anchor_slots is not None else {i:i for i in range(1,len(geometry.C)+1)}
 def __call__(self,name):
  if name in self.cache:return self.cache[name]
  result=self.source(name);entries=result['entries'];count=result.get('count');obj=dict(seen=False,box_available=False,frames=[],first=None,tie_index=None,count=count,count_conf=result.get('count_conf'),refusal='not seen')
  if not entries:self.cache[name]=obj;return obj
  e=entries[0];m=np.asarray(e['masks'],bool);members=(np.flatnonzero(m.reshape(len(m),-1).any(1))+1).tolist()
  printed=sorted(self.mapping[f] for f in members if f in self.mapping)
  if not printed:self.cache[name]=obj;return obj
  first=e.get('first_override',min(members));first=self.mapping.get(first)
  obj.update(seen=first is not None,frames=printed,first=first,tie_index=e.get('tie_index',(min(members),0)),refusal=None)
  if first is None:self.cache[name]=obj;return obj
  try:
   if self.rule=='today':
    lifted=G.lift_bestspread(name,m,self.geometry);best=min(lifted['frames'],key=lambda f:(-lifted['areas'][str(f)],f));raw=G.MinAreaBoxProvider()(name,lifted,self.geometry,best)
   else:
    hook,gate=box_hook(True);points={};areas={}
    for f,mask in enumerate(m,1):
     if not mask.any() or not self.geometry.has(f):continue
     p,pc,sp=self.geometry.lift(f,G.mask_pixels(mask),mode='center');keep=np.isfinite(p).all(1)&np.isfinite(pc).all(1)&(pc[:,2]>0)
     if keep.any():p,sp=p[keep],sp[keep];points[f]=p[sp<=np.median(sp)];areas[f]=mask.mean()
    best=min(points,key=lambda f:(-areas[f],f));fused=hook.fusion_box(points,best,gate['rule'],G.min_area_box)
    raw=B.in_f1(self.geometry,fused['centroid'],fused['axesLengths'],fused['normalizedAxes'])
   # Dense views affect the box; the formatter receives only original LM slots.
   visible_best=best if best in self.mapping else min((f for f in members if f in self.mapping),key=lambda f:(-m[f-1].mean(),f))
   text=B.serialize(name,'B'+str(len(self.registry.records)+1),printed,self.mapping[visible_best],raw)
   self.registry.ingest(text,raw);parsed=B.parse(text)
   obj.update(box_available=True,printed_lengths=parsed['value']['lengths'],response=text)
  except ValueError as exc:obj.update(refusal='box unavailable: '+str(exc))
  self.cache[name]=obj;return obj
 def gap(self,a,b):
  self(a);self(b);text,_=self.registry.gap(a,[b],'box_grid_5cm');match=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',text)
  return float(match[1]) if match else None
