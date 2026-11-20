from common import *
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');expected=J.load(D/'TREE24L4T_SEAL.json')
files=inventory(T);tree=digest(files)
assert files==expected['files'] and tree==expected['tree_sha256']
seals={};changes={};allowed={'BUILD.json','SHA256SUMS.txt','k/7.json','k/a.json','k/c.json','k/c0.json','k/n.json','k/p.json'}
for name in ('q','n','n_go','qd'):
 k=kit(name);seals[name]=verify(k)
 current={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
 assert set(current)==set(base[name])
 changes[name]=[rel for rel in current if current[rel]!=base[name][rel]]
 control=J.load(k/'k/a.json');tarpath=control['source']['path']
 assert set(changes[name])==allowed|{tarpath},(name,changes[name])
 assert control['GO']==(name=='n_go') and J.load(k/'BUILD.json')['GO']==(name=='n_go')
 assert control['source']['tree_sha256']==tree
 check_archive(file_pin(k/tarpath),files)
 assert J.load(k/'k/7.json')['files']==files
 for rel in ('k/c.json','k/n.json'):
  cfg=J.load(k/rel);old=J.load(L/'attic/build24m4'/k.relative_to(L)/rel)
  cfg.pop('code',None);old.pop('code',None);assert cfg==old,(name,rel)
  assert cfg['routing_opener_init']=='keep' and cfg['r2_identity']['init']['step']==544
 for rel in current:
  if rel.startswith('b/') or rel.endswith('.sh'):assert current[rel]==base[name][rel]
 for rel in ('k/a.json','BUILD.json'):
  new=J.load(k/rel);old=J.load(L/'attic/build24m4'/k.relative_to(L)/rel)
  if rel=='k/a.json':
   for x in ('sha256','tree_sha256'):new['source'].pop(x);old['source'].pop(x)
  else:
   for x in ('source_seal','kit_sha256'):new.pop(x);old.pop(x)
  assert new==old,(name,rel)
 # The only upload-spec delta is its code capsule and the corresponding pin map.
 new=J.load(k/'k/p.json');old=J.load(L/'attic/build24m4'/k.relative_to(L)/'k/p.json')
 nh=new.pop('code_sha256');oh=old.pop('code_sha256')
 for obj,h in ((new,nh),(old,oh)):
  obj['uploads']=[v for v in obj['uploads'] if v['sha256']!=h];obj['pin_paths'].pop(h)
 assert new==old,name
for path,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(path)==h
iv=dict(status='PASS',tree_sha256=tree,tree_files=len(files),kits=seals,changed=changes,only_source_and_dependent_seals_changed=True,kit_runtime_bytes_unchanged=True,config_semantics_unchanged=True,GO='false except unuploaded n_go',prior_packages_unchanged=True,prior_package_count=len(J.load(D/'PRIOR_PACKAGES.json')))
J.write(D/'INVARIANTS.json',iv)
upload=D/'upload';upload.mkdir();records=[]
def record(p,name,action):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action=action)
for name in ('q','n','qd'):
 for rel in sorted(changes[name]):
  p=kit(name)/rel;dest=upload/name/rel;dest.parent.mkdir(parents=True,exist_ok=True);os.link(p,dest)
  records.append(record(dest,name+'/'+rel,'replace'))
old_codes={J.load(L/'attic/build24m4'/kit(n).relative_to(L)/'k/p.json')['code_sha256'] for n in ('q','n','qd')}
new_codes={J.load(kit(n)/'k/p.json')['code_sha256'] for n in ('q','n','qd')}
for h in sorted(new_codes-old_codes):
 p=D/'u'/h;dest=upload/'u'/h;dest.parent.mkdir(exist_ok=True);os.link(p,dest);records.append(record(dest,'u/'+h,'add'))
value=dict(schema='build24m4-upload-diff-v1',baseline='out/DELIVERY_24M3.json',baseline_sha256=J.sha(L/'out/DELIVERY_24M3.json'),stream_root=str(upload),top_directories=['q','n','qd','u'],files=records,total_files=len(records),total_bytes=sum(v['bytes'] for v in records),kits={n:seals[n] for n in ('q','n','qd')},GO=False,outside_kit_files=[],n_go_upload_authorized=False)
J.write(L/'out/UPLOADS_24M4.json',value)
(L/'out/UPLOADS_24M4.list').write_text(''.join(v['name']+'\n' for v in records))
go=[]
for p in sorted(kit('n_go').rglob('*')):
 if p.is_file():
  rel=p.relative_to(kit('n_go'))
  if J.sha(p)!=J.sha(kit('n')/rel):go.append(record(p,'n/'+str(rel),'replace'))
assert {v['name'] for v in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4_GO.json',dict(schema='build24m4-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(v['bytes'] for v in go),upload_authorized=False,requires='Orchestrator launch GO after native admission and matching independent review'))
print('Invariants and upload diff PASS',len(records),value['total_bytes'])
