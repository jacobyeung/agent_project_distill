"""Compare every v7 row with sb_alias2 using independent room and list logic."""
import argparse
from collections import Counter
import csv
import hashlib
import io
from itertools import zip_longest
import json
from pathlib import Path
import re
import shlex
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {}


def pin(path, expected=None):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError('MISSING: '+str(path))
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(4*1024*1024), b''):
            digest.update(chunk)
    INPUTS[str(path)] = {'sha256': digest.hexdigest(), 'bytes': path.stat().st_size}
    if expected is not None:
        assert digest.hexdigest() == expected, ('input hash', str(path))
    return path


def document(path, expected=None):
    return json.loads(pin(path, expected).read_text())


def compare(audit_path):
    pin(__file__)
    report = document(audit_path)
    original = document(ROOT/'inputs/comparison/ROOM_AUDIT_TIERED.raw')
    alias_path = ROOT/'inputs/comparison/TIERED_ALIAS_MAP.raw'
    aliases = document(alias_path)['aliases']
    assert any(p['sha256'] == INPUTS[str(alias_path.resolve())]['sha256']
               for p in report['inputs'].values()), 'Audit must use the sb_alias2 alias map'
    assert report['complete'] and report['status'] == 'PASS'
    assert report['rows'] == report['resolved_rows'] == original['rows'] == 204413
    assert report['unresolved_rows'] == original['unresolved_rows'] == 0
    source = pin(report['store'], original['store']['sha256'])
    assert report['inputs'][str(source)]['sha256'] == original['store']['sha256']
    rows_path = pin(audit_path.parent/report['row_records']['path'], report['row_records']['sha256'])
    lists = ROOT/'inputs/lists'
    manifest = document(lists/'manifest.json')
    visit_pin = manifest['authority']['visits']
    visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(io.StringIO(
        pin(lists/visit_pin['path'], visit_pin['sha256']).read_text()))}

    def norm(value):
        return value.replace('scannetppv2/', 'scannetpp/', 1)

    def physical_room(canonical):
        dataset, capture = canonical.split('/', 1)
        if dataset == 'scannet':
            match = re.fullmatch(r'(scene[0-9]{4})_[0-9]{2}', capture)
            assert match, canonical
            return dataset+'/'+match.group(1)
        if dataset in ('scannetpp', 'scannetppv2'):
            assert re.fullmatch(r'[0-9a-f]{10}', capture), canonical
            return 'scannetpp/'+capture
        assert dataset == 'arkitscenes' and capture in visits, canonical
        visit = visits[capture]
        return 'arkitscenes/venue'+visit if visit and visit != 'NA' else 'arkitscenes/capture'+capture

    names = ('R0', 'withheld-80', 'BENCH v2', 'dev-S1', 'K1')
    sets = {}
    for name in names:
        entry = manifest['lists'][name]
        raw = pin(lists/entry['path'], original['list_checks'][name]['pin']['sha256']).read_text()
        if name == 'R0':
            values = raw.split()
        elif name == 'K1':
            captures = [c for c in json.loads(raw)['captures'] if c['k1_split'] == 'heldout']
            assert all(physical_room(c['canonical']) == norm(c['room']) for c in captures)
            values = [c['room'] for c in captures]
        else:
            values = json.loads(raw)['rooms' if name == 'withheld-80' else 'physical_groups']
        sets[name] = {norm(value) for value in values}
        assert len(sets[name]) == original['list_checks'][name]['rooms']
    counts, tiers, streams, families, joint, coverage = (Counter() for _ in range(6))
    unique_rooms, token_counts = set(), Counter()
    checked = 0
    with sqlite3.connect(source.as_uri()+'?mode=ro&immutable=1', uri=True) as src, \
            sqlite3.connect(rows_path.as_uri()+'?mode=ro&immutable=1', uri=True) as dst:
        source_rows = src.execute('SELECT i,row FROM rows ORDER BY i')
        persisted_rows = dst.execute('SELECT * FROM rows ORDER BY row_index')
        for source_row, actual in zip_longest(source_rows, persisted_rows):
            assert source_row is not None and actual is not None, 'Row count mismatch'
            index, raw = source_row
            row = json.loads(raw)
            dataset, scene_token = row.get('dataset', ''), row.get('scene', '')
            prefix = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2',
                      'arkitscenes': 'd3'}.get(dataset, dataset)
            token = prefix+'/'+scene_token
            entry = aliases[token]
            canonical, tier = norm(entry['canonical']), entry['tier']
            room = physical_room(canonical)
            stream, family = str(row.get('pool', 'MISSING')), str(row.get('question_type', 'MISSING'))
            matched = [name for name in names if room in sets[name]]
            expected = (index, str(row.get('qid', 'MISSING')), dataset, scene_token, token,
                        canonical, room, tier, stream, family, json.dumps(matched), None)
            assert actual == expected, ('Row differs from sb_alias2', index, actual, expected)
            checked += 1
            coverage[tier] += 1
            token_counts[token] += 1
            unique_rooms.add(room)
            for name in matched:
                counts[name] += 1
                tiers[(name, tier)] += 1
                streams[(name, stream)] += 1
                families[(name, family)] += 1
                joint[(name, tier, stream, family)] += 1
    assert checked == report['rows']
    assert {n: counts[n] for n in names} == report['hits'] == original['hits']
    for field, counter in (('hits_by_tier', tiers), ('hits_by_stream', streams), ('hits_by_family', families)):
        for name in names:
            expected = {key[1]: value for key, value in counter.items() if key[0] == name}
            assert report[field][name] == expected
            assert {k: v for k, v in original[field][name].items() if v} == expected
    for summary in (report, original):
        assert joint == Counter({(r['list'], r['tier'], r['stream'], r['family']): r['rows']
                                 for r in summary['hits_by_list_tier_stream_family']})
    assert dict(coverage) == report['coverage_by_tier'] == {
        tier: entry['rows'] for tier, entry in original['room_resolved_coverage'].items()}
    assert len(unique_rooms) == report['rooms_resolved'] == original['rooms_resolved']
    for tier, entry in original['room_resolved_coverage'].items():
        assert sum(aliases[token]['tier'] == tier for token in token_counts) == entry['tokens']
    return dict(status='PASS', rows_checked=checked, row_mismatches=0,
                hits=report['hits'], unresolved_rows=0, rooms=len(unique_rooms),
                joint_counts_checked=len(joint), coverage_by_tier=dict(coverage),
                comparison='Every persisted row column equals the source row plus the pinned sb_alias2 mapping, independent room derivation, and independent list membership.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compare(args.audit.resolve())
    except (OSError, ValueError, KeyError, AssertionError, sqlite3.Error) as error:
        result = dict(status='MISSING' if isinstance(error, FileNotFoundError) else 'FAIL', error=str(error))
    result.update(schema='auditfix2-alias2-comparison-v1', inputs=INPUTS,
                  command=shlex.join([sys.executable, '-s', '-B', *sys.argv]))
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(result['status'], result.get('rows_checked'), result.get('hits', result.get('error')))
    sys.exit(0 if result['status'] == 'PASS' else 1)
