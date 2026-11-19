from pathlib import Path
import datetime,gzip,hashlib,json,os,re,shutil,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'))
sys.path.insert(0,str(D));import joblib as J
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
size=lambda root:sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
before=size(L);assert before<5_800_000_000 and shutil.disk_usage('/scratch').free>85*1024**3
checks=[D/'KIT_TESTS.json',D/'RESOLVER_TESTS.json',D/'proofs/tests23/TESTS.json',D/'proofs/tests23b/TESTS.json',L/'work/build22/proofs/new_tests/TESTS.json']
assert all(J.load(p)['successful'] for p in checks)
assert all(x['returncode']==0 for x in J.load(L/'work/build21/FINAL_CHECKS.json'))
assert len(J.load(D/'REGRESSIONS.json'))==5 and all(x['returncode']==0 for x in J.load(D/'REGRESSIONS.json'))
assert all(J.load(D/('SCAN_'+n+'.json'))['status']=='PASS' for n in ('q','n'))
assert all(J.load(D/('LOOKAHEAD_'+n+'.json'))['classification']=='boundary' for n in ('q','n'))
assert J.load(D/'proofs/capacity/final/RESULT.json')['status']=='ADMIT'
assert J.load(D/'proofs/capacity/final/VERIFIED.json')['status']=='PASS'
assert J.load(D/'LAUNCH_MODE.json')['status']=='PASS'
assert J.load(D/'proofs/capacity/600/q/RESULT.json')['status']=='ADMIT'
assert J.load(D/'proofs/capacity/final/RESULT.json')['tree_sha256']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
current={str(p.relative_to(T)):J.sha(p) for p in T.rglob('*') if p.is_file()}
assert current==J.load(D/'TREE_FILES.json')
for n in ('q','n'):assert J.seal(D/'kits'/n)==J.load(D/'KIT.json')[n]['kit_seal']
selected={}
def add(p,name=None):
 p=Path(p);name=name or str(p.relative_to(L));assert p.is_file() and not p.is_symlink();selected[name]=p
base=J.load(L/'work/build22/PACKAGE_MANIFEST.json')
for name in base['files']:
 p=T/name.removeprefix('work/tree_r1/') if name.startswith('work/tree_r1/') else L/name
 if p.is_file():add(p,name)
for p in T.rglob('*'):
 if p.is_file():add(p,'work/tree_r1/'+str(p.relative_to(T)))
for p in (L/'work/build21').glob('*.py'):add(p)
for p in (L/'work/build22').glob('*.py'):add(p)
for p in D.glob('*'):
 if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','DELIVERY.json','package24.log','capacity.log') and p.suffix in ('.py','.json','.md','.patch','.diff','.log'):add(p)
snapshot=D/'package_logs';snapshot.mkdir(exist_ok=True)
shutil.copyfile(D/'capacity.log',snapshot/'capacity.log');add(snapshot/'capacity.log','work/build24/capacity.log')
for folder in ('inputs','kits','upload_minimal','scanners','proofs/tests23','proofs/tests23b','proofs/resolver','proofs/resolver23'):
 for p in (D/folder).rglob('*'):
  if p.is_file() and (folder!='proofs/resolver' or p.stat().st_size<5_000_000):add(p)
for p in (D/'proofs/before23b').rglob('*.json'):
 if not p.is_relative_to(D/'proofs/before23b/tree'):add(p)
capacity=D/'proofs/capacity'
complete400=(capacity/'400/q/RESULT.json').exists() and J.load(capacity/'400/q/RESULT.json').get('status')=='ADMIT'
for p in capacity.rglob('*'):
 if not p.is_file():continue
 if p.relative_to(capacity).parts[0]=='400' and not complete400:continue
 # Native producer stores are rebuilt from the supplied fixtures. Retain all
 # small JSON proof receipts, source inventories, losses and aggregate audits.
 if p.suffix=='.json' and p.stat().st_size<5_000_000:add(p)
