from pathlib import Path
import json
B=Path(__file__).resolve().parent
for p in (B/'SUITE_RUNS.json',B/'proofs/final/suite_tree/generator/NOT_RERUN.json',B/'proofs/final/suite_tree/legacy/NOT_RERUN.json'):
    value=json.loads(p.read_text())
    records=(value,) if 'reason' in value else (value['generator'],value['legacy'])
    for record in records:record['reason']='The required input is absent. Historical totals do not qualify the current source.'
    p.write_text(json.dumps(value,indent=2)+'\n')
p=B/'suite18.py';text=p.read_text();text=text.replace('The complete suite source binding changed; historical totals are not transferred to build 17.','The required input is absent. Historical totals do not qualify the current source.');p.write_text(text)
