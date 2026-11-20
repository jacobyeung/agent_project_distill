"""Point-input admission; the sealed payload lacks the geometric prompt API."""
import json
import math
from pathlib import Path

MISSING = ('_get_dummy_prompt return type and its positive-point construction API '
           '(sam3/model/sam3_image.py and geometric prompt class source are absent from payload)')


def validate(value):
    if not isinstance(value, dict): raise ValueError('point map must be an object')
    for item, names in value.items():
        if not isinstance(item, str) or not isinstance(names, dict): raise ValueError('item map')
        for name, frames in names.items():
            if not isinstance(name, str) or not name or not isinstance(frames, dict): raise ValueError('object map')
            for index, point in frames.items():
                if not isinstance(index, str) or not index.isdigit(): raise ValueError('source index')
                if point is None: continue
                if (not isinstance(point, list) or len(point) != 2 or
                    any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in point)):
                    raise ValueError('point outside normalized anchor frame')
    return value


def admit(path):
    validate(json.loads(Path(path).read_text()))
    raise RuntimeError('Point mode unavailable: '+MISSING)
