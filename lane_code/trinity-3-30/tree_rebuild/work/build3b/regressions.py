"""Accept the full suite only when every failure has a passing closure result."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
read=lambda p:json.loads(p.read_text())
paths=sorted((L/'out').glob('B3B_*TEST_RESULTS.json'),key=lambda p:p.stat().st_mtime_ns)
latest={}
for path in paths:
    value=read(path)
    bad={label[label.index('(')+1:-1] for label,_ in value['errors']+value['failures']+value['skipped']}
    for row in value['records']:
        latest[row['test']]=dict(passed=row['test'] not in bad,evidence=str(path.relative_to(L)))
required={row['test'] for row in read(L/'out/B3B_ALL_TEST_RESULTS.json')['records']}
result=dict(full_suite_source='out/B3B_ALL_TEST_RESULTS.json',required_tests=len(required),
            final_tests=len(latest),all_required_pass=all(latest[name]['passed'] for name in required),
            all_latest_pass=all(item['passed'] for item in latest.values()),tests=latest,
            method='Full suite plus later targeted closure; earlier failures remain in their original reports')
(L/'out/B3B_REGRESSION_ACCEPTANCE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='tests'},indent=2))
assert result['all_required_pass'] and result['all_latest_pass']
