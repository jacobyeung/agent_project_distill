from pathlib import Path
import datetime,gzip,hashlib,io,json,os,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build20'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
subprocess.run(['date','-u'],check=True)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
if shutil.disk_usage('/scratch').free<85*1024**3:raise SystemExit('Scratch free-space guard')
seal=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'];target=L/'out'/('tree_rebuild_b20_'+seal[:8]+'.tar')
selected={}
def add(p,name=None):
    if not p.is_file() or p.is_symlink():return
    name=name or str(p.relative_to(L))
    if name in selected and selected[name]!=p:raise ValueError(name)
    selected[name]=p
for p in (L/'work/tree_r1').rglob('*'):add(p)
for p in (B/'kits/q').rglob('*'):add(p)
for p in B.iterdir():
    if p.suffix in ('.py','.sh','.md','.json','.log') and p.name not in ('DELIVERY.json','PACKAGE_MANIFEST.json','package.log'):add(p)
for directory in ('inputs','base'):
    for p in (B/directory).rglob('*'):add(p)
excluded={'frozen','suite_tree','persisted','model','source','s','node','run','export','checkpoint','export17','n1fix','r1','b16'}
for p in (B/'proofs').rglob('*'):
    if not p.is_file() or p.is_symlink():continue
    rel=p.relative_to(B/'proofs')
    if set(rel.parts)&excluded:continue
    if p.suffix in ('.json','.md','.log','.txt','.py') and p.stat().st_size<=2_000_000:add(p)
for name in ('TREE_SEAL.json','TREE_FILES.sha256','TREE.diff','BUILD20_REPORT.md'):add(L/'out'/name)
for name in ('console.log',):add(B/'proofs/final/suite_tree/r2'/name)
for name in ('generator','legacy'):add(B/'proofs/final/suite_tree'/name/'NOT_RERUN.json')
uploads=json.loads((B/'UPLOADS.json').read_text())
for row in uploads['files']:
    p=Path(row['local_path'])
    if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Upload changed '+str(p))
    if row['opaque_name'].startswith('u/'):add(p,'work/build20/upload/'+row['opaque_name'])
    else:assert selected['work/build20/kits/'+row['opaque_name']]==p
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(selected.items())}
value=dict(schema='build20-delivery-members-v1',GO=False,tree_seal=seal,files=manifest,
    omissions=['Generated checkpoints, stores, frame sets and caches','Repeated historical proof payloads and prior delivery archives','Mutant and frozen working trees'],
    base_package=dict(name='tree_rebuild_b19_8ea1fe6b.tar',sha256='390ffc32e881fec212ed5973725b4c4f2eac9c1c98585a5b2a9051c6d1a3e179',tree_seal='8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa'))
write(B/'PACKAGE_MANIFEST.json',value);add(B/'PACKAGE_MANIFEST.json')
before=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
old=target.stat().st_size if target.exists() else 0
limit=min(149_000_000,1_500_000_000-before+old-500_000)
if limit<=0:raise SystemExit('Workspace capacity guard')
class Bound:
    def __init__(self,f):self.f=f;self.n=0
    def write(self,b):
        if self.n+len(b)>limit:raise ValueError('Package would exceed workspace capacity')
        self.n+=len(b);return self.f.write(b)
    def flush(self):self.f.flush()
with target.open('wb') as raw:
    bound=Bound(raw)
    with gzip.GzipFile(filename='',fileobj=bound,mode='wb',compresslevel=9,mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as archive:
            for name,p in sorted(selected.items()):
                info=archive.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
                with p.open('rb') as source:archive.addfile(info,source)
seen={}
with tarfile.open(target,'r|gz') as archive:
    for member in archive:
        h=hashlib.sha256();f=archive.extractfile(member)
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
        seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build20/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=sha(B/'PACKAGE_MANIFEST.json'))}
assert seen==expected
after=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
assert after<1_500_000_000 and target.stat().st_size<150_000_000
result=dict(verdict='NO-GO',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,
    sha256=sha(target),tree_seal=seal,manifest='work/build20/PACKAGE_MANIFEST.json',members=len(seen),
    verified_streaming=True,workspace_bytes_after=after,upload_bytes=uploads['total_bytes'],
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),base=value['base_package'],omissions=value['omissions'])
write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
