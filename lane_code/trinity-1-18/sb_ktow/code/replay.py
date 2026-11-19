"""Replay reader stage 1 at N frames; keep printed frame IDs in the LM's 32 anchors."""
import copy, re
import numpy as np
from common import *

KBOX_WINNING_BOX_HOOK=ROOT/'configs/KBOX_WINNING_BOX_RULE.json'

def winning_box(context=None):
 """The one deferred kbox binding: a reviewed PASS receipt and importable implementation."""
 if not KBOX_WINNING_BOX_HOOK.exists():return None
 cfg=read_json(KBOX_WINNING_BOX_HOOK)
 if cfg['status']!='PASS':return None
 decision=read_json(cfg['decision_path']);assert sha(cfg['decision_path'])==cfg['decision_sha256']
 verdict=decision
 for key in cfg['pass_pointer'].split('/'):
  if key:verdict=verdict[int(key)] if isinstance(verdict,list) else verdict[key]
 if verdict!='PASS':return None
 path=local(cfg['module_path']);assert sha(path)==cfg['module_sha256']
 import importlib.util
 spec=importlib.util.spec_from_file_location('kbox_winner',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return getattr(module,cfg['callable'])(context)

def cached_detections(cache,name,n_frames):
 from student_pilot.routed_candidates import small_rle
 from student_pilot.routed_features import resize,SHAPE
 key=name.strip().lower()
 if key not in cache['phrases']:raise ValueError('MISSING raw prompt '+repr(key))
 result=[]
 for i in range(n_frames):
  r=cache['frames'][str(i)]['phrases'][key]
  raw=[p for p in r.get('instances') or [] if p.get('source_prompt',key)==key]
  presence=float(raw[0]['source_presence']) if raw and 'source_presence' in raw[0] else float(r['presence'])
  if raw and len({p.get('source_presence') for p in raw})!=1:raise ValueError('Raw-name source presence differs')
  chosen=[p for p in sorted(raw,key=lambda p:-float(p['score'])) if float(p['score'])*presence>=.05][:30]
  # Decode the exact cached native mask before the reader's 480x640 resize.
  values=[]
  for p in chosen:
   rle=p['mask'];h,w=rle['size'];counts=np.asarray(rle['counts'],int)
   if (counts<0).any() or counts.sum()!=h*w:raise ValueError('Invalid RLE')
   mask=np.repeat(np.arange(len(counts))%2,counts).reshape((h,w),order='F').astype(bool)
   values.append(dict(mask=resize(mask,SHAPE),score=float(p['score']),presence=presence))
  result.append(values)
 return result

def load_selector():
 from selector_head import load_head
 root=Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso')
 for name in ('selector_head.json','selector_head.safetensors'):sha(root/name)
 return load_head(root)[0]

def make_stage(cache,geometry,n,head=None):
 from e2e_reader.stage1 import StageOne
 from e2e_reader.grounding import StageOneSocket
 head=load_selector() if head is None else head
 stage=StageOne(lambda name:cached_detections(cache,name,n),head,geometry,n_frames=n)
 # A0 uses candidates_argmax; the same head and vectors, excluding only the null slot.
 def select(inputs):
  import torch
  with torch.no_grad():return int(torch.argmax(head(inputs['x'],None,inputs['name'])))
 socket=StageOneSocket(stage.propose,select,(240,320),n)
 memo={}
 def cached(name):
  if name not in memo:memo[name]=socket(name)
  return memo[name]
 return stage,cached

def printed_frames(dense_members,anchor_slots):
 mapping={int(slot)+1:i+1 for i,slot in enumerate(anchor_slots)}
 return sorted({mapping[f] for f in dense_members if f in mapping})

def make_session(geometry,socket,anchor_slots=None,box_rule=None):
 from trace_format.ground_v313 import Session
 from student_pilot import ground_lifting
 from e2e_reader.grounding import MinAreaBoxProvider,lift_bestspread
 class Provider(MinAreaBoxProvider):
  def __call__(self,name,obj,geometry,best):
   if '_dense_box' in obj:return obj['_dense_box']
   return super().__call__(name,obj,geometry,best)
 class S(Session):
  def __init__(self):
   super().__init__(ground_lifting,geometry,None,instances=lambda name:(),program_version='3.14',multi_instance=True,geometry_mode='sensor',box_provider=Provider())
  def _instances(self,name):
   output=[]
   for e in socket(name):
    r=box_rule(name,e['masks'],geometry) if box_rule else lift_bestspread(name,e['masks'],geometry)
    if not r['seen']:continue
    # Box fit uses all tower-frame points. Only the textual member list is projected.
    members=np.flatnonzero(np.asarray(e['masks']).reshape(len(e['masks']),-1).any(1))+1
    r=dict(r,instance_id=e['instance_id'],first=min(r['frames']))
    if anchor_slots is not None:
     mapping={int(slot)+1:i+1 for i,slot in enumerate(anchor_slots)}
     shared=[f for f in r['frames'] if f in mapping]
     if not shared:continue
     dense_best=min(r['visible'],key=lambda f:(-r['areas'][str(f)],f))
     if dense_best not in r['frames']:continue
     box=MinAreaBoxProvider()(name,r,geometry,dense_best)
     r=dict(r,_dense_box=box,frames=[mapping[f] for f in shared],visible=[mapping[f] for f in shared],
       areas={str(mapping[f]):r['areas'][str(f)] for f in shared},points={},first=min(mapping[f] for f in shared))
    output.append(r)
   return output
 return S()

def price(c,geometry,cache=None,n=32,gt=None,head=None,box_rule=None):
 from e2e_reader.grounding import lift_bestspread
 stage=socket=None
 if gt is None:stage,socket=make_stage(cache,geometry,n,head)
 rows=[]
 for row in c['rows']:
  if row['type']!='object_abs_distance':continue
  if gt is not None:
   def socket(name):
    iid=row.get('gt_instances',{}).get(name)
    if iid is None:return []
    masks=gt['inst']==iid;masks[~gt['valid'].astype(bool)]=False
    return [dict(instance_id=str(iid),masks=masks)]
  session=make_session(geometry,socket,c['anchor_slots'] if n==64 else None,box_rule)
  names=row['operands'];ground=[];members=[]
  for name in names:
   ground.append(session.execute(f'<ground obj="{name}" mode="box">'))
   entries=socket(name);members.append(sorted((np.flatnonzero(entries[0]['masks'].reshape(n,-1).any(1))+1).tolist()) if entries else [])
  text=session.execute(f'<gap a="{names[0]}" b="{names[1]}" rule="box_grid_5cm">')
  m=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',text)
  rows.append(dict(row_id=row['id'],capture=c['canonical'],room=c['room'],split=c['k1_split'],prediction=float(m[1]) if m else None,response=text,ground=ground,member_frames=members,printed_frames=[printed_frames(v,c['anchor_slots']) for v in members] if n==64 else members,min_member_frames=min(map(len,[printed_frames(v,c['anchor_slots']) for v in members] if n==64 else members)),dense_min_member_frames=min(map(len,members)),box_records=copy.deepcopy(session.box_registry.records),box_bindings=copy.deepcopy(session.box_registry.bindings),names=names))
 return rows

def flagged_row(base,dense):
 """Use each operand's dense box iff its baseline printed response has <3 frames."""
 from trace_format.box_v313 import BoxRegistry as Registry
 registry=Registry();chosen=[]
 for name,btext,dtext in zip(base['names'],base['ground'],dense['ground'],strict=True):
  m=re.search(r': frames ([0-9,]+)',btext)
  count=len(m[1].split(',')) if m else 0
  source=dense if count<3 else base
  labels=source['box_bindings'].get(name,[])
  if not labels:registry.invalidate(name);chosen.append(count<3);continue
  record=source['box_records'][labels[0]]
  from trace_format.box_v313 import serialize
  text=serialize(name,'B'+str(len(registry.records)+1),record['frames'],record['best'],record['value'])
  registry.ingest(text,record['value']);chosen.append(count<3)
 text,_=registry.gap(base['names'][0],[base['names'][1]],'box_grid_5cm')
 match=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',text)
 return dict(base,response=text,prediction=float(match[1]) if match else None,dense_operands=chosen)

def selector_diagnostics(c,cache,geometry,n,gt,head=None):
 """Report the label rule on the 32 authoritative GT anchors for both N values.

 Full 64-view labels remain MISSING; dense-only proposals are unlabelled.
 The K1 label rule is IoU > .5 on at least half of the labelled member masks.
 """
 import torch
 from scipy import ndimage
 stage,_=make_stage(cache,geometry,n,head)
 truth=np.asarray(gt['inst']);h,w=truth.shape[1:]
 if (h,w)!=(240,320):truth=np.stack([ndimage.zoom(f,(240/h,320/w),order=0,prefilter=False) for f in truth])
 mapping={int(s)+1:i for i,s in enumerate(c['anchor_slots'])} if n==64 else {i+1:i for i in range(32)}
 objects=[]
 for name in sorted({v.strip().lower() for r in c['rows'] for v in r.get('operands',[])}):
  if name not in c['gt_name_ids']:objects.append(dict(name=name,status='MISSING',reason='No named GT instance authority'));continue
  accepted,x=stage.features(name);labels=[]
  for cand in accepted:
   hits=[]
   for f,mask in cand['masks'].items():
    if int(f) not in mapping or not gt['valid'][mapping[int(f)]]:continue
    target=truth[mapping[int(f)]];ious=[]
    for iid in c['gt_name_ids'][name]:
     t=target==iid;union=np.logical_or(mask,t).sum();ious.append(float(np.logical_and(mask,t).sum()/union) if union else 0.)
    hits.append(max(ious,default=0.)>.5)
   labels.append(int(np.mean(hits)>=.5) if hits else None)
  if not accepted:objects.append(dict(name=name,status='NO_CANDIDATE',correct=False,has_positive=False));continue
  with torch.no_grad():k=int(torch.argmax(stage.head(torch.tensor(x,dtype=torch.float64),None,name)))
  objects.append(dict(name=name,status='OK' if labels[k] is not None else 'MISSING',chosen_id=accepted[k]['candidate_id'],correct=labels[k]==1 if labels[k] is not None else None,has_positive=1 in labels,candidate_labels=labels))
 eligible=[r for r in objects if r.get('has_positive') and r.get('correct') is not None]
 return dict(N=n,label_scope='32 GT anchors only',full_64_frame_labels='MISSING' if n==64 else 'not applicable',objects=objects,eligible_objects=len(eligible),top1=sum(r['correct'] for r in eligible)/len(eligible) if eligible else None)
