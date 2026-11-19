import json
import sys
from pathlib import Path
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import build
from student_pilot.p3_provenance import file_pin, write
from tests.test_r2_build import inputs
output=L/'work/build4'/sys.argv[1]
output.mkdir(parents=True,exist_ok=False)
dense=output/'dense.json'
write(dense,dict(schema='r2-dense-manifest-v1',synthetic=True,reconstruct_then_subsample=True,
                clips=[dict(id='fixture',frames=list(range(64)))]))
results=[]
for name, connector in (('a0','none'),('a2','gf1')):
    result=build(L/'work/kit07ca49df_meta/m',output/name,connector=connector,records=inputs(),
                 dense_manifest=file_pin(dense) if connector=='gf1' else None)
    result['kit_path']=str((output/name).relative_to(L))
    results.append(result)
    print(name,result['kit_sha256'],flush=True)
write(output/'RESULTS.json',results)
