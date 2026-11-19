"""Reproduce the K1 census and removal lists using pinned local inputs."""
import ast
import collections
import csv
import hashlib
import io
import json
import re
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'out'
AUDIT_BASE = Path('/scratch/jjyeung/orch_n30/sb_alias2')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
COMMAND = '/usr/bin/python3 out/build_lists.py'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def status(message):
    (BASE / 'STATUS.md').write_text(message + '\n')


inputs = {}


def snapshot(name, original, expected=None, parse=True):
    path = BASE / 'inputs' / (name + '.input')
    if not path.exists():
        raise FileNotFoundError('MISSING {} (snapshot {})'.format(original, path))
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if expected:
        assert sha == expected, (original, sha, expected)
    inputs[str(original)] = dict(sha256=sha, bytes=len(data), snapshot=str(path))
    return json.loads(data) if parse else data.decode()


audit = snapshot('audit', AUDIT_BASE / 'out/ROOM_AUDIT_TIERED.json')
aliases_doc = snapshot('aliases', AUDIT_BASE / 'out/TIERED_ALIAS_MAP.json')
report = snapshot('audit_report', AUDIT_BASE / 'out/ROOM_AUDIT_REPORT.md', parse=False)
u_text = snapshot('u', TREE / 'w18/work/build18/inputs/u.json',
                  '43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6', False)
u_rows = [json.loads(line) for line in u_text.splitlines()]
keys = ['canonical', 'reason', 'row_key']
assert all(list(r) == keys and r['reason'] == 'k1_heldout_v7' for r in u_rows)
assert u_rows == sorted(u_rows, key=lambda r: r['row_key'])
u = {r['row_key']: r for r in u_rows}
assert len(u) == len(u_rows) == 2637

prior_path = TREE / 'w17b/work/build17/proofs/rooms/RESULT.json'
prior = snapshot('prior', prior_path, audit['inputs'][str(prior_path)]['sha256'])['audit']
room_path = TREE / 'w17b/work/tree_r1/student_pilot/r1_rooms.py'
room_source = snapshot('rooms', room_path, audit['inputs'][str(room_path)]['sha256'], False)
split_pin = prior['authority']['split']
split = snapshot('split', split_pin['path'], split_pin['sha256'])
visit_pin = prior['authority']['visits']
visits = snapshot('visits', visit_pin['path'], visit_pin['sha256'], False)
k1_pin = audit['list_checks']['K1']['pin']
k1 = snapshot('k1', k1_pin['path'], k1_pin['sha256'])
archive = AUDIT_BASE / 'out/sb_alias2.tar'
archive_sha = digest(archive)
assert archive_sha == 'c7743a8b0c282b6aafd89b4b00bd41a29dba8735390f1f6947a2076ff4dd08ea'
assert archive_sha in report
inputs[str(archive)] = dict(sha256=archive_sha, bytes=archive.stat().st_size)
db = Path(audit['store']['path'])
assert str(db.resolve()).startswith('/scratch/')
assert digest(db) == audit['store']['sha256'] == prior['store']['database']['sha256']
inputs[str(db)] = dict(sha256=audit['store']['sha256'], bytes=db.stat().st_size)
inputs[str(Path(__file__).resolve())] = dict(sha256=digest(__file__), bytes=Path(__file__).stat().st_size)
status('Input validation passed: the removal list, audit archive, store, K1 source, room methods, split and visit metadata match their pinned SHA-256 hashes. The full row census is in progress.')

# Reuse only the two audited methods; do not import their application dependencies.
tree = ast.parse(room_source)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Rooms')
tree.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in ('canonical', 'room')]
ns = {'re': re}
exec(compile(tree, str(room_path), 'exec'), ns)
Rooms = type('Rooms', (), {name: ns[name] for name in ('canonical', 'room')})
rooms = Rooms()
rooms.visits = {r['video_id']: r['visit_id'] for r in csv.DictReader(io.StringIO(visits))}
aliases = aliases_doc['aliases']
rooms.aliases = {k: v['canonical'] for k, v in aliases.items()}
norm = lambda c: c.replace('scannetppv2/', 'scannetpp/', 1)
assert split['teacher_k1']['sha256'] == k1_pin['sha256']
raw_captures = {norm(c['canonical']): c['k1_split'] for c in k1['captures']}
assert raw_captures == {norm(c['canonical']): c['k1_split'] for c in split['teacher_k1']['captures']}
held = {c['room'] for c in split['teacher_k1']['captures'] if c['k1_split'] == 'heldout'}
assert held == {rooms.room(c) for c, s in raw_captures.items() if s == 'heldout'}
assert len(held) == 50
assert audit['complete'] and aliases_doc['complete']
assert not aliases_doc['conflicts'] and not aliases_doc['quarantined_tokens']

