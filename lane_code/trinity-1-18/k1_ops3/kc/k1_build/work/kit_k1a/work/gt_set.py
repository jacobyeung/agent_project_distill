"""Explicit downstream GT selection; manifest and capture identities stay frozen."""
import hashlib
import json
from pathlib import Path
import gate


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate GT set key: ' + key)
        result[key] = value
    return result


def load(path, sensitivity=False):
    if path is None:
        if sensitivity:
            raise ValueError('--sensitivity requires --gt-set')
        return None
    data = Path(path).read_bytes()
    entries = json.loads(data, object_pairs_hook=_unique)
    if not isinstance(entries, dict) or not entries:
        raise ValueError('GT set must be a nonempty canonical mapping')
    for canonical, pin in entries.items():
        if not isinstance(pin, dict) or type(pin.get('pinned')) is not bool:
            raise ValueError('GT set requires a boolean pinned field: ' + canonical)
        if not isinstance(pin.get('path'), str) or not Path(pin['path']).is_absolute():
            raise ValueError('GT set requires absolute raster paths')
        sha = pin.get('sha256')
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('Invalid GT set sha256')
        if not pin['pinned'] and not sensitivity:
            raise ValueError('Unpinned GT requires --sensitivity')
    return dict(path=str(Path(path).resolve()), sha256=hashlib.sha256(data).hexdigest(),
                entries=entries, sensitivity=bool(sensitivity))


def metadata(selection, canonicals):
    if selection is None:
        return None
    entries = selection['entries']
    if not set(entries) <= set(canonicals):
        raise ValueError('GT set contains captures outside the manifest/inventory')
    return dict(path=selection['path'], sha256=selection['sha256'], n=len(entries),
                pinned=sum(p['pinned'] for p in entries.values()),
                unpinned=sum(not p['pinned'] for p in entries.values()),
                captures=sorted(entries), skipped=sorted(set(canonicals) - set(entries)),
                analysis='SENSITIVITY' if selection['sensitivity'] else 'PRIMARY')


def select(m, selection):
    meta = metadata(selection, [c['canonical'] for c in m['captures']])
    captures = m['captures'] if selection is None else [c for c in m['captures'] if c['canonical'] in selection['entries']]
    if selection is not None:
        for c in captures:
            pin = selection['entries'][c['canonical']]
            if pin['pinned'] and pin['sha256'] != c['gt']['sha256']:
                raise ValueError('Pinned GT differs from manifest pin: ' + c['canonical'])
            if 'manifest_pin' in pin and pin['manifest_pin'] != c['gt']['sha256']:
                raise ValueError('GT manifest_pin differs: ' + c['canonical'])
    return captures, meta


def require(receipt, meta):
    if receipt.get('gt_set') != meta:
        raise ValueError('Downstream GT set receipt differs; use the same --gt-set and --sensitivity')


def write(path, record, meta, *, exclusive=True):
    """Keep JSON parseable while making the analysis visible on its first line."""
    record = dict(record, gt_set=meta)
    body = json.dumps(record, indent=2, allow_nan=False)
    body = '{"analysis": ' + json.dumps(meta['analysis']) + ',\n' + body[2:] + '\n'
    with Path(path).open('x' if exclusive else 'w') as stream:
        stream.write(body)


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=gate.sha(path))


def check_table(receipt, m, selection):
    captures, meta = select(m, selection)
    require(receipt, meta)
    digest = hashlib.sha256(json.dumps(m, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if receipt['manifest_sha256'] != digest or receipt['inventory'] != m['inventory']:
        raise ValueError('Table manifest binding differs')
    return captures, meta
