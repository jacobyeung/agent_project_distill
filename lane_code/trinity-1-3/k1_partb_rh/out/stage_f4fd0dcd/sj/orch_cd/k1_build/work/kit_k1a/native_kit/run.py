"""Plan or run a bound training-scene cache manifest; no transport or submission."""
import os,sys,json,time,shutil,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B,pipeline as P

def validate_manifest(m,synthetic=False):
 if m.get('schema')!='o3-training-cache-v1' or m.get('synthetic') is not synthetic:raise ValueError('Manifest mode/schema differs')
 if not m.get('captures'):raise ValueError('Empty capture list')
 seen=set();ids=set()
 for c in m['captures']:
  P.validate_capture(c,m['exclusions'])
  if c['canonical'] in seen:raise ValueError('Duplicate capture')
  seen.add(c['canonical'])
  for r in c['rows']:
   if r['id'] in ids:raise ValueError('Duplicate row across captures')
   ids.add(r['id'])
 if not synthetic:
  cfg=B.load(B.checked(m['gpu']['config']))
  for field,name in [('benchmark_scene_exclusions','benchmark'),('dev_scene_exclusions','dev_s1')]:
   authority=m['exclusions']['authorities'][name]
   if authority.get('sha256')!=cfg[field]['sha256']:raise ValueError('Sealed exclusion authority differs')
   original=B.load(B.checked(authority))
   # Store an explicit normalization receipt; no unknown set silently passes.
   if not isinstance(original,dict):raise ValueError('Exclusion authority schema unknown')
   if m['exclusions'].get('normalization')!='canonical-scenes-and-physical-rooms-v1':raise ValueError('Unverified exclusion normalization')
   normalized=m['exclusions'].get('normalized_authorities',{}).get(name)
   if normalized is None or normalized.get('source_sha256')!=authority['sha256']:raise ValueError('Missing exclusion normalization receipt')
   source_scenes=original.get('canonical_scenes',original.get('scenes'))
   source_rooms=original.get('rooms',original.get('physical_rooms'))
   if not isinstance(source_scenes,list) or not isinstance(source_rooms,list):raise ValueError('Exclusion schema needs explicit adapter')
   if set(source_scenes)!=set(normalized['scenes']) or set(source_rooms)!=set(normalized['rooms']):raise ValueError('Exclusion normalization differs')
   if not set(source_scenes)<=set(m['exclusions']['scenes']) or not set(source_rooms)<=set(m['exclusions']['rooms']):raise ValueError('Exclusion coverage incomplete')
  if B.load(B.checked(m['gpu']['artifact']))['step']!=544:raise ValueError('Wrong checkpoint step')
 return m

def plan(m):
 names={(c['canonical'],B.kitlib.normalize_phrase(n)) for c in m['captures'] for r in c['rows'] for n in r['operands']}
 dense={f['sha256']:f for c in m['captures'] for f in c['dense_frames']}
 return dict(captures=len(m['captures']),rows=sum(len(c['rows']) for c in m['captures']),dense_frames=len(dense),operand_names=len(names),sam_prompt_calls=sum(1+len(B.variantlib.aliases(n)) for _,n in names),dense_frame_bytes=sum(f.get('bytes',0) for f in dense.values()) if all('bytes' in f for f in dense.values()) else None,geometry_gpu_hours_estimate=len(m['captures'])*24.6/3600,synthetic=m['synthetic'])

def execute(m,out,boundary,max_seconds=14400,max_bytes=10_000_000_000,reserve_bytes=100*1024**3):
 out=Path(out).resolve()
 if str(out).startswith(('/home/','/data')):raise ValueError('Output must be on local disk')
 out.mkdir(parents=True,exist_ok=True)
 if (out/'HALTED.json').exists():raise ValueError('HALTED run requires operator review and fresh output root')
 binding=dict(manifest_sha256=B.digest(m),sources=B.source_identity(),synthetic=boundary.synthetic)
 if (out/'BINDING.json').exists():
  if B.load(out/'BINDING.json')!=binding:raise ValueError('Resume binding differs')
 else:B.write(out/'BINDING.json',binding)
 start=time.monotonic();completed=[]
 try:
  for c in m['captures']:
   if (out/'STOP').exists() and (out/'STOP').read_text().strip()!='RESUME':return 4
   if time.monotonic()-start>=max_seconds:return 4
   if not boundary.synthetic and shutil.disk_usage(out).free<reserve_bytes+max_bytes:raise ValueError('Disk reserve insufficient')
   dest=out/B.digest(c['canonical'])[:16];done=dest/'COMPLETE.json'
   if done.exists():
    receipt=B.load(done)
    if receipt['capture_sha256']!=B.digest(c) or receipt['sources']!=binding['sources'] or receipt['checkpoint']!=boundary.checkpoint or receipt['synthetic']!=boundary.synthetic:raise ValueError('Resume capture differs')
    for p in receipt['files'].values():B.checked(p)
   elif dest.exists():raise ValueError('Incomplete capture: preserved, never resumed automatically')
   else:receipt=P.run_capture(c,m['exclusions'],boundary,dest)
   completed.append(receipt)
   with (out/'PROGRESS.jsonl').open('a') as f:f.write(json.dumps(dict(canonical=c['canonical'],elapsed=time.monotonic()-start,labels=receipt['labels']))+'\n')
   used=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
   if used>max_bytes:raise ValueError('Output cap exceeded')
  if not (out/'COMPLETE.json').exists():B.write(out/'COMPLETE.json',dict(binding=binding,captures=len(completed),seconds=time.monotonic()-start,synthetic=boundary.synthetic))
  return 0
 except Exception as e:
  if not (out/'HALTED.json').exists():B.write(out/'HALTED.json',dict(error=type(e).__name__+': '+str(e),automatic_retry=False))
  raise

def main():
 p=argparse.ArgumentParser(__doc__);p.add_argument('mode',choices=['plan','run']);p.add_argument('--manifest',required=True);p.add_argument('--out',required=True);p.add_argument('--max-seconds',type=int,default=14400);p.add_argument('--max-bytes',type=int,default=10_000_000_000)
 a=p.parse_args();m=validate_manifest(B.load(a.manifest),False)
 if a.mode=='plan':B.write(a.out,plan(m));return 0
 from boundaries import GPU
 return execute(m,a.out,GPU(m['gpu']),a.max_seconds,a.max_bytes)
if __name__=='__main__':sys.exit(main())
