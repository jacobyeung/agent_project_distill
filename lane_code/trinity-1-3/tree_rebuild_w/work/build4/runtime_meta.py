import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/kit07ca49df_meta/m/k/0.json').read_text())
print('keys',list(value))
for key in ('closure','np','fla','venv','bwrap'):
    print(key,value.get(key))
