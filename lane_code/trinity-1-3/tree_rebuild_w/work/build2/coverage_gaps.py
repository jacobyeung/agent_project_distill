import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for filename in ['B2_COVERAGE.json','B2_NEW_COVERAGE.json']:
    data=json.loads((L/'out'/filename).read_text())
    print(filename)
    for name,info in data.items():
        if info['uncovered'] and not name.startswith('tests/'):
            print(name,info['executed'],info['changed_statements'],info['uncovered'])