for folder in (L/'work/build21/proofs',L/'work/build22/proofs/new_tests'):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix=='.json' and p.stat().st_size<3_000_000:add(p)
for name in ('FINAL_CHECKS.json','final_focused.log','edges.log','producer_edges.log'):add(L/'work/build21'/name)
for p in (L/'out').glob('*'):
 if p.is_file() and p.name not in ('BUILD24_REPORT.md','DELIVERY.json') and p.suffix in ('.json','.md','.py','.list','.txt'):
  if p.name.startswith(('BUILD','LOOKAHEAD_KITQ')) and not p.name.startswith('BUILD24'):continue
  add(p)
prerequisites=J.load(D/'FIXTURE_PREREQUISITES.json');assert sum(x['bytes'] for x in prerequisites)<60_000_000
for item in prerequisites:add(L/item['path'])
# Keep the exact merge inputs and the preserved resolver for repeatable before tests.
for name in ('joblib23.py','23b_MINIMAL_TREE.patch','23b_MINIMAL_MERGE_NOTES.md','23b_BUILD23B_REPORT.md'):add(L/'attic/build24'/name)
add(L/'attic/build23/tree/launch_r1/entry.py')
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
value=dict(schema='build24-delivery-members-v1',GO=False,package_seal=seal,tree=J.load(L/'out/TREE_SEAL.json'),kits=J.load(D/'KIT.json'),files=manifest,
 fixture_prerequisites=prerequisites,omissions=['Generated capacity databases and unlisted checkpoint tensors; native24.py rebuilds them. Listed small fixture prerequisites are included.',
 'Production weights, frames, databases, and future step-600 files.','Python environment /scratch/jjyeung/envs/p1cpu is external.',
 'BUILD24_REPORT.md and DELIVERY.json are external to avoid a circular checksum.'])
J.write(D/'PACKAGE_MANIFEST.json',value);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24_'+seal[:8]+'.tar');assert not target.exists()
seen_blobs={};links={}
with target.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=9,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|',dereference=True) as tar:
 for name,p in sorted(selected.items()):
  item=tar.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
  is_blob=bool(re.search(r'/u/[a-f0-9]{64}$',name))
  is_fixture_artifact=('proofs/capacity/' in name or 'proofs/resolver/' in name or '/kits/' in name) and p.suffix in ('.tar','.pt','.safetensors')
  if is_blob or is_fixture_artifact or (p.stat().st_size >= 100_000 and p.suffix not in ('.py','.sh') and not name.startswith('work/tree_r1/')):
   h=J.sha(p)
   if is_blob:assert p.name==h
   if h in seen_blobs:
    item.type=tarfile.LNKTYPE;item.linkname=seen_blobs[h];item.size=0;links[name]=item.linkname;tar.addfile(item);continue
   seen_blobs[h]=name
  with p.open('rb') as f:tar.addfile(item,f)
assert target.stat().st_size<150_000_000
seen={}
with tarfile.open(target,'r|gz') as tar:
 for m in tar:
  assert m.name not in seen
  if m.islnk():assert links[m.name]==m.linkname;seen[m.name]=dict(seen[m.linkname]);continue
  assert m.isfile();h=hashlib.sha256()
  with tar.extractfile(m) as f:
   for b in iter(lambda:f.read(1<<20),b''):h.update(b)
  seen[m.name]=dict(bytes=m.size,sha256=h.hexdigest())
expected={**manifest,'work/build24/PACKAGE_MANIFEST.json':dict(bytes=(D/'PACKAGE_MANIFEST.json').stat().st_size,sha256=J.sha(D/'PACKAGE_MANIFEST.json'))}
assert seen==expected;after=size(L);assert after<6_000_000_000
record=dict(status='PASS',GO=False,package=str(target.relative_to(L)),package_seal=seal,sha256=J.sha(target),bytes=target.stat().st_size,
 members=len(seen),stream_verified=True,immutable_blob_hardlinks=len(links),workspace_bytes=after,fixture_prerequisite_bytes=sum(x['bytes'] for x in prerequisites),
 tree=J.load(L/'out/TREE_SEAL.json'),kits=J.load(D/'KIT.json'),timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',record);J.write(L/'out/DELIVERY.json',record);print(json.dumps(record,indent=2))
