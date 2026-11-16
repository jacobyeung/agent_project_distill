"""One content-bound room draw, using the sealed exclusion alias rule."""
import hashlib
import json
from pathlib import Path
import re
from .r2_exclusions import normalize

SHA256 = '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed'
LOST = 'bf737b729a8f9414f400a639d33e997242f1788353ccab5e0c4e1f0fdb12e09f'


def room(name):
    value = normalize(name)
    return re.sub(r'_\d\d$', '', value) if value.startswith('scannet/scene') else value


def shape(data):
    rooms = data['rooms']
    if (len(set(rooms)) != 80 or len(rooms) != 80 or data['seed'] != 20261115
            or sum(x.startswith('scannet/') for x in rooms) != 40
            or sum(x.startswith('scannetpp/') for x in rooms) != 40):
        raise ValueError('Wrong withheld size or balance')
    return rooms


class Withheld:
    def __init__(self, pin=None):
        path = Path(__file__).with_name('r2_withheld.json') if pin is None else Path(pin['path'])
        raw = path.read_bytes()
        if (pin is not None and pin['sha256'] != SHA256) or hashlib.sha256(raw).hexdigest() != SHA256:
            raise ValueError('Foreign or edited withheld-room list')
        data = json.loads(raw)
        rooms = shape(data)
        self.rooms_sha256 = hashlib.sha256(json.dumps(sorted(rooms),separators=(',',':')).encode()).hexdigest()
        self.aliases = {room(x) for key, aliases in data['aliases'].items() for x in [key, *aliases]}
        self.aliases.update(room(x) for x in rooms)

    def touches(self, row, coverage):
        names = list(coverage.get('names', []))
        names += [row['dataset']+'/'+row['scene']]
        names += [v for v in (row.get('canonical'), row.get('provenance', {}).get('canonical'),
                              row.get('provenance', {}).get('alias')) if v]
        return bool({room(x) for x in names} & self.aliases)
