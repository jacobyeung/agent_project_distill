"""Show one existing traceback for each still-uncategorized base-matched cause."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
rows=json.loads((B/'SUITE_COMPARISON.json').read_text())['failures']
causes={}
for row in rows:
    if row['preexisting'] and row['cause'].startswith('unclassified:'):
        causes.setdefault(row['cause'],[]).append(row)
for cause,group in causes.items():
    print(json.dumps(dict(cause=cause,tests=[r['test'] for r in group],
                          example=group[0]['tree_error'][-5000:])))
