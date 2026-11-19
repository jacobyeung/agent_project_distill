"""Build and verify the immutable 24f overlay on the delivered 24e package."""
from pathlib import Path
import datetime,gzip,hashlib,io,json,sys,tarfile

L=Path(__file__).resolve().parents[2];D=L/'work/build24f'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory

assert inventory(L/'work/tree_r1')==J.load(D/'TREE_FILES.json')
assert J.load(D/'FINAL_VALIDATION.json')['status']=='PASS'
assert all(v['returncode']==0 for v in J.load(D/'SUITES.json'))
for n,k in [('q',L/'work/build24/kits/q'),('n',L/'work/build24/kits/n'),('n_go',L/'out/kit_n_go')]:
    scan=json.loads(gzip.decompress((D/('SCAN_'+n+'.json.gz')).read_bytes()))
    assert scan['status']=='PASS' and scan['kit_seal']==J.seal(k)
for n,v in J.load(L/'work/build24e/INVARIANTS.json')['packages'].items():
    assert J.sha(L/'out'/n)==v['sha256']
e=J.load(L/'out/DELIVERY_24E.json');assert J.sha(L/e['package'])==e['sha256']
for row in J.load(L/'out/UPLOADS_24F.json')['files']:
    assert J.sha(row['local_path'])==row['sha256']

selected={}
def add(p):
    if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in inventory(L/'work/tree_r1'):add(L/'work/tree_r1'/name)
for root in (L/'work/build24/kits',L/'out/kit_n_go',D/'upload'):
    for p in root.rglob('*'):add(p)
for p in D.iterdir():
    if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','package.log','report.log','prepare_only.log'):
        add(p)
for folder in ('guard_q','guard_n','runtime','runtime_verified'):
    root=D/folder
    for p in root.glob('*.json'):add(p)
# The external rehearsal uses the existing lane's authenticated synthetic stores.
# Include its small evidence, without duplicating databases or prepared caches.
for p in (D/'rehearsal').glob('*.json'):add(p)
for p in (D/'rehearsal').glob('*.log'):add(p)
for name in ('p2/q/RESULT.json','p2/q/a/audit.json','p2/q/p/phase_prepare.complete.json','p2/q/p/phase_frames.complete.json'):
    add(D/'rehearsal'/name)
for name in ('attic/build24f/persistence.py','work/build24/joblib.py','work/build24c/runtime.py','out/TREE_SEAL.json','out/TREE_FILES.sha256',
             'out/PERSIST24F.patch','out/SESSION_NAMES_24F.json','out/UPLOADS_24F.json','out/UPLOADS_24F.list',
             'out/UPLOADS_24F_GO.json','out/N_CARD_KIT_ROWS.md','out/BUILD24F_REPORT.md','out/DELIVERY_24E.json'):
    add(L/name)
blobs={n:p.read_bytes() for n,p in selected.items()}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for n,raw in sorted(blobs.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base=J.load(L/'out/DELIVERY_24E.json')
kits={n:J.seal(k) for n,k in [('q',L/'work/build24/kits/q'),('n',L/'work/build24/kits/n'),('n_go',L/'out/kit_n_go')]}
record=dict(schema='build24f-overlay-v1',package_seal=seal,
            base=dict(path=base['package'],sha256=base['sha256']),files=manifest,
            tree=J.load(L/'out/TREE_SEAL.json'),kits=kits,
            rehearsal='Requires retained lane fixture stores and external localhost TCP; no distributed completion claimed')
J.write(D/'PACKAGE_MANIFEST.json',record)
blobs['work/build24f/PACKAGE_MANIFEST.json']=(D/'PACKAGE_MANIFEST.json').read_bytes()
target=L/'out'/('tree_rebuild_b24f_'+seal[:8]+'.tar')
seen={}
with target.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
    for name,raw in sorted(blobs.items()):
        info=tarfile.TarInfo(name);info.mode=0o755 if name.endswith('.sh') or name.endswith('cpu_python') else 0o644
        digest=hashlib.sha256(raw).hexdigest()
        if digest in seen:
            info.type=tarfile.LNKTYPE;info.linkname=seen[digest];t.addfile(info)
        else:
            seen[digest]=name;info.size=len(raw);t.addfile(info,io.BytesIO(raw))
with tarfile.open(target) as t:
    assert {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}=={n:hashlib.sha256(b).hexdigest() for n,b in blobs.items()}
baseline=J.load(D/'BASELINE.json')
import subprocess
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
initial=baseline.get('bytes',baseline.get('workspace_bytes'))
assert initial is not None,baseline
growth=size-initial
assert growth<300_000_000,(growth,target.stat().st_size)
delivery=dict(status='PACKAGED',package=str(target.relative_to(L)),bytes=target.stat().st_size,
              sha256=J.sha(target),package_seal=seal,verified_members=len(blobs),tree=record['tree'],kits=kits,
              utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace_growth_bytes=growth,
              GO=False,distributed_rehearsal='EXTERNAL_SCRIPT_REQUIRED',
              canary='ADMIT' if (D/'rehearsal/PREPARED.json').exists() else 'NOT_CERTIFIED')
J.write(L/'out/DELIVERY_24F.json',delivery)
print(json.dumps(delivery,indent=2))
