"""Run the production builder against the authoritative local payload inventory."""
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT/'src'))
from orchard_h10 import build as builder

builder.K=OUT
builder.T=OUT/'src/orchard_h10/vendor'
names=set(json.loads((OUT/'BASE_INVENTORY.json').read_text()))-{'8.py','items/devs1_routed.json','items/r0dev.json'}
names.update({'items/room134.json','inputs/room_captures.json','h1eval/room134.py'})
names.add('b/e2e_reader/perception_memo.py')
builder.sources=lambda:{name:OUT/'src'/name for name in sorted(names)}
# The production builder reads operator.py separately for its 8.py entry point.
# Supply that single source under K without copying or refreshing any dependencies.
(OUT/'orchard_h10').mkdir(exist_ok=True)
(OUT/'orchard_h10/operator.py').write_bytes((OUT/'src/orchard_h10/operator.py').read_bytes())
repin=OUT/'reader_repin';(repin/'e2e_reader').mkdir(parents=True,exist_ok=True)
for p in (OUT/'src/b/e2e_reader').glob('*.py'):(repin/'e2e_reader'/p.name).write_bytes(p.read_bytes())
pins={str(p.relative_to(OUT/'src/b')):__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in (OUT/'src/b/e2e_reader').glob('*.py')}
(OUT/'reader_repin.json').write_text(json.dumps(dict(source=str(repin),sha256=pins)))
result=builder.build(OUT/'package',token=(OUT/'TOKEN').read_text().strip(),
                     refresh=(OUT/'package/CONFIG.json').exists(),reader_repin=OUT/'reader_repin.json')
(OUT/'0.tgz').write_bytes((OUT/'package/0.tgz').read_bytes())
(OUT/'BUILD.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))

import tarfile
with tarfile.open(OUT/'0.tgz') as t:(OUT/'src/9.json').write_bytes(t.extractfile('9.json').read())
