"""Build and stream-verify the delivery without touching prior packages or reports."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';A=L/'attic/build21e';E=L.parent/'ext/m400real'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
start=read(D/'START.json')
assert read(D/'SCAN.json')['status']=='PASS'
assert all(x['returncode']==0 for x in read(D/'SUITES.json'))
assert all(x['failures']==x['errors']==0 for x in read(D/'TESTS.json'))
assert read(D/'KIT_CHECK.json')['after']==sha(B/'kits/q/SHA256SUMS.txt')
assert read(D/'UPLOAD_DIFF.json')['after_bytes']==read(B/'UPLOADS.json')['total_bytes']
for base in start['bases']:assert sha(L/base['path'])==base['sha256']
assert shutil.disk_usage('/scratch').free>=85*1024**3
before=size(L);assert before-start['workspace_bytes']<2_000_000_000
uploads=read(B/'UPLOADS.json');deps=read(L/'work/build21c/DEPENDENCIES.json')
sources={'work/build21/upload/'+x['opaque_name']:Path(x['local_path']) for x in uploads['files'] if x['opaque_name'].startswith('u/')}
sources.update({x['name']:Path(x['source']) for x in deps['files']})
selected={}
def add(p,name=None):
    if not p.is_file() or p.is_symlink():raise ValueError('Missing delivery input: '+str(p))
    selected[name or str(p.relative_to(L))]=p
original=read(A/'PACKAGE_MANIFEST.json')
for name in original['files']:
    if name in ('work/build21/PACKAGE_MANIFEST.json','work/build21/DELIVERY.json'):continue
    add(sources.get(name,L/name),name)
for p in B.glob('*21e.py'):
    if p.name not in ('inspect21e.py','probe21e.py'):add(p)
for name in ('kit.py','joblib.py','jobtest.py','OPERATOR.md','STATUS.md','UPLOADS.json','FINAL_KITS.json','FINAL_CHECKS.json'):add(B/name)
for p in (B/'kits/q').rglob('*'):
    if p.is_file():add(p)
for record in read(D/'TESTS.json'):
    for p in (L/record['source']).parent.glob('*.json'):add(p)
for p in D.glob('*'):
    if p.is_file() and p.suffix in ('.json','.log','.diff') and p.name not in ('DELIVERY.json','inspect.log','package.log'):add(p)
for group in ('regression21c','regression21d'):
    for p in (D/group).glob('*.json'):add(p)
for p in (D/'proofs/replay').rglob('*.json'):add(p)
add(D/'proofs/real/resolved.json')
for name in ('joblib.py','kit.py','jobtest.py','UPLOADS.json','PACKAGE_MANIFEST.json'):add(A/name)
# Bundle the supplied small real input bytes; large absent files stay absent.
real_inputs=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.suffix=='.json':
        name='work/build21e/inputs/m400real/'+str(p.relative_to(E));add(p,name)
        real_inputs.append(dict(name=name,bytes=p.stat().st_size,sha256=sha(p)))
write(D/'REAL_INPUTS.json',dict(files=real_inputs,bytes=sum(x['bytes'] for x in real_inputs)))
add(D/'REAL_INPUTS.json')
for entry in uploads['files']:
    p=Path(entry['local_path']);assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(selected.items())}
for name,value in original['files'].items():
    if name.startswith('work/tree_r1/'):assert manifest[name]==value,name
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
tree=read(L/'out/TREE_SEAL.json');assert tree==start['tree']
value=dict(schema='build21e-delivery-members-v1',GO=False,package_seal=seal,tree_seal=tree['tree_sha256'],files=manifest,
    base_packages=start['bases'],kit_seal_before=start['kit_seal'],kit_seal_after=sha(B/'kits/q/SHA256SUMS.txt'),
    fixture_dependencies='work/build21c/DEPENDENCIES.json',real_inputs='work/build21e/REAL_INPUTS.json',
    omissions=['Production weights, database/frame data, tokenizer bytes and missing archive members; see FIXTURE.json.',
        'Large generated capacity stores and the prerequisites listed in work/build21c/DEPENDENCIES.json.',
        'The final package checksum and report remain external to avoid a circular checksum.'])
write(B/'PACKAGE_MANIFEST.json',value);add(B/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b21e_'+seal[:8]+'.tar')
if target.exists():raise ValueError('Delivery target already exists')
class Bound:
    def __init__(self,f):self.f=f;self.n=0
    def write(self,b):
        self.n+=len(b)
        if self.n>=150_000_000 or before-start['workspace_bytes']+self.n>=2_000_000_000:raise ValueError('Delivery storage guard')
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
for base in start['bases']:assert sha(L/base['path'])==base['sha256'] and (L/base['path']).stat().st_size==base['bytes']
after=size(L);assert after-start['workspace_bytes']<2_000_000_000
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,
    sha256=sha(target),package_seal=seal,tree_seal=tree['tree_sha256'],tree_files=tree['files'],
    kit_seal_before=start['kit_seal'],kit_seal_after=sha(B/'kits/q/SHA256SUMS.txt'),members=len(seen),stream_verified=True,
    upload_bytes=uploads['total_bytes'],upload_files=len(uploads['files']),base_packages_unchanged=True,bases=start['bases'],
    real_fixture_bytes=sum(x['bytes'] for x in real_inputs),real_fixture_files=len(real_inputs),
    workspace_bytes=after,workspace_growth_bytes=after-start['workspace_bytes'],timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(D/'DELIVERY.json',result);write(B/'DELIVERY.json',result)
print(json.dumps(result,indent=2))
