"""Build a complete package by streaming the unchanged base and applying a small overlay."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23c';A=L/'attic/build23c'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
base=J.load(A/'PACKAGE_MANIFEST.json');start=J.load(D/'START.json');kit=J.load(D/'KIT.json')
source=L/'out/tree_rebuild_b23b_cb24ed96.tar'
assert J.sha(source)==start['packages'][str(source.relative_to(L))]['sha256']
assert len(J.load(D/'SUITES.json'))==5 and all(x['successful'] for x in J.load(D/'SUITES.json'))
assert J.load(D/'SCAN.json')['status']=='PASS'
assert len((L/'out/BUILD23C_REPORT.md').read_text().splitlines())<40
workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
free=shutil.disk_usage('/scratch').free
assert workspace<2_900_000_000,workspace
assert free>85*1024**3
overlay={}
def add(p):
 assert p.is_file() and not p.is_symlink(),p
 overlay[str(p.relative_to(L))]=p
for p in (B/'kits/q').rglob('*'):
 if p.is_file():add(p)
for name in ('kit.py','UPLOADS.json','FINAL_KITS.json','OPERATOR.md'):add(B/name)
for p in D.rglob('*'):
 if p.is_file() and p.name not in ('DELIVERY.json','package.log'):add(p)
for p in A.iterdir():
 if p.is_file():add(p)
for group in ('resolver','kit','naming21c','naming21d','scanner'):
 for p in (B/'proofs'/('b23c_'+group)).rglob('*'):
  if p.is_file() and p.suffix in ('.json','.log'):add(p)
for name in ('BUILD23C_REPORT.md','GUARD_PATCH.md','GUARD_PATCH.diff','UPLOADS_NEW_23C.json'):add(L/'out'/name)
manifest=dict(base['files'])
for n,p in overlay.items():manifest[n]=dict(bytes=p.stat().st_size,sha256=J.sha(p))
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
metadata=dict(schema='build23c-delivery-v1',GO=False,package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],base_package=start['packages'][str(source.relative_to(L))],files=manifest,
 omissions=base['omissions']+['No production or capacity rerun is claimed. Inherited evidence remains in the base package; build23c evidence is under work/build23c.'])
J.write(B/'PACKAGE_MANIFEST.json',metadata);add(B/'PACKAGE_MANIFEST.json')
expected={**manifest,'work/build21/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=J.sha(B/'PACKAGE_MANIFEST.json'))}
target=L/'out'/('tree_rebuild_b23c_'+seal[:8]+'.tar');assert not target.exists()
class Bounded:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  self.n+=len(b)
  if self.n>=150_000_000 or workspace+self.n+2_000_000>=3_000_000_000:raise ValueError('PACKAGE_STORAGE_BOUND')
  return self.f.write(b)
 def flush(self):return self.f.flush()
written=set()
with target.open('xb') as raw:
 with gzip.GzipFile(filename='',fileobj=Bounded(raw),mode='wb',compresslevel=6,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w|') as output:
   with tarfile.open(source,'r|gz') as original:
    for member in original:
     assert member.isfile() and member.name not in written
     if member.name in overlay:continue
     assert member.name in manifest and member.size==manifest[member.name]['bytes']
     with original.extractfile(member) as f:output.addfile(member,f)
     written.add(member.name)
   for name,p in sorted(overlay.items()):
    assert name not in written
    member=output.gettarinfo(str(p),arcname=name);member.uid=member.gid=0;member.uname=member.gname='';member.mtime=0
    with p.open('rb') as f:output.addfile(member,f)
    written.add(name)
assert written==set(expected)
seen={}
with tarfile.open(target,'r|gz') as archive:
 for member in archive:
  assert member.isfile() and member.name not in seen
  h=hashlib.sha256()
  with archive.extractfile(member) as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
assert seen==expected
for name,v in start['packages'].items():assert J.sha(L/name)==v['sha256']
after=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink());assert after<3_000_000_000,after
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],members=len(seen),stream_verified=True,existing_packages_unchanged=True,workspace_bytes=after,free_before=free,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',result);J.write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
