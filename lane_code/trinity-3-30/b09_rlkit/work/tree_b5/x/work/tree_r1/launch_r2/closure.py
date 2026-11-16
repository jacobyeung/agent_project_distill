"""Transport small bound metadata and all of its pinned dependencies together."""
import hashlib
import json
from student_pilot.p3_provenance import pinned


def transport(bindings, put_bytes):
    """Rebind nested pins by content; preserve each original digest in the map."""
    moved, active = {}, set()

    def visit(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256'}:
                return pack(value)
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, str) and value in moved:
            return moved[value]['sha256']
        return value

    def pack(pin):
        identity = pin['sha256']
        if identity in moved:
            return moved[identity]
        if identity in active:
            raise ValueError('Cyclic metadata closure')
        path = pinned(pin)
        if path.stat().st_size > 16000000 or path.suffix not in ('.json', '.jsonl', '.tsv', '.md', '.txt'):
            raise ValueError('Only small evidence metadata belongs in the closure')
        active.add(identity)
        raw = path.read_bytes()
        suffix = '.dat'
        if path.suffix == '.json':
            value = json.loads(raw)
            translated = visit(value)
            raw = (json.dumps(translated, sort_keys=True, separators=(',', ':'))+'\n').encode()
            suffix = '.json'
        result = put_bytes(raw, suffix)
        active.discard(identity)
        moved[identity] = result
        return result

    # Hash references inside count and index records depend on this order.
    result = {name: pack(bindings[name]) for name in ('mix', 'registry', 'counts', 'indices', 'source_presence')
              if name in bindings}
    if set(result) != set(bindings):
        raise ValueError('Unknown closure binding')
    return result, moved
