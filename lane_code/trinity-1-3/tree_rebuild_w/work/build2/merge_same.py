"""Union the final fallback proof over the same sealed source."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]; O=L/'out'
read=lambda name:json.loads((O/name).read_text())
prior=read('B2_COMBINED_COVERAGE.json'); latest=read('B2_FALLBACK_COVERAGE.json')
for name,item in latest.items():
    previous=prior[name]
    universe=set(item['executed_lines'])|set(item['uncovered'])
    if universe != set(previous['executed_lines'])|set(previous['uncovered']):
        raise ValueError('Changed source invalidates direct coverage union')
    executed=set(item['executed_lines'])|set(previous['executed_lines'])
    prior[name]=dict(changed_statements=len(universe),executed=len(executed),
                     executed_lines=sorted(executed),uncovered=sorted(universe-executed))
(O/'B2_COMBINED_COVERAGE.json').write_text(json.dumps(prior,indent=2)+'\n')
