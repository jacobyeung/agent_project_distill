"""Check required deliverables after report assembly, without rewriting the tree."""
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
read=lambda path:json.loads(path.read_text())
required=['work/tree_r1/student_pilot/r2_dev_merged.json','out/TREE.diff','out/TREE_FILES.sha256',
          'out/TREE_SEAL.json','out/BUILD3B_REPORT.md','out/DESIGN_RECORD_tree_rebuild_20261115.md',
          'out/PRELAUNCH_CARD.md','out/FRAME_HOST_JOB.md','out/B3B_POOL_BATCH_PROOF.json',
          'out/B3B_NATIVE_PROOF.json','out/B3B_REGRESSION_ACCEPTANCE.json','out/B3B_COVERAGE_CLASSIFIED.json']
assert all((L/name).is_file() for name in required)
seal=read(L/'out/TREE_SEAL.json')
assert hashlib.sha256((L/'out/TREE.diff').read_bytes()).hexdigest()==seal['diff_sha256']
for name,digest in seal['files'].items():
    assert hashlib.sha256((L/'work/tree_r1'/name).read_bytes()).hexdigest()==digest
assert (L/'out/DESIGN_RECORD_tree_rebuild_20261115.md').read_text().count('\n## Build 3b\n')==1
size=lambda path:sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
value=dict(deliverables=required,tree_sha256=seal['tree_sha256'],tree_verified=True,
           tmp_bytes=size(L/'work/tmp'),lane_bytes=size(L))
assert value['tmp_bytes']<=200000000 and value['lane_bytes']<=2000000000
(L/'out/B3B_DELIVERED.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='deliverables'},indent=2))
