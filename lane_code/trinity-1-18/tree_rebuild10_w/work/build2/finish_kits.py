"""Stage the final bounded inspection kits, then record their actual disk sizes."""
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import build,verify
from tests.test_r2_build import inputs
from student_pilot.p3_provenance import file_pin,load,sha256

tmp=L/'work/tmp'
size=lambda p:sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
records=inputs()
records['mix']=L/'out/MIX_A0.json'
records['slots']=L/'out/COMPONENT_SLOTS.json'
records['prereg_text']=L/'work/records/design/REFREEZE_PREREGISTRATION_20261115.md'
for pattern in ('*.jsonl','*.tsv'):
    for path in (L/'work/kit07ca49df_meta/m/k').glob(pattern):
        records['parent_'+path.stem]=path
root=L/'work/build2/kits';root.mkdir(exist_ok=True)
dense=L/'work/build2/CPU_DENSE_FIXTURE.json'
dense.write_text(json.dumps(dict(schema='r2-dense-manifest-v1',synthetic=True,
    reconstruct_then_subsample=True,clips=[dict(id='cpu-proof-only',frames=list(range(64)))]),indent=2)+'\n')
results=[]
for connector,key in [('none','b0b0b0b0'),('gf1','b2b2b2b2')]:
    before=size(tmp)
    if before>200000000 or size(L)>2000000000:raise ValueError('Storage guard')
    result=build(L/'work/kit07ca49df_meta/m',root/key,connector=connector,records=records,
                 dense_manifest=file_pin(dense) if connector=='gf1' else None)
    after=size(tmp)
    if after>200000000 or size(L)>2000000000:raise ValueError('Storage guard')
    results.append(dict(connector=connector,kit_path=str((root/key).relative_to(L)),
        kit_sha256=verify(root/key),staged_bytes=size(root/key),tmp_before=before,tmp_after=after,
        source_sha256=result['source_sha256'],admission=False,dense_fixture=connector=='gf1'))
(L/'out/B2_KITS.json').write_text(json.dumps(results,indent=2)+'\n')
zero=load(L/'work/kit07ca49df_meta/m/k/0.json')
pose=[x for x in zero['extra'] if '/a3v2/' in x.get('dest','') or '/a2v3/' in x.get('dest','')]
external=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/rows_rebuild/ORCHARD_INVENTORY_S0.md')
previous=load(L/'out/POSE_SOURCE_BINDINGS.json')
(L/'out/POSE_SOURCE_BINDINGS.json').write_text(json.dumps(dict(sources=pose,
    staging_source='work/kit07ca49df_meta/m/k/0.json',staging_sha256=sha256(L/'work/kit07ca49df_meta/m/k/0.json'),
    inventory_path=str(external),inventory_sha256=previous['inventory_sha256'],second_source_found=True,
    presence_checked_here=False,k6=dict(shards=12,members=290880,map_present=True),
    note='Counts and presence are from the named inventory; no Orchard call ran here.'),indent=2)+'\n')
print(json.dumps(results,indent=2))
