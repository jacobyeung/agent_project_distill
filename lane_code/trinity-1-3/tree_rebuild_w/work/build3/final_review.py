"""Verify final artifact consistency and record local storage bounds."""
import hashlib
import json
from pathlib import Path
import sys

L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
from launch_r2.build import verify

seal=load(L/'out/TREE_SEAL.json')
assert digest(inventory(L/'work/tree_r1'))==seal['tree_sha256']
assert hashlib.sha256((L/'out/TREE.diff').read_bytes()).hexdigest()==seal['diff_sha256']
kits=load(L/'out/B3_KITS.json')
for item in kits:
    root=L/item['kit_path']
    assert verify(root)==item['kit_sha256']
    assert item['source_sha256']==seal['tree_sha256']
    assert not (root/'o/ee000001').exists()
    assert not (root/'o/ee000002').exists()
    assert not load(root/'k/launch.json')['production_authorized']
fresh=load(L/'out/B3_FRESH_ENTRY_PROOF.json')
assert {x['kit'] for x in fresh}=={x['kit_path'] for x in kits}
assert all(x['reason']=='Missing component evidence: init_m544' and x['exit_code']!=0 for x in fresh)
for name in ('BUILD3_REPORT.md','FRAME_HOST_JOB.md','PRELAUNCH_CARD.md',
             'TREE_FILES.sha256','DESIGN_RECORD_tree_rebuild_20261115.md'):
    assert (L/'out'/name).stat().st_size>0
size=lambda p:sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
tmp,lane=size(L/'work/tmp'),size(L)
assert tmp<=200000000 and lane<=2000000000
coverage=load(L/'out/B3_COVERAGE_CLASSIFIED.json')
result=dict(schema='build3-final-artifact-review-v1',tree_sha256=seal['tree_sha256'],
    kits_match=True,kits_pristine=True,production_authorized=False,
    tmp_bytes=tmp,tmp_limit_bytes=200000000,lane_bytes=lane,lane_limit_bytes=2000000000,
    cpu_statement_gate=coverage['strict_cpu_gate'],unexecuted=coverage['unexecuted_by_class'],
    input_availability=load(L/'out/B3_INPUT_AVAILABILITY.json'),
    host_job_run=False,gpu_run=False)
(L/'out/B3_FINAL_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
