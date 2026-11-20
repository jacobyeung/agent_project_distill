#!/usr/bin/env python3
"""Add a stream-scoped protected list; native job steps regenerate dependent evidence."""
from pathlib import Path
import base64
import hashlib
import json
import os
import sys
import time

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 value=json.loads(Path(p).read_text())
 if isinstance(value,dict) and 'payload' in value:
  raw=base64.b64decode(value['payload'],validate=True)
  if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('CAPSULE_HASH_DIFFERS')
  return json.loads(raw)
 return value
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def capsule(value):
 raw=encoded(value)
 return encoded(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()))
def apply(root,stream,source):
 root=Path(root).resolve();source=Path(source).resolve()
 if stream not in ('pose','routing','vqa','pointing'):raise ValueError('R1_PROTECTED_REMOVAL_STREAM_REQUIRED')
 raw=source.read_bytes();h=hashlib.sha256(raw).hexdigest()
 rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
 if not rows or any(not isinstance(v.get('row_key'),str) or not v['row_key'] for v in rows):raise ValueError('R1_PROTECTED_LIST_INVALID')
 kits={n:root/('out/kit_n_go' if n=='n_go' else 'out/kit_qd' if n=='qd' else 'work/build24/kits/'+n) for n in ('q','n','n_go','qd')}
 # Validate every kit before making any change.
 for name,k in kits.items():
  control=load(k/'k/a.json')
  if control['GO']!=(name=='n_go'):raise ValueError('R1_GO_SCOPE_DIFFERS')
  if not all((k/'b'/f).is_file() for f in ('sc.py','cs.py')):raise ValueError('R1_NATIVE_REGENERATION_STEP_MISSING')
  for doc in ('k/c.json','k/n.json'):
   cfg=load(k/doc)
   if h in [p['sha256'] for p in cfg['remove_files']]:raise ValueError('R1_NAMING_REMOVAL_ORDER')
  if 'verify_census' not in (k/'b/h.py').read_text():raise ValueError('R1_CENSUS_BINDING_MISSING')
 stamp=h[:16]+'_'+str(time.time_ns())
 attic=root/'attic'/('protected_'+stamp)
 def replace(p,body):
  if p.exists():
   old=attic/p.relative_to(root);old.parent.mkdir(parents=True,exist_ok=True);p.rename(old)
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
 delivery=root/'work/build24m3'/('delta_'+stamp);u=delivery/'u';u.mkdir(parents=True)
 (u/h).write_bytes(raw)
 before={n:{str(p.relative_to(k)):sha(p) for p in k.rglob('*') if p.is_file()} for n,k in kits.items()}
 seals={}
 for name,k in kits.items():
  for doc in ('k/c.json','k/n.json'):
   cfg=load(k/doc)
   cfg['remove_files'].insert(-1,dict(path='u/'+h,sha256=h,role='protected_rooms',stream=stream))
   cfg['r1_training']['launch22']['removal_order']=[p['sha256'] for p in cfg['remove_files']]
   replace(k/doc,capsule(cfg))
  spec=load(k/'k/p.json');spec['uploads'].append(dict(sha256=h,bytes=len(raw)))
  spec['pin_paths']={v['sha256']:spec['namespace']+'/u/'+v['sha256'] for v in spec['uploads']}
  replace(k/'k/p.json',capsule(spec))
  files={str(p.relative_to(k)):sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt')}
  sums=''.join(v+'  '+n+'\n' for n,v in sorted(files.items())).encode()
  replace(k/'SHA256SUMS.txt',sums)
  seal=hashlib.sha256(sums).hexdigest()
  build=load(k/'BUILD.json');build['kit_sha256']=seal;replace(k/'BUILD.json',capsule(build));seals[name]=seal
 def records(names):
  out=[]
  for name in names:
   k=kits[name]
   for p in sorted(k.rglob('*')):
    if not p.is_file():continue
    rel=str(p.relative_to(k))
    if before[name].get(rel)==sha(p):continue
    target=delivery/name/rel;target.parent.mkdir(parents=True,exist_ok=True);os.link(p,target)
    out.append(dict(name=('n' if name=='n_go' else name)+'/'+rel,sha256=sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(target)))
  out.append(dict(name='u/'+h,sha256=h,bytes=len(raw),mode='0644',local_path=str(u/h)))
  return out
 files=records(('q','n','qd'));go=records(('n_go',))
 value=dict(schema='protected-kit-delta-v1',stream=stream,list_sha256=h,row_keys=len(rows),stream_root=str(delivery),top_directories=['q','n','qd','u'],files=files,kits=seals,GO=False,
            dependent_receipts='Regenerated in each fresh job by native pool prepare, room census, scene rebuild, stream materialization/target-filter and preparation; final census is rebound by h.py.',
            launch='Requires bound PASS census, native host PASS, independent matching review and orchestrator GO.')
 out=root/'out'/('UPLOADS_PROTECTED_'+h[:16]+'.json')
 replace(out,encoded(value));replace(out.with_suffix('.list'),''.join(v['name']+'\n' for v in files).encode())
 replace(out.with_name(out.stem+'_GO.json'),encoded(dict(files=go,kit_seal=seals['n_go'],upload_authorized=False)))
 return value
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('usage: bind_protected.py <stream> <list.jsonl>')
 print(json.dumps(apply(Path(__file__).resolve().parents[1],sys.argv[1],sys.argv[2]),indent=2))
