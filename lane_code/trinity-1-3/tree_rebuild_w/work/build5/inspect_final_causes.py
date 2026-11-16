"""Inspect exact base traces still needing a human-readable cause label."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/build5/SUITE_COMPARISON.json').read_text())
for row in value['failures']:
    if row['cause'].startswith('unclassified:'):
        print(row['test'])
        print(row['base_error'][-2500:])
