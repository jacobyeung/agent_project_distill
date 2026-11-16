"""Manifest intake to native SQLite stores; frame-host boundary is an explicit receipt."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
from .p3_provenance import digest, file_pin, write
from .r2_contract import CONTRACT, expand_frames
from .r2_dense import build_training
from .r2_frames import MEMO, NeedsFrameHost, verify_frame
from .r2_intake import intake

MAX_ROWS_PER_FAMILY = 2000


def materialize(manifests, output, *, limit=2000, full=False, select_types=None, metadata_only=False, dense=True, mix_binding=None):
    if mix_binding is not None:
        from .r2_mix import preflight
        preflight(**mix_binding)
    if full and (os.environ.get('STUDENT_R2_LOCAL_NODE') == '1' or (Path.cwd()/'.r2_local_node').exists()
                 or os.uname().nodename.startswith('trinity')):
        raise ValueError('Full store forbidden on a local node; use slices of at most 2000 rows per family')
    if full:
        if os.environ.get('STUDENT_R2_FRAME_HOST') != '1':
            raise ValueError('Full materialization requires an explicit frame-host admission')
        limit = None
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows, reports, identities, family_counts = [], [], {}, {}
    for manifest in manifests:
        accepted, report = intake(manifest, limit=limit, select_types=(select_types or {}).get(str(manifest)))
        reports.append(report)
        family = report['family']
        family_counts[family] = family_counts.get(family, 0) + sum(c['seen'] for c in report['counts'].values())
        if not full and family_counts[family] > MAX_ROWS_PER_FAMILY:
            raise ValueError('Combined manifests exceed the per-family slice limit')
        for item in accepted:
            row = item['row']
            if row['qid'] in identities:
                raise ValueError('Unfiltered route-planning ID collision: select sealed routing by type before combining re-rendered rows; QID=' + row['qid'])
            identities[row['qid']] = item['family']
            rows.append(item)
    before, missing, built, clips = MEMO.stats(), [], [], {}
    for item in rows:
        try:
            row = item['row']
            if dense:
                row, key = build_training(row)
                clips.setdefault(key, []).append(row['qid'])
            else:
                row = {**row, 'student_input': expand_frames(row['student_input'])}
            if metadata_only:
                raise NeedsFrameHost('needs the frame host: metadata-only proof; RGB was not read')
            for pin in row['student_input'].get('geometry_dense', row['student_input'])['frames']:
                verify_frame(pin)
            if item['stream'] == 'routing':
                from .carrier_c1_routing import c1_row
                inputs = row['student_input']
                rgb = dict(inputs, frames=[dict(pin, source_index=i) for i, pin in zip(inputs['frame_indices'], inputs['frames'], strict=True)])
                row = c1_row(row, rgb)
            built.append({**item, 'row': row})
        except NeedsFrameHost as error:
            missing.append(dict(qid=item['row']['qid'], family=item['family'], reason=str(error)))
    report = dict(schema='r2-materialization-v1', intake=reports, missing=missing,
                  status='needs the frame host' if missing else 'ready',
                  hashes_before=before, hashes_after=MEMO.stats(), content_clips=clips,
                  frame_roots=sorted({str(Path(p['path']).parent) for item in rows for p in expand_frames(item['row']['student_input'])['frames']}))
    if missing:
        write(output/'materialization.json', report)
        return report
    # Admission failure is never hidden by a partially useful store.
    unexpected = [r for rep in reports for r in rep['refusals'] if r['reason'] != 'type_selection' and not r['reason'].startswith(('excluded:', 'lineage_less_room:'))]
    if unexpected:
        write(output/'materialization.json', report)
        raise ValueError('Intake refused invalid rows; see materialization.json')
    streams, members = {}, {}
    for stream in sorted({item['stream'] for item in built}):
        path = output/(stream+'.sqlite')
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
            selected = [item for item in built if item['stream'] == stream]
            for index, item in enumerate(selected):
                connection.execute('INSERT INTO rows VALUES (?,?,?)', (index, json.dumps(item['row']), json.dumps(item['target'])))
                members[item['row']['qid']] = digest(dict(row=item['row'], target=item['target'], stream=stream))
        streams[stream] = dict(database=file_pin(path), count=len(selected))
    membership = output/'membership.json'
    write(membership, dict(contract=CONTRACT, rows=members, intake=reports, content_clips=clips))
    receipt = dict(schema='r2-native-stores-v1', streams=streams, r2_membership=file_pin(membership),
                   frame_layout='duplicate', training_mode='final')
    write(output/'receipt.json', receipt)
    report['receipt'] = file_pin(output/'receipt.json')
    write(output/'materialization.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', action='append', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=2000)
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--no-dense', action='store_true')
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args(argv)
    print(json.dumps(materialize(args.manifest, args.output, limit=args.limit,
                                metadata_only=args.metadata_only, dense=not args.no_dense, full=args.full), sort_keys=True))


if __name__ == '__main__':
    main()
