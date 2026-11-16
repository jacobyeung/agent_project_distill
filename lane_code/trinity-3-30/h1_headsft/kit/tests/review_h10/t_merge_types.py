"""Refute: the Orchard return (journals/<type>/<gpu>) cannot be merged/scored by h1eval.h10.merge."""
import json
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/h1_headsft/kit')
D = K/'tmp/b8/rehearsal/a6e2bacffbbd5'
import h1eval.h10.merge as M
J = D/'r/metadata/journals'
b = json.loads((J/'0/0/environment.json').read_text())['binding']
M.code_hash = lambda root=None: b['evaluator_code_sha256']   # neutralise the copy-location hash only
out = Path(__import__('os').environ['A_TEST'])
result=M.merge_types(sorted(J.glob('*/*')),out/'merged',items=D/'items.json')
assert result['records']==110 and result['items']==50
print('all_types OK',result)
