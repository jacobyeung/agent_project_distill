"""Refute: the Orchard return (journals/<type>/<gpu>) cannot be merged/scored by h1eval.h10.merge."""
import json
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/h1_headsft/kit')
D = K/'tmp/b8/rehearsal/a6e2bacffbbd5'
import h1eval.h10.merge as M
J = D/'r/metadata/journals'
b = json.loads((J/'0/0/environment.json').read_text())['binding']
M.code_hash = lambda root=None: b['evaluator_code_sha256']   # neutralise the copy-location hash only
out = Path('/dev/shm/jjyeung_rv10')
for name, dirs in [('one_type', [J/'0/0', J/'0/1']), ('all_types', sorted(J.glob('*/*')))]:
    try:
        print(name, 'OK', M.merge(dirs, out/('m_'+name), items=D/'items.json'))
    except Exception as e:
        print(name, 'FAIL', type(e).__name__, e)