hits = {}
u_seen = {}
seen = set()
with sqlite3.connect(db.as_uri() + '?mode=ro&immutable=1', uri=True) as conn:
    conn.execute('PRAGMA cache_size=-32768')
    for index, raw in conn.execute('select i,row from rows order by i'):
        row = json.loads(raw)
        qid = row['qid']
        assert isinstance(qid, str) and qid and qid not in seen, qid
        seen.add(qid)
        ds = row.get('dataset', '')
        token = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'arkitscenes': 'd3'}.get(ds, ds) + '/' + row.get('scene', '')
        entry = aliases[token]
        canonical, route = rooms.canonical(row)
        assert norm(canonical) == entry['canonical']
        room = rooms.room(canonical)
        record = dict(row_key=qid, canonical=entry['canonical'], room=room,
                      tier=entry['tier'], stream=row.get('pool', 'MISSING'),
                      family=row.get('question_type', 'MISSING'), row_index=index,
                      scene=row.get('scene'), dataset=ds, token=token)
        if qid in u:
            u_seen[qid] = record
            assert norm(u[qid]['canonical']) == record['canonical'], qid
        if room in held:
            hits[qid] = record
assert len(seen) == audit['rows'] == 204413
assert len(hits) == audit['hits']['K1'] == 4959


def counts(records, field):
    return dict(sorted(collections.Counter(r[field] for r in records).items()))


for field in ('stream', 'family', 'tier'):
    assert counts(hits.values(), field) == audit['hits_by_' + field]['K1']
joint = collections.Counter((r['tier'], r['stream'], r['family']) for r in hits.values())
assert joint == collections.Counter({(r['tier'], r['stream'], r['family']): r['rows']
                                    for r in audit['hits_by_list_tier_stream_family'] if r['list'] == 'K1'})
for tier, examples in audit['examples_by_list_tier']['K1'].items():
    for example in examples:
        record = hits[example['row_id']]
        assert all(record[k] == example[k] for k in ('canonical', 'room', 'tier', 'stream', 'family', 'row_index', 'token'))
outside = [dict(u[k], audit=u_seen.get(k, 'MISSING: row_key absent from pinned store')) for k in sorted(set(u) - set(hits))]
added = sorted(set(hits) - set(u))
u2_rows = [dict(canonical=hits[k]['canonical'], reason='k1_heldout_v7', row_key=k) for k in added]
union = dict(u)
union.update({r['row_key']: r for r in u2_rows})
union_rows = [union[k] for k in sorted(union)]
assert not (set(added) & set(u))
assert set(union) == set(u) | set(hits)
status('Census validation passed: all 204,413 store rows have unique qid identities; all K1 stream, family, tier and joint counts match the audit. The set difference and union are computed; output serialization and packaging remain.')

output_pins = {}
for name, records in [('u2.json', u2_rows), ('u_union.json', union_rows)]:
    path = OUT / name
    path.write_text(''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in records))
    decoded = [json.loads(line) for line in path.read_text().splitlines()]
    assert decoded == records and all(list(r) == keys for r in decoded)
    output_pins[name] = dict(sha256=digest(path), rows=len(records), metadata='U2_METADATA.json')
groups = {'audit': list(hits.values()), 'u': list(u_seen.values()), 'u2': [hits[k] for k in added],
          'union': [hits.get(k, u_seen.get(k)) for k in sorted(union)]}
assert all(r is not None for records in groups.values() for r in records)
summaries = {group: {field: counts(records, field) for field in ('stream', 'family', 'tier')}
             for group, records in groups.items()}
