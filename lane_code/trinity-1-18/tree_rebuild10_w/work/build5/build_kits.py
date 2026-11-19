"""Stage the final source into both empty kits and scan their visible surfaces."""
import json
import os
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
os.environ['R2_FIXTURES']=str(L/'fixtures')
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import build, scan, verify
from student_pilot.p3_provenance import file_pin, write, load
from tests.test_r2_build import inputs
output=L/'work/build5/kits'
output.mkdir(parents=True,exist_ok=True)
dense=output/'dense.json'
write(dense,dict(schema='r2-dense-manifest-v1',synthetic=True,reconstruct_then_subsample=True,
                clips=[dict(id='fixture',frames=list(range(64)))]))
results=[]
for name,connector in (('a0','none'),('a2','gf1')):
    kit=output/name
    if kit.exists() and any(kit.iterdir()):raise ValueError('Final kit must stage from empty')
    result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),
                 dense_manifest=file_pin(dense) if connector=='gf1' else None)
    result.update(kit_path=str(kit.relative_to(L)),scan=scan(kit),verified_sha256=verify(kit),
                  production_authorized=False,dense_fixture=connector=='gf1')
    assert result['verified_sha256']==result['kit_sha256']
    results.append(result)
    print(json.dumps(dict(kit=name,sha256=result['kit_sha256'],scan=result['scan'])),flush=True)
write(output/'RESULTS.json',results)
