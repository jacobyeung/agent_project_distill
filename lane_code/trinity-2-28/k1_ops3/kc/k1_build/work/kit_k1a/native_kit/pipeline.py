"""CPU control path: dense inference, frozen proposals, native selector/renderer, GT-only filtering."""
import sys,json,re,math,time,os,shutil
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B
TYPES=('object_abs_distance','room_size_estimation')
SETTING=dict(joint_floor=.05,cap=100,prompts='dense_aliases',mask_threshold=.5,resolution=1008,dtype='bf16',link_instance_floor=.3)


def validate_capture(c,exclusions):
 if not exclusions.get('complete') or set(exclusions.get('authorities',{}))!={'benchmark','dev_s1'}:raise ValueError('Unknown exclusion closure')
 if c['canonical'] in exclusions['scenes'] or c['room'] in exclusions['rooms']:raise ValueError('Excluded scene/room')
 if c.get('split')!='train':raise ValueError('Training membership unproved')
 frames=c['dense_frames'];indices=[x['index'] for x in frames];slots=c['anchor_slots']
 # Dense here means the full declared 64/96-frame reconstruction sequence, before 32 LM anchors.
 if len(frames) not in (64,96) or len(slots)!=32:raise ValueError('Require dense 64/96 sequence before 32 anchors')
 if any(type(x) is not int for x in indices+slots) or indices[0]<0 or any(np.diff(indices)<=0) or slots[0]!=0 or any(np.diff(slots)<=0) or slots[-1]>=len(frames):raise ValueError('Invalid frame order')
 if [indices[s] for s in slots]!=c['anchor_indices']:raise ValueError('Dense/anchor identity mismatch')
 if not c.get('dense_source_authority'):raise ValueError('Dense sequence needs provenance')
 if not c['rows']:raise ValueError('Capture has no rows')
 ids=set()
 for r in c['rows']:
  if r['id'] in ids:raise ValueError('Duplicate row')
  ids.add(r['id'])
  if r['type'] not in TYPES:raise ValueError('Unsupported routing type')
  if not math.isfinite(float(r['gt_value'])) or r['gt_value']<0:raise ValueError('Invalid GT value')
  if r['unit'] not in ('m','m2'):raise ValueError('Input values must use canonical units')
  if r['type']==TYPES[0]:
   if len(r['operands'])!=2 or len(set(r['operands']))!=2:raise ValueError('Distance needs two different operands')
   for n in r['operands']:
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9 _-]*",n) or not re.search(r'(?<!\w)'+re.escape(n)+r'(?!\w)',r['question'],re.I):raise ValueError('Operand has no question provenance')
  elif r['operands']:raise ValueError('Room rows do not need masks')
 return c


def calls_for(row):
 if row['type']==TYPES[1]:return ['<ground mode="room">']
 a,b=row['operands']
 return [f'<ground obj="{a}" mode="box">',f'<ground obj="{b}" mode="box">',f'<gap a="{a}" b="{b}" rule="box_grid_5cm">']


def proposals(c,images,boundary):
 """Real frozen postprocessing and alias merge; only model inference is replaceable."""
 import torch
 import torch.nn.functional as F
 from sam3_tower import FrameDetections,_map_tensors
 names=sorted({n for r in c['rows'] for n in r['operands']});phrases=sorted({B.kitlib.normalize_phrase(n) for n in names})
 raw=dict(contract=SETTING,stub=boundary.synthetic,phrases=phrases,frame_indices=c['anchor_indices'],frames={str(k):dict(size=[images[0].width,images[0].height],phrases={}) for k in range(32)})
 if not phrases:return raw
 tower=boundary.sam();features=tower.encode(images)
 def detect(prompt):
  ds=B.sam_backend.detect_prompt(tower,features,prompt,B.sam_backend.make_postprocess(F,torch,FrameDetections,.05,30),_map_tensors)
  if len(ds)!=32:raise ValueError('SAM frame count differs')
  return [B.sam_backend.prediction(d,n,prompt,B.sam_backend.rle_encode) for d,n in ds]
 for ph in phrases:
  recs=detect(ph)
  for alias in B.variantlib.aliases(ph):
   extra=detect(alias)
   recs=[B.variant_cache.merge_record(a,b,(images[0].height,images[0].width),alias) for a,b in zip(recs,extra,strict=True)]
  for k,r in enumerate(recs):
   if len(r['instances'])>100:raise ValueError('Frozen combined proposal cap exceeded')
   raw['frames'][str(k)]['phrases'][ph]=r
 raw.update(contract=SETTING,stub=boundary.synthetic)
 return raw