metadata = dict(schema='sb_k1list-provenance-v1', command=COMMAND, inputs=inputs,
                inherited_audit_inputs=audit['inputs'], outputs=output_pins,
                format=dict(encoding='JSON Lines', keys=keys, identity='row_key equals store qid',
                            order='ascending lexicographic row_key', header=None,
                            provenance_location='U2_METADATA.json; input u.json has no metadata/header'),
                counts={k: len(v) for k, v in groups.items()}, summaries=summaries,
                checks=dict(u_subset_of_audit_k1=not outside, u_outside_k1=outside,
                            u_missing_from_store=sorted(set(u) - set(u_seen)),
                            u_u2_overlap=0, union_equals_audit_k1=set(union) == set(hits),
                            duplicate_store_qids=0, all_audit_marginals_and_joint_counts_match=True),
                audit_k1_rows=[hits[k] for k in sorted(hits)])
(OUT / 'U2_METADATA.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')

lines = [
    'Vehicle N: u2 contains {} additional K1 rows; u contains {}; their union contains {}.'.format(len(added), len(u), len(union)),
    'All 4,959 audit K1 identities and every marginal/joint count were reproduced from the pinned 204,413-row store.',
    'Identity: row_key = store qid; ordering: ascending row_key; keys: canonical, reason, row_key; reason: k1_heldout_v7.',
    'Schema constraint: u.json is headerless JSON Lines. Both outputs preserve it; U2_METADATA.json records all input SHA-256 hashes and binds each output hash.',
    'Overlap: u subset of audit K1 = {}; u outside K1 = {}; u/u2 intersection = 0; union equals audit K1 = {}.'.format(not outside, len(outside), set(union) == set(hits)),
    'u rows outside K1, with scenes: ' + ('none.' if not outside else json.dumps(outside, sort_keys=True)),
    'Count columns below are audit / u / u2 / union. MISSING denotes a missing row.pool field, not missing proof.',
    '', '| Stream | Counts | Family | Counts |', '|---|---|---|---|'
]
streams = sorted(summaries['audit']['stream'])
families = sorted(summaries['audit']['family'])


def cell(field, key):
    return ' / '.join(str(summaries[g][field].get(key, 0)) for g in ('audit', 'u', 'u2', 'union')) if key else ''


for i in range(max(len(streams), len(families))):
    stream = streams[i] if i < len(streams) else ''
    family = families[i] if i < len(families) else ''
    lines.append('| {} | {} | {} | {} |'.format(stream, cell('stream', stream), family, cell('family', family)))
lines += ['', 'Proof tiers (audit / u / u2 / union): ' + '; '.join(t + ': ' + cell('tier', t) for t in 'ABC') + '.',
          'Audit archive SHA-256: `' + archive_sha + '` (verified).',
          'Store SHA-256: `' + audit['store']['sha256'] + '` (verified).',
          'K1 source SHA-256: `' + k1_pin['sha256'] + '` (verified).',
          'u SHA-256: `' + inputs[str(TREE / 'w18/work/build18/inputs/u.json')]['sha256'] + '` (verified).',
          'u2 SHA-256: `' + output_pins['u2.json']['sha256'] + '`.',
          'Union SHA-256: `' + output_pins['u_union.json']['sha256'] + '`.',
          'All counts, overlaps, identity/schema/order checks and input hashes: `' + COMMAND + '`.',
          'Package: `tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --exclude=out/sb_k1list.tar --exclude=out/sb_k1list.tar.sha256 -cf out/sb_k1list.tar out`.',
          'Archive digest: `sha256sum out/sb_k1list.tar > out/sb_k1list.tar.sha256`; verify: `sha256sum -c out/sb_k1list.tar.sha256`.',
          'Archive excludes itself and its checksum sidecar. Borderline historical wording retained: none.']
assert len(lines) <= 40, len(lines)
(OUT / 'U2_REPORT.md').write_text('\n'.join(lines) + '\n')
status('Lists validated: u2 has {} rows and the union has {} rows. The u subset check is {}; the u/u2 intersection is empty. U2_REPORT.md and U2_METADATA.json contain counts, provenance and reproduction commands. Archive packaging remains.'.format(len(added), len(union), not outside))
print(json.dumps(dict(counts=metadata['counts'], checks=metadata['checks'], u2=output_pins['u2.json'], union=output_pins['u_union.json'], tiers=summaries['u2']['tier']), indent=2))
