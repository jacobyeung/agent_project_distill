from pathlib import Path
import json,sys
B=Path(__file__).resolve().parent;L=B.parents[1];T=L/'work/tree_r1'
sys.path[:0]=[str(T),str(B)]
from student_pilot.p3_provenance import load,sha256,digest
from student_pilot.source_seal import inventory,check_archive
from launch_r1.build import verify
from naming21 import scan_decoded
files=inventory(T);seal=digest(files)
assert load(L/'out/TREE_SEAL.json')['tree_sha256']==seal
records={}
for name in ('r1','q'):
    kit=B/'kits'/name;record=load(kit/'BUILD.json');control=load(kit/'k/a.json')
    assert record['GO'] is False and control['GO'] is False
    assert record['source_seal']==seal==control['source']['tree_sha256']
    assert verify(kit)==record['kit_sha256']
    src=control['source'];check_archive(dict(path=str(kit/src['path']),sha256=src['sha256']),files)
    records[name]=record
scan=scan_decoded(B/'kits/q')
(B/'proofs/operator/SCAN.json').write_text(json.dumps(scan,indent=2)+'\n')
uploads=load(B/'UPLOADS.json');total=0
for row in uploads['files']:
    p=Path(row['local_path']);assert p.stat().st_size==row['bytes'] and sha256(p)==row['sha256']
    total+=row['bytes']
assert total==uploads['total_bytes']
staged={r['sha256'] for r in uploads['files']}
receipts=load(B/'proofs/receipts/RESULT.json')
assert {r['sha256'] for r in receipts['fetched']}<=staged
for group in ('receipts','prepared','children'):
    assert {r['pin']['sha256'] for r in receipts[group]}<=staged
binding=load(B/'proofs/v2h/BINDING.json')
assert {r['sha256'] for r in binding['files'].values()}<=staged
assert binding['union']['union']['sha256'] in staged and binding['split']['sha256'] in staged
cfg=load(B/'inputs/config.json');prior=load(L/'work/build20/inputs/config.json')
from student_pilot.r1_training import PARENT
assert cfg['init_artifact']['artifact']['sha256']==PARENT and cfg['r2_identity']['init']['step']==544
assert cfg['camera_overrides']['weight_scale']==0.04
assert [p for p in cfg['remove_files'] if p['sha256']!=binding['union']['union']['sha256']]==prior['remove_files']
result=dict(status='PASS',GO=False,tree_seal=seal,kits=records,decoded_scan=scan,
            upload_bytes=total,upload_files=len(uploads['files']),from_empty=load(B/'RESTAGED.json'))
(B/'FINAL_KITS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status='PASS',tree_seal=seal,upload_bytes=total,upload_files=len(uploads['files']))))
