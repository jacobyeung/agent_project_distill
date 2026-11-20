"""Verify final kit invariants and write the upload delta and delivery evidence."""
from common import *
import tarfile,copy
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

def decoded(raw):
 v=json.loads(raw)
 if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json'):
  raw=base64.b64decode(v['payload']);assert hashlib.sha256(raw).hexdigest()==v['sha256'];return json.loads(raw)
 return v

base=J.load(L/'work/build24m2/BASELINE.json');tree=inventory(T)
assert tree==J.load(L/'work/build24m2/TREE24L3_SEAL.json')['files']
treehash=digest(tree);kits={};old={}
with tarfile.open(L/'out/tree_rebuild_b24m1_63d040db.tar') as archive:
 for name in ('q','n','n_go'):
  prefix=('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)+'/'
  for part in ('k/c.json','k/n.json','k/p.json','b/z.py','b/resolve.py'):
   old[name,part]=archive.extractfile(prefix+part).read()
source_hash=None
for name in ('q','n','n_go','qd'):
 k=kit(name);a=J.load(k/'k/a.json');cfg=J.load(k/'k/c.json');original='q' if name=='qd' else name
 assert a['GO']==(name=='n_go')
 for part in ('k/c.json','k/n.json'):
  before=decoded(old[original,part]);after=J.load(k/part)
  assert set(before)==set(after)
  assert all(before[key]==after[key] for key in before if key!='code'),(name,part)
  if part=='k/c.json':assert after['code']['sha256']==J.sha(k/after['code']['path'])
  else:
   encoded=json.loads((k/'k/c0.json').read_text())
   assert after['code']==dict(path='u/'+encoded['sha256'],sha256=encoded['sha256'])
 for part in ('b/z.py','b/resolve.py'):assert (k/part).read_bytes()==old[original,part],(name,part)
 assert cfg['r2_scene_rebuild'] is None and cfg['scene_coverage'] is None
 assert not (k/'b/sc.py').exists() and 'from sc import bind' not in (k/'b/pl.py').read_text()
 for part in ('k/7.json','k/c0.json'):
  code=J.load(k/part);assert code['files']==tree
  assert code['tree_sha256']==treehash
  for path,h in code['sources'].items():assert tree[path]==h
  assert code['archive']['sha256']==a['source']['sha256']
 assert a['source']['tree_sha256']==treehash
 tar=k/a['source']['path'];assert J.sha(tar)==a['source']['sha256']
 if source_hash is None:
  with tarfile.open(tar) as archive:
   actual={m.name:hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive if m.isfile()}
  assert actual==tree;source_hash=J.sha(tar)
 assert source_hash==a['source']['sha256']
 for p in k.rglob('*.sh'):assert p.stat().st_mode&511==0o755,p
 seal=verify(k);assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==seal
 kits[name]=dict(kit_seal=seal,GO=a['GO'],tree_seal=treehash)
for part in ('k/c.json','k/n.json','k/p.json','k/l.json','k/7.json','k/c0.json','b/h.py','b/sv.py'):
 assert (kit('q')/part).read_bytes()==(kit('qd')/part).read_bytes(),part
qd=J.load(kit('qd')/'BUILD.json');assert qd['discovery'] is True and qd['claims']=='nothing'
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=treehash,source_archive_sha256=source_hash,tree_files=len(tree),kits=kits,config_changes=['code only'],resolver_identity_checks='byte-identical to 24m1',qd_config_stores_removals_admission='byte-identical to q',scene_rebuild='STOPPED; null pins retained',pointing_13th_list='STOPPED; twelve lists retained',GO='false except n_go'))

