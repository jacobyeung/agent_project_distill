"""Create and stream-verify a separate delivery; never modify the base archive."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
    return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
start=json.loads((C/'START.json').read_text());base=L/start['base']['path']
assert sha(base)==start['base']['sha256']
assert shutil.disk_usage('/scratch').free>=85*1024**3
before=size(L);assert before-start['workspace_bytes']<3_000_000_000
uploads=json.loads((B/'UPLOADS.json').read_text())
byname={'work/build21/upload/'+x['opaque_name']:Path(x['local_path']) for x in uploads['files'] if x['opaque_name'].startswith('u/')}
selected={}
def add(p,name=None):
    if not p.is_file() or p.is_symlink():raise ValueError('Missing delivery input: '+str(p))
    name=name or str(p.relative_to(L))
    if name in selected:assert sha(selected[name])==sha(p),name
    selected[name]=p
with tarfile.open(base,'r:gz') as archive:
    old=json.load(archive.extractfile('work/build21/PACKAGE_MANIFEST.json'))
    for name in old['files']:
        if name in ('work/build21/PACKAGE_MANIFEST.json','work/build21/DELIVERY.json'):continue
        add(byname.get(name,L/name),name)
for name,p in byname.items():add(p,name)
for p in (B/'kits').rglob('*'):
    if p.is_file():add(p)
for p in B.glob('*.py'):
    if p.name not in ('inspect21c.py','maps21c.py','start21c.py'):add(p)
for name in ('OPERATOR.md','UPLOADS.json','FINAL_KITS.json','FINAL_CHECKS.json'):add(B/name)
for group in ('final_focused','edges','producer_edges','kit21c','naming21c','extra21c'):
    for p in (B/'proofs'/group).glob('*.json'):add(p)
for p in C.iterdir():
    if p.is_file() and p.suffix in ('.json','.diff') and p.name not in ('DELIVERY.json','PACKAGE_CHECK.json'):add(p)
for name in ('kit.log','verify.log','naming.log','focused.log','kit_tests.log','capacity_preview.log'):
    add(C/name)
for p in (C/'proofs/capacity_preview').rglob('*.json'):add(p)
deps=json.loads((C/'DEPENDENCIES.json').read_text());assert deps['bytes']<40_000_000
for entry in deps['files']:
    p=Path(entry['source']);assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
    add(p,entry['name'])
# Preserve the exact before-test capsule without shipping a second kit.
add(L/'attic/build21c/kit/k/p.json')
for name in ('joblib.py','naming21.py','kit.py','test21.py'):add(L/'attic/build21c'/name)
for entry in uploads['files']:
    p=Path(entry['local_path']);assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(selected.items())}
canonical=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
seal=hashlib.sha256(canonical).hexdigest()
tree=json.loads((L/'out/TREE_SEAL.json').read_text())
value=dict(schema='build21c-delivery-members-v1',GO=False,package_seal=seal,tree_seal=tree['tree_sha256'],
    files=manifest,base_package=start['base'],fixture_dependencies='work/build21c/DEPENDENCIES.json',
    omissions=['Large generated capacity stores, checkpoints, frame sets and caches',
               'Unbundled focused-suite prerequisites are enumerated with hashes in DEPENDENCIES.json',
               'The final package checksum and report are external to avoid a self-referential checksum'])
write(B/'PACKAGE_MANIFEST.json',value);add(B/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b21c_'+seal[:8]+'.tar')
if target.exists():raise ValueError('Delivery target already exists')
class Bound:
    def __init__(self,f):self.f=f;self.n=0
    def write(self,b):
        self.n+=len(b)
        if self.n>=150_000_000 or before-start['workspace_bytes']+self.n>=3_000_000_000:
            raise ValueError('Delivery storage guard')
        return self.f.write(b)
    def flush(self):return self.f.flush()
with target.open('xb') as raw:
    with gzip.GzipFile(filename='',fileobj=Bound(raw),mode='wb',compresslevel=6,mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as archive:
            for name,p in sorted(selected.items()):
                item=archive.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
                with p.open('rb') as f:archive.addfile(item,f)
seen={}
with tarfile.open(target,'r|gz') as archive:
    for member in archive:
        assert member.isfile() and member.name not in seen
        h=hashlib.sha256();f=archive.extractfile(member)
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
        seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build21/PACKAGE_MANIFEST.json':dict(bytes=(B/'PACKAGE_MANIFEST.json').stat().st_size,sha256=sha(B/'PACKAGE_MANIFEST.json'))}
assert seen==expected
assert sha(base)==start['base']['sha256'] and base.stat().st_size==start['base']['bytes']
after=size(L);assert after-start['workspace_bytes']<3_000_000_000
kits=json.loads((B/'FINAL_KITS.json').read_text())
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,
    sha256=sha(target),package_seal=seal,tree_seal=tree['tree_sha256'],tree_files=tree['files'],
    kit_seal=kits['kits']['q']['kit_sha256'],members=len(seen),stream_verified=True,
    upload_bytes=uploads['total_bytes'],upload_files=len(uploads['files']),fixture_bytes=deps['bytes'],
    fixture_files=len(deps['files']),base_unchanged=True,base=start['base'],
    workspace_bytes=after,workspace_growth_bytes=after-start['workspace_bytes'],
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(C/'DELIVERY.json',result);write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
