"""Build and validate the 580-item development-only distance manifest (Python 3.6)."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

SETS = ('R0-dev-reworded', 'R0-dev-twin')
CAPTURE = ('dataset', 'scene', 'native', 'room', 'room_key', 'fps', 'frame_indices',
           'source_frame_indices', 'frame_paths', 'num_frames', 'total_num_frames')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate(m, rooms, dev):
    assert m['schema'] == 'h1-items-v1' and m['status'] == 'ready' and m['name'] == 'dist580'
    assert m['development_only'] is True and m['fitting_permitted'] is False
    rows = m['items']; byid = {r['id']: r for r in rows}
    assert len(rows) == len(byid) == m['count'] == 580
    assert rows == sorted(rows, key=lambda r: r['id']) and digest(rows) == m['item_set_sha256']
    assert m['per_type'] == {'object_abs_distance': 580}
    assert m['r0_check'] == dict(pin=rooms['r0_check']['pin'], checked=580, found=580)
    assert m['frames_manifest_sha256'] == rooms['frames_manifest_sha256']
    r0ids = set(rooms['sets']['R0-dev'])
    captures = {r['room_key']: r for r in rooms['items'] if r['id'] in r0ids}
    assert len(captures) == 98 and set(captures) <= dev
    reworded = [r for r in rows if r['id'].endswith('_ho')]
    twins = [r for r in rows if not r['id'].endswith('_ho')]
    assert len(reworded) == len(twins) == 290
    assert Counter(r['unit'] for r in reworded) == dict(m=73, ft=73, **{'in':72, 'cm':72})
    assert Counter(r['unit'] for r in twins) == {'m': 290}
    assert m['sets'] == {SETS[0]: sorted(r['id'] for r in reworded),
                         SETS[1]: sorted(r['id'] for r in twins), 'R0-dev': sorted(byid)}
    assert len({r['room_key'] for r in rows}) == 98
    for r in rows:
        assert r['room_key'] in dev and r['r0_split'] == 'R0-dev'
        assert r['development_only'] is True and r['question_type'] == 'object_abs_distance'
        assert r['scorer'] == 'official_vsi_mra' and r['answer_type'] == 'numeric'
        assert r['qid'] == r['id'] and r['options'] == []
        assert all(r[k] == captures[r['room_key']][k] for k in CAPTURE)
        assert len(r['frame_paths']) == len(r['frame_indices']) == 32
        twin = byid[r['twin_id']]
        assert twin['twin_id'] == r['id'] and twin['room_key'] == r['room_key']
        assert twin['gt']['distance_m'] == r['gt']['distance_m']
        assert twin['gt']['pair'] == r['gt']['pair']
        if r['id'].endswith('_ho'):
            assert r['id'] == twin['id'] + '_ho' and twin in twins
    assert len({r['twin_id'] for r in reworded}) == 290
    return m


def make(source, rooms, dev):
    rows = copy.deepcopy(source if isinstance(source, list) else source['items'])
    r0ids = set(rooms['sets']['R0-dev'])
    captures = {r['room_key']: r for r in rooms['items'] if r['id'] in r0ids}
    for r in rows:
        c = captures[r['room_key']]
        assert r['frame_indices'] == c['frame_indices'], r['id']
        for k in CAPTURE:
            if k in r: assert r[k] == c[k], (r['id'], k)
            r[k] = copy.deepcopy(c[k])
    rows.sort(key=lambda r: r['id'])
    m = dict(schema='h1-items-v1', name='dist580', status='ready', count=len(rows),
             development_only=True, fitting_permitted=False, items=rows,
             frames_manifest_sha256=rooms['frames_manifest_sha256'], item_set_sha256=digest(rows),
             per_type=dict(Counter(r['question_type'] for r in rows)),
             r0_check=dict(pin=rooms['r0_check']['pin'], checked=len(rows), found=len(rows)),
             sets={SETS[0]: [r['id'] for r in rows if r['id'].endswith('_ho')],
                   SETS[1]: [r['id'] for r in rows if not r['id'].endswith('_ho')],
                   'R0-dev': [r['id'] for r in rows]})
    return validate(m, rooms, dev)


def validate_payload(m):
    from h1eval.items import K
    rooms = json.loads((K/'items/room134.json').read_text())
    dev = set((K/'auth/R0_DEV_ROOMS.txt').read_text().splitlines())
    validate(m, rooms, dev)


def bind(items, settings):
    """Bind new IDs to the authenticated R0 capture, preserving each item answer."""
    from h1eval.items import K
    from e2e_reader import parity
    extra = json.loads((K/'inputs/room_captures.json').read_text())['captures']
    settings.update(frames_json={'captures': extra}, dense_manifest={'captures': extra}, require_dense64=False)
    mapped = {}; mapping = []
    for item in items:
        task = dict(item)
        c = extra[task['native']]
        assert task['frame_paths'] == [f['path'] for f in c['frames']]
        b = parity.bind_item(task, settings, verify=False)
        mapped[item['id']] = task
        mapping.append(dict(id=item['id'], key=parity.key(task), native=task['native'],
                            task_sha256=digest(task), layout_count=32,
                            anchor_indices=b['frames']['anchor_indices'], dense_count=32,
                            frame_binding_sha256=digest(c)))
    mapping.sort(key=lambda r: r['id'])
    assert len({r['key'] for r in mapping}) == len(items)
    return mapped, dict(schema='h10-parity-mapping-v1', items=mapping, sha256=digest(mapping))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('items'); p.add_argument('room134'); p.add_argument('out')
    p.add_argument('--rooms', help='R0_DEV_ROOMS.txt; default: room134 parent/../auth')
    a = p.parse_args(); roompath = Path(a.room134)
    devpath = Path(a.rooms) if a.rooms else roompath.parent.parent/'auth/R0_DEV_ROOMS.txt'
    m = make(json.loads(Path(a.items).read_text()), json.loads(roompath.read_text()),
             set(devpath.read_text().splitlines()))
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, sort_keys=True, indent=1, allow_nan=False)+'\n')
    print(json.dumps(dict(count=m['count'], item_set_sha256=m['item_set_sha256'], out=str(out))))


if __name__ == '__main__': main()
