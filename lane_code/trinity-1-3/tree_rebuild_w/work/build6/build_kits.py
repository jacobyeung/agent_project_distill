"""Stage A2 first, then its fallback; both authorizations stay closed."""
import json,os,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];out=L/'work/build6/kits'
os.environ['R2_FIXTURES']=str(L/'fixtures');sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import build,scan,verify
from student_pilot.p3_provenance import file_pin,write,load
from tests.test_r2_build import inputs
out.mkdir(parents=True,exist_ok=True);dense=out/'dense.json'
write(dense,dict(schema='r2-dense-manifest-v1',synthetic=True,reconstruct_then_subsample=True,clips=[dict(id='fixture',frames=list(range(64)))]))
results=[]
for name,connector in (('a2','gf1'),('a0','none')):
    kit=out/name
    if kit.exists() and any(kit.iterdir()):raise ValueError('Kit must stage from empty')
    result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector=connector,records=inputs(),
                 dense_manifest=file_pin(dense) if connector=='gf1' else None,init_pin=file_pin(L/'out/INIT_INPUT.json'))
    result.update(kit_path=str(kit.relative_to(L)),scan=scan(kit),verified_sha256=verify(kit),production_authorized=False,
                  dense_fixture=connector=='gf1',init_selection=file_pin(L/'out/INIT_INPUT.json'))
    assert result['kit_sha256']==result['verified_sha256'];results.append(result)
    print(json.dumps(dict(kit=name,sha256=result['kit_sha256'],scan=result['scan'])),flush=True)
write(out/'RESULTS.json',results)
