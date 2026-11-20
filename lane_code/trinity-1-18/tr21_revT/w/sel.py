import json, hashlib
from pathlib import Path
D = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/work/build24m4v')
f = D/'inputs/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'
raw = f.read_bytes(); print('sha ok', hashlib.sha256(raw).hexdigest() == f.name)
s = json.loads(raw)
print('schema', s.get('schema'), 'keys', list(s.keys())[:15])
for n, e in sorted(s['sources'].items()):
    print(f"{n:20s} {e['status']:12s} kind={e.get('kind')} declared={e.get('declared_rows')} reason={str(e.get('reason'))[:60]}")
el = sorted(n for n, e in s['sources'].items() if e['status'] == 'ELIGIBLE')
names = json.loads((D/'SOURCES.json').read_text())['names']
print('ELIGIBLE == list:', el == sorted(names), el)
