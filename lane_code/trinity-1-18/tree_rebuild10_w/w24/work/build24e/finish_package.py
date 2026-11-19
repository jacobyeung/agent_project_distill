from pathlib import Path
import datetime,gzip,hashlib,json,sys,tarfile,io
L=Path(__file__).resolve().parents[2];D=L/'work/build24e'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
assert inventory(L/'work/tree_r1')==J.load(L/'work/build24b/TREE_FILES.json')
for n in ('q','n','n_go'):
 k=L/'out/kit_n_go' if n=='n_go' else L/'work/build24/kits'/n
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==J.seal(k)
for n in ('LAUNCH_TESTS','NAMING_TESTS','RESOLVER_TESTS','REFRESH_TESTS'):assert J.load(D/(n+'.json'))['successful']
assert all(r['returncode']==0 for r in J.load(D/'SUITES.json'))
for n,v in J.load(D/'INVARIANTS.json')['packages'].items():assert J.sha(L/'out'/n)==v['sha256']
for r in J.load(L/'out/UPLOADS_24E.json')['files']:assert J.sha(r['local_path'])==r['sha256']
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for root in (L/'work/build24/kits',L/'out/kit_n_go',D/'upload',D/'scanners',D/'pins'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and p.name not in ('PACKAGE_MANIFEST.json','DELIVERY.json'):add(p)
for p in (D/'go').glob('*.json'):add(p)
for p in (D/'go').glob('*.log'):add(p)
for n in ('work/build24/joblib.py','work/build24c/runtime.py','out/UPLOADS_24E.json','out/UPLOADS_24E.list','out/UPLOADS_24E_GO.json','out/N_CARD_KIT_ROWS.md','out/BUILD24E_REPORT.md'):add(L/n)
# Freeze bytes, including proof logs, in memory before constructing the manifest.
blobs={n:p.read_bytes() for n,p in selected.items()}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for n,raw in sorted(blobs.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base=L/'out/tree_rebuild_b24d_7babb413.tar'
record=dict(schema='build24e-kit-overlay-v1',package_seal=seal,base=dict(path=base.name,sha256=J.sha(base)),files=manifest,tree=J.load(L/'out/TREE_SEAL.json'),kits=J.load(D/'KIT.json'))
J.write(D/'PACKAGE_MANIFEST.json',record);blobs['work/build24e/PACKAGE_MANIFEST.json']=(D/'PACKAGE_MANIFEST.json').read_bytes()
p=L/'out'/('tree_rebuild_b24e_'+seal[:8]+'.tar')
with p.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
 for n,raw in sorted(blobs.items()):
  i=tarfile.TarInfo(n);i.size=len(raw);i.mode=0o755 if n.endswith('.sh') or n.endswith('cpu_python') else 0o644;t.addfile(i,io.BytesIO(raw))
with tarfile.open(p) as t:
 assert {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}=={n:hashlib.sha256(b).hexdigest() for n,b in blobs.items()}
v=dict(status='PACKAGED',package=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=J.sha(p),package_seal=seal,tree=record['tree'],kits=record['kits'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),GO=False,distributed_rehearsal='BLOCKED_LOCALHOST_TCP')
J.write(L/'out/DELIVERY_24E.json',v);print(json.dumps(v,indent=2))
