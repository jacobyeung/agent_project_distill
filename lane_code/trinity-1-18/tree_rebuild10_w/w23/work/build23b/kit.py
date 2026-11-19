from pathlib import Path
from copy import deepcopy
import sys,json,base64,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23b';A=L/'attic/build23b';T=L/'work/tree_r1';K=B/'kits/q'
sys.path[:0]=[str(T),str(B)]
import joblib as J
from student_pilot.p3_provenance import digest,file_pin,pinned,source_files
from student_pilot.source_seal import inventory,archive,check_archive,create
from student_pilot.r1_persisted import scope
from student_pilot.r1_coverage import AUDIT_SOURCE_NAMES,deferred
from launch_r2.build import capsule_json
def cap(n,v):(K/n).write_bytes(capsule_json(v))
old=J.load(A/'UPLOADS.json');uploads={v['sha256']:v for v in old['files'] if v['opaque_name'].startswith('u/')}
paths={v['sha256']:v['local_path'] for v in old['files']}
cfg=J.load(A/'q/k/n.json');spec=J.load(A/'q/k/p.json');ns=spec['namespace']
with scope(paths):
 old_sources=J.load(pinned(cfg['r1_training']['row_sources']));audit=J.load(pinned(cfg['r1_training']['room_audit']))
 source_pin=J.write(B/'inputs/a23b.json',{k:v for k,v in old_sources.items() if k in AUDIT_SOURCE_NAMES})
 member_pin=J.write(B/'inputs/b23b.json',dict(schema='r1-source-catalog-v1',sources={}))
 audit.update(row_sources=source_pin,slices={})
 audit_pin=J.write(B/'inputs/c23b.json',audit)
for p in (source_pin,member_pin,audit_pin):
 path=Path(p['path']);uploads[p['sha256']]=dict(local_path=str(path),opaque_name='u/'+p['sha256'],sha256=p['sha256'],bytes=path.stat().st_size)
cfg['r1_training'].update(row_sources=source_pin,source_membership=member_pin,room_audit=audit_pin)
with scope({h:v['local_path'] for h,v in uploads.items()}):deferred(cfg,read_pins=True)
for name in ('config.json','kit_config.json'):
 p=B/'inputs'/name
 if not (A/name).exists():p.rename(A/name)
 J.write(p,cfg)
cap('k/n.json',cfg)
files=inventory(T);seal=digest(files);control=J.load(K/'k/a.json');oldtar=K/control['source']['path']
oldtar.rename(A/('retained_'+oldtar.name))
target=K/'k'/('t_'+seal[:16]+'.tar');archive(T,target,files,compress=True);check_archive(file_pin(target),files)
source=dict(path=str(target.relative_to(K)),sha256=J.sha(target),tree_sha256=seal)
closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
code=dict(schema='c1-sealed-source-v1',commit='sha256:'+seal,tree_sha256=seal,files=files,archive={k:source[k] for k in ('path','sha256')},sources=closure,operation_sources=closure)
cap('k/7.json',code)
qcode=create(T,target,closure,{},archive_path=ns+'/t.tar');raw=(json.dumps(qcode,sort_keys=True,indent=2)+'\n').encode()
(K/'k/c0.json').write_text(json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())))
spec['code_sha256']=hashlib.sha256(raw).hexdigest();spec['uploads']=[{k:v for k,v in x.items() if k!='local_path'} for x in uploads.values()];spec['pin_paths']={h:ns+'/u/'+h for h in uploads};cap('k/p.json',spec)
control['source']=source;cap('k/a.json',control)
portable=J.load(A/'q/k/c.json')
for name,pin in (('row_sources',source_pin),('source_membership',member_pin),('room_audit',audit_pin)):
 portable['r1_training'][name]=dict(pin,path=spec['pin_paths'][pin['sha256']])
portable['code']=dict(path='k/7.json',sha256=J.sha(K/'k/7.json'));cap('k/c.json',portable)
request=J.load(A/'q/k/r.json')
if 'room_audit' in request:request['room_audit']=audit_pin
cap('k/r.json',request)
manifest={str(p.relative_to(K)):J.sha(p) for p in K.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
(K/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(manifest.items())))
record=J.load(K/'BUILD.json');record.update(GO=False,kit_sha256=J.seal(K),source_seal=seal);cap('BUILD.json',record)
all_uploads=list(uploads.values())+[dict(local_path=str(p),opaque_name='q/'+str(p.relative_to(K)),bytes=p.stat().st_size,sha256=J.sha(p)) for p in K.rglob('*') if p.is_file()]
J.write(B/'UPLOADS.json',dict(files=all_uploads,total_bytes=sum(x['bytes'] for x in all_uploads)))
J.write(L/'out/TREE_SEAL.json',dict(tree_sha256=seal,files=len(files)))
(L/'out/TREE_FILES.sha256').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
p=B/'naming21.py';s=p.read_text();a=s.index('SOURCE_SEALS={');b=s.index('\nINPUT_IDENTITIES=',a)
pins={(doc,key):digest(J.load(K/doc)[key]) for doc in ('k/7.json','k/c0.json') for key in ('files','sources','operation_sources')}
p.write_text(s[:a]+'SOURCE_SEALS='+repr(pins)+'\n'+s[b:])
J.write(D/'KIT.json',dict(GO=False,tree_seal=seal,kit_seal=J.seal(K),removed_active_sources=sorted(set(old_sources)-AUDIT_SOURCE_NAMES),retained_audit_sources=sorted(set(old_sources)&AUDIT_SOURCE_NAMES),uploads=len(all_uploads)))
print(json.dumps(J.load(D/'KIT.json')))
