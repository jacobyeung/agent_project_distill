"""Join exact staged scene/index fields to existing local frame-manifest records."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
from camera_records import records

def main():
 staged=records();request=Path('/scratch/jjyeung/devs1_r2/REQUEST.json');req=read_json(request)
 root=local(req['frame_root']);assert root==Path('/scratch/jjyeung/devs1_frames')
 index={};dense={};sources=[]
 wanted={(r['scene'],tuple(r['source_frame_indices'])) for r in staged}
 base=request.parent/'anchors'
 # Bounded two-group metadata search, never a filename-to-scene inference.
 for group in ('g3s32','g3s64'):
  for p in sorted((base/group).glob('*/A_MANIFEST.json')):
   d=read_json(p)
   for selection in d['selections']:
    key=(selection['scene'],tuple(selection['frame_indices']))
    if key not in wanted:continue
    frames=selection['frames'];assert [f['index'] for f in frames]==list(key[1])
    if key in index:assert index[key]['frames']==frames,('Ambiguous frame authority',key)
    index.setdefault(key,dict(frames=frames,sources=[]))['sources'].append(str(p))
    q=p.parent/'DENSE.json'
    if q.exists():
     dd=read_json(q);assert local(dd['render_root'])==root
     clip=dd['clips'].get(key[0])
     if clip and len(clip['frames'])==64:
      slots=clip['anchor_slots'];assert len(slots)==32
      assert all(0<=a<b<64 for a,b in zip(slots,slots[1:]))
      if [clip['frames'][s] for s in slots]!=frames:continue
      if key in dense:assert dense[key]['frames']==clip['frames']
      dense[key]=dict(clip,source=str(q))
 items=[];skipped=[];bytes_checked=0;verified={}
 def bind_frames(frames):
  nonlocal bytes_checked
  out=[]
  for f in frames:
   p=local(root/f['path']);assert p.is_relative_to(root)
   if not p.is_file():raise FileNotFoundError(str(p))
   if str(p) not in verified:
    actual=sha(p);assert actual==f['sha256'],('Frame hash mismatch',str(p))
    verified[str(p)]=actual;bytes_checked+=p.stat().st_size
   out.append(dict(index=f['index'],path=str(p),sha256=verified[str(p)]))
  return out
 for r in staged:
  key=(r['scene'],tuple(r['source_frame_indices']))
  if key not in index:
   skipped.append(dict(id=r['id'],status='MISSING',expected_path=str(request),missing_field='items[id='+r['id']+'].frames[].{index,path,sha256}',scene=r['scene'],source_frame_indices=r['source_frame_indices'],reason='No local manifest selection has these exact scene and source-frame-index fields'));continue
  authority=index[key]
  try:frames=bind_frames(authority['frames'])
  except FileNotFoundError as e:
   skipped.append(dict(id=r['id'],status='MISSING',expected_path=str(e)));continue
  item=dict(id=r['id'],scene=r['scene'],frames=frames,sources=authority['sources'])
  if key in dense:
   try:
    item['dense_frames']=bind_frames(dense[key]['frames']);item['anchor_slots']=dense[key]['anchor_slots'];item['dense_source']=dense[key]['source']
   except FileNotFoundError as e:item['dense_missing']=dict(status='MISSING',expected_path=str(e))
  if 'dense_frames' not in item and 'dense_missing' not in item:
   expected=[str(Path(source).parent.parent.parent/'g3s64'/Path(source).parent.name/'DENSE.json') for source in authority['sources']]
   item['dense_missing']=dict(status='MISSING',expected_paths=sorted(set(expected)),reason='No 64-frame manifest with matching anchor hashes; available g3s32 manifest has 32 frames')
  items.append(item)
 result=dict(status='PASS' if len(items)==450 else 'MISSING',items=items,skipped=skipped,dense_missing=[dict(id=r['id'],scene=r['scene'],**r['dense_missing']) for r in items if 'dense_missing' in r],bound=len(items),bound64=sum('dense_frames' in r for r in items),unique_frames_verified=len(verified),frame_bytes_verified=bytes_checked,request_path=str(request),request_bundle_sha256=req['bundle_sha256'],join_rule='Exact staged scene + complete ordered source_frame_indices == existing A_MANIFEST selection; verify PNG bytes; dense anchor records equal selected frame records',command='bash scripts/cpu.sh scripts/bind_camera.py')
 # Snapshot metadata for portable review; retain original hashes in the output.
 dest=ROOT/'inputs/camera_sources';dest.mkdir(exist_ok=True)
 for p,h in list(INPUTS.items()):
  if p.startswith(str(base)):
   target=dest/Path(p).relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(Path(p).read_bytes());assert sha(target)==h
 write_json(ROOT/'inputs/CAMERA_FRAME_JOINS.json',result)
 write_json(ROOT/'out/CAMERA_BINDING.json',{k:v for k,v in result.items() if k!='items'})
 (ROOT/'STATUS.md').write_text(f"Local camera metadata binds {len(items)} of 450 staged records, with {result['bound64']} dense-frame bindings. Every bound PNG matches its recorded SHA256. Missing joins are listed exactly in out/CAMERA_BINDING.json. The CPU dry run is pending; no GPU work ran.\n")
 print(json.dumps({k:v for k,v in result.items() if k not in ('items','skipped','dense_missing')}))
if __name__=='__main__':main()
