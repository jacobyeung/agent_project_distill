import json,sys
from pathlib import Path
p=Path(sys.argv[sys.argv.index("--out")+1])
with p.open("x") as f:json.dump(dict(partition="general",fixture=True),f)
