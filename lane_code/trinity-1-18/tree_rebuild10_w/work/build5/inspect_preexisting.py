"""Print bounded cause evidence for same-case base failures."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/build5/LEGACY_COMPARISON.json').read_text())
seen=set()
for row in value['failures']:
    if not row['preexisting'] or not row['cause'].startswith('unclassified:') or row['cause'] in seen:
        continue
    seen.add(row['cause'])
    print(row['test'])
    print(row['base_error'].strip().splitlines()[-1])
