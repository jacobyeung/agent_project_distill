"""Record artifact identity and review outcomes without repository operations."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load, digest
from student_pilot.source_seal import inventory
from launch_r2.build import verify
runpy.run_path(str(L/'work/build2/seal.py'),run_name='__main__')
seal=load(L/'out/TREE_SEAL.json');seal['schema']='build3b-source-inventory-v1'
(L/'out/TREE_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
kits=load(L/'out/B3B_KITS.json')
for item in kits:
    root=L/item['kit_path']
    assert verify(root)==item['kit_sha256']
    assert item['source_sha256']==seal['tree_sha256']
    cfg=load(root/load(root/'BUILD.json')['config']['path'])
    assert cfg['r2_all_stream_exclusions'] is True
    assert cfg['dev_scene_exclusions']['sha256']==load(L/'out/B3B_MERGED_BINDING.json')['merged']['sha256']
    assert cfg['scene_coverage'] is None
    assert cfg['r2_scene_rebuild'] is None
    assert load(root/'k/f.json')['scene_rebuild'] is None
    assert not load(root/'k/launch.json')['production_authorized']
    assert not (root/'o/ee000001').exists()
coverage=load(L/'out/B3B_COVERAGE_CLASSIFIED.json')
assert coverage['strict_cpu_gate'], 'Unexecuted CPU statements remain'
regressions=load(L/'out/B3B_REGRESSION_ACCEPTANCE.json')
assert regressions['all_required_pass'] and regressions['all_latest_pass']
size=lambda p:sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
result=dict(tree_sha256=seal['tree_sha256'],kits_match=True,production_authorized=False,
            tmp_bytes=size(L/'work/tmp'),lane_bytes=size(L),cpu_statement_gate=coverage['strict_cpu_gate'],
            unexecuted=coverage['unexecuted_by_class'],host_job_run=False,gpu_run=False)
assert result['tmp_bytes']<=200000000 and result['lane_bytes']<=2000000000
(L/'out/B3B_FINAL_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
