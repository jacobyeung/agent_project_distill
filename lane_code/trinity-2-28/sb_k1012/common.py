"""Shared helpers: every input read is pinned by sha256, and every output JSON carries those pins."""
import hashlib, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE/'out'
B = Path('/scratch/jjyeung/orch_n30')
ROWSETS = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS')
PINS = {}


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def pin(path):
    p = Path(path).resolve()
    assert str(p).startswith('/scratch/'), p
    PINS[str(p)] = sha(p)
    return PINS[str(p)]


def read(path):
    p = Path(path).resolve()
    assert str(p).startswith('/scratch/'), p
    raw = p.read_bytes()
    PINS[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw


def jread(path):
    return json.loads(read(path))


def clean(v):
    if isinstance(v, np.ndarray):
        return clean(v.tolist())
    if isinstance(v, np.generic):
        return clean(v.item())
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    return v


def write(name, data, extra_pins=None):
    """Write out/<name> with the sha256 of every input this process read, plus this script and common.py."""
    import __main__, sys
    pin(__main__.__file__); pin(__file__)
    for m in list(sys.modules.values()):
        f = getattr(m, '__file__', None) or ''
        if f.endswith('.py') and f.startswith('/scratch/jjyeung/') and '/envs/' not in f:
            pin(f)
    pins = dict(PINS)
    pins.update(extra_pins or {})
    OUT.mkdir(exist_ok=True)
    path = OUT/name
    path.write_text(json.dumps(clean(dict(data, input_sha256=pins)), indent=1, allow_nan=False)+'\n')
    return path


def rowset(name):
    """A rowset from out/ (written by legality.py) or the pinned K1_ROWSETS folder."""
    p = OUT/name if (OUT/name).exists() else ROWSETS/name
    return read(p).decode().splitlines()
