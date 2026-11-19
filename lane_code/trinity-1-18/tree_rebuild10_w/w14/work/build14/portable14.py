"""Check preservation evidence and prepare reproducible proof drivers."""
from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build14'
s=(L/'work/build12/confusables12.py').read_text().replace("B=L/'work/build12'","B=L/'work/build14'")
(B/'confusables14.py').write_text(s)
s=(L/'work/build13/mapping13.py').read_text().replace('work/build13','work/build14')
(B/'mapping14.py').write_text(s)
v=json.loads((L/'fixtures/work/kit07ca49df_meta/m/k/b02e4385.json').read_text())
print('fixture preparation present:',bool(v.get('preparation')))
print('source report counts:',{k:json.loads((L/'work/build13/SUITE_COMPARISON.json').read_text())[k] for k in ['run','passed','preexisting','regressions','skipped','r2_failures']})
