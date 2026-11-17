"""Show current assertion failures beside their prior recorded outcomes."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
old=json.loads((L/'work/build7/SUITE_COMPARISON.json').read_text())['failures']
prior={r['test']:r for r in old}
for name,error in json.loads((B/'proofs/suite_tree/legacy/live_failures.json').read_text()):
 record=prior.get(name,{})
 print(json.dumps(dict(test=name,last_line=error.strip().splitlines()[-1],prior_preexisting=record.get('preexisting'),prior_cause=record.get('cause'))))
for name,error in json.loads((B/'proofs/suite_tree/legacy/live_errors.json').read_text()):
 if name not in prior:
  print(json.dumps(dict(new_error_id=name,last_line=error.strip().splitlines()[-1])))
