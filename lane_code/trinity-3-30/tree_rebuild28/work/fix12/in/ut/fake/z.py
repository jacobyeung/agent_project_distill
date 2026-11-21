import json
from pathlib import Path
def load(p): return json.loads(Path(p).read_text())