def mask_agreement(record,row,gt,frame_indices):
 """Require every accepted instance to match the row's designated GT ID on >= half its supported frames."""
 from student_pilot.live_instances314 import unpack_mask
 if row['type']==TYPES[1]:return dict(ok=True,applicable=False,operands=[])
 if gt is None:return dict(ok=False,reason='GT masks unavailable')
 if gt['frame_indices'].tolist()!=frame_indices:raise ValueError('GT anchor order mismatch')
 evidence=[]
 for name in row['operands']:
  queries=[q for q in record['heads']['ground_queries'] if q.get('name')==name]
  target=row.get('gt_instances',{}).get(name)
  if target is None or not queries or not queries[-1].get('instances'):return dict(ok=False,reason='GT identity/accepted mask missing')
  for inst in queries[-1]['instances']:
   masks=unpack_mask(inst);truth=gt['instances']==target
   if masks.shape!=truth.shape:raise ValueError('GT and accepted mask rasters differ')
   support=masks.reshape(32,-1).sum(1)>0
   inter=(masks&truth).reshape(32,-1).sum(1);union=(masks|truth).reshape(32,-1).sum(1)
   iou=inter/np.maximum(union,1);fraction=float(np.mean(iou[support]>.5)) if support.any() else 0.
   # Mixed identities are not accepted by a majority over different IDs.
   evidence.append(dict(name=name,gt_instance=target,support=int(support.sum()),match_fraction=fraction,ok=fraction>=.5))
 return dict(ok=bool(evidence) and all(e['ok'] for e in evidence),applicable=True,operands=evidence)


def failure(call):
 return call.get('kind')=='error' or bool(call.get('code')) or bool(re.search(r'\b(?:not_seen|not seen|unavailable|refused|error)\b',call['response'],re.I))


def classify(row,record,match):
 failed=any(failure(c) for c in record['calls'])
 if failed:return dict(label='fallback',reason='runtime_failure',value=None)
 body=record['calls'][-1]['response']
 if row['type']==TYPES[0]:
  m=re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m',body);value=float(m[1]) if m else None
 else:
  from trace_format.room_v314 import parse_response
  try:value=float(parse_response(body)['area_m2'])
  except (ValueError,KeyError):value=None
 if value is None or not math.isfinite(value):return dict(label='left_out',reason='unparsed_success',value=None)
 gt=float(row['gt_value']);agrees=abs(value-gt)<=.15*abs(gt)
 return dict(label='trust' if agrees and match['ok'] else 'left_out',reason='agrees_and_instance_matches' if agrees and match['ok'] else 'numeric_or_instance_mismatch',value=value)


def render_row(row,geometry,raw,c,dest,gt):
 names=tuple(raw['phrases']);source=NS(cache=raw,reader=NS(phrase=B.kitlib.normalize_phrase,rle_decode=B.kitlib.decode),live=None,names=names,frame_indices=tuple(c['anchor_indices']),identity='o3:'+B.digest(raw))
 batch=dict(video_sha256=c['video_sha256'],frame_indices=c['anchor_indices'])
 task=dict(question_type=row['type'],student_input=dict(question=row['question'],options=[]))
 backend=B.perception.backend(task,batch,geometry,source,dest) if row['operands'] else None
 record=B.perception.execute_calls(geometry,backend,calls_for(row))
 # Keep the first real failure. No invalid follow-on call enters a fallback training trace.
 for i,call in enumerate(record['calls']):
  if failure(call):record['calls']=record['calls'][:i+1];break
 match=mask_agreement(record,row,gt,c['anchor_indices']) if not any(failure(x) for x in record['calls']) else dict(ok=False,reason='runtime_failure')
 decision=classify(row,record,match)
 return dict(id=row['id'],type=row['type'],canonical=c['canonical'],decision=decision,mask_match=match,calls=record['calls'],ground_queries=[dict(name=q.get('name'),state=q.get('state'),instance_ids=[i['instance_id'] for i in q.get('instances',[])],merge_rule=q.get('merge_rule')) for q in record['heads']['ground_queries']],synthetic=raw.get('stub',False),training_admitted=False)


