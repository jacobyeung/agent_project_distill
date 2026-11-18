import json, sys
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_h1read5/work/k/kit/launcher')
import orchard_launcher as L
B = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9')
old = json.loads((B/'CONFIG.json').read_text())
new = L.prepare('adff67f7ae9', Path(sys.argv[1]), 544, run='469ddece', generation='mstop', families=['a7'], types=old['spec'].get('types'))
print('types', old['spec'].get('types'), 'CONFIG identical', old == new, sorted(k for k in set(old)|set(new) if old.get(k)!=new.get(k)))
print('BATCH identical', (B/'BATCH.sh').read_bytes() == (Path(sys.argv[1])/'BATCH.sh').read_bytes())
