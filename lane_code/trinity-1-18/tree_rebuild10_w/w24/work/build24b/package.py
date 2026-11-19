from pathlib import Path
import datetime,gzip,hashlib,json,os,re,shutil,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';T=L/'work/tree_r1';sys.path.insert(0,str(L/'work/build24'));import joblib as J
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
start_bytes=3892780280
size=lambda:int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
before=size();assert before-start_bytes<750_000_000 and shutil.disk_usage('/scratch').free>85*1024**3
assert J.load(D/'TEST_COUNTS.json')['successful'] and J.load(D/'TEST_COUNTS.json')['base_tests']==356 and J.load(D/'TEST_COUNTS.json')['tests']==418
assert J.load(D/'CPU_SUMMARY.json')['status']=='PASS' and J.load(D/'REAL_REPLAY.json')['status']=='PASS'
assert len(J.load(L/'work/build24/REGRESSIONS.json'))==5 and all(x['returncode']==0 for x in J.load(L/'work/build24/REGRESSIONS.json'))
assert J.load(D/'COVERAGE.json')['covered']==J.load(D/'COVERAGE.json')['total']==44
for n in ('q','n'):
 assert J.load(D/('SCAN_'+n+'.json'))['status']=='PASS'
 assert J.load(D/('LOOKAHEAD_'+n+'.json'))['classification']=='boundary'
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==J.seal(L/'work/build24/kits'/n)==J.load(D/'KIT.json')[n]['kit_seal']
 assert J.load(D/('LOOKAHEAD_'+n+'.json'))['kit_seal']==J.seal(L/'work/build24/kits'/n)
current={str(p.relative_to(T)):J.sha(p) for p in T.rglob('*') if p.is_file()};assert current==J.load(D/'TREE_FILES.json')
assert J.load(D/'CPU_SUMMARY.json')['tree_sha256']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
assert J.sha(L/'out/tree_rebuild_b24_90637cdf.tar')=='239a6d2b3ea00f1bce309a11d1082a0b186e465da43f4bb333ba0b3884435654'
selected={}
def add(p,name=None):
 p=Path(p);name=name or str(p.relative_to(L));assert p.is_file() and not p.is_symlink();selected[name]=p
base=J.load(L/'work/build24/PACKAGE_MANIFEST.json')
for name in base['files']:
 if name.startswith('work/build24/upload_minimal/') or name in ('out/M600_PINS.json','out/M600_HANDOVER.md'):continue
 p=L/name
 if p.is_file():add(p)
for root in (T,L/'work/build24/kits',D):
 for p in root.rglob('*'):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(root)
  if root==D:
   if p.name in ('PACKAGE_MANIFEST.json','DELIVERY.json','package.log','report.log'):continue
   if p.name in ('INSPECT.txt','j_before.sh'):continue
   if p.suffix=='.log' and p.name not in ('pin_tests_complete.log','proof_tests.log','init_tests_after.log','capacity.log','real_replay.log','scan_delivery.log','lookahead_delivery.log','kit_delivery.log'):continue
   if p.name=='big.json' or p.suffix in ('.sqlite','.db'):continue
  add(p)
for name in ('KIT.json','UPLOADS_q.json','UPLOADS_n.json','kit.py','kit_tests.py','resolver_tests.py','resolver23_tests.py','tests23b.py','joblib.py','REGRESSIONS.json','RESOLVER_TESTS.json','KIT_TESTS.json'):
 add(L/'work/build24'/name)
for p in (L/'work/build21').glob('*.py'):add(p)
for p in (L/'work/build22').glob('*.py'):add(p)
for folder in (L/'attic/build24b/tree',L/'attic/build24b/kit_n'):
 for p in folder.rglob('*'):
  if p.is_file():add(p)
for name in ('joblib.py','work/build24/kits/q/b/g.py'):add(L/'attic/build24b'/name)
for name in ('M400_PINS.json','N_LAUNCH.json','N_LAUNCH_CONFIG.json','N_CARD_KIT_ROWS.md','OPERATOR_24B.md','UPLOADS_24B.json','UPLOADS_24B.list','UPLOADS_MINIMAL.json','UPLOADS_MINIMAL.list','TREE_SEAL.json'):add(L/'out'/name)
# Include every final result of the 418-test census, including new regression directories.
for v in J.load(D/'TEST_COUNTS.json')['suites'].values():add(L/v['evidence'])
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
prereq=J.load(L/'work/build24/FIXTURE_PREREQUISITES.json');additional=J.load(D/'PREREQUISITES.json')
value=dict(schema='build24b-delivery-members-v1',GO=False,package_seal=seal,tree=J.load(L/'out/TREE_SEAL.json'),kits=J.load(D/'KIT.json'),files=manifest,
 fixture_prerequisite_bytes=sum(x['bytes'] for x in prereq)+additional['total_bytes'],
 omissions=['Generated capacity databases: the CPU proof reused the native build24 stores; native24.py provides the producer harness.',
 'Production weights, RGB and databases; the real small archive and eight external model metadata files were not available locally.',
 'The unchanged build24 upload stream stays in the baseline package/workspace; UPLOADS_24B contains its complete delta.',
 'Python CPU environment remains external. BUILD24B_REPORT.md and DELIVERY_24B.json are external to avoid a checksum cycle.'])
assert value['fixture_prerequisite_bytes']<60_000_000
J.write(D/'PACKAGE_MANIFEST.json',value);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24b_'+seal[:8]+'.tar');assert not target.exists()
seen_blobs={};links={}
with target.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=9,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|',dereference=True) as tar:
 for name,p in sorted(selected.items()):
  item=tar.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
  # Deduplicate identical immutable content across retained receipts and test fixtures.
  h=manifest.get(name,{}).get('sha256') or J.sha(p)
  if p.stat().st_size>=10000 and p.suffix not in ('.py','.sh') and not name.startswith('work/tree_r1/'):
   if h in seen_blobs:
    item.type=tarfile.LNKTYPE;item.linkname=seen_blobs[h];item.size=0;links[name]=item.linkname;tar.addfile(item);continue
   seen_blobs[h]=name
  with p.open('rb') as f:tar.addfile(item,f)
print('Written',target.name,target.stat().st_size,flush=True)
assert target.stat().st_size<150_000_000
seen={}
with tarfile.open(target,'r|gz') as tar:
 for member in tar:
  assert member.name not in seen
  if member.islnk():
   assert links[member.name]==member.linkname;seen[member.name]=dict(seen[member.linkname]);continue
  assert member.isfile();h=hashlib.sha256()
  with tar.extractfile(member) as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build24b/PACKAGE_MANIFEST.json':dict(bytes=(D/'PACKAGE_MANIFEST.json').stat().st_size,sha256=J.sha(D/'PACKAGE_MANIFEST.json'))};assert seen==expected
final=size();assert final-start_bytes<=1_000_000_000
record=dict(status='PASS',GO=False,package=str(target.relative_to(L)),package_seal=seal,sha256=J.sha(target),bytes=target.stat().st_size,members=len(seen),stream_verified=True,
 immutable_blob_hardlinks=len(links),workspace_start_bytes=start_bytes,workspace_bytes=final,workspace_growth_bytes=final-start_bytes,
 tree=J.load(L/'out/TREE_SEAL.json'),kits=J.load(D/'KIT.json'),fixture_prerequisite_bytes=value['fixture_prerequisite_bytes'],timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',record);J.write(L/'out/DELIVERY_24B.json',record);print(json.dumps(record,indent=2))
