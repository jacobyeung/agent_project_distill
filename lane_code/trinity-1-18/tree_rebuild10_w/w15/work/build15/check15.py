from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
for rel in ('proofs/final_focused/TESTS.json','KIT_RESULT.json','SUITE_RUNS.json','CHANGED_COVERAGE.json','GAPS.json','proofs/mutations/RESULT.json'):
    p=B/rel
    if not p.exists():print(rel,'pending');continue
    v=json.loads(p.read_text())
    if rel.endswith('TESTS.json'):v={k:v[k] for k in ('tests','successful','failures','errors')}
    elif rel=='KIT_RESULT.json':v={k:{x:r.get(x) for x in ('kit_sha256','GO')} for k,r in v.items()}
    elif rel=='CHANGED_COVERAGE.json':v={k:v.get(k) for k in ('classes','executed','total')}
    elif rel=='GAPS.json':v=[(r['file'],r['line']) for r in v]
    print(rel,json.dumps(v))
p=B/'PRESERVATION.json'
if p.exists():print('inherited',json.dumps({k:dict(qualified=v['inherited_result_qualified'],mismatch=v.get('observed_source_mismatches')) for k,v in json.loads(p.read_text())['unavailable'].items()}))
root=B/'proofs/final/suite_tree/r2'
for name in ('progress.json','latest_failure.json','latest_error.json'):
    p=root/name
    if p.exists():print(name,p.read_text()[:1200])
print('workspace_bytes',sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))
