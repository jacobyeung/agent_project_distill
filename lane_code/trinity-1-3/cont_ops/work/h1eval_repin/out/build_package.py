"""Run the production builder against the authoritative local payload inventory."""
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT/'src'))
from orchard_h10 import build as builder

builder.K=OUT
builder.T=OUT/'src/orchard_h10/vendor'
names=set(json.loads((OUT/'production/9.json').read_text())['payload_pins'])-{'8.py'}
names.add('orchard_h10/export_pins.py')
builder.sources=lambda:{name:OUT/'src'/name for name in sorted(names)}
# The production builder reads operator.py separately for its 8.py entry point.
original_read=builder.K
# Supply that single source under K without copying or refreshing any dependencies.
(OUT/'orchard_h10').mkdir(exist_ok=True)
(OUT/'orchard_h10/operator.py').write_bytes((OUT/'src/orchard_h10/operator.py').read_bytes())
result=builder.build(OUT/'package',token=(OUT/'TOKEN').read_text().strip(),
                     refresh=(OUT/'package/CONFIG.json').exists())
(OUT/'0.tgz').write_bytes((OUT/'package/0.tgz').read_bytes())
(OUT/'BUILD.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
