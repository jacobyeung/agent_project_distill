"""Manifest intake to native SQLite stores; frame-host boundary is an explicit receipt."""
import argparse
import json
import os
from .job_env import key as env_key
from pathlib import Path
import sqlite3
from .p3_provenance import digest, file_pin, write, load, pinned
from .r2_contract import CONTRACT, expand_frames
from .r2_dense import build_training
from .r2_frames import MEMO, NeedsFrameHost, verify_frame
from .r2_intake import intake

MAX_ROWS_PER_FAMILY = 2000


def materialize(manifests, output, *, limit=2000, full=False, select_types=None, metadata_only=False, dense=True, mix_binding=None,
                limits=None, progress=None):
    if mix_binding is not None:
        from .r2_mix import preflight
        preflight(**mix_binding)
    if full and (os.environ.get('STUDENT_R2_LOCAL_NODE') == '1' or (Path.cwd()/'.r2_local_node').exists()
                 or os.uname().nodename.startswith('trinity')):
        raise ValueError('Full store forbidden on a local node; use slices of at most 2000 rows per family')
    if full:
        if os.environ.get(env_key('STUDENT_R2_FRAME_HOST')) != '1':
            raise ValueError('Full materialization requires an explicit frame-host admission')
        limit = None
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows, reports, identities, family_counts, row_reports = [], [], {}, {}, {}
    extent_rows, extent_sources = {}, []
    for manifest in manifests:
        extent_pin = load(manifest).get('extent_receipt')
        if extent_pin:
            extent = load(pinned(extent_pin))
            for qid, entry in extent['rows'].items():
                if qid in extent_rows and extent_rows[qid] != entry:
                    raise ValueError('EXTENT_RECEIPTS_CONFLICT')
                extent_rows[qid] = entry
            extent_sources.append(extent_pin)
        accepted, report = intake(manifest, limit=limit, select_types=(select_types or {}).get(str(manifest)))
        reports.append(report)
        family = report['family']
        family_counts[family] = family_counts.get(family, 0) + sum(c['seen'] for c in report['counts'].values())
        if not full and family_counts[family] > MAX_ROWS_PER_FAMILY:
            raise ValueError('Combined manifests exceed the per-family slice limit')
        for item in accepted:
            row = item['row']
            if row['qid'] in identities:
                reason = 'Duplicate QID across families: '+identities[row['qid']]+' / '+item['family']+'; QID='+row['qid']
                report['refusals'].append(dict(qid=row['qid'], type=row.get('question_type'), reason=reason))
                count = report['counts'][row.get('question_type', item['stream'])]
                count['admitted'] -= 1
                count['refused'] += 1
                count['reasons'][reason] += 1
                continue
            identities[row['qid']] = item['family']
            row_reports[row['qid']] = report
            rows.append(item)
    before, missing, built, clips, dense_clips = MEMO.stats(), [], [], {}, {}
    for item in rows:
        try:
            row = item['row']
            if dense:
                row, key = build_training(row)
                clips.setdefault(key, []).append(row['qid'])
                dense_clips.setdefault(key, row['student_input']['geometry_dense'])
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
            if progress is not None:
                progress()
        except NeedsFrameHost as error:
            missing.append(dict(qid=item['row']['qid'], family=item['family'], reason=str(error)))
        except (KeyError, TypeError, ValueError) as error:
            family_report = row_reports[item['row']['qid']]
            kind = item['row'].get('question_type', item['stream'])
            reason = 'materialization: '+str(error)
            family_report['refusals'].append(dict(qid=item['row']['qid'], type=kind, reason=reason))
            count = family_report['counts'][kind]
            count['admitted'] -= 1
            count['refused'] += 1
            count['reasons'][reason] += 1
    pairs = {}
    for item in built:
        assignment = item.get('mix_cell') or {}
        if assignment.get('type') == 'facing_pairs':
            if not assignment.get('pair'):
                raise ValueError('Missing final facing pair identity')
            pairs.setdefault(assignment['pair'], []).append(item)
    if any(len(pair) > 2 for pair in pairs.values()):
        raise ValueError('Facing pair has too many rows')
    orphaned = {pair[0]['row']['qid'] for pair in pairs.values() if len(pair) == 1}
    for item in built:
        if item['row']['qid'] in orphaned:
            family_report = row_reports[item['row']['qid']]
            kind = item['row'].get('question_type', item['stream'])
            reason = 'materialization: facing twin refused'
            family_report['refusals'].append(dict(qid=item['row']['qid'], type=kind, reason=reason))
            count = family_report['counts'][kind]
            count['admitted'] -= 1
            count['refused'] += 1
            count['reasons'][reason] += 1
    built = [item for item in built if item['row']['qid'] not in orphaned]
    retained = {item['row']['qid'] for item in built}
    if not missing:
        clips = {key:[qid for qid in qids if qid in retained] for key,qids in clips.items()}
        clips = {key:qids for key,qids in clips.items() if qids}
        dense_clips = {key:value for key,value in dense_clips.items() if key in clips}
    report = dict(schema='r2-materialization-v1', intake=reports, missing=missing,
                  status='needs the frame host' if missing else 'ready' if built else 'empty',
                  hashes_before=before, hashes_after=MEMO.stats(), content_clips=clips,
                  frame_roots=sorted({str(Path(p['path']).parent) for item in rows for p in expand_frames(item['row']['student_input'])['frames']}))
    if missing:
        write(output/'materialization.json', report)
        return report
    if full and mix_binding is None:
        write(output/'materialization.json', report)
        raise ValueError('Full materialization requires the bound sampling table')
    sampling = None
    if mix_binding is not None:
        from .r2_mix import reindex
        try:
            sampling = reindex(built, mix_binding, output/'s')
        except ValueError as error:
            report.update(status='refused', sampling_refusal=str(error))
            write(output/'materialization.json', report)
            raise
    streams, members = {}, {}
    for stream in sorted({item['stream'] for item in built}):
        path = output/(stream+'.sqlite')
        with sqlite3.connect(path) as connection:
            if limits is not None:
                pages = limits[stream]//connection.execute('PRAGMA page_size').fetchone()[0]
                if pages < 2:
                    raise ValueError('Store over its per-file limit: '+stream)
                connection.execute('PRAGMA max_page_count='+str(pages))
            connection.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
            selected = [item for item in built if item['stream'] == stream]
            for index, item in enumerate(selected):
                connection.execute('INSERT INTO rows VALUES (?,?,?)', (index, json.dumps(item['row']), json.dumps(item['target'])))
                members[item['row']['qid']] = digest(dict(row=item['row'], target=item['target'], stream=stream))
        streams[stream] = dict(database=file_pin(path), count=len(selected))
    membership = output/'membership.json'
    membership_value = dict(contract=CONTRACT, rows=members, intake=reports, content_clips=clips)
    if limits is not None and len(json.dumps(membership_value).encode()) > limits['membership']:
        raise ValueError('Store over its per-file limit: membership')
    write(membership, membership_value)
    receipt = dict(schema='r2-native-stores-v1', streams=streams, r2_membership=file_pin(membership),
                   frame_layout='duplicate', training_mode='final')
    if extent_sources:
        write(output/'extents.json', dict(schema='full-extent-receipt-v1', sources=extent_sources, rows=extent_rows))
        receipt['extent_receipt'] = file_pin(output/'extents.json')
    if sampling is not None:
        receipt['r2_sampling'] = sampling
    if dense:
        value = dict(schema='r2-dense-manifest-v1', reconstruct_then_subsample=True, clips=dense_clips)
        if limits is not None and len(json.dumps(value).encode()) > limits['dense']:
            raise ValueError('Store over its per-file limit: dense')
        write(output/'d.json', value)
        receipt['dense_manifest'] = file_pin(output/'d.json')
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
