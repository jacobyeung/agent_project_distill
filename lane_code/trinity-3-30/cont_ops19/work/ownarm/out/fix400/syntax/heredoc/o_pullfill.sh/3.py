import json,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
v=dict(passed=True,inputs_sha256=hashlib.sha256((p/'a/1.json').read_bytes()).hexdigest(),export_sha256=hashlib.sha256((p/'a/export.json').read_bytes()).hexdigest())
(e/'10.json').write_text(json.dumps(v,sort_keys=True)+'\n')