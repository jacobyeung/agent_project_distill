"""Pinned launch inputs for vehicle N; no inference behavior."""
import re

STREAMS = ('pose', 'vqa', 'routing', 'pointing')

NAMING_REMOVE = 'd1454a4461e96fda9e0db27eb75fe0080a555d77a4d05f8e036d49530626db29'
REMOVAL_ORDER = (
    '62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3',
    '4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c',
    '6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc',
    '8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    '6add0ad53515e14e6adb1e192ed002ec0ddd22b6c6bd112ccb756d1f8be48d8c',
    '43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6',
    '1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2',
    '02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411',
    'caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad',
    NAMING_REMOVE)

def bound(cfg):
    value = cfg.get('r1_training') or {}
    return bool(value) and ('launch22' in value or 'direction_twins' in value or 'camera_wording_exclusion' in value
            or any(p.get('sha256') == NAMING_REMOVE for p in cfg.get('remove_files', [])))

def validate_removals(cfg):
    value = cfg.get('r1_training') or {}
    spec = value.get('launch22')
    files = cfg.get('remove_files', [])
    has_roles = any(isinstance(p, dict) and ('role' in p or 'stream' in p) for p in files)
    if not bound(cfg) and not has_roles:
        return
    if not isinstance(spec, dict):
        raise ValueError('R1_NAMING_REMOVAL_ORDER' if has_roles else 'R1_NAMING_REMOVAL_BINDING_REQUIRED')
    if any(not isinstance(p, dict) for p in files):
        raise ValueError('R1_NAMING_REMOVAL_ORDER')
    actual = [p.get('sha256') for p in files]
    extras = files[11:-1]
    if (len(files) < 12 or tuple(actual[:11]) != REMOVAL_ORDER[:11]
            or actual[-1] != NAMING_REMOVE or actual != spec.get('removal_order')
            or any('role' in p or 'stream' in p for p in files[:11] + files[-1:])
            or any(set(p) != {'path', 'sha256', 'role', 'stream'}
                   or p.get('role') != 'protected_rooms' or p.get('stream') not in STREAMS
                   or not isinstance(p.get('sha256'), str)
                   or not re.fullmatch('[0-9a-f]{64}', p['sha256']) for p in extras)):
        raise ValueError('R1_NAMING_REMOVAL_ORDER')
    # The sealed prefix deliberately contains two identical empty-list pins.
    seen = set(REMOVAL_ORDER)
    for p in extras:
        if p['sha256'] in seen:
            raise ValueError('R1_NAMING_REMOVAL_ORDER')
        seen.add(p['sha256'])
    from .p3_provenance import pinned
    pinned(files[-1])
    for p in extras:
        pinned({k: p[k] for k in ('path', 'sha256')})

def naming_rows(pin):
    from .p3_provenance import load, pinned
    value = load(pinned(pin))
    rows = value.get('rows', [])
    keys = [r.get('qid') for r in rows]
    if len(keys) != 109 or len(set(keys)) != 109 or any(not isinstance(k, str) or not k for k in keys):
        raise ValueError('R1_NAMING_REMOVAL_CONTENT')
    return [dict(row_key=k) for k in keys]
