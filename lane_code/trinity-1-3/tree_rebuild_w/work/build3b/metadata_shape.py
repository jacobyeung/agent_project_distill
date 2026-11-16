import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/kit07ca49df_meta/m/k/pool_manifest.json').read_text())
print(json.dumps({k:v for k,v in value.items() if k not in ('sets','exclusions')},indent=2)[:4000])
