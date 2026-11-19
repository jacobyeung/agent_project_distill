"""Resolve every relative config input against the parent's authenticated inventory."""
import base64
import hashlib
from pathlib import Path
from student_pilot.p3_provenance import load, sha256
from .staging import AS, AL, relative_paths, validate_plan


def make(cfg, paths, base):
    parent = load(Path(base)/'k/0.json')
    verified_sources = load(Path(__file__).with_name('staging_sources.json'))
    metadata = {sha256(p):p for p in (Path(base)/'k').glob('*') if p.is_file() and p.stat().st_size < 20_000_000}
    merged = Path(__file__).parents[1]/'student_pilot/r2_dev_merged.json'
    metadata[sha256(merged)] = merged
    pins = {}
    def visit(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                pins[value['path']] = value['sha256']
            for key, item in value.items():
                if len(key) == 64 and all(c in '0123456789abcdef' for c in key) and isinstance(item,str):
                    pins[item] = key
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(cfg)
    reverse = {v:k for k,v in paths.items()}
    extras = {e['dest']:e for e in parent['extra']}
    archives = {}
    for a in parent['tars']:
        for member, h in a['files'].items():
            for prefix in (AS, AL):
                archives[prefix+'/'+member] = dict(archive=dict(parts=a['parts'], sha256=a.get('sha256'),
                    inventory=a['files'], inventory_sha256=hashlib.sha256(json_bytes(a['files'])).hexdigest()), member=member, sha256=h)
    entries = {}
    for name in sorted(relative_paths(cfg)):
        original = reverse.get(name)
        expected = pins.get(name)
        if expected in metadata:
            entries[name] = dict(payload=base64.b64encode(metadata[expected].read_bytes()).decode(), sha256=expected)
        elif expected in verified_sources:
            entries[name] = verified_sources[expected]
        elif original in extras:
            entries[name] = {k:extras[original][k] for k in ('parts', 'sha256')}
        elif original in archives:
            entries[name] = archives[original]
        elif expected and original:
            # The parent's small archive retains absolute paths without a leading slash.
            entries[name] = dict(archive=dict(parts=[parent['small']['file']], sha256=parent['small']['sha256']),
                                 member=original.lstrip('/'), sha256=expected)
        elif expected:
            # New evidence remains an explicit delivery requirement, not a substituted parent export.
            entries[name] = dict(required_parameter='artifact_'+expected, sha256=expected)
        elif original:
            role = 'model' if '/models/' in original else 'art' if '/art/' in original else None
            if role:
                pin = parent[role]
                entries[name] = dict(directory=dict(parts=[pin['file']], sha256=pin['sha256']),
                                     member='', sha256=pin['sha256'])
            else:
                raise ValueError('Unresolved relative directory: '+original)
        else:
            raise ValueError('Unknown relative staging pin: '+name)
    validate_plan(cfg, entries)
    return dict(venv=parent['venv'], bwrap=parent['bwrap'], entries=entries)


def json_bytes(value):
    import json
    return json.dumps(value,sort_keys=True).encode()
