from pathlib import Path
import hashlib,inspect,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build20';T=L/'work/tree_r1';sys.path[:0]=[str(T),str(B)]
from launch_r1.build import verify
from launch_r2.build import scan
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
import joblib
def read(p):return json.loads(p.read_text())
seal=read(L/'out/TREE_SEAL.json')['tree_sha256'];assert digest(inventory(T))==seal
kit=B/'kits/q';actual=verify(kit);assert actual==read(B/'proofs/operator/RESULT.json')['kit_sha256'];scan(kit)
assert joblib.sha(B/'joblib.py')==joblib.sha(kit/'b/z.py')
uploads=read(B/'UPLOADS.json');members=read(B/'PACKAGE_MANIFEST.json')['files']
for r in uploads['files']:
    name='work/build20/'+('kits/' if r['opaque_name'].startswith('q/') else 'upload/')+r['opaque_name']
    assert members[name]==dict(bytes=r['bytes'],sha256=r['sha256'])
assert all(r['caught'] and r['control']==0 for p in ('mutations','job_mutations') for r in read(B/'proofs'/p/'RESULT.json'))
assert read(B/'RESTAGED.json')['from_empty']
for step in ('400','600'):
    r=read(B/'proofs/native'/step/'q/RESULT.json');assert r['GO'] is False
    assert r['refusal']=='ValueError:R1_POST_FILTER_CAPACITY_SHORTFALL:pose'
source=read(B/'DELTA_COVERAGE.json');assert source['observed']==source['total']
value=dict(status='PASS',GO=False,source_seal=seal,kit_seal=actual,opaque_scan='PASS',upload_members_verified=len(uploads['files']),
    scope='Source inventory, kit seals and scanner, upload inclusion, mutation outcomes and recorded native refusals; no new runtime qualification.')
out=B/'proofs/delivery';out.mkdir(exist_ok=True);(out/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n')
status=(B/'STATUS.md').read_text().replace('Source sealed; packaging is in progress.','Source and kit seals verified. DELIVERY.json records the packaged bytes, hash and streaming verification. GO=false.')
(B/'STATUS.md').write_text(status)
print(json.dumps(value))
