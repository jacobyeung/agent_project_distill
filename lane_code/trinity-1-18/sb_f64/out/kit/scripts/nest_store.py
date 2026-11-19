"""Rewrite a 32-viewpoint C1 row store into nested 64-viewpoint rows (frame host transform).

  nest_store.py plan  --store rows.sqlite --out DECODE_PLAN.json
  nest_store.py apply --store rows.sqlite --pins PINS.json --out nested.sqlite --report REPORT.json

PLAN lists, per video, the bisection ordinals a frame host must decode. PINS maps video key ->
{ordinal: {path, sha256}}. apply nests every multi-frame row with student_pilot.frame_input.nest_row,
passes single-image rows through, and defers rows it cannot nest with the reason; the report keeps
every source row in its denominator. Needs the trainer tree (tree_f64) on sys.path.
"""
import argparse
import json
import sqlite3
from pathlib import Path


def video_key(inputs):
    identity = inputs.get('video_identity') or {}
    if identity.get('video_sha256'):
        return identity['video_sha256']
    return json.dumps([inputs.get('fps'), inputs.get('total_num_frames'), [f['sha256'] for f in inputs['frames']][:1]])


def rows(store):
    with sqlite3.connect(f'file:{store}?mode=ro', uri=True) as connection:
        yield from connection.execute('SELECT i, row, target FROM rows ORDER BY i')


def plan(store):
    from student_pilot.carrier_c1_data import nested_indices
    videos, short = {}, []
    for i, text, _ in rows(store):
        inputs = json.loads(text)['student_input']
        if len(inputs.get('frames') or ()) <= 1:
            continue
        try:
            indices, _ = nested_indices(inputs['frame_indices'], 64)
        except ValueError as error:
            short.append(dict(i=i, reason=str(error)))
            continue
        entry = videos.setdefault(video_key(inputs), dict(fps=inputs['fps'], total_num_frames=inputs.get('total_num_frames'),
                                                          frames=[], ordinals=set()))
        entry['ordinals'] |= set(indices) - set(inputs['frame_indices'])
    for entry in videos.values():
        entry['ordinals'] = sorted(entry['ordinals'])
    return dict(schema='f64-decode-plan-v1', store=str(store), videos=videos, short_clips=short,
                frames_to_decode=sum(len(v['ordinals']) for v in videos.values()))


def apply(store, pins, out):
    from student_pilot.frame_input import NESTED, check_row, nest_row
    pins = {key: {int(k): v for k, v in value.items()} for key, value in pins.items()}
    counts = dict(source=0, nested=0, single_image=0, deferred=0)
    deferred, mapping = [], []
    if Path(out).exists():
        raise ValueError('output store exists')
    with sqlite3.connect(out) as connection:
        connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
        for i, text, target in rows(store):
            counts['source'] += 1
            row = json.loads(text)
            inputs = row['student_input']
            try:
                if len(inputs.get('frames') or ()) <= 1:
                    counts['single_image'] += 1
                else:
                    row = nest_row(row, pins.get(video_key(inputs), {}))
                    check_row(row, NESTED)
                    counts['nested'] += 1
            except ValueError as error:
                counts['deferred'] += 1
                deferred.append(dict(i=i, qid=row.get('qid'), reason=str(error)))
                continue
            connection.execute('INSERT INTO rows VALUES (?,?,?)', (len(mapping), json.dumps(row), target))
            mapping.append(i)
    return dict(schema='f64-nest-report-v1', store=str(store), out=str(out), counts=counts,
                deferred=deferred, source_index_of_row=mapping)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('plan', 'apply'))
    parser.add_argument('--store', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--pins')
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.mode == 'plan':
        Path(args.out).write_text(json.dumps(plan(args.store), indent=1, sort_keys=True) + '\n')
        return
    report = apply(args.store, json.loads(Path(args.pins).read_text()), args.out)
    Path(args.report).write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
