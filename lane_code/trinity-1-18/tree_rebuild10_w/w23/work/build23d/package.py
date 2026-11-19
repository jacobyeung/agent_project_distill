"""Stream the immutable base package with the kit-only overlay and verify every member."""
from pathlib import Path
import datetime,gzip,hashlib,json,os,shutil,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23d';A=L/'attic/build23d'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
base=J.load(A/'PACKAGE_MANIFEST.json');start=J.load(D/'START.json');kit=J.load(D/'KIT.json')
source=L/'out/tree_rebuild_b23c_db042c7c.tar'
assert J.sha(source)==start['packages'][str(source.relative_to(L))]['sha256']
assert len(J.load(D/'SUITES.json'))==5 and all(x['successful'] for x in J.load(D/'SUITES.json'))
assert J.load(D/'SCAN.json')['status']=='PASS'
assert len((L/'out/BUILD23D_REPORT.md').read_text().splitlines())<25
def workspace_size():
 total=0
 for root,dirs,files in os.walk(L):
  if Path(root)==L/'work':dirs[:]=[n for n in dirs if n!='build23b']
  for name in files:
   p=Path(root)/name
   if p==A/'package.partial':continue
   if not p.is_symlink():total+=p.stat().st_size
 return total
workspace=workspace_size();free=shutil.disk_usage('/scratch').free
assert workspace<2_890_000_000,workspace
assert free>85*1024**3
overlay={}
def add(p):
 assert p.is_file() and not p.is_symlink(),p
 assert not str(p.relative_to(L)).startswith('work/build23b/')
 overlay[str(p.relative_to(L))]=p
for p in (B/'kits/q').rglob('*'):
 if p.is_file():add(p)
for name in ('kit.py','UPLOADS.json','FINAL_KITS.json','OPERATOR.md'):add(B/name)
for p in D.rglob('*'):
 if p.is_file() and p.name not in ('DELIVERY.json','package.log'):add(p)
for p in A.rglob('*'):
 if p.is_file() and p.name!='package.partial':add(p)
for group in ('resolver','kit','naming21c','naming21d','scanner'):
 for p in (B/'proofs'/('b23d_'+group)).rglob('*'):
  if p.is_file() and p.suffix in ('.json','.log'):add(p)
for name in ('BUILD23D_REPORT.md','GUARD_PATCH.md','GUARD_PATCH.diff','UPLOADS_NEW_23D.json'):add(L/'out'/name)
manifest=dict(base['files'])
for n,p in overlay.items():manifest[n]=dict(bytes=p.stat().st_size,sha256=J.sha(p))
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
metadata=dict(schema='build23d-delivery-v1',GO=False,package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],base_package=start['packages'][str(source.relative_to(L))],files=manifest,
 omissions=base['omissions']+['No production or capacity replay ran. Active work/build23b was not accessed; its inherited package members are streamed from the immutable base package.'])
J.write(B/'PACKAGE_MANIFEST.json',metadata);add(B/'PACKAGE_MANIFEST.json')
expected={**manifest,'work/build21/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=J.sha(B/'PACKAGE_MANIFEST.json'))}
target=L/'out'/('tree_rebuild_b23d_'+seal[:8]+'.tar');assert not target.exists()
class Bounded:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  self.n+=len(b)
  if self.n>=150_000_000 or workspace+self.n+2_000_000>=3_000_000_000:raise ValueError('PACKAGE_STORAGE_BOUND')
  return self.f.write(b)
 def flush(self):return self.f.flush()
written=set()
temporary=A/'package.partial'
with temporary.open('wb') as raw:
 with gzip.GzipFile(filename='',fileobj=Bounded(raw),mode='wb',compresslevel=6,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as output:
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
with tarfile.open(temporary,'r|gz') as archive:
 for member in archive:
  assert member.isfile() and member.name not in seen
  h=hashlib.sha256()
  with archive.extractfile(member) as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
assert seen==expected
for name,v in start['packages'].items():assert J.sha(L/name)==v['sha256']
temporary.rename(target)
after=workspace_size();assert after<3_000_000_000,after
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],members=len(seen),stream_verified=True,existing_packages_unchanged=True,workspace_bytes_excluding_active_replay=after,storage_exclusion='Concurrent work/build23b not traversed or measured; its growth is outside this kit-only build.',free_before=free,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(D/'DELIVERY.json',result);J.write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
