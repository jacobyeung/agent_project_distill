"""Record the sealed-mode fix and its local evidence."""
import hashlib, json
from pathlib import Path

H = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda n: json.loads((H / n).read_text())
tests = load('evidence/fix3/tests.json')
assert len(tests) == 11 and all(t['status'] == 'PASS' for t in tests)
modes = load('evidence/fix3_modes.json')
assert all(v.get('status') == 'PASS' for k, v in modes['cases'].items() if not k.endswith('_round2'))
assert modes['guards_and_restore'] == modes['prepare_final_and_certify_writes'] == 'PASS'
assert load('evidence/fix3/package.json')['status'] == 'PASS'
ids = load('ids.json'); up = load('UPLOAD.json'); old = load('evidence/fix3_before/UPLOAD.json')
before = load('evidence/fix3_before/hashes.json')
assert ids == load('evidence/fix3_before/ids.json')
assert sha(H / 'tests/RERUN_CHAIN.sh') == before['tests/RERUN_CHAIN.sh']
text = f'''Cause: copied 0400 files and 0500 directories rejected ordinary writes; round-2 fails at b/r.sh on the observed Orchard fixture.
`tools/sealed_output.py:10` / `payload/d.py:57`: confine chmod/writes to the output; grant u+w to file and parent, restore exact modes in finally; refuse links/escapes.
`tools/make_deriver.py:126` generates `tools/derive_kit_h1.py` and `payload/d.py` with the same embedded writer.
`payload/d.py:454`: every replace_once patch uses it: b/r.sh (both patches), b/h.py, b/i.py, job.sh, b/c.sh and b/p0.sh.
`payload/d.py:481`: archive and 7.json copies, s1_record.json (:484), and archive.json (:499) preserve existing modes.
`payload/d.py:600`: initial b/ and job copies preserve source modes; k/o/runs creation (:602), k copies (:608) and add_k writes (:611) use scoped writes.
`payload/d.py:638`: config, 1.json, 0.json, launch.json (:672), SHA256SUMS.txt (:676) and ANON_OK.json (:678–680) preserve modes.
New k members inherit k/1.json's mode; renamed configs inherit the source config mode; new runtime dirs are 0700; source dirs retain exact modes.
`payload/d.py:682`: empty overrides preserve the root mode and add no absent runtime dirs; complete fixtures reproduce the entire source byte- and mode-identically.
`tools/orchard_records.py` / `payload/r.py:80,92`: temporary final launch and final certificate writes use the scoped writer; other writes target the mutable bundle only.
`payload/r.py:55,83,88`: empty reproduction and final comparison check modes explicitly and record mode digests; SHA256SUMS.txt itself remains byte-only.
Audit: `payload/z.sh:17–20` only checks sums/dispatches; `payload/v.py:27–54` only reads staging data and does not compare modes. Neither writes sealed members.
`tests/test_sealed_modes.py:64,69`: round-2 fails; H1, D0 and empty overrides pass on observed-mode and fully sealed fixtures, with source bytes/modes unchanged.
`tests/test_sealed_modes.py:87,112`: new files under 0500 dirs, restoration on failure, escape refusals, prepare, final comparison, mode-only rejection and certificate writes pass.
Two unavailable payloads use small stand-ins and a test-only manifest pin; complete production-kit availability remains unverified (`evidence/fix3_modes.json`).
PASS: four original checks, stop_bridge, fix1, visible_names, rv_mut, rv_g_a2, rv_gate and rv_g_fx (`evidence/fix3/tests.json`); CPU fallback reaches 200 and verifies its slot.
PASS: review syntax, unchanged RERUN_CHAIN.sh, deterministic repeated upload, archive metadata, embedded transport and payload sums (`evidence/fix3/package.json`). Existing chain_r1 was untouched.
`tools/audit_packet.py`, `tools/write_report.py` and `tools/seal_packet.py` regenerate DIFF.md, REPORT.md and SHA256SUMS.txt with current evidence; `tools/write_fix3.py` records full changed hashes.
Changed hashes: d.py {sha(H/'payload/d.py')[:16]}, r.py {sha(H/'payload/r.py')[:16]}, sums {sha(H/'payload/sums.txt')[:16]}, orch_h1.sh {sha(H/'orch_h1.sh')[:16]} (full values in evidence/hash_changes_fix3.json).
Upload SHA256: {old['sha256']} → {up['sha256']}; archive build/{up['archive']}.
Identity 6e4f2846 and contract 9a527092 are unchanged, as are all IDs, trainer pins, fixture byte manifest and wrapper. The target-exists refusal remains active for operator re-upload.
Work stayed local and CPU-only; no SSH, network, Orchard, GPU, Git, deletion, chain creation or chain-runner modification occurred.
'''
assert len(text.splitlines()) <= 25
(H / 'FIX3.md').write_text(text)
names = set(before) | {'tools/sealed_output.py', 'tools/write_fix3.py', 'tests/test_sealed_modes.py', 'FIX3.md'}
names.update(str(p.relative_to(H)) for p in (H / 'evidence/fix3').iterdir() if p.is_file())
names.add('evidence/fix3_modes.json')
excluded = {'SHA256SUMS.txt', 'evidence/final_checks.json'}
changes = {n: dict(before=before.get(n), after=sha(H / n)) for n in sorted(names - excluded)
           if (H / n).is_file() and before.get(n) != sha(H / n)}
record = dict(status='PASS', reason='Preserve sealed file/directory modes across all derivation writes and compare modes explicitly.',
              before_manifest_sha256=before['SHA256SUMS.txt'], changes=changes,
              upload_archive=dict(before=old['sha256'], after=up['sha256'], file='build/' + up['archive']),
              identity=ids['identity'], contract=ids['contract'], ids_unchanged=True,
              outer_seal='SHA256SUMS.txt seals this record and final_checks.json after generation.')
(H / 'evidence/hash_changes_fix3.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print('Wrote FIX3.md:', len(text.splitlines()), 'lines; recorded', len(changes), 'changed hashes')
