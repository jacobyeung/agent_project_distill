"""Package the sealed tree, launch inputs, tests, and bounded proof evidence."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,shutil,subprocess,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
subprocess.run(['date','-u'],check=True);subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=100*1024**3
before=size(L);assert before<6_000_000_000
assert read(D/'SCAN.json')['status']=='PASS'
assert read(D/'KIT_TESTS.json')['successful']
assert read(D/'proofs/new_tests/TESTS.json')['successful']
assert len(read(D/'REGRESSIONS.json'))==5 and all(x['returncode']==0 for x in read(D/'REGRESSIONS.json'))
assert all(x['returncode']==0 for x in read(B/'FINAL_CHECKS.json'))
assert read(D/'proofs/capacity/RESULT.json')['complete_native_fixture']
assert read(D/'proofs/capacity/RESULT.json').get('requested_milestones')==[600]
assert read(D/'proofs/capacity/VERIFIED.json')['600']['tree_sha256']==read(L/'out/TREE_SEAL.json')['tree_sha256']
assert read(D/'proofs/census/PLAN_RUN.json')['largest_repeat']<=4
current={str(p.relative_to(L/'work/tree_r1')):sha(p) for p in (L/'work/tree_r1').rglob('*') if p.is_file()}
assert current==read(D/'TREE_FILES.json')
kit=D/'kits/q';assert sha(kit/'SHA256SUMS.txt')==read(D/'KIT_INTEGRITY.json')['kit_q_seal']
for line in (kit/'SHA256SUMS.txt').read_text().splitlines():
    h,name=line.split('  ',1);assert sha(kit/name)==h
selected={};omitted={}
def add(p,name=None):
    p=Path(p)
    name=name or str(p.relative_to(L))
    if (p.name=='SCAN.json' and name!='work/build22/SCAN.json') or name.startswith('work/build21/kits/r1/') or name in (
        'work/build21/FINAL_KITS.json','out/BUILD21_REPORT.md',
        'work/build22/NEUTRAL_SCAN_PREVIEW.json','work/build22/NAMED_CAPACITY.json',
        'work/build22/package_inspect.py',
        'work/build22/proofs/resolver/proofs/real/mutated.tar',
        'work/build22/proofs/resolver/proofs/real/pool/h_6ed2c7aa/m400/s.tar'):
        omitted[name]='Superseded or duplicate evidence; current decoded scan and final-tree proofs are included.'
        return
    if not p.is_file() or p.is_symlink():raise ValueError('Missing delivery input: '+str(p))
    selected[name]=p
base=read(B/'PACKAGE_MANIFEST.json')
for name in base['files']:
    if name.endswith(('/PACKAGE_MANIFEST.json','/DELIVERY.json')):continue
    add(L/name,name)
for p in (L/'work/tree_r1').rglob('*'):
    if p.is_file():add(p)
for p in B.glob('*.py'):add(p)
for name in ('FINAL_CHECKS.json','final_focused.log','edges.log','producer_edges.log'):add(B/name)
for name in ('final_focused','edges','producer_edges','build22_scanner','build22_resolver','build22_kit','build22_naming21c','build22_naming21d'):
    for p in (B/'proofs'/name).glob('*.json'):add(p)
for p in D.glob('*'):
    if p.is_file() and p.name not in ('DELIVERY.json','PACKAGE_MANIFEST.json','package.log','DIRECTION_ROWS.json') and p.suffix in ('.py','.json','.md','.log','.diff'):
        add(p)
for folder in ('inputs','before','kits/q','proofs/new_tests','proofs/absence','proofs/operator','proofs/resolver'):
    for p in (D/folder).rglob('*'):
        if p.is_file():add(p)
for p in (D/'proofs/census').glob('*.json'):add(p)
capacity=D/'proofs/capacity'
for name in ('RESULT.json','VERIFIED.json','CAPACITY.json','code.json','STORAGE.jsonl','hits.json','source_hashes.json','results.json','MONITOR_STORAGE.json','EXTERNAL_PROJECT_READS.json'):
    if (capacity/name).is_file():add(capacity/name)
for step in ('600','400'):
    for name in ('request.json','request_config.json','h.json','binding.json','config.json','checkpoint/complete.json',
                 'export/artifact.json','p_prepare/receipt.json','TWINS.json','q/RESULT.json','q/f.json','q/a/RESULT.json',
                 'q/p/data_receipt.json','q/b/receipt.json','q/h/config.json','q/h/receipt.json'):
        if (capacity/step/name).is_file():add(capacity/step/name)
    for p in (capacity/step/'twins').glob('*/RESULT.json'):add(p)
prerequisites=read(D/'FIXTURE_PREREQUISITES.json')
assert sum(x['bytes'] for x in prerequisites)<60_000_000
for item in prerequisites:add(L/item['path'])
uploads=read(D/'UPLOADS.json')
for entry in uploads['files']:
    p=Path(entry['local_path']);assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
    if entry['opaque_name'].startswith('u/'):add(p,'work/build22/upload/'+entry['opaque_name'])
add(L/'out/TREE_SEAL.json');add(L/'out/LOOKAHEAD_KITQ.md')
manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
value=dict(schema='build22-delivery-members-v1',GO=False,package_seal=seal,tree=read(L/'out/TREE_SEAL.json'),
    kit_q_seal=sha(D/'kits/q/SHA256SUMS.txt'),files=manifest,fixture_prerequisites=prerequisites,omitted_duplicate_evidence=omitted,
    omissions=['Production weights, frames, databases, and future step-600 publication files.',
      'Generated capacity databases and transient producer stores; native22.py rebuilds them.',
      'The Python environment at /scratch/jjyeung/envs/p1cpu is an external prerequisite.',
      'BUILD22_REPORT.md and DELIVERY.json remain external to avoid a circular package checksum.'])
write(D/'PACKAGE_MANIFEST.json',value);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b22_'+seal[:8]+'.tar');assert not target.exists()
class Bound:
    def __init__(self,f):self.f=f;self.n=0
    def write(self,b):
        self.n+=len(b)
        if self.n>=150_000_000 or before+self.n>=6_000_000_000:raise ValueError('Delivery storage guard')
        return self.f.write(b)
    def flush(self):return self.f.flush()
immutable={};hardlinks={}
def upload_name(name):return bool(re.fullmatch(r'work/build(?:21|22)/upload/u/[a-f0-9]{64}',name))
with target.open('xb') as raw:
    with gzip.GzipFile(filename='',fileobj=Bound(raw),mode='wb',compresslevel=9,mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as archive:
            for name,p in sorted(selected.items()):
                item=archive.gettarinfo(str(p),arcname=name);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
                if upload_name(name):
                    h=manifest[name]['sha256'];assert Path(name).name==h
                    if h in immutable:
                        item.type=tarfile.LNKTYPE;item.linkname=immutable[h];item.size=0
                        hardlinks[name]=immutable[h];archive.addfile(item);continue
                    immutable[h]=name
                with p.open('rb') as f:archive.addfile(item,f)
seen={}
with tarfile.open(target,'r|gz') as archive:
    for member in archive:
        assert member.name not in seen
        if member.islnk():
            assert upload_name(member.name) and upload_name(member.linkname) and hardlinks.get(member.name)==member.linkname
            assert member.linkname in seen and Path(member.name).name==seen[member.linkname]['sha256']
            seen[member.name]=dict(seen[member.linkname]);continue
        assert member.isfile()
        h=hashlib.sha256();f=archive.extractfile(member)
        for raw in iter(lambda:f.read(1<<20),b''):h.update(raw)
        seen[member.name]=dict(bytes=member.size,sha256=h.hexdigest())
expected={**manifest,'work/build22/PACKAGE_MANIFEST.json':dict(bytes=(D/'PACKAGE_MANIFEST.json').stat().st_size,sha256=sha(D/'PACKAGE_MANIFEST.json'))}
assert seen==expected
after=size(L);assert after<6_000_000_000
result=dict(status='PASS',GO=False,package=str(target.relative_to(L)),compression='gzip',bytes=target.stat().st_size,
    sha256=sha(target),package_seal=seal,tree=read(L/'out/TREE_SEAL.json'),kit_q_seal=sha(D/'kits/q/SHA256SUMS.txt'),
    members=len(seen),stream_verified=True,immutable_upload_hardlinks=len(hardlinks),upload_bytes=uploads['total_bytes'],upload_files=len(uploads['files']),
    fixture_prerequisite_bytes=sum(x['bytes'] for x in prerequisites),workspace_bytes=after,
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
write(D/'DELIVERY.json',result);print(json.dumps(result,indent=2))
