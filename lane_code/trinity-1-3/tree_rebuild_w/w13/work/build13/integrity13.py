from pathlib import Path
import json,hashlib,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build13';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
seal=json.loads((L/'out/TREE_SEAL.json').read_text())
assert digest(inventory(L/'work/tree_r1'))==seal['tree_sha256']
d=json.loads((B/'DELIVERY.json').read_text());p=L/d['path']
assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256']
assert p.stat().st_size==d['bytes']<150_000_000
a=json.loads((B/'proofs/final/package/ARCHIVE.json').read_text())
assert a['sha256']==d['sha256'] and a['source_sha256']==seal['tree_sha256']
with tarfile.open(p) as f:
    for name in ('out/BUILD13_REPORT.md','out/DESIGN_RECORD_tree_rebuild_20261115.md','out/TREE_SEAL.json','out/TREE_FILES.sha256','out/TREE.diff'):
        assert f.extractfile(name).read()==(L/name).read_bytes(),name
k=json.loads((B/'KIT_RESULT.json').read_text())
assert all(v.get('source_sha256',v.get('source_seal'))==seal['tree_sha256'] and v['GO'] is False for v in k.values())
record=dict(status='PASS',seal=seal['tree_sha256'],archive=d,archive_verified=a,
    report_bytes_equal=True,kit_sources_equal=True,GO=False)
o=B/'proofs/integrity';o.mkdir(parents=True,exist_ok=True);(o/'RESULT.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
