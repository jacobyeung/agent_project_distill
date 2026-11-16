"""Fail-closed room gate. Default CLI checks training; tuning needs --purpose tuning."""
import argparse
import functools
import hashlib
import json
import re
from pathlib import Path

AUTHORITY = Path(__file__).with_name('EVAL_ROOMS.json')
ALIASES = {'d1': 'scannet', 'scannet': 'scannet', 'd2': 'scannetpp',
           'scannetpp': 'scannetpp', 'scannetppv2': 'scannetpp', 'scannet++': 'scannetpp',
           'd3': 'arkitscenes', 'arkit': 'arkitscenes', 'arkitscenes': 'arkitscenes'}


class RoomViolation(ValueError):
    pass


def dataset_name(dataset):
    try:
        return ALIASES[str(dataset).lower()]
    except KeyError:
        raise RoomViolation(f'Unknown dataset: {dataset}') from None


def canonical(dataset, scan):
    dataset = dataset_name(dataset)
    scan = str(scan)
    if '/' in scan or '\\' in scan or '..' in scan:
        raise RoomViolation(f'Invalid scan component: {scan}')
    pattern = {'scannet': r'scene\d{4}_\d{2}', 'scannetpp': r'[0-9a-f]{10}',
               'arkitscenes': r'\d+'}[dataset]
    if not re.fullmatch(pattern, scan):
        raise RoomViolation(f'Unresolved native scan: {dataset}/{scan}')
    return f'{dataset}/{scan}'


@functools.lru_cache(maxsize=1)
def authority():
    raw = AUTHORITY.read_bytes()
    pin = AUTHORITY.with_suffix('.sha256').read_text().split()[0]
    if hashlib.sha256(raw).hexdigest() != pin:
        raise RoomViolation('EVAL_ROOMS sha256 mismatch')
    return json.loads(raw)


@functools.lru_cache(maxsize=1)
def authority_sha256():
    authority()
    return hashlib.sha256(AUTHORITY.read_bytes()).hexdigest()


def room(dataset, scan):
    key = canonical(dataset, scan)
    dataset, scan = key.split('/')
    if dataset == 'scannet':
        return f'{dataset}/{scan[:-3]}'
    if dataset == 'scannetpp':
        return key
    try:
        return authority()['arkit_rooms'][scan]
    except KeyError:
        raise RoomViolation(f'ARKit scene absent from venue authority: {scan}') from None


def is_evaluation_room(dataset, scan):
    return room(dataset, scan) in set(authority()['evaluation_rooms'])


def scene_of(row):
    if 'dataset' in row and 'scan' in row:
        scene = canonical(row['dataset'], row['scan'])
        if 'scene' in row and canonical(*row['scene'].split('/')) != scene:
            raise RoomViolation('Conflicting scene and dataset/scan')
        return scene
    if 'scene' in row:
        return canonical(*row['scene'].split('/'))
    raise RoomViolation('Row lacks native dataset/scan or scene')


def guard_path(path, purpose=None):
    """Reject clean scan names even when buried in a path or mask reference."""
    text = str(path)
    scans = {s.split('/')[1] for s in authority()['clean_scenes']}
    if any(s in text.lower() for s in scans):
        raise RoomViolation(f'Clean-33 path forbidden: {path}')
    if purpose == 'training':
        for scan in re.findall(r'scene\d{4}_\d{2}', text):
            if is_evaluation_room('scannet', scan):
                raise RoomViolation(f'Evaluation room in training path: {path}')
        alternatives='|'.join(re.escape(k) for k in sorted(ALIASES,key=len,reverse=True))
        for dataset, scan in re.findall('('+alternatives+r')(?:__|/)([A-Za-z0-9_]+)', text.lower()):
            d = dataset_name(dataset)
            aliases = authority().get('alias_rooms', {})
            key = dataset+'/'+scan
            if key in aliases:
                r = aliases[key]
            elif d == 'scannet' and re.fullmatch(r'scene\d{4}', scan):
                r = d+'/'+scan
            elif d == 'arkitscenes' and re.fullmatch(r'venue\d+', scan):
                r = d+'/'+scan
            else:
                r = room(dataset, scan)
            if r in authority()['evaluation_rooms']:
                raise RoomViolation(f'Evaluation room in training reference: {path}')


def check_row(row, purpose='training'):
    scene = scene_of(row)
    r = room(*scene.split('/'))
    if row.get('room', r) != r:
        raise RoomViolation(f'False room field: {row.get("room")} != {r}')
    a = authority()
    if 'authority_sha256' in row and row['authority_sha256'] != authority_sha256():
        raise RoomViolation('Row authority_sha256 differs from current room gate')
    if scene in a['clean_scenes']:
        raise RoomViolation(f'Clean-33 scan forbidden: {scene}')
    if purpose == 'training':
        if r in a['evaluation_rooms']:
            raise RoomViolation(f'Evaluation room forbidden for fitting/labelling: {r}')
        if row.get('split', 'train') not in ('train', 'val'):
            raise RoomViolation('Training input has a non-training split')
    elif purpose == 'tuning':
        if scene not in a['tuning_scenes'] or row.get('split', 'tuning') not in ('tune', 'tuning'):
            raise RoomViolation(f'Only the 31 tuning scans may be evaluated: {scene}')
    else:
        raise RoomViolation(f'Unknown purpose: {purpose}')
    def visit(value):
        if isinstance(value, dict):
            for v in value.values():
                visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)
        elif isinstance(value, str):
            guard_path(value, purpose)
    visit(row)
    return r


def read_manifest(path, purpose='training'):
    """Validate every row before returning any rows to a fitting caller."""
    guard_path(path, purpose)
    rows = []
    seen_rooms = {}
    with Path(path).open() as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                r = check_row(row, purpose)
                if purpose == 'training':
                    split = row.get('split', 'train')
                    if r in seen_rooms and seen_rooms[r] != split:
                        raise RoomViolation(f'Room in train and val: {r}')
                    seen_rooms[r] = split
            except RoomViolation as e:
                raise RoomViolation(f'{path}:{line_number}: {e}') from e
            rows.append(row)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['check'])
    p.add_argument('manifest')
    p.add_argument('--purpose', choices=['training', 'tuning'], default='training')
    a = p.parse_args()
    try:
        rows = read_manifest(a.manifest, a.purpose)
    except (ValueError, OSError, KeyError) as e:
        print(str(e))
        return 3
    print(json.dumps(dict(status='PASS', rows=len(rows), purpose=a.purpose,
                          authority_sha256=hashlib.sha256(AUTHORITY.read_bytes()).hexdigest())))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
