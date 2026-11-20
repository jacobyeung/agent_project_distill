from common import *
old=J.load(D/'DEPENDENT_PINS.json')['n']['runtime_code']['before'];records={};seals={}
for name in NAMES:
 k=kit(name);capsule=J.load_raw(k/'k/c0.json');h=capsule['sha256'];raw=base64.b64decode(capsule['payload'])
 assert hashlib.sha256(raw).hexdigest()==h
 p=D/'inputs'/h
 if p.exists():assert p.read_bytes()==raw
 else:p.write_bytes(raw)
 v=J.load(k/'k/p.json');rows=[]
 for r in v['uploads']:
  if r['sha256']==old:r=dict(r,sha256=h,bytes=len(raw),opaque_name='u/'+h)
  rows.append(r)
 assert any(r['sha256']==h for r in rows)
 v['uploads']=sorted(rows,key=lambda r:r['sha256']);v['pin_paths']={r['sha256']:v['namespace']+'/u/'+r['sha256'] for r in rows}
 cap(k/'k/p.json',v);seals[name]=reseal(k)
 records[name]=dict(old=old,new=h,bytes=len(raw),path=str(p))
J.write(D/'SEALS.json',seals);J.write(D/'RUNTIME_PIN_UPDATE.json',records)
J.write(D/'ARM_BASE_SEALS.json',seals)
J.write(D/'ARM_BASE_FILES.json',{n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES})
pins=J.load(D/'DEPENDENT_PINS.json')
for name in NAMES:
 pins[name]['runtime_upload']=records[name]
 pins[name]['changed_files']={str(p.relative_to(kit(name))):J.sha(p) for p in kit(name).rglob('*') if p.is_file() and J.load(D/'BASE_FILES.json')[name].get(str(p.relative_to(kit(name))),{}).get('sha256')!=J.sha(p)}
J.write(D/'DEPENDENT_PINS.json',pins)
print('Runtime code upload rebound',records);print('SEALS',seals)
