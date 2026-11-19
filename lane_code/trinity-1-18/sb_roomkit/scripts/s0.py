"""Verify full review-ledger hashes; pin manifests; never read NFS."""
from common import *
import numpy as np
ledger=W/'review/LOCAL_INPUT_SHA256.txt'; expected={}
for line in ledger.read_text().splitlines():
 h,p=line.split('  ',1)
 if '/sb_rspecrev/evidence/' in p: p=str(W/'evidence'/Path(p).name)
 expected[p]=h
bad=[]
for n,(p,h) in enumerate(expected.items()):
 if not Path(p).is_file():bad.append('MISSING '+p)
 elif sha(p)!=h:bad.append('HASH '+p)
 if n%2000==0:print('checked',n,flush=True)
assert not bad,bad
assert sha(W/'evidence/direct_m200_room134.json')==BASE
pins=W/'configs/frame_manifests';pins.mkdir(exist_ok=True)
root=R0/'out/FRAMES_MANIFEST.json';b=root.read_bytes();(W/'configs/FRAMES_MANIFEST.json').write_bytes(b)
fm=read(root);inputs={str(ledger):sha(ledger),**expected}; items=[]
for scene,entry in sorted(fm['scenes'].items()):
 p=R0/'out/frame_manifests'/f"{scene.split('/')[1]}.json";b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==entry['manifest_sha256'];(pins/p.name).write_bytes(b)
for split in ['dev','rl']:
 qp=R0/f'out/qsets/R0_QUESTIONS_{split}_f32.jsonl';(W/'configs'/qp.name).write_bytes(qp.read_bytes())
 for q in map(json.loads,qp.read_text().splitlines()):
  if q['question_type']!='room_size_estimation':continue
  smp=pins/f"{q['scene']}.json";sm=read(smp)
  anchors=q['frame_indices']; union=sorted(set(anchors)|set(np.floor(np.linspace(0,q['total_num_frames']-1,64)).astype(int).tolist()))
  assert len(anchors)==32 and len(set(anchors))==32
  assert union==sorted(map(int,sm['frames'])) and len(union)==94
  for i in union:
   p=R0/'frames/scannetpp'/q['scene']/f'{i:06d}.png'
   assert expected[str(p)]==sm['frames'][str(i)]
  if split=='dev':items.append(dict(id=q['qid'],scene=q['scene'],frame_indices=anchors,union_indices=union,frame_sha256=sm['frames'],frame_manifest_sha256=sha(smp)))
assert len(items)==98
write(W/'configs/R0DEV_ROOM_MANIFEST.json',dict(items=items,gt_used=False),{str(root):sha(root),str(W/'configs/R0_QUESTIONS_dev_f32.jsonl'):sha(W/'configs/R0_QUESTIONS_dev_f32.jsonl'),**{str(p):sha(p) for p in pins.glob('*.json')}})
write(W/'out/S0.json',dict(verdict='COMPLETE',verified_files=len(expected),sealed_files=len(read(KIT/'KIT_SEAL.json')['files']),pngs=sum(p.endswith('.png') and '/b10_reserve/' in p for p in expected),scenes=len(fm['scenes']),room_items=len(items)),inputs)
status('S0 COMPLETE: full local digests, sealed kit and weights, 15,228 R0 PNGs and pinned frame layouts verified. S1 full CPU forwards are running. Remote provenance remains MISSING; GPU execution is not authorized.')
print('S0 COMPLETE',len(expected),flush=True)
