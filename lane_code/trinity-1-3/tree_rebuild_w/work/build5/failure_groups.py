"""Summarize diagnostic exceptions without retaining new test products."""
from collections import defaultdict
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
data=json.loads((L/'work/build5/proofs/legacy_tree/results.json').read_text())
groups=defaultdict(list)
for name,error in data['failures']+data['errors']:
    groups[error.strip().splitlines()[-1]].append(name)
for reason,names in groups.items():
    if not any(x in reason for x in ('FileNotFoundError','PermissionError','ModuleNotFoundError','ImportError')):
        print(json.dumps(dict(reason=reason,tests=names)))
