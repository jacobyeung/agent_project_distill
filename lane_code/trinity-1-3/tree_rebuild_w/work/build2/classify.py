"""Classify every remaining changed statement without assigning CPU gaps to hardware."""
import ast
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';O=L/'out'
coverage=json.loads((O/'B2_COMBINED_COVERAGE.json').read_text())
rows=[]
for name,entry in coverage.items():
    text=(T/name).read_text().splitlines()
    for line in entry['uncovered']:
        category='CPU-only';reason='Not exercised; CPU coverage requirement remains open.'
        if name=='student_pilot/r2_materialize.py' and line < 35:
            category='frame-host';reason='Full-store branch is prohibited on Trinity.'
        elif name=='student_pilot/carrier_c1_run.py':
            category='model-loader';reason='Native admission path requires loaded model/host receipts; not exercised by the focused producer proof.'
        rows.append(dict(file=name,line=line,statement=text[line-1],category=category,reason=reason))
summary={category:sum(r['category']==category and not r['file'].startswith('tests/') for r in rows)
         for category in ['CPU-only','model-loader','frame-host','GPU']}
result=dict(schema='build2-changed-statement-coverage-v1',
    total=sum(v['changed_statements'] for v in coverage.values()),executed=sum(v['executed'] for v in coverage.values()),
    production_total=sum(v['changed_statements'] for k,v in coverage.items() if not k.startswith('tests/')),
    production_executed=sum(v['executed'] for k,v in coverage.items() if not k.startswith('tests/')),
    unexecuted_by_class=summary,statements=rows,strict_cpu_gate=summary['CPU-only']==0,
    source='out/B2_COMBINED_COVERAGE.json')
(O/'B2_COVERAGE_CLASSIFIED.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='statements'},indent=2))
for row in rows:
    if not row['file'].startswith('tests/'):
        print(row['category'],row['file'],row['line'],row['statement'].strip())
