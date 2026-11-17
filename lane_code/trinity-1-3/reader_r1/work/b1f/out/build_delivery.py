from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;P=O/'package'
sys.path.insert(0,str(O/'src'))
from orchard_h10.common import template,sha
from orchard_h10.build import CORE
template(O/'src/orchard_h10/vendor');import orchard_launcher as L
(P/'a/1.json').write_bytes((O/'inputs_tower.json').read_bytes())
(P/'a/export.json').write_bytes((O/'export_544.json').read_bytes())
files={str(p.relative_to(P)):p.read_bytes() for p in P.rglob('*') if p.is_file()}
assert set(files)=={'0.tgz','0.json','3.py','BATCH.sh','CONFIG.json','SUBMIT.cmd','PACKAGE.json','INPUTS.example.json','a/1.json','a/export.json','a/5.py','a/6.py'}
(O/'1.tgz').write_bytes(L.tar_bytes(files))
print(json.dumps(dict(delivery_sha256=sha(O/'1.tgz'),payload_sha256=sha(P/'0.tgz'),package_sha256=sha(P/'PACKAGE.json'))))
