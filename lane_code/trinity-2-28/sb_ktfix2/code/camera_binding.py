"""Consume only explicit item/frame joins supplied by the named staging request."""
from common import *
from camera_records import records
REQUEST=Path('/scratch/jjyeung/devs1_r2/REQUEST.json')

def camera_items():
 staged=records();request=read_json(REQUEST)
 joined=ROOT/'inputs/CAMERA_FRAME_JOINS.json'
 req=read_json(joined) if joined.exists() else request
 if joined.exists():
  assert req['input_sha256'][str(REQUEST)]==sha(REQUEST)
  assert req['input_sha256'][str(ROOT/'inputs/ROUTED_FULL_544_devS1_camera.jsonl.gz')]==sha(ROOT/'inputs/ROUTED_FULL_544_devS1_camera.jsonl.gz')
  # Metadata and image byte hashes are explicit evidence, never derived from a scene name.
  for path,expected in req['input_sha256'].items():
   if path.startswith(str(REQUEST.parent/'anchors')):assert sha(path)==expected
 if 'items' not in req:raise ValueError('MISSING '+str(REQUEST)+' items[].frames[].{index,path,sha256}; bundle hash alone cannot bind an item')
 explicit={r['id']:r for r in req['items']};items=[];caps=[];skipped=[]
 for r in staged:
  e=explicit.get(r['id'])
  if e is None:skipped.append(next((x for x in req.get('skipped',[]) if x['id']==r['id']),dict(id=r['id'],status='MISSING',expected_path=str(REQUEST),reason='MISSING explicit frame join')));continue
  assert e.get('scene',r['scene'])==r['scene']
  frames=e['frames']
  assert len(frames)==32 and [f['index'] for f in frames]==r['source_frame_indices']
  absent=[f['path'] for f in frames if not Path(f['path']).is_file()]
  if absent:skipped.append(dict(id=r['id'],reason='MISSING bound frames',paths=absent));continue
  for f in frames:
   p=local(f['path']);assert p.is_relative_to('/scratch/jjyeung/devs1_frames') and sha(p)==f['sha256']
  dense=e.get('dense_frames',[]);slots=e.get('anchor_slots',[])
  has64=len(dense)==64 and len(slots)==32
  if has64:
   assert all(a<b for a,b in zip(slots,slots[1:]))
   assert all(dense[s]['sha256']==f['sha256'] for s,f in zip(slots,frames))
   has64=all(local(f['path']).is_relative_to('/scratch/jjyeung/devs1_frames') and Path(f['path']).is_file() for f in dense)
   if has64:
    for f in dense:assert sha(f['path'])==f['sha256']
  if not has64:dense=frames;slots=list(range(32))
  # Identical explicit frame hashes share one GPU unit; no scene-to-file inference.
  unit='camera-input-'+digest(dict(frame_hashes=[f['sha256'] for f in dense],anchor_slots=slots))[:20]
  cap=dict(canonical=unit,dense_frames=dense,anchor_slots=slots,anchor_indices=r['source_frame_indices'],has64=has64)
  matches=[c for c in caps if c['canonical']==unit]
  if matches:assert matches[0]==cap
  else:caps.append(cap)
  items.append(dict(r,capture=cap['canonical'],anchor_slots=slots,has64=has64))
 return dict(items=items,captures=caps,skipped=skipped,input_sha256=dict(INPUTS))
