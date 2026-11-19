"""Create and verify the build24k overlay without changing any prior package."""
from pathlib import Path
import datetime,gzip,hashlib,io,json,sys,tarfile,ast
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r1.build import verify
audit=J.load(D/'INVARIANTS.json');assert J.load(D/'VALIDATION.json')['status']=='PASS'
tree=J.load(D/'TREE24J_SEAL.json')['files'];seals=audit['kits']
for name,seal in seals.items():
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name);assert verify(k)==seal
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==seal
for name,record in J.load(D/'SEQUENCE.json').items():assert record['production_kit_seal']==seals[name]
for name,h in J.load(D/'BASELINE.json')['packages'].items():assert J.sha(L/'out'/name)==h
assert not (D/'rehearsal_k').exists(),'External rehearsal must remain unrun'
for p in D.glob('*.py'):ast.parse(p.read_text())
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in tree:add(L/'work/tree_r1'/name)
for k in (L/'work/build24/kits/q',L/'work/build24/kits/n',L/'out/kit_n_go'):
 for p in k.rglob('*'):add(p)
for root in (D/'upload',D/'scanners',D/'retained_evidence',D/'evidence_a'):
 for p in root.rglob('*'):add(p)
for p in D.iterdir():
 if p.is_file() and (p.suffix in ('.py','.sh','.json','.log','.md','.patch') or p.name=='rehearsal_cpu_python') and p.name not in ('PACKAGE_MANIFEST.json','package.log','PACKAGE_CHECK.json'):add(p)
for folder in ('guard_q','guard_n'):
 for p in (D/folder).glob('*.json'):add(p)
for name in ('prep_diff.py','PREP_FIELDS.json','PREP_FIELDS.md','arm_go.py','arm_routing.py','jr.sh','N_PRODUCTION_CONFIG.json','N_IDENTITY.txt','REVIEW_SCHEMA.md','PRODUCTION_BLOCKERS.md','UPLOADS_24K.json','UPLOADS_24K.list','UPLOADS_24K_GO.json','BUILD24K_REPORT.md','N_CARD_KIT_ROWS.md','SESSION_NAMES_24F.json','DELIVERY_24I.json','TREE_SEAL.json','TREE_FILES.sha256'):add(L/'out'/name)
for name in ('work/build24/joblib.py','work/build21/environment21f.py'):add(L/name)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base=J.load(L/'out/DELIVERY_24I.json');basepin=dict(path=base['package'],sha256=base['sha256'])
record=dict(schema='build24k-overlay-v1',package_seal=seal,base=basepin,files=manifest,tree_sha256=audit['tree_sha256'],kits=seals,production_admission='BLOCKED',fixture_payloads='Local reversible blobs are excluded; evidence and reconstruction manifests are included.',delivery_record='out/DELIVERY_24K.json is the external final archive-hash record.')
J.write(D/'PACKAGE_MANIFEST.json',record);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24k_'+seal[:8]+'.tar');seen={}
with target.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
 for n,p in sorted(selected.items()):
  raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(n);info.mode=0o755 if p.stat().st_mode&0o111 else 0o644
  key=(h,info.mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];t.addfile(info)
  else:seen[key]=n;info.size=len(raw);t.addfile(info,io.BytesIO(raw))
expected={n:J.sha(p) for n,p in selected.items()}
with tarfile.open(target) as t:
 observed={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t};assert observed==expected
up=J.load(L/'out/UPLOADS_24K.json')
delivery=dict(status='PACKAGED_BLOCKED',package=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,verified_members=len(selected),base=basepin,
 tree=dict(tree_sha256=audit['tree_sha256'],files=len(tree)),kits=seals,GO=False,production_host_receipt=False,production_review=False,production_routing_selection=False,production_admission='BLOCKED',
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root']),checks='PASS',rehearsal='WRITTEN_NOT_RUN',
 rehearsal_script='work/build24k/go_rehearsal_k.sh',routing_job='out/jr.sh',routing_arming='out/arm_routing.py',prior_packages_unchanged=len(J.load(D/'BASELINE.json')['packages']))
J.write(L/'out/DELIVERY_24K.json',delivery);J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',sha256=delivery['sha256'],members=len(selected),all_member_bytes_verified=True))
print(json.dumps(delivery,indent=2))
