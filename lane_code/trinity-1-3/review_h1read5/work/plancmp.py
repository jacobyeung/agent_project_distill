import json, sys
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/review_h1read5/work/k')
sys.path.insert(0, str(K/'kit/launcher'))
import orchard_launcher as L
B = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build')
for tok in sys.argv[2:]:
    old = json.loads((B/tok/'CONFIG.json').read_text()); s = old['spec']
    kw = dict(run=s.get('run_id', None))
    print(tok, {k:s[k] for k in s if k in ('step','families','types','generation')}, sorted(s)[:40])
