"""Prepare the exact K1 plan from pool metadata, without staging or opening RGB."""
import argparse,collections,gzip,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
import numpy as np
def prepare(inventory,frames_root,gpu_settings):
 inv=json.loads(Path(inventory).read_text());selected={x['canonical']:x for x in inv['pilot']}
 if len(selected)!=300:raise ValueError('Incomplete pilot')
 frames=collections.defaultdict(dict)
 with (Path(inventory).parent/'FRAME_SOURCES.jsonl').open() as f:
  for line in f:
   r=json.loads(line)
   if r['canonical'] in selected:frames[r['canonical']][r['i']]=r
 rows=collections.defaultdict(dict);pins={};gtmeta={}
 for canon,c in selected.items():
  with np.load(c['gt']['path'],allow_pickle=False) as z:
   gtmeta[canon]=dict(indices=z['frame_indices'].tolist(),ids=z['ids'].tolist(),labels=z['labels'].tolist())
 for p in sorted((gate.ROOT/'dose_pool/out/POOL_S1').glob('*_admitted.jsonl.gz')):
  pins[str(p)]=gate.sha(p)
  with gzip.open(p,'rt') as f:
   for line in f:
    r=json.loads(line);canon=gate.normalize(r['canonical'])
    if canon not in selected or r.get('type') not in ('object_abs_distance','room_size_estimation'):continue
    if r['frame_indices']!=gtmeta[canon]['indices']:continue
    roles=r.get('roles',{});operands=[roles[k] for k in ('a','b')] if r['type']=='object_abs_distance' else []
    identity=r.get('candidate_id',r['qid'])
    row=dict(id=identity,source_qid=r['qid'],type=r['type'],question=r['question'],operands=operands,unit='m' if operands else 'm2',gt_value=float(r['gt_answer']))
    if operands:
     boxes=r.get('program_audit',{}).get('independent_ordered_boxes',[])
     ids={b['name']:b['instance_id'] for b in boxes if 'name' in b and 'instance_id' in b}
     row['gt_instances']={n:ids[n] for n in operands if n in ids}
    rows[canon].setdefault(identity,row)
 captures=[];missing=[];missing_dense=[]
 for canon,selection in sorted(selected.items()):
  anchors=gtmeta[canon]['indices'];available=frames[canon]
  if not set(anchors)<=set(available):raise ValueError('Anchor map missing: '+canon)
  dense=set(anchors)
  # Add the farthest available samples until the nested 64-frame grid is complete.
  while len(dense)<64:
   remaining=set(available)-dense
   if not remaining:
    missing_dense.append(dict(canonical=canon,mapped_frames=len(dense),required_frames=64,reason='Original dense RGB source is absent from the k6 map'))
    break
   dense.add(max(remaining,key=lambda i:(min(abs(i-j) for j in dense),-i)))
  dense=sorted(dense);pins32=[]
  for i in dense:
   f=available[i];h=f['sha256'];pins32.append(dict(index=i,path=str(Path(frames_root)/h[:2]/(h+'.png')),sha256=h,source_path=f['path']))
  if not rows[canon]:raise ValueError('Capture has no rows on GT anchors: '+canon)
  labels=gtmeta[canon];named={}
  for r in rows[canon].values():
   for name in r['operands']:
    named.setdefault(name.lower(),set()).update(int(i) for i,label in zip(labels['ids'],labels['labels']) if str(label).lower()==name.lower())
    if name in r.get('gt_instances',{}):named[name.lower()].add(int(r['gt_instances'][name]))
  missing.extend(dict(canonical=canon,phrase=n) for n,ids in named.items() if not ids)
  import hashlib
  clip=hashlib.sha256(json.dumps([f['sha256'] for f in pins32]).encode()).hexdigest()
  slots=[dense.index(i) for i in anchors];first=next(iter(rows[canon].values()));gt=selection['gt']
  framepins=[{k:pins32[s][k] for k in ('path','sha256')} for s in slots]
  ds,cap=canon.split('/');native_ds={'scannet':'d1','scannetpp':'d2','arkitscenes':'d3'}[ds]
  model_row=dict(qid='k1:'+canon,dataset=native_ds,scene=canon,question_type=first['type'],student_input=dict(question=first['question'],options=[],frames=framepins,frame_indices=anchors,
     fps=None,timestamps=None,total_num_frames=None,video_identity=dict(video_sha256=clip,identity_kind='sha256_ordered_dense_rgb_pins')))
  captures.append(dict(canonical=canon,room=selection['room'],split='train',k1_split=selection['split'],dense_source_authority='k6 MAP; deterministic nested 64-frame grid from mapped native indices; '+gate.sha(__file__),
    dense_frames=pins32,anchor_slots=slots,anchor_indices=anchors,video_sha256=clip,model_row=model_row,rows=list(rows[canon].values()),
    gt=dict(path=gt['path'],sha256=gt['expected_sha256']),gt_name_ids={k:sorted(v) for k,v in named.items()},gt_name_ids_authority='GT ids/labels plus row independent_ordered_boxes; unmapped names stay unresolved'))
 m=dict(schema='b6-k1-manifest-v1',inventory=dict(path=str(Path(inventory).resolve()),sha256=gate.sha(inventory)),captures=captures,gpu=gpu_settings,unresolved_dense_sources=missing_dense,
   inputs=pins,unresolved_gt_names=missing,frame_staging_authorized=False,production_ready=False,
   pending=['Operator verifies/stages pinned dense RGB and records exact bytes','Bind native source video metadata: fps, timestamps, total_num_frames, scene identity','Fill and verify step-544/G3T/SAM GPU settings','Resolve empty named GT identities','Supply reviewed visual fallback traces from rs_rows'])
 return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--frames-root',required=True);p.add_argument('--gpu-settings',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 m=prepare(a.inventory,a.frames_root,json.loads(Path(a.gpu_settings).read_text()));Path(a.out).write_text(json.dumps(m,indent=2)+'\n')
 summary=dict(captures=len(m['captures']),rows=sum(len(c['rows']) for c in m['captures']),unresolved_gt_names=len(m['unresolved_gt_names']),unresolved_dense_captures=len(m['unresolved_dense_sources']),mapped_planned_frames=sum(len(c['dense_frames']) for c in m['captures']),exact_frame_bytes=None,production_ready=False)
 Path(a.out).with_name('K1_PLAN_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
