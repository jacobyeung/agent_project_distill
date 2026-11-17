"""Keep every supplemental attempt and report each case's latest observed outcome."""
import collections,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
root=B/'proofs/coverage_final'
paths=[B/'proofs/final_targeted/results.json',root/'initial/results.json']
paths+=sorted(root.glob('history/*/results.json'),key=lambda p:p.stat().st_mtime_ns)
paths+=[root/'results.json']
latest={};attempts=[]
for path in paths:
 if not path.exists():continue
 value=json.loads(path.read_text());source=str(path.relative_to(L))
 attempts.append(dict(source=source,run=value['tests'],passed=len(value['passed']),
                      errors=len(value['errors']),failures=len(value['failures']),complete=value['complete']))
 for test in value['passed']:latest[test]=dict(status='passed',source=source)
 for kind in ('errors','failures'):
  for test,error in value[kind]:latest[test]=dict(status=kind,source=source,cause=error.strip().splitlines()[-1])
record=dict(attempts=attempts,executions=sum(a['run'] for a in attempts),latest_counts=dict(collections.Counter(v['status'] for v in latest.values())),
            cases=latest,complete=all(a['complete'] for a in attempts),
            note='Latest outcomes reconcile supplemental fixture corrections only. The frozen package comparison and its regressions are unchanged; all original attempts remain available.')
(B/'FOLLOWUP_RESULTS.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('cases','attempts')}))
