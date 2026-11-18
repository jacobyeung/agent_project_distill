from pathlib import Path
import json
B=Path(__file__).resolve().parent
v=json.loads((B/'EAT1_GROUP_EVIDENCE.json').read_text())
for reader in ('gf1','c8r'):
    for group in ('G1','G2','G4','G5','G6','G7'):
        print(reader,group)
        for r in v[reader]['groups'].get(group,[]):
            print(r.get('rule'),Path(r.get('file','')).name,r.get('line'),r.get('function'),r.get('text','')[:180])
