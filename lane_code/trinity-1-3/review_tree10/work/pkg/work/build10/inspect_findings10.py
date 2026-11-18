from pathlib import Path
import json
B=Path(__file__).resolve().parent
data=json.loads((B/'EAT1_GROUP_EVIDENCE.json').read_text())
for name in ('gf1','c8r','b04'):
    rows=[r for group in data[name]['groups'].values() for r in group if r['clause']=='A4']
    print(name,json.dumps(rows[:2]))
