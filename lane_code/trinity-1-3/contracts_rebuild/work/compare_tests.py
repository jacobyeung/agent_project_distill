from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[1]
before={}
for tag in ('BASE_BEFORE_FINAL','BASE_EXTRA'):
    before.update(json.loads((L/f'out/{tag}_results.json').read_text()))
after=json.loads((L/'out/BASE_AFTER_FINAL_results.json').read_text())
regressions={k:v for k,v in after.items() if v['outcome']=='failed' and before.get(k,{}).get('outcome')=='passed'}
improved=[k for k,v in after.items() if v['outcome']=='passed' and before.get(k,{}).get('outcome')=='failed']
report=dict(before=dict(Counter(v['outcome'] for v in before.values())),after=dict(Counter(v['outcome'] for v in after.values())),
    regressions=regressions,improved=improved,new_tests=[k for k in after if k not in before])
(L/'out/BASE_COMPARISON.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
