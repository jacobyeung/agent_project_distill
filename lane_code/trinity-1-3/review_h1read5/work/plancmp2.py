import json, sys
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/review_h1read5/work/k')
sys.path.insert(0, str(K/'kit/launcher'))
import orchard_launcher as L
B = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build')
W = Path(sys.argv[1]); W.mkdir()
integrity = {'payload_pins','payload_sha256','launcher_pins','launcher_review','launcher_review_pin'}
for tok, types in (('a5f07824bb3','direct'),('aed15a8b7cb',None)):
    old = json.loads((B/tok/'CONFIG.json').read_text())
    new = L.prepare(tok, W/tok, 544, run='469ddece', generation='mstop', families=['a7'], types=types)
    a = json.dumps(old['spec'], sort_keys=True); b = json.dumps(new['spec'], sort_keys=True)
    changed = sorted(k for k in set(old)|set(new) if old.get(k) != new.get(k))
    print(tok, 'spec_equal', a == b, 'plan_equal', old['plan_sha256'] == new['plan_sha256'], new['plan_sha256'], 'changed', changed)
