"""Rewrite a 32-viewpoint C1 row store into nested 64-viewpoint rows (frame host transform).

  nest_store.py plan  --store rows.sqlite --out DECODE_PLAN.json
  nest_store.py apply --store rows.sqlite --pins PINS.json --out nested.sqlite --report REPORT.json

PLAN lists, per video, the bisection ordinals a frame host must decode, and the rows apply would refuse.
PINS maps video key -> {ordinal: {path, sha256}}. apply checks every source row before it writes anything:
a video row needs strictly increasing anchors, a pin for every bisection ordinal, and all 64 of its frames
present on this host under their pinned sha256 (`r2_frames.verify_frame`; STUDENT_FRAME_ROOT_MAP applies).
One refused row refuses the whole store, nothing is published, and the report names every refused row.
A published store holds every source row under its own index with its own target and anchor frames, so the
row count, the sampler's indices and the targets are the source's. Single-image rows keep their exact text.
Needs the trainer tree (tree_f64) on sys.path. Exit status 2 means refused.
"""
import argparse
import contextlib
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

SCHEMA = 'f64-nest-report-v2'
CHANGED = ('frames', 'frame_indices', 'timestamps', 'anchor_slots')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha256(path):
    with open(path, 'rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def video_key(inputs):
    identity = inputs.get('video_identity') or {}
    if identity.get('video_sha256'):
        return identity['video_sha256']
    return json.dumps([inputs.get('fps'), inputs.get('total_num_frames'), [f['sha256'] for f in inputs['frames']][:1]])


def rows(store):
    with contextlib.closing(sqlite3.connect(f'file:{store}?mode=ro', uri=True)) as connection:
        yield from connection.execute('SELECT i, row, target FROM rows ORDER BY i')


def increasing(anchors):
    return (isinstance(anchors, list) and all(type(k) is int and k >= 0 for k in anchors)
            and all(a < b for a, b in zip(anchors, anchors[1:])))


def nest(row, pins, verify):
    """One source row -> its published row; ValueError names why the store cannot be published."""
    from student_pilot.frame_input import NESTED, check_row, nest_row
    inputs = row['student_input']
    frames = list(inputs.get('frames') or ())
    if len(frames) <= 1:
        return row
    anchors = inputs.get('frame_indices')
    if not increasing(anchors):
        raise ValueError('SOURCE_ANCHORS_NOT_INCREASING')
    absent = [slot for slot, frame in enumerate(frames)
              if not isinstance(frame, dict) or not frame.get('path') or not frame.get('sha256')]
    if absent:
        raise ValueError(f'SOURCE_FRAME_MISSING:{absent[:4]}')
    nested = nest_row(row, pins)
    check_row(nested, NESTED)
    si = nested['student_input']
    slots = si['anchor_slots']
    if ([si['frame_indices'][s] for s in slots] != anchors or [si['frames'][s] for s in slots] != frames
            or [si['timestamps'][s] for s in slots] != inputs['timestamps']):
        raise ValueError('NESTED_ANCHORS_DIFFER')
    if ({k: v for k, v in nested.items() if k != 'student_input'} != {k: v for k, v in row.items() if k != 'student_input'}
            or {k: v for k, v in si.items() if k not in CHANGED} != {k: v for k, v in inputs.items() if k not in CHANGED}):
        raise ValueError('NESTED_ROW_CHANGED_BEYOND_FRAMES')
    for ordinal, pin in zip(si['frame_indices'], si['frames']):
        try:
            verify(pin)
        except (OSError, ValueError) as error:
            raise ValueError(f'FRAME_MISSING:{ordinal}:{type(error).__name__}: {str(error)[:120]}') from None
    return nested


def plan(store):
    from student_pilot.carrier_c1_data import nested_indices
    videos, refused = {}, []
    for i, text, _ in rows(store):
        inputs = json.loads(text)['student_input']
        if len(inputs.get('frames') or ()) <= 1:
            continue
        if not increasing(inputs.get('frame_indices')):
            refused.append(dict(i=i, reason='SOURCE_ANCHORS_NOT_INCREASING'))
            continue
        try:
            indices, _ = nested_indices(inputs['frame_indices'], 64)
        except ValueError as error:
            refused.append(dict(i=i, reason=f'FRAME_INPUT_CLIP_TOO_SHORT:{error}'))
            continue
        entry = videos.setdefault(video_key(inputs), dict(fps=inputs['fps'], total_num_frames=inputs.get('total_num_frames'),
                                                          ordinals=set()))
        entry['ordinals'] |= set(indices) - set(inputs['frame_indices'])
    for entry in videos.values():
        entry['ordinals'] = sorted(entry['ordinals'])
    return dict(schema='f64-decode-plan-v2', store=str(store), videos=videos, refused=refused,
                frames_to_decode=sum(len(v['ordinals']) for v in videos.values()))


def apply(store, pins, out, verify=None):
    """Publish `out` only when every source row nests; otherwise return a REFUSED report and write nothing."""
    if verify is None:
        from student_pilot.r2_frames import verify_frame as verify
    out = Path(out)
    partial = out.with_name(out.name + '.partial')
    if out.exists() or partial.exists():
        raise ValueError('output store exists')
    pins = {key: {int(k): v for k, v in value.items()} for key, value in pins.items()}
    counts = dict(source=0, nested=0, single_image=0, refused=0)
    refused, digests = [], []
    for i, text, _ in rows(store):
        counts['source'] += 1
        row = json.loads(text)
        try:
            value = nest(row, pins.get(video_key(row['student_input']), {}), verify)
        except (KeyError, TypeError, ValueError) as error:
            counts['refused'] += 1
            refused.append(dict(i=i, qid=row.get('qid'), reason=f'{type(error).__name__}: {error}'[:300]))
            continue
        counts['single_image' if value is row else 'nested'] += 1
        digests.append(text if value is row else digest(value))
    report = dict(schema=SCHEMA, store=dict(path=str(store), sha256=file_sha256(store)), pins_sha256=digest(
        {k: {str(o): p for o, p in v.items()} for k, v in pins.items()}), counts=counts, refused=refused)
    if refused or not counts['source']:
        return dict(report, status='REFUSED', published=False, out=None,
                    reason='empty source store' if not counts['source'] else f'{len(refused)} of {counts["source"]} rows refused')
    with contextlib.closing(sqlite3.connect(partial)) as connection:
        with connection:
            connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
            for n, (i, text, target) in enumerate(rows(store)):
                row = json.loads(text)
                value = nest(row, pins.get(video_key(row['student_input']), {}), verify)
                encoded = text if value is row else json.dumps(value)
                if (text if value is row else digest(value)) != digests[n]:
                    raise ValueError('nesting differs between the check and the write')
                connection.execute('INSERT INTO rows VALUES (?,?,?)', (i, encoded, target))
    check_published(store, partial, counts['source'])
    os.rename(partial, out)
    return dict(report, status='PUBLISHED', published=True, index_map='identity',
                out=dict(path=str(out), sha256=file_sha256(out), count=counts['source']))


def check_published(store, out, count):
    """Same indices, same targets, same row count; each nested row keeps its source anchors in order."""
    from student_pilot.frame_input import anchors
    published = list(rows(out))
    if len(published) != count:
        raise ValueError('published row count differs from the source')
    for (i, text, target), (j, new, new_target) in zip(rows(store), published):
        if i != j or target != new_target:
            raise ValueError(f'published row {j} differs from source row {i} in index or target')
        source, result = json.loads(text)['student_input'], json.loads(new)['student_input']
        if 'anchor_slots' in result and anchors(result) != source['frame_indices']:
            raise ValueError(f'published row {j} reorders its anchors')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('plan', 'apply'))
    parser.add_argument('--store', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--pins')
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.mode == 'plan':
        value = plan(args.store)
        Path(args.out).write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
        print(json.dumps(dict(frames_to_decode=value['frames_to_decode'], refused=len(value['refused']))))
        sys.exit(2 if value['refused'] else 0)
    if not args.pins or not args.report:
        parser.error('apply needs --pins and --report')
    report = apply(args.store, json.loads(Path(args.pins).read_text()), args.out)
    report['pins_file'] = dict(path=args.pins, sha256=file_sha256(args.pins))
    Path(args.report).write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(status=report['status'], counts=report['counts'])))
    sys.exit(0 if report['published'] else 2)


if __name__ == '__main__':
    main()
