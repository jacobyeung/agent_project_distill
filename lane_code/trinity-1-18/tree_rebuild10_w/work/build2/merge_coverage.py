"""Union stable-source coverage from the complete suite and focused closing tests."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];O=L/'out'
a=json.loads((O/'B2_FINAL_COVERAGE.json').read_text())
b=json.loads((O/'B2_CLOSING_COVERAGE.json').read_text())
for name,value in b.items():
    previous=a.get(name,dict(executed_lines=[]))
    executed=set(previous['executed_lines'])|set(value['executed_lines'])
    universe=set(value['executed_lines'])|set(value['uncovered'])
    a[name]=dict(changed_statements=len(universe),executed=len(executed & universe),
                 executed_lines=sorted(executed & universe),uncovered=sorted(universe-executed))
(O/'B2_COMBINED_COVERAGE.json').write_text(json.dumps(a,indent=2)+'\n')
