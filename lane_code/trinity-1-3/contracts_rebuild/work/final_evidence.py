from pathlib import Path
import hashlib
import json
import re
from collections import Counter

L=Path(__file__).resolve().parents[1]
base=L/'work/base/work/base/tree_b01ce449'
out=L/'out'
load=lambda name:json.loads((out/name).read_text())
checks=[]
for line in (L/'work/base/out/BASE_FILES_b01ce449.sha256').read_text().splitlines():
    digest,name=line.split(None,1)
    path=base/name.strip()
    assert path.stat().st_size<20_000_000
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual==digest,name
    checks.append(name)
manifest=load('PATCH_MANIFEST.json')
manifest['patch_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('PATCH_*.diff')}
manifest['base_file_inventory']=str(L/'work/base/out/BASE_FILES_b01ce449.sha256')
manifest['base_file_inventory_sha256']=hashlib.sha256((L/'work/base/out/BASE_FILES_b01ce449.sha256').read_bytes()).hexdigest()
manifest['base_files_verified']=len(checks)
(out/'PATCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')

before={}
for tag in ('BASE_BEFORE_FINAL','BASE_EXTRA'):
    before.update(load(tag+'_results.json'))
after=load('BASE_AFTER_FINAL_results.json')
targeted=load('B1_FINAL_results.json')
for name,value in targeted.items():
    name=name.removeprefix('trees/patched/')
    if name in after:after[name]=value
remaining={name:value for name,value in after.items() if value['outcome']=='failed' and before.get(name,{}).get('outcome')=='passed'}
assert not remaining,remaining
assert all(v['outcome']=='passed' for v in targeted.values())

def counts(tag):
    text=(out/(tag+'.log')).read_text()
    line=text.splitlines()[-1]
    return {kind:int(count) for count,kind in re.findall(r'(\d+) (passed|failed|skipped|errors)',line)}
coverage=load('COVERAGE_DETAIL.json')
proof=load('CPU_PROOF_B1.json')
inverted=[v for k,v in proof['fixtures'].items() if k.startswith('inverted')]
record=dict(base_seal=manifest['base_seal'],files_changed=len(manifest['files']),
    source_files_changed=sum(not n.startswith('tests/') for n in manifest['files']),
    inherited_test_files_changed=sum(n.startswith('tests/') for n in manifest['files']),
    base_files_verified=len(checks),
    final_suite=counts('B1_FINAL'),final_suite_source=str(out/'B1_FINAL.log'),
    inherited_before_runs={tag:counts(tag) for tag in ('BASE_BEFORE_FINAL','BASE_EXTRA')},
    inherited_after_broad=counts('BASE_AFTER_FINAL'),
    inherited_after_targeted_outcomes=dict(Counter(v['outcome'] for v in after.values())),
    remaining_new_failed_test_ids=remaining,
    inherited_after_note='Broad run plus targeted final correction; outcome JSON combines call failures and setup errors and omits collection errors. Consult raw pytest log counts.',
    coverage={g:dict(executed=v['executed'],total=v['total']) for g,v in coverage.items()},
    guard_grid=load('GUARD_GRID.json'),
    cpu_fixtures=len(proof['fixtures']),inverted_fixtures=len(inverted),
    inverted_refused=sum(v['patched_verdict']=='reference_camera_up_opposes_gravity' for v in inverted),
    replay_off_equal_fixtures=sum(v['replay_off_byte_equal'] for v in proof['fixtures'].values()),
    final_tree_test_source=str(out/'B1_FINAL_results.json'),
    lane_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file()))
assert record['lane_bytes']<2_000_000_000
(out/'VALIDATION_SUMMARY.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
