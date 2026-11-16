from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[1];mode=sys.argv[1]
tree=L/'work/base/work/base/tree_b01ce449' if mode=='base' else L/'work/trees/r5_applied'
sys.path[:0]=[str(tree),str(L/'work/tests_r5')]
from fixtures_contracts import fixture,masks
from student_pilot import ground_lifting
from student_pilot.ground_replay import record_mask
from trace_format.ground_v313 import Session
P=L/'work/review2_inputs/base_sensor313_generated.json'
if mode=='base':
    records=[]
    for kind in ('landscape','portrait','rolled'):
        geo=fixture(kind)[1]()
        session=Session(ground_lifting,geo,None,program_version='3.13',geometry_mode='sensor',
            instances=lambda n:[dict(instance_id='selected',masks=masks(n).masks,prob=[1.]*32)])
        calls=['<ground obj="chair" mode="box">','<ground obj="table" mode="box">','<gap a="chair" b="table" rule="sampled_box_512">']
        queries=[dict(name=name,box_provider_id=session.box_provider_id,geometry_mode='sensor',
                      **record_mask(masks(name).masks,[1.]*32,.5,geo)) for name in ('chair','table')]
        records.append(dict(kind=kind,queries=queries,calls=calls,texts=[session.execute(c) for c in calls]))
    P.write_text(json.dumps(dict(base_source=str(tree),fixture_source=str(L/'work/tests_r5/fixtures_contracts.py'),records=records),indent=2))
else:
    from trace_format.contracts import contract_epoch
    from student_pilot.live_trace313 import AuditSession
    source=json.loads(P.read_text());checks=[]
    with contract_epoch(False):
        for row in source['records']:
            session=AuditSession(row['queries'],program_version='3.13')
            actual=[session.execute(c) for c in row['calls']]
            checks.append(dict(kind=row['kind'],calls=len(actual),equal=actual==row['texts'],actual=actual,expected=row['texts']))
    result=dict(source=str(P),source_kind='Generated with sealed base code and lane fixtures; POOL has rendered rows, not live replay queries.',
                traces=len(checks),calls=sum(c['calls'] for c in checks),mismatches=sum(not c['equal'] for c in checks),checks=checks)
    (L/'work/test_artifacts_r5/SENSOR313_REPLAY_R5.json').write_text(json.dumps(result,indent=2))
    assert result['mismatches']==0,result
