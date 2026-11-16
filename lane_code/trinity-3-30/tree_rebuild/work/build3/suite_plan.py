import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
modules=set()
for prefix in ('B2_FINAL_','B2_CLOSING_','B2_INTEGRATION_','B2_CONFIG_','B2_FALLBACK_'):
    v=json.loads((L/'out'/(prefix+'TEST_RESULTS.json')).read_text())
    print(prefix, sum(max(0,r['tmp_after']-r['tmp_before']) for r in v['records']))
    for r in v['records']:
        parts=r['test'].split('.')
        modules.add('.'.join(parts[:-2]))
(L/'work/build3/suite.json').write_text(json.dumps(sorted(modules)))
print(sorted(modules))
