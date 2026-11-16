"""Usage: contract.py KIT_DIR -> identity and admission contract digest, computed with the kit's own b/ code."""
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root / 'b'))
from g import digest
from i import identity
from d import contract
launch = json.loads((root / 'k/launch.json').read_text()); cfg = json.loads((root / launch['config']['file']).read_text())
print(json.dumps(dict(identity=identity(cfg), contract=digest(contract(launch, cfg)))))
