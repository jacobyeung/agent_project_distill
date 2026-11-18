"""Pinned reserve-room exclusion using the trainer's scene and selection machinery."""
import copy
import re
from pathlib import Path
from .s1_exclusions import Exclusions, selection
from .carrier_c1_routing import excluded
from .p3_provenance import pinned, digest, file_pin, load, write

R0_SHA256 = 'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'


def room_keys(row):
    rule = Exclusions(None)
    rule.corpora.update(('3rscan', 'multiscan'))
    rule.aliases.update(scannetv2='d1', scannetppv2='d2')
    # Native task files use native/scene_name; trainer rows use scene/canonical.
    row = copy.deepcopy(row)
    for field in ('native', 'room_key'):
        if isinstance(row.get(field), str):
            row.setdefault('canonical', row[field])
    if not row.get('scene'):
        row['scene'] = row.get('scene_name', row.get('scene_id'))
    keys = rule.identifiers(row)
    result = set()
    for key in keys:
        dataset, name = key.split('/', 1)
        dataset = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}.get(dataset, dataset)
        if dataset == 'scannet':
            name = re.sub(r'^(scene\d+)_\d+$', r'\1', name)
        result.add(dataset+'/'+name)
    # ARKit native capture IDs and physical venue IDs are different granularities.
    venues = {k for k in result if re.fullmatch(r'arkitscenes/venue\d+', k)}
    if len(venues)==1 and all(k.startswith('arkitscenes/') for k in result):
        return venues
    return result


def room_key(row):
    keys = room_keys(row)
    if len(keys) != 1:
        raise ValueError('Ambiguous room identifiers: '+str(sorted(keys)))
    return next(iter(keys))


class Reserve(Exclusions):
    def __init__(self, pin):
        super().__init__(None)
        if pin.get('sha256') != R0_SHA256:
            raise ValueError('R0 pin differs from the registered R0_SHA256')
        resolved = dict(pin)
        if not Path(pin['path']).is_absolute():
            root = Path(__file__).resolve().parents[1]
            candidate = (root/pin['path']).resolve()
            if not candidate.is_relative_to(root):raise ValueError('R0 pin escapes kit root')
            resolved['path'] = str(candidate)
        path = pinned(resolved)
        names = [s.strip() for s in path.read_text().splitlines() if s.strip() and not s.startswith('#')]
        if len(names) != len(set(names)) or any(not re.fullmatch(r'(scannet/scene\d+|scannetpp/[A-Za-z0-9]+)', s) for s in names):
            raise ValueError('Invalid R0 room list')
        self.rooms = set(names)
        self.pin = pin

    def identifiers(self, row):
        return room_keys(row)

    def excluded(self, row):
        return excluded(self.rooms, *self.identifiers(row))

    def counts(self, source):
        return self.sources.setdefault(source, dict(seen=0, removed=0, retained=0))

    def expect(self, source, rows, population=None):
        # selection() supplies a census iterator; keep() counts its second pass.
        pass

    def keep(self, row, source):
        reject = self.excluded(row)
        c = self.counts(source)
        c['seen'] += 1
        c['removed'] += int(reject)
        c['retained'] += int(not reject)
        return not reject


def apply(streams, pin, output):
    rule = Reserve(pin)
    result = {}
    for name, value in streams.items():
        key, selected, changes = selection(name, value, rule)
        path = Path(output)/('h1_r0_'+name+'_'+digest(selected)+'.json')
        if path.exists():
            if load(path) != selected:
                raise ValueError('R0 selection file differs')
        else:
            write(path, selected)
        result[name] = {**copy.deepcopy(value), **changes, key: file_pin(path)}
    counts = {}
    for source, values in rule.sources.items():
        c = counts.setdefault(source.split('/')[0], dict(seen=0, removed=0, retained=0))
        for k, v in values.items():
            c[k] += v
    return result, dict(pin=pin, per_stream=counts, per_source=rule.sources)


def prepare(receipt, cfg, phase='preparation'):
    pin = cfg.get('h1', {}).get('r0_rooms')
    if pin is None:
        return receipt
    streams, report = apply(receipt['streams'], pin, cfg['preparation_output'])
    if any(v['count'] == 0 for v in streams.values()):
        raise ValueError('R0 exclusions leave a required stream empty')
    result = {**receipt, 'streams': streams, 'h1_r0': report}
    if phase == 'preparation':
        result['h1_r0_sources'] = receipt['streams']
    return result


def before_admission(receipt, cfg):
    pin = cfg.get('h1', {}).get('r0_rooms')
    old = receipt.get('h1_r0', {}).get('pin')
    if old is not None and old != pin:
        raise ValueError('R0 preparation pin differs')
    if pin is None:
        return receipt
    Reserve(pin)  # authenticate again before admission and any frame loading
    if old is not None:
        expected, report = apply(receipt['h1_r0_sources'], pin, cfg['preparation_output'])
        if expected != receipt['streams'] or report != receipt['h1_r0']:
            raise ValueError('R0 preparation selections or accounting differ')
        return {**receipt, 'streams': receipt['h1_r0_sources']}
    return receipt
