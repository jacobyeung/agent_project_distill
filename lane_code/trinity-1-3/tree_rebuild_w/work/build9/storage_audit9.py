"""Report bounded-test refusals separately from final retained storage."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
groups={}
for name in ('suite_tree','suite_base','packet','final_targeted','cpu_weighted'):
    for path in sorted((B/'proofs'/name).rglob('temporary_sizes.json')):
        rows=json.loads(path.read_text())
        exceeded=[r for r in rows if r['after_bytes']>200_000_000]
        groups[str(path.relative_to(L))]=dict(tests=len(rows),
            maximum_before_bytes=max((r['before_bytes'] for r in rows),default=0),
            maximum_after_bytes=max((r['after_bytes'] for r in rows),default=0),
            refused_after_test=exceeded)
value=dict(groups=groups,policy='The unchanged harness refuses any test whose measured after-test size exceeds the cap and compacts its own scratch products before the next test. Such a test is not a pass. Final retained storage is a separate measurement.',
    total_refused_after_test=sum(len(v['refused_after_test']) for v in groups.values()))
(B/'STORAGE_AUDIT.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='groups'}))
