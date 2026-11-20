from common import *
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');files=inventory(T);expected=J.load(D/'TREE24L4R_SEAL.json')['files']
assert files==expected
tree=digest(files);assert tree=='92fe11f83f9e79234f00ed56521e8ad0b1dd48c80ffc593e9c0f6814610186b9'
seals={}
point='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
from student_pilot.r1_launch22 import REMOVAL_ORDER,validate_removals
from student_pilot.r1_persisted import scope
paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if x['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
for name in ('q','n','n_go','qd'):
 k=kit(name);seals[name]=verify(k)
 assert J.load(k/'k/a.json')['GO']==(name=='n_go')==J.load(k/'BUILD.json')['GO']
 assert J.load(k/'k/a.json')['source']['tree_sha256']==tree
 for rel in ('k/c.json','k/n.json'):
  cfg=J.load(k/rel);rem=cfg['remove_files']
  assert len(rem)==13 and [p['sha256'] for p in rem[:11]]==list(REMOVAL_ORDER[:11]) and rem[-1]['sha256']==REMOVAL_ORDER[-1]
  assert rem[11]==dict(path='u/'+point,sha256=point,role='protected_rooms',stream='pointing')
  assert cfg['r1_training']['launch22']['removal_order']==[p['sha256'] for p in rem]
  assert cfg['r2_all_stream_exclusions'] and cfg['routing_opener_init']=='keep' and cfg['r2_identity']['init']['step']==544
  with scope(paths):validate_removals(cfg)
  old=J.load(L/'attic/build24m3'/k.relative_to(L)/rel)
  for obj in (cfg,old):
   obj.pop('code',None);obj.pop('remove_files',None);obj['r1_training']['launch22'].pop('removal_order',None)
  assert cfg==old,(name,rel)
 for rel in ('b/cs.py','b/sc.py','b/h.py','b/pl.py'):
  assert (k/rel).is_file()
for path,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(path)==h
assert J.sha(L/'out/dbb2.py')=='a7cbfb9f3093ee50bf373838cd952405de190cb8b5dbcc29a0ab0aa1a48d06e5'
iv=dict(status='PASS',tree_sha256=tree,tree_files=len(files),kits=seals,first_eleven_and_naming_unchanged=True,only_authorized_config_deltas=True,step544_unchanged=True,GO='false except unuploaded n_go',prior_packages_unchanged=True,prior_package_count=len(J.load(D/'PRIOR_PACKAGES.json')),dbb2_unchanged=True)
J.write(D/'INVARIANTS.json',iv)
upload=D/'upload';upload.mkdir()
records=[]
def record(p,name,action):
 return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action=action)
for name in ('q','n','qd'):
 k=kit(name)
 actual={str(p.relative_to(k)):p for p in k.rglob('*') if p.is_file()}
 assert set(base[name])<=set(actual)
 for rel,p in sorted(actual.items()):
  h=J.sha(p);old=base[name].get(rel)
  if old and h==old['sha256'] and p.stat().st_mode&511==old['mode']:continue
  dst=upload/name/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(p,dst)
  records.append(record(dst,name+'/'+rel,'replace' if old else 'add'))
for p in sorted((D/'u').iterdir()):
 assert len(p.name)==64 and J.sha(p)==p.name
 dst=upload/'u'/p.name;dst.parent.mkdir(exist_ok=True);os.link(p,dst);records.append(record(dst,'u/'+p.name,'add'))
off=[]
for name in ('jd.sh','dbb2.py'):
 r=record(L/'out'/name,name,'replace' if name=='jd.sh' else 'add')
 r['destination']='/project/community/jjyeung/okh7/x_22c714e1/'+name;off.append(r)
value=dict(schema='build24m3-upload-diff-v1',baseline='out/DELIVERY_24M2D.json',baseline_sha256=J.sha(L/'out/DELIVERY_24M2D.json'),stream_root=str(upload),top_directories=['q','n','qd','u'],files=records,total_files=len(records),total_bytes=sum(v['bytes'] for v in records),kits={n:seals[n] for n in ('q','n','qd')},GO=False,outside_kit_files=off,n_go_upload_authorized=False)
replace(L/'out/UPLOADS_24M3.json',json.dumps(value,sort_keys=True,indent=2)+'\n')
replace(L/'out/UPLOADS_24M3.list',''.join(v['name']+'\n' for v in records))
go=[]
for p in sorted(kit('n_go').rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(kit('n_go'))
 if J.sha(p)!=J.sha(kit('n')/rel):go.append(record(p,'n/'+str(rel),'replace'))
assert {v['name'] for v in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
replace(L/'out/UPLOADS_24M3_GO.json',json.dumps(dict(schema='build24m3-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(v['bytes'] for v in go),upload_authorized=False,requires='Orchestrator launch GO after native admission and matching independent review'),sort_keys=True,indent=2)+'\n')
print('Invariants and upload diff PASS',len(records),sum(v['bytes'] for v in records))
