from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';T=L/'work/tree_r1'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
START=4657032546
size=lambda:int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
assert shutil.disk_usage('/scratch').free>85*(1<<30)
assert size()-START<975_000_000
assert {str(p.relative_to(T)):J.sha(p) for p in T.rglob('*') if p.is_file()}==J.load(L/'work/build24b/TREE_FILES.json')
for n in ('q','n','n_go'):
 k=L/'out/kit_n_go' if n=='n_go' else L/'work/build24/kits'/n
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==J.seal(k)
assert all(x['returncode']==0 for x in J.load(D/'SUITES.json'))
for n in ('RESOLVER_TESTS','LAUNCH_TESTS','NAMING_TESTS','REFRESH_TESTS'):assert J.load(D/(n+'.json'))['successful']
for name,v in J.load(D/'INVARIANTS.json')['packages'].items():assert J.sha(L/'out'/name)==v['sha256']
selected={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for root in (T,L/'work/build24/kits',L/'out/kit_n_go',L/'attic/build24d/work/build24/kits'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','DELIVERY.json','package.log') and p.suffix in ('.py','.json','.log','.sh','.diff'):add(p)
add(D/'cpu_python')
for folder in ('scanners','guard_q','guard_n','upload'):
 for p in (D/folder).rglob('*'):add(p)
for name in ('q','n'):
 root=D/'sequence'/name
 for label in ('fixture.py','operator/shell.log','own.json','request.json','roomcfg.json','guard.py','boundary.py'):add(root/label)
 node=root/'q_22c714e1_20'
 for label in ('q.log','rooms.log','rooms.json','p/q/RESULT.json','o/RESULT.json','j.sh'):add(node/label)
for p in (D/'go').iterdir():
 if p.suffix in ('.json','.log'):add(p)
for dirname in ('p','p2'):
 for label in ('q/RESULT.json','q/f.json','q/h/config.json','q/c.json','i/r.json'):add(D/'go'/dirname/label)
for p in (D/'go/train').glob('*.json*'):add(p)
for name in ('work/build24/joblib.py','work/build24c/runtime.py','attic/build24d/work/build24/joblib.py','attic/build24d/runtime.py'):add(L/name)
for name in ('GO_TRAIN.json','go/stage2.log'):add(L/'attic/build24d/go_gates_first'/name)
for name in ('GO_TRAIN.json','go/stage2.log'):add(L/'attic/build24d/go_gates_second'/name)
for name in ('UPLOADS_24D.json','UPLOADS_24D.list','UPLOADS_24D_GO.json','TREE_SEAL.json'):add(L/'out'/name)
# Freeze evidence that a still-running CPU proof may append while packaging.
# Archive names remain the original workspace-relative paths.
snapshot=D/'package_snapshot';snapshot.mkdir(exist_ok=False)
for name,p in list(selected.items()):
 if p.is_relative_to(D) and p.suffix in ('.json','.log'):
  frozen=snapshot/p.relative_to(D);frozen.parent.mkdir(parents=True,exist_ok=True)
  frozen.write_bytes(p.read_bytes());selected[name]=frozen
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base=L/'out/tree_rebuild_b24c_22859833.tar'
value=dict(schema='build24d-kit-overlay-v1',GO=False,package_seal=seal,base=dict(package=base.name,sha256=J.sha(base),bytes=base.stat().st_size),tree_sha256=J.load(L/'out/TREE_SEAL.json')['tree_sha256'],kits=J.load(D/'KIT.json'),go_variant=dict(path='out/kit_n_go',kit_seal=J.seal(L/'out/kit_n_go'),upload_authorized=False),files=manifest,
 omitted=['Generated databases and redundant extracted source copies remain in the workspace; fixture prerequisites are inherited from the base layers','BUILD24D_REPORT.md and DELIVERY_24D.json are adjacent to the archive to avoid a checksum cycle'],
 included=['Complete deployable q/n kits; GO variant only under out/kit_n_go','Byte-identical sealed source tree','Changed external generators, regressions, CPU evidence and upload stream'])
J.write(D/'PACKAGE_MANIFEST.json',value);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24d_'+seal[:8]+'.tar');assert not target.exists()
blobs={}
with target.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=6,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w|') as archive:
 for name,p in sorted(selected.items()):
  info=archive.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  h=manifest.get(name,{}).get('sha256') or J.sha(p)
  if p.stat().st_size>=10000 and p.suffix not in ('.py','.sh') and not name.startswith('work/tree_r1/'):
   if h in blobs:
    info.type=tarfile.LNKTYPE;info.linkname=blobs[h];info.size=0;archive.addfile(info);continue
   blobs[h]=name
  with p.open('rb') as f:archive.addfile(info,f)
seen={}
with tarfile.open(target,'r|gz') as archive:
 for m in archive:
  assert m.name not in seen
  if m.islnk():seen[m.name]=dict(seen[m.linkname]);continue
  assert m.isfile();h=hashlib.sha256()
  with archive.extractfile(m) as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  seen[m.name]=dict(bytes=m.size,sha256=h.hexdigest())
p=D/'PACKAGE_MANIFEST.json';expected={**manifest,str(p.relative_to(L)):dict(bytes=p.stat().st_size,sha256=J.sha(p))};assert seen==expected
growth=size()-START;assert growth<1_000_000_000,growth
record=dict(status='PASS',GO=False,package=str(target.relative_to(L)),sha256=J.sha(target),bytes=target.stat().st_size,package_seal=seal,members=len(seen),stream_verified=True,tree_sha256=value['tree_sha256'],kits=value['kits'],go_variant=value['go_variant'],workspace_start_bytes=START,workspace_growth_bytes=growth,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',record);J.write(L/'out/DELIVERY_24D.json',record);print(json.dumps(record,indent=2))
