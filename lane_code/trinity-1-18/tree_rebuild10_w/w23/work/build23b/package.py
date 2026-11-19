"""Seal the delivery and verify every archived byte without extracting another tree."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23b';A=L/'attic/build23b'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
for name in ('SCAN.json','INTEGRITY.json'):assert read(D/name)['status']=='PASS'
pending=read(D/'FIXTURE.json')['status']=='INCOMPLETE'
assert pending or read(D/'FIXTURE.json')['status']=='PASS'
assert len(read(D/'SUITES.json'))==6 and all(r['returncode']==0 for r in read(D/'SUITES.json'))
assert read(D/'TEST_COUNTS.json')['inherited']==204
assert len((L/'out/BUILD23B_REPORT.md').read_text().splitlines())<60
workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert workspace<2_900_000_000,workspace
assert shutil.disk_usage('/scratch').free>85*1024**3
selected={}
def add(p,name=None):
 assert p.is_file() and not p.is_symlink(),str(p)
 selected[name or str(p.relative_to(L))]=p
for name in read(A/'PACKAGE_MANIFEST.json')['files']:
 if name in ('work/build21/PACKAGE_MANIFEST.json','work/build21/DELIVERY.json'):continue
 if name.startswith('work/build21/kits/q/'):continue
 if name.startswith('work/build21/upload/u/'):continue
 add(L/name)
for p in (B/'kits/q').rglob('*'):
 if p.is_file():add(p)
for name in ('UPLOADS.json','FINAL_KITS.json','OPERATOR.md','naming21.py'):add(B/name)
for name in ('a23b.json','b23b.json','c23b.json'):add(B/'inputs'/name)
for p in D.rglob('*'):
 if pending and (p.is_relative_to(D/'proofs') or p.name in ('capacity_final.log','CAPACITY.json')):continue
 if not p.is_file() or p.is_symlink() or p.name in ('DELIVERY.json','package.log'):continue
 if p.suffix in ('.json','.jsonl','.py','.sh','.md','.log') or p==D/'source.tar':
  if p.stat().st_size<10_000_000:add(p)
for p in A.glob('*'):
 if p.is_file() and p.suffix in ('.json','.py','.md'):add(p)
for subtree in ('q','tree'):
 for p in (A/subtree).rglob('*'):
  if p.is_file():add(p)
for name in ('MINIMAL_TREE.patch','MINIMAL_MERGE_NOTES.md','UPLOADS_NEW_23B.json','BUILD23B_REPORT.md','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/name)
for group in ('final_focused','edges','producer_edges','b23b_resolver','b23b_kit','b23b_naming21c','b23b_naming21d','b23b_scanner'):
 for name in ('TESTS.json','hits.json','source_hashes.json','MONITOR_STORAGE.json'):add(B/'proofs'/group/name)
for row in read(B/'UPLOADS.json')['files']:
 p=Path(row['local_path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 if row['opaque_name'].startswith('u/'):add(p,'work/build21/upload/'+row['opaque_name'])
manifest={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest();kit=read(D/'KIT.json')
value=dict(schema='build23b-delivery-v1',GO=False,package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],
 base_tree='b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',files=manifest,
 omissions=['Capacity databases, source rows and model/export/checkpoint payloads; capacity.py reconstructs the synthetic fixture.',
 'Production databases, frames and large model weights; production host/GPU execution remains required.',
 'DELIVERY.json is external to avoid a circular package checksum.',
 'The active capacity output is omitted when pending; CAPACITY_PENDING.json records the authenticated preparation snapshot.'])
write(B/'PACKAGE_MANIFEST.json',value);add(B/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b23b_'+seal[:8]+'.tar');assert not target.exists()
class Bounded:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  self.n+=len(b)
  if self.n>=150_000_000 or workspace+self.n>=3_000_000_000:raise ValueError('PACKAGE_STORAGE_BOUND')
  return self.f.write(b)
 def flush(self):return self.f.flush()
with target.open('xb') as raw:
 with gzip.GzipFile(filename='',fileobj=Bounded(raw),mode='wb',compresslevel=6,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w|') as archive:
   for name,p in sorted(selected.items()):
    item=archive.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
    with p.open('rb') as f:archive.addfile(item,f)
expected={**manifest,'work/build21/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=sha(B/'PACKAGE_MANIFEST.json'))};seen={}
with tarfile.open(target,'r|gz') as archive:
 for member in archive:
  assert member.isfile() and member.name not in seen;h=hashlib.sha256()
  with archive.extractfile(member) as f:
   for block in iter(lambda:f.read(1<<20),b''):h.update(block)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
assert seen==expected
assert sha(L/'out/tree_rebuild_b23_40abf77b.tar')==read(D/'INTEGRITY.json')['base_package_sha256']
after=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink());assert after<3_000_000_000,after
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,sha256=sha(target),package_seal=seal,tree_seal=kit['tree_seal'],kit_q_seal=kit['kit_seal'],members=len(seen),stream_verified=True,workspace_bytes=after,timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(D/'DELIVERY.json',result);write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
