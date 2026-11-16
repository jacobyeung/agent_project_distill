import gzip
import hashlib
import json
from pathlib import Path

def read_json(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as f:
        return json.load(f)

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')

def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def ordered_id_sha256(ids):
    """UTF-8 episode ids, each terminated by LF, in evaluation order."""
    return hashlib.sha256(''.join(str(i) + '\n' for i in ids).encode()).hexdigest()
