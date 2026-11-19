"""Audit the local index snapshot and its available, hash-checked native inputs."""
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tool'))
import ingest_read as ingest

index = ROOT / 'evidence/INDEX.jsonl'
entries = [json.loads(line) for line in index.open()]
records = []
formats = collections.Counter()
for entry in entries:
    metadata = entry.get('raw_metadata', {})
    paths = [source.get('logical', '') for source in entry['sources']]
    kind = ('native' if 'native/paired/request.json' in metadata else
            'offread' if any(p.startswith('a0/results/') for p in paths) else
            'kit' if 'SPEC.json' in metadata else 'routed')
    formats[kind] += 1
    reports = [p for p in paths if '/report/' in p]
    if kind == 'kit' and reports:
        assert entry['orphan_count'] == 0
        basis = ('inferred: zero published orphans; the rejected actual-ID alias in review 2 leaves an orphan. '
                 'The index omits per-item IDs, so a collision with a separate devrows-prefixed generation ID cannot be excluded here.')
    elif kind == 'kit':
        basis = 'code/index: no family report sources; the changed alias lookup cannot supply scores'
    elif kind == 'native':
        basis = 'inferred: validation does not rewrite successful output; matching declared key sets, equal arm/union counts, and compatible mirrored task identities'
    else:
        basis = 'code: these adapter normalization and emission paths are unchanged'
    records.append(dict(read_id=entry['read_id'], format=kind, item_count=entry['item_count'],
                        arms={k: v['items'] for k, v in entry['arm_stats'].items()},
                        default='unchanged', enabled_decision='unchanged', basis=basis,
                        orphan_count=entry['orphan_count'], report_sources=len(reports), output=entry['output']))

native = next(entry for entry in entries if 'native/paired/request.json' in entry['raw_metadata'])
metadata = native['raw_metadata']
keys = metadata['native/paired/request.json']['keys']
report_keys = metadata['native/R1.json']['expected_keys']
assert len(keys) == len(set(keys)) == len(report_keys) == len(set(report_keys)) == 636
assert set(keys) == set(report_keys)
assert metadata['native/paired/request.json']['arm'] == 'paired'
assert {k: v['items'] for k, v in native['arm_stats'].items()} == {'scripted': 636, 'unflagged': 636}
assert native['item_count'] == 636
store = ingest.Store(review2_checks=True)
checked_sources = []
for source in native['sources']:
    if not source.get('logical', '').startswith('inputs/'):
        continue
    mirror = pathlib.Path('/scratch/jjyeung/orch_n30/so_in' + source['path'])
    fingerprint = ingest.fingerprint(mirror)
    assert fingerprint['sha256'] == source['sha256']
    assert fingerprint['bytes'] == source['bytes']
    with mirror.open('rb') as stream:
        store.consume(source['logical'], stream)
    checked_sources.append(dict(logical=source['logical'], mirror=str(mirror), sha256=fingerprint['sha256'], bytes=fingerprint['bytes']))
conflicts, matched, additive = [], 0, 0
for key in keys:
    candidates = [json.loads(data) for data, in store.db.execute(
        'SELECT data FROM tasks WHERE id=? ORDER BY path', (key[len('devrows:'):],))]
    matched += bool(candidates)
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
    if candidates and any(set(task) != set(candidates[0]) for task in candidates[1:]):
        additive += 1
assert not conflicts
assert matched == 636
summary = dict(index_bytes=index.stat().st_size, index_sha256=hashlib.sha256(index.read_bytes()).hexdigest(),
               reads=len(records), formats=dict(formats), reads_detail=records,
               native=dict(request_keys=len(keys), report_keys=len(report_keys), matched_tasks=matched,
                           conflicting_identity_fields=len(conflicts), tasks_with_additive_fields=additive,
                           checked_sources=checked_sources),
               decision='No re-ingest indicated by this static audit; no published bytes were rewritten or compared directly.')
with (ROOT / 'evidence/published_audit.json').open('w') as f:
    json.dump(summary, f, indent=2, sort_keys=True)
print('INDEX: %d bytes; sha256=%s' % (summary['index_bytes'], summary['index_sha256']))
print('READS: %d; formats=%s' % (len(records), json.dumps(dict(formats), sort_keys=True)))
print('NATIVE: 636 request keys = 636 report keys; scripted=636; unflagged=636; union=636')
print('NATIVE INPUTS: %d hash-verified files; %d matched tasks; %d conflicting fields; %d tasks with additive fields' %
      (len(checked_sources), matched, len(conflicts), additive))
for record in records:
    print('%s | %s | %s | unchanged | %s' % (record['read_id'], record['format'],
          ','.join('%s:%s' % (a, n) for a, n in record['arms'].items()), record['basis']))
print(summary['decision'])
