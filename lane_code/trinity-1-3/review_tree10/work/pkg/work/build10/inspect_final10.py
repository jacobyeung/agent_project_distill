from pathlib import Path
import json
B=Path(__file__).resolve().parent
for name in ('SUITE_COMPARISON.json','FINAL_PASS.json','DELIVERY.json','PATCH.json'):
    p=B/name
    if not p.is_file():continue
    value=json.loads(p.read_text())
    print(name,json.dumps({k:v for k,v in value.items() if k not in ('failures','evidence','statements','coverage_sources')}))
    if name=='SUITE_COMPARISON.json':
        for r in value['failures']:
            if not r['preexisting']:print(json.dumps({k:r[k] for k in ('test','cause','base_cause')}))
