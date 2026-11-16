import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
for name, record in json.loads((root/'out/COVERAGE.json').read_text()).items():
    lines = (root/'work/tree_r1'/name).read_text().splitlines()
    print(name, record['executed'], '/', record['changed_statements'])
    for number in record['uncovered']:
        print(number, lines[number-1].strip())
