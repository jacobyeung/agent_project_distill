from common import *
import tarfile,copy
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
base=J.load(D/'BASELINE.json');tree=inventory(T)
assert tree==J.load(L/'work/build24m2/TREE24L3_SEAL.json')['files']
assert digest(tree)=='96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf'
kits={};changes={}
for name in ('q','n','n_go','qd'):
 k=kit(name);seal=verify(k);assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==seal
 assert J.load(k/'k/a.json')['GO']==(name=='n_go')
 changed=[]
 for p in k.rglob('*'):
  if not p.is_file():continue
  rel=str(p.relative_to(k));old=base[name].get(rel)
  if not old or J.sha(p)!=old['sha256'] or p.stat().st_mode&511!=old['mode']:changed.append(rel)
 assert set(changed)=={'b/pl.py','b/rg.py','b/rb.py','BUILD.json','SHA256SUMS.txt'},(name,changed)
 assert not set(base[name])-set(str(p.relative_to(k)) for p in k.rglob('*') if p.is_file())
 oldrg=(L/'attic/build24m2d'/k.relative_to(L)/'b/rg.py').read_text();newrg=(k/'b/rg.py').read_text()
 compare=lambda s:s[s.index('    comparison=None'):s.index('    value=dict')]
 assert compare(oldrg)==compare(newrg)
 kits[name]=dict(kit_seal=seal,GO=name=='n_go');changes[name]=sorted(changed)
for p,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(p)==h
J.write(D/'INVARIANTS.json',dict(status='PASS',kits=kits,changes=changes,tree_sha256=digest(tree),tree_files=len(tree),config_and_gates_unchanged=True,comparison_body_unchanged=True,resolver_identity_checks_unchanged=True,prior_packages_unchanged=len(J.load(D/'PRIOR_PACKAGES.json'))))
root=D/'upload';root.mkdir(exist_ok=True)
for n in ('q','n','qd','u'):(root/n).mkdir(exist_ok=True)
files=[]
for name in ('q','n','qd'):
 for rel in changes[name]:
  p=kit(name)/rel;target=root/name/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():os.link(p,target)
  files.append(dict(name=name+'/'+rel,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(target),action='replace' if rel in base[name] else 'add'))
up=dict(schema='build24m2d-upload-diff-v1',baseline='out/DELIVERY_24M2.json',baseline_sha256=J.sha(L/'out/DELIVERY_24M2.json'),stream_root=str(root),top_directories=['q','n','qd','u'],files=files,total_files=len(files),total_bytes=sum(v['bytes'] for v in files),kits=kits,GO=False,upload_authorized=False,production_admission='BLOCKED',shared_uploads='No shared u/ bytes changed from 24m2c; retain the base uploads.')
J.write(L/'out/UPLOADS_24M2D.json',up);(L/'out/UPLOADS_24M2D.list').write_text(''.join(v['name']+'\n' for v in files))
go=[]
for p in sorted(kit('n_go').rglob('*')):
 if p.is_file() and J.sha(p)!=J.sha(kit('n')/p.relative_to(kit('n_go'))):
  go.append(dict(name='n/'+str(p.relative_to(kit('n_go'))),sha256=J.sha(p),bytes=p.stat().st_size,local_path=str(p),mode=format(p.stat().st_mode&511,'04o'),action='replace'))
assert [x['name'] for x in go]==['n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json']
J.write(L/'out/UPLOADS_24M2D_GO.json',dict(schema='build24m2d-go-diff-v1',base_kit_seal=kits['n']['kit_seal'],kit_seal=kits['n_go']['kit_seal'],upload_authorized=False,requires='Orchestrator launch GO',files=go,total_files=len(go),total_bytes=sum(v['bytes'] for v in go)))
checks={}
for n in ['HIDDEN_PATH_TESTS','RECONSTRUCTION_TESTS','STAGE_OUTPUT_TESTS','QD_OWN_SELECTION_TESTS','PIN_TESTS','P_REFRESH_TESTS','ROUTING_TESTS','NATIVE_HOST_TESTS','PUBLICATION_TESTS','DISCOVERY_SHELL_TESTS','SOURCE_PIN_TESTS','FRAME_TESTS','STATIC_TESTS',*['PLANNER_TESTS_'+n for n in kits]]:
 value=J.load(D/(n+'.json'));assert value['status']=='PASS',(n,value)
 checks[n]=dict(status='PASS',sha256=J.sha(D/(n+'.json')))
suites=J.load(D/'SUITES.json')+J.load(D/'EXTRA_SUITES.json');assert all(v['returncode']==0 for v in suites)
J.write(D/'VALIDATION.json',dict(status='PASS',checks=checks,suites=suites,scans={n:J.load(D/('SCAN_'+n+'.json')) for n in kits},boundaries=dict(production='Not run: real receipts and authenticated inventory boundaries only; e00 and production stores unavailable',reconstruction='Native fixture producer; production pin constants replaced only in the fixture module',planner='Native closure, hash checks, localization and host substitution; export copying and pool producer boundaries controlled in small fixtures',review='Real handover/review/publication logic against synthetic stores',runtime_catalog='Synthetic member proves SHA lookup; production eac5f9f0 membership remains unverified')))
print(json.dumps(dict(kits=kits,files=len(files),bytes=up['total_bytes']),indent=2))