def train_events(row,result):
 """Ground-form events keep response spans maskable. Fallback trace requires independent supplied evidence."""
 if result['decision']['label']=='left_out':return None
 label=result['decision']['label'];events=[dict(kind='ground_trace_start',trace_revision='3.14'),dict(kind='canonical_text',text='<think>\nI will measure the scene with the tool.\n')]
 for i,call in enumerate(result['calls']):
  events.extend([dict(kind='ground_call',token=call['call']+'\n',call_id=f'ground-{i}'),dict(kind='ground_response',text='<tool_response>\n'+call['response']+'\n</tool_response>',call_id=f'ground-{i}'),dict(kind='canonical_text',text='\n')])
 if label=='fallback':
  direct=row.get('fallback')
  if not direct or not direct.get('visual_evidence_verified') or not direct.get('trace') or not direct.get('answer'):
   return None
  if re.search(r'<(?:ground|gap|tool_response)|\d',direct['trace']):raise ValueError('Fallback trace must be qualitative and contain no new tool call')
  closing=direct['trace'];answer=str(direct['answer'])
 else:
  closing='I use the printed measurement.';answer=f"{result['decision']['value']:.2f}"
 events.append(dict(kind='canonical_text',text=closing+'\n</think>\n<answer>'+answer+'</answer>'))
 from student_pilot.ground_rows import render_ground
 target,spans,segments=render_ground(events,answer)
 return dict(id=row['id'],events=events,answer=answer,target=target,tool_output_spans=spans,label=label,synthetic=result['synthetic'],training_admitted=False)


def run_capture(c,exclusions,boundary,dest):
 from PIL import Image
 from student_pilot.ground_profiles import load_geometry
 from student_pilot.scene_state import FrameMap
 validate_capture(c,exclusions);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
 images=[]
 for f in c['dense_frames']:
  with Image.open(B.checked(f)) as im:images.append(im.convert('RGB'))
 if any(im.size!=images[0].size for im in images):raise ValueError('Frame raster changed')
 state=boundary.tower(c,images)
 anchors=[images[i] for i in c['anchor_slots']]
 if state.frame_indices[state.anchor_slots].tolist()!=c['anchor_indices']:raise ValueError('Tower anchors differ')
 own,gravity=boundary.own(c,anchors,state)
 gpath=dest/'geometry.npz';gmeta=B.geometry.convert(state,own,gravity,(images[0].height,images[0].width),gpath)
 geo=load_geometry(gpath,FrameMap(tuple(c['anchor_indices'])),'tower_scaled')
 raw=proposals(c,anchors,boundary);B.write(dest/'candidates.json',raw)
 # GT is opened only after deployed inference and proposal selection inputs have been fixed.
 gt=None
 if c.get('gt'):
  with np.load(B.checked(c['gt']),allow_pickle=False) as z:gt={k:z[k] for k in ('instances','frame_indices')}
 outputs=[];events=[]
 for row in c['rows']:
  r=render_row(row,geo,raw,c,dest/'audit',gt);outputs.append(r)
  e=train_events(row,r)
  if e is not None:events.append(e)
 B.write(dest/'responses.json',outputs);B.write(dest/'training_events.json',events)
 receipt=dict(schema='o3-capture-v1',canonical=c['canonical'],capture_sha256=B.digest(c),synthetic=boundary.synthetic,geometry=gmeta,checkpoint=boundary.checkpoint,setting=SETTING,sources=B.source_identity(),files={n:B.pin(dest/n) for n in ['geometry.npz','candidates.json','responses.json','training_events.json']},labels={k:sum(r['decision']['label']==k for r in outputs) for k in ['trust','fallback','left_out']})
 B.write(dest/'COMPLETE.json',receipt)
 return receipt
