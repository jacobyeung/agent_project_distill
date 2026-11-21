import json
from pathlib import Path
def pinned(pin): return Path(pin['path'])
def load(p): return json.loads(Path(p).read_text())
def file_pin(p): return dict(path=str(p),sha256='x')
