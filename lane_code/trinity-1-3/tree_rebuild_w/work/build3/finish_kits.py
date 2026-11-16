"""Stage source-addressed executable deliverables; never replace a populated kit."""
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r2.build import build, verify, TREE
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import file_pin, digest
from tests.test_r2_build import inputs
records=inputs()
records.update(mix=L/'out/MIX_A0.json',slots=L/'out/COMPONENT_SLOTS.json',
               prereg_text=L/'work/records/design/REFREEZE_PREREGISTRATION_20261115.md')
for pattern in ('*.jsonl','*.tsv'):
    for path in (L/'work/kit07ca49df_meta/m/k').glob(pattern):
        records['parent_'+path.stem]=path
source=digest(inventory(TREE))
root=L/'work/build3/kits';root.mkdir(parents=True,exist_ok=True)
dense=L/'work/build3/CPU_DENSE_FIXTURE.json'
dense.write_text(json.dumps(dict(schema='r2-dense-manifest-v1',synthetic=True,
    reconstruct_then_subsample=True,clips=[dict(id='cpu-proof-only',frames=list(range(64)))]))+'\n')
size=lambda p:sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
results=[]
for connector in ('none','gf1'):
    before=size(L/'work/tmp')
    if before>200000000 or size(L)>2000000000:raise ValueError('Storage guard')
    key=digest(dict(source=source,connector=connector))[:12]
    destination=root/key
    if destination.exists():
        result=json.loads((destination/'BUILD.json').read_text())
        if result['source_sha256']!=source:raise ValueError('Existing kit source differs')
    else:
        result=build(L/'work/kit07ca49df_meta/m',destination,connector=connector,records=records,
                     dense_manifest=file_pin(dense) if connector=='gf1' else None)
    results.append(dict(connector=connector,kit_path=str(destination.relative_to(L)),
        kit_sha256=verify(destination),source_sha256=source,staged_bytes=size(destination),
        tmp_before=before,tmp_after=size(L/'work/tmp'),admission=False,dense_fixture=connector=='gf1'))
(L/'out/B3_KITS.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
