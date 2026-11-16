"""Record the manifest-boundary fix and the verified local packet."""
import hashlib, json
from pathlib import Path

H = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda n: json.loads((H / n).read_text())
before = load('evidence/fix4_before/hashes.json')
ids, up, old = load('ids.json'), load('UPLOAD.json'), load('evidence/fix4_before/UPLOAD.json')
assert ids == load('evidence/fix4_before/ids.json')
tests = load('evidence/fix4/tests.json')
assert len(tests) == 11 and all(t['status'] == 'PASS' for t in tests)
assert load('evidence/fix4_listing.json')['status'] == 'PASS'
assert load('evidence/fix4/package.json')['status'] == 'PASS'
modes = load('evidence/fix4_sealed_modes.json')
assert modes['guards_and_restore'] == modes['prepare_final_and_certify_writes'] == 'PASS'
assert all(v.get('status') == 'PASS' for k, v in modes['cases'].items() if not k.endswith('_round2'))
text = f'''Cause: whole-tree mode inventory compared 90 unmanifested runtime entries present only in the real source kit; shared member modes matched.
`tools/sealed_output.py:7,20,24` / `payload/d.py:51,64,68`: inventory SHA256SUMS members, their ancestor directories and the root only.
`tools/make_deriver.py:138` generates `payload/d.py:567,627`: validate and copy only sealed members; never walk source runtime trees or copy unlisted b/k files.
`payload/d.py:417,653`: restrict source JSON dependency reads and overwrite checks to manifest membership.
`payload/d.py:632,702`: create fresh empty 0700 runtime directories and an UNREVIEWED certificate; do not read or copy source runtime state or its certificate.
`payload/r.py:55,83,88`: prepare, final comparison and mode digests share the scoped inventory; z.sh dispatches these checks.
`tests/test_runtime_inventory.py:1`: exact 193-entry SRC fixture includes all 90 runtime entries; fix-3 fails at member modes, current prepare/empty/final/certify pass.
The fixture denies unlisted source opens/stats/traversal, ignores poisoned b/k records and a dangling link, and rejects sealed-file/directory/root mode differences.
`tests/test_sealed_modes.py:28,77`: reproduction helpers compare sealed scope; six permission derivations, restoration, confinement and certificate writes pass.
PASS: four originals, stop_bridge, fix1, visible_names and four runnable reviewer checks; review harness syntax passes. Evidence: evidence/fix4/tests.json.
PASS: deterministic repeated upload/fixture builds, independent trainer rebuild, archive metadata, embedded transport and payload sums (evidence/fix4/package.json).
REVIEW4.md covers orch_h1/o/prepare/stage, g, z/final/certify, s, v and jb preflight, with OK/FIXED verdicts and retained prerequisites.
Changed d.py SHA256: {sha(H/'payload/d.py')}; r.py: {sha(H/'payload/r.py')}.
Changed sums SHA256: {sha(H/'payload/sums.txt')}; orch_h1.sh: {sha(H/'orch_h1.sh')}.
Upload SHA256: {old['sha256']} -> {up['sha256']} (build/{up['archive']}).
All changed file hashes are in evidence/hash_changes_fix4.json; SHA256SUMS.txt seals that record, current reports and evidence.
Identity {ids['identity']} and contract {ids['contract']} are unchanged; all IDs, trainer pins, fixture manifest and wrapper are unchanged.
The operator must rename i_1be16f28 to i_1be16f28.f2 before re-upload; the target-exists refusal remains active.
Work was local and CPU-only. No SSH/network/Orchard/GPU/Git/deletion, chain creation or chain-runner edit occurred; the four-rank harness was not run.
'''
assert len(text.splitlines()) <= 20
(H / 'FIX4.md').write_text(text)
names = set(before) | {'FIX4.md', 'REVIEW4.md', 'tests/test_runtime_inventory.py',
    'tools/check_fix4.py', 'tools/check_fix4_package.py', 'tools/write_fix4.py',
    'evidence/fix4_listing.json', 'evidence/fix4_sealed_modes.json'}
names.update(str(p.relative_to(H)) for p in (H / 'evidence/fix4').iterdir() if p.is_file())
names.difference_update({'SHA256SUMS.txt', 'evidence/final_checks.json'})
changes = {n: dict(before=before.get(n), after=sha(H / n)) for n in sorted(names)
           if (H / n).is_file() and before.get(n) != sha(H / n)}
record = dict(status='PASS', changes=changes, ids_unchanged=True,
              identity=ids['identity'], contract=ids['contract'],
              upload_archive=dict(before=old['sha256'], after=up['sha256'], file='build/' + up['archive']),
              before_manifest_sha256=before['SHA256SUMS.txt'],
              outer_seal='SHA256SUMS.txt seals this record after generation.')
(H / 'evidence/hash_changes_fix4.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print('FIX4.md:', len(text.splitlines()), 'lines;', len(changes), 'changed hashes')
