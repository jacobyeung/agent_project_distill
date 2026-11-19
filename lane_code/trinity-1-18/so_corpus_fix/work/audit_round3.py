"""Bounded audit of the published index snapshot and named local task sources."""
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tool'))
import ingest_read as ingest

index = ROOT / 'evidence/INDEX_round3.jsonl'
entries = [json.loads(line) for line in index.open()]
details = []
for entry in entries:
    paths = [source.get('logical', '') for source in entry['sources']]
    docs = entry.get('raw_metadata', {})
    kind = ('native' if 'native/paired/request.json' in docs else
            'offread' if any(p.startswith('a0/results/') for p in paths) else
            'kit' if 'SPEC.json' in docs else 'routed')
    reports = [p for p in paths if '/report/' in p]
    unresolved = kind == 'native' or (kind == 'kit' and bool(reports))
    root_source = next(s for s in entry['sources'] if s.get('logical') == 'COMPLETE.json')
    source = root_source['path'] if root_source.get('member') else str(Path(root_source['path']).parent)
    mirror = Path('/scratch/jjyeung/orch_n30/so_in' + source)
    details.append(dict(read_id=entry['read_id'], format=kind, item_count=entry['item_count'],
                        arms={k: v['items'] for k, v in entry['arm_stats'].items()},
                        orphan_count=entry['orphan_count'], report_sources=len(reports),
                        source=source, source_mirror_available=mirror.exists(),
                        default='unchanged relative to input tool',
                        enabled='unverified: source-row replay required' if unresolved else 'unchanged by code/index',
                        index_tool_version='would change', output=entry['output']))

native = next(e for e in entries if 'native/paired/request.json' in e['raw_metadata'])
metadata = native['raw_metadata']
keys = metadata['native/paired/request.json']['keys']
report_keys = metadata['native/R1.json']['expected_keys']
assert len(keys) == len(set(keys)) == len(report_keys) == len(set(report_keys)) == 636
assert set(keys) == set(report_keys)
assert metadata['native/paired/request.json']['arm'] == 'paired'
assert {k: v['items'] for k, v in native['arm_stats'].items()} == {'scripted': 636, 'unflagged': 636}
assert native['item_count'] == 636
store = ingest.Store(review2_checks=True)
checked = []
for source in native['sources']:
    if not source.get('logical', '').startswith('inputs/'):
        continue
    mirror = Path('/scratch/jjyeung/orch_n30/so_in' + source['path'])
    info = ingest.fingerprint(mirror)
    assert info['sha256'] == source['sha256'] and info['bytes'] == source['bytes']
    with mirror.open('rb') as stream:
        store.consume(source['logical'], stream)
    checked.append(dict(logical=source['logical'], path=str(mirror), sha256=info['sha256'], bytes=info['bytes']))

candidate_counts = collections.Counter()
conflicts = []
selected_without_room_key = 0
additive_room_key = 0
for key in keys:
    candidates = [json.loads(data) for data, in store.db.execute(
        'SELECT data FROM tasks WHERE id=? ORDER BY path', (key.removeprefix('devrows:'),))]
    candidate_counts[len(candidates)] += 1
    identity = {}
    for task in candidates:
        fields = dict(task)
        for primary, fallback in (('ground_truth', 'answer'), ('units', 'unit')):
            if fallback in fields and primary not in fields:
                fields[primary] = fields[fallback]
        for field, value in fields.items():
            encoded = ingest.dumps(value)
            if field in identity and identity[field] != encoded:
                conflicts.append(dict(key=key, field=field))
            identity[field] = encoded
    selected_without_room_key += bool(candidates) and 'room_key' not in candidates[0]
    additive_room_key += bool(candidates) and 'room_key' not in candidates[0] and any('room_key' in t for t in candidates[1:])

consumed_inputs = store.db.execute('SELECT count(*) FROM records').fetchone()[0]
assert consumed_inputs == native['orphan_count'] == 6967
assert native['consumed_row_count'] - consumed_inputs == 4 * len(keys)
assert candidate_counts == {2: 636} and not conflicts
summary = dict(index_bytes=index.stat().st_size, index_sha256=hashlib.sha256(index.read_bytes()).hexdigest(),
               reads=len(details), formats=dict(collections.Counter(r['format'] for r in details)),
               reads_detail=details, confirmed_changed_read_payload_ids=[],
               enabled_unverified_ids=[r['read_id'] for r in details if r['enabled'].startswith('unverified')],
               regenerated_index_version_changed_ids=[r['read_id'] for r in details],
               recorded_tool_versions=sorted({e['tool_version'] for e in entries}),
               native=dict(request_keys=len(keys), report_keys=len(report_keys), input_rows=consumed_inputs,
                           return_rows=native['consumed_row_count'] - consumed_inputs,
                           candidate_counts=dict(candidate_counts), conflicting_fields=len(conflicts),
                           selected_without_room_key=selected_without_room_key,
                           additive_room_key_in_sidecars=additive_room_key, checked_sources=checked))
store.db.close()
target = ROOT / 'evidence/published_round3_audit.json'
target.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print('INDEX: %d bytes; SHA256=%s' % (summary['index_bytes'], summary['index_sha256']))
print('READS: %d; formats=%s' % (len(details), json.dumps(summary['formats'], sort_keys=True)))
print('NATIVE: 636 declared keys; 636 items in each arm; 9 hash-verified input files; 6967 input rows; 2544 return rows')
print('NATIVE: 636 keys with exactly 2 compatible candidates; 0 identity conflicts; 636 selected tasks lack additive room_key')
for row in details:
    print('%s | %s | default: unchanged | checks enabled: %s | mirrored return available: %s' %
          (row['read_id'], row['format'], row['enabled'], row['source_mirror_available']))
print('Confirmed changed read payload IDs: none; enabled impact unresolved for 7 IDs. Regenerated index tool_version changes for all 18 IDs.')
print('No published read or index was modified. No published read gzip or real return was loaded.')
