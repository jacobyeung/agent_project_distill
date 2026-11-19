"""Import-only probe executed by the pinned reader wrapper with -B -I."""
import importlib,json,sys,hashlib
from pathlib import Path
required=json.loads((Path(__file__).resolve().parent/'inputs/ENV_REQUIRED.json').read_text())
modules={}
for name in required['modules']:
 m=importlib.import_module(name);p=Path(m.__file__).resolve()
 modules[name]={'version':m.__version__,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps({'python':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'modules':modules}))