root=D/'upload';root.mkdir(exist_ok=True);needed=[];shared={}
baseline_u={v['opaque_name']:v for v in J.load(L/'work/build24m1/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
def add(p,name,action,previous=None):
 p=Path(p);h=J.sha(p);mode=p.stat().st_mode&511;target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():os.link(p,target)
 assert J.sha(target)==h and target.stat().st_mode&511==mode
 needed.append(dict(name=name,sha256=h,bytes=p.stat().st_size,mode=format(mode,'04o'),local_path=str(target),action=action,mode_only=bool(previous and previous['sha256']==h)))
for name in ('q','n','qd'):
 k=kit(name);files=[]
 for v in J.load(D/('UPLOADS_'+name+'.json'))['files']:
  if not v['opaque_name'].startswith('u/'):continue
  p=Path(v['local_path']);assert J.sha(p)==v['sha256'];assert p.stat().st_size==v['bytes'];files.append(v);shared[v['opaque_name']]=v
 for p in sorted(k.rglob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(k));h=J.sha(p);mode=p.stat().st_mode&511
  files.append(dict(local_path=str(p),opaque_name=name+'/'+rel,sha256=h,bytes=p.stat().st_size,mode=format(mode,'04o'),needed_minimal=True))
  previous=base['kits'].get(name,{}).get(rel)
  if previous and previous['sha256']==h and previous['mode']==mode:continue
  add(p,name+'/'+rel,'replace' if previous else 'add',previous)
 J.write(D/('UPLOADS_'+name+'.json'),dict(files=files,total_bytes=sum(v['bytes'] for v in files)))
for name,v in shared.items():
 if name not in baseline_u:add(v['local_path'],name,'add')
 else:assert v['sha256']==baseline_u[name]['sha256']
add(L/'out/jd.sh','jd.sh','add')
up=dict(schema='build24m2-upload-diff-v1',GO=False,baseline=dict(delivery='out/DELIVERY_24M1.json',sha256=J.sha(L/'out/DELIVERY_24M1.json')),kits=kits,files=needed,total_files=len(needed),total_bytes=sum(v['bytes'] for v in needed),stream_root=str(root),includes_permission_changes=True,discovery_top_directory='qd/',upload_authorized=False,production_admission='BLOCKED')
replace(L/'out/UPLOADS_24M2.json',json.dumps(up,sort_keys=True,indent=2)+'\n')
replace(L/'out/UPLOADS_24M2.list',''.join(v['name']+'\n' for v in needed))
go=[]
for p in sorted(kit('n_go').rglob('*')):
 if p.is_file() and J.sha(p)!=J.sha(kit('n')/p.relative_to(kit('n_go'))):
  go.append(dict(name='n/'+str(p.relative_to(kit('n_go'))),bytes=p.stat().st_size,sha256=J.sha(p),mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action='replace'))
assert [v['name'] for v in go]==['n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json']
replace(L/'out/UPLOADS_24M2_GO.json',json.dumps(dict(schema='build24m2-go-diff-v1',upload_authorized=False,requires='Orchestrator launch GO',base_kit_seal=kits['n']['kit_seal'],kit_seal=kits['n_go']['kit_seal'],files=go,total_files=len(go),total_bytes=sum(v['bytes'] for v in go)),sort_keys=True,indent=2)+'\n')

suites={v['name']:v for v in J.load(D/'SUITES.json')}
suites.update({v['name']:v for v in J.load(D/'GUARD_RERUN.json')})
assert all(v['returncode']==0 for v in suites.values())
checks={}
for name in ('TREE_VERIFICATION','FRAME_TESTS','STATIC_TESTS','P_REFRESH_TESTS','CENSUS_TESTS','NATIVE_HOST_TESTS','PUBLICATION_TESTS','ROUTING_TESTS','DISCOVERY_SHELL_TESTS','HIDDEN_PATH_TESTS','PIN_TESTS','PLANNER_TESTS','INVARIANTS'):
 v=J.load(D/(name+'.json'));assert v['status']=='PASS',(name,v);checks[name]=dict(status='PASS',sha256=J.sha(D/(name+'.json')))
for name in kits:
 v=J.load(D/('SCAN_'+name+'.json'));assert v['status']=='PASS';checks['SCAN_'+name]=v
J.write(D/'VALIDATION.json',dict(status='PASS',suites=list(suites.values()),checks=checks,guard_record_repair='Initial guard assertions passed; only output directories were absent. Four reruns with directories passed.',production_admission='BLOCKED',boundaries=dict(hidden='Real receipt bytes; unavailable inventoried large payloads are stand-ins; absent P routing database is not invented.',discovery='Decoded r-to-q shell, real host/review/publication checks; preparation and capacity producer boundaries use fixtures. Native routing regeneration and native host gates tested separately.'),stopped_items={'2b':'Missing authenticated source population 4e8e6c04','2c':'R1_NAMING_REMOVAL_ORDER for thirteenth list'}))
print(json.dumps(dict(kits=kits,upload_files=len(needed),upload_bytes=up['total_bytes'],validation='PASS'),indent=2))
