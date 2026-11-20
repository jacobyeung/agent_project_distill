"""Authenticate local reader definitions used by CPU analysis."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PINS=json.loads((Path(__file__).parent/'READER_PINS.json').read_text())


def checked(path):
    path=Path(path);relative=str(path.relative_to(ROOT));raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PINS[relative]:raise ValueError('reader source pin differs: '+relative)
    return raw.decode()
