"""Keep concise diagnosis of the incomplete exploratory run, not test payloads."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/build5/proofs/suite_tree/results.json').read_text())
record={key:value[key] for key in ('tests','fatal','tmp_bytes')}
record.update(passed=len(value['passed']),skipped=len(value['skips']),
              r2_errors=[(name,error) for name,error in value['errors']+value['failures'] if name.startswith('tests.test_r2')],
              legacy_errors=[dict(test=name,reason=error.strip().splitlines()[-1]) for name,error in value['errors']+value['failures'] if not name.startswith('tests.test_r2')],
              status='Incomplete; no qualification claim',
              source='work/build5/proofs/suite_tree/results.json before final-package overwrite')
(L/'work/build5/EXPLORATORY.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:record[key] for key in ('tests','passed','skipped','status')}))
