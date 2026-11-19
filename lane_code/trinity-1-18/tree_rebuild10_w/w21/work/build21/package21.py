from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
seal=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'];target=L/'out'/('tree_rebuild_b21_'+seal[:8]+'.tar')
selected={}
def add(p,name=None):
 if not p.is_file() or p.is_symlink():return
 name=name or str(p.relative_to(L));assert name not in selected or selected[name]==p
 selected[name]=p
for line in (L/'out/TREE_FILES.sha256').read_text().splitlines():
 _,name=line.split('  ',1);add(L/'work/tree_r1'/name)
for directory in (B/'kits',B/'inputs',B/'base'):
 for p in directory.rglob('*'):add(p)
for p in B.iterdir():
 if p.suffix in ('.py','.sh','.md','.json','.log') and p.name not in ('DELIVERY.json','PACKAGE_MANIFEST.json','package.log'):add(p)
excluded={'model','persisted','export','checkpoint','s','node','old_layout','new_layout','job','review_controls','retained_q','chunk'}
for p in (B/'proofs').rglob('*'):
 if not p.is_file() or p.is_symlink():continue
 rel=p.relative_to(B/'proofs')
 if set(rel.parts)&excluded or any(n.startswith('retained_') for n in rel.parts):continue
 if p.suffix in ('.json','.md','.log','.txt','.py') and p.stat().st_size<=2_000_000:add(p)
for name in ('TREE_SEAL.json','TREE_FILES.sha256','TREE.diff','BUILD21_REPORT.md'):add(L/'out'/name)
uploads=json.loads((B/'UPLOADS.json').read_text())
for row in uploads['files']:
 p=Path(row['local_path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 if row['opaque_name'].startswith('u/'):add(p,'work/build21/upload/'+row['opaque_name'])
 else:assert selected['work/build21/kits/'+row['opaque_name']]==p
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(selected.items())}
value=dict(schema='build21-delivery-members-v1',GO=False,tree_seal=seal,files=manifest,
 omissions=['Generated stores, checkpoints, frame sets and caches','Mutant tree and retained intermediate kits','Historical workspaces and prior delivery packages'],
 base_package=dict(name='tree_rebuild_b20_780ca7b4.tar',sha256='3d58bd34ebbd44472cb7bc85adecfe79df53ccaa4c395bb866d111ac8741c442',tree_seal='780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278'))
write(B/'PACKAGE_MANIFEST.json',value);add(B/'PACKAGE_MANIFEST.json')
size=lambda root:sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
before=size(L);start=json.loads((B/'STORAGE_START.json').read_text())['workspace'];capacity=size(B/'proofs/capacity')
old=target.stat().st_size if target.exists() else 0
limit=min(149_000_000,start+3_500_000_000-before+old-500_000)
assert limit>0 and capacity<=3_000_000_000 and before-start-capacity<1_500_000_000
class Bound:
 def __init__(self,f):self.f=f;self.n=0
 def write(self,b):
  if self.n+len(b)>limit:raise ValueError('Package storage guard')
  self.n+=len(b);return self.f.write(b)
 def flush(self):self.f.flush()
with target.open('wb') as raw:
 with gzip.GzipFile(filename='',fileobj=Bound(raw),mode='wb',compresslevel=9,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as archive:
   for name,p in sorted(selected.items()):
    info=archive.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
    with p.open('rb') as f:archive.addfile(info,f)
seen={}
with tarfile.open(target,'r|gz') as archive:
 for member in archive:
  h=hashlib.sha256();f=archive.extractfile(member)
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
  seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build21/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=sha(B/'PACKAGE_MANIFEST.json'))}
assert seen==expected
after=size(L);assert after-start<3_500_000_000 and target.stat().st_size<150_000_000
verdict=(L/'out/BUILD21_REPORT.md').read_text().splitlines()[0]
result=dict(verdict=verdict,GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,
 sha256=sha(target),tree_seal=seal,manifest='work/build21/PACKAGE_MANIFEST.json',members=len(seen),verified_streaming=True,
 workspace_bytes_after=after,workspace_start_bytes=start,increment_bytes=after-start,capacity_bytes=capacity,
 upload_bytes=uploads['total_bytes'],timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),base=value['base_package'],omissions=value['omissions'])
write(B/'DELIVERY.json',result);print(json.dumps(result,indent=2))
