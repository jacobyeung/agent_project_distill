"""Verify the G5 package, test evidence and exact FAMILY delta; publish the result."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile

B = Path(__file__).resolve().parents[1]
O = B / 'out'
K = O / 'guard_kit'
sys.path.insert(0, str(K))
from guard_core import read, write, sha
from transport import regular_tar
from worker import REPORT_SHA256

baseline = read(B / 'work/G5_BASELINE.json')
family = read(O / 'FAMILY.json')
tests = read(O / 'TESTS.json')
mutants = read(O / 'MUTANTS.json')
seal = read(O / 'G5_SEAL.json')
assert baseline['family_sha256'] == '2b5563214dd1c99b49551278fe4ec53c3867d5a746b141e36c543d94f0eec7a5'
assert REPORT_SHA256 == '5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11'
expected_family = dict(baseline['family'], code_pins=dict(baseline['family']['code_pins'], **{'worker.py': sha(K / 'worker.py')}))
assert family == expected_family and family['release_ready'] is False
assert family['code_pins']['worker.py'] != baseline['family']['code_pins']['worker.py']
old_report_pin = baseline['report_pin']['required_sha256']
worker_before = (K / 'worker.py').read_text().replace(REPORT_SHA256, old_report_pin)
assert hashlib.sha256(worker_before.encode()).hexdigest() == baseline['family']['code_pins']['worker.py']
fields = ['code_pins.worker.py']
write(O / 'FAMILY_CHANGES_G5.json', dict(
    baseline_sha256=baseline['family_sha256'], current_sha256=sha(O / 'FAMILY.json'),
    changed_fields=fields, release_ready_changed=False,
    changes={fields[0]: dict(before=baseline['family']['code_pins']['worker.py'], after=family['code_pins']['worker.py'])},
    reason='The coordinator requires the final report source authorized in BRIEF_G5.md.'))

assert tests['build_round'] == 'G5' and tests['status'] == 'PASS'
assert {s['name'] for s in tests['suites']} == {s['name'] for s in baseline['tests']['suites']}
assert tests['tests'] == sum(s['tests'] for s in tests['suites'])
assert tests['family_sha256'] == sha(O / 'FAMILY.json')
assert tests['admission_sha256'] == sha(K / 'admission.py')
for suite in tests['suites']:
    assert suite['status'] == 'PASS' and suite['returncode'] == suite['failures'] == suite['errors'] == 0
    result = read(B / suite['path'])
    assert all(result[key] == suite[key] for key in ('tests', 'failures', 'errors'))
    if 'status' in result:
        assert result['status'] == 'PASS'
    assert '\nOK\n' in (B / suite['log']).read_text()
assert mutants['complete'] and mutants['killed'] == mutants['total']
assert all(row['killed'] for row in mutants['results'])
assert tests['mutants_returncode'] == 0 and tests['mutants_reused_from_same_g4_source'] is False
assert tests['report_sha256'] == tests['mutants_report_sha256'] == mutants['report_sha256'] == REPORT_SHA256
report_inputs = read(B / 'work/G5_REPORT_INPUTS.json')
for name, pin in report_inputs.items():
    assert sha(B.parent / 'report' / name) == pin
assert report_inputs['guard_read.py'] == REPORT_SHA256
mutant_tree = ast.parse((B.parent / 'report/tests/mutants.py').read_text())
definitions = ast.literal_eval(next(node.value for node in mutant_tree.body if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == 'MUTANTS' for target in node.targets)))
assert [row['name'] for row in mutants['results']] == [row[0] for row in definitions]
assert mutants['total'] == len(definitions)

for name, pin in family['code_pins'].items():
    assert sha(K / name) == pin, name
for name, pin in family['inputs'].items():
    assert sha(O / 'inputs' / name) == pin['sha256'], name
for manifest_name, archive_name in [('CODE_MANIFEST.json', 'code_g2.tar'), ('INPUT_MANIFEST.json', 'inputs_g2.tar')]:
    manifest = read(O / manifest_name)
    archive = O / archive_name
    assert sha(archive) == manifest['sha256'] and archive.stat().st_size == manifest['bytes']
    regular_tar(archive)
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        inventory = {m.name: dict(bytes=m.size, sha256=hashlib.sha256(stream.extractfile(m).read()).hexdigest()) for m in members}
        assert all(m.mtime == 0 and m.uid == m.gid == 0 for m in members)
    assert len(members) == len(inventory) and inventory == manifest['members']
    if archive_name == 'code_g2.tar':
        assert {n: v['sha256'] for n, v in inventory.items()} == family['code_pins']
        assert set(inventory) == set(baseline['code_manifest']['members'])
        assert [n for n in inventory if inventory[n] != baseline['code_manifest']['members'][n]] == ['worker.py']
        assert not any('rehearsal' in Path(n).parts or n.endswith('.g2_orig.py') for n in inventory)
assert seal['status'] == 'PASS' and seal['changed_production_members'] == ['worker.py']
assert seal['code_sha256'] == sha(O / 'code_g2.tar') and seal['family_sha256'] == sha(O / 'FAMILY.json')
assert read(O / 'INPUT_MANIFEST.json') == baseline['input_manifest']
identity = read(O / 'SOURCE_IDENTITY.json')
assert identity['all_equal']
for row in identity['files']:
    assert sha(B / row['file']) == row['sha256'] == row['current_sha256']
assert read(O / 'RESTORATION_TEST.json')['status'] == 'PASS'
meta = read(O / 'candidate_m50/CLOSURE.json')
assert sha(O / 'candidate_m50/metadata.tar') == meta['archive']['sha256'] == baseline['audit']['metadata_sha256']
diff = read(O / 'DIFF_C8R.json')
assert sha(O / 'DIFF_C8R.patch') == diff['patch_sha256'] == sha(O / 'DIFF.patch')
for row in diff['changed_files']:
    assert sha(B / row['file']) == row['sha256']

checked = []
paths = [K / name for name in family['code_pins'] if name.endswith('.py')]
for root in (B / 'work', O / 'tests', O / 'rehearsal', O / 'operator'):
    paths.extend(root.glob('*.py'))
for path in sorted(paths):
    compile(path.read_text(), str(path), 'exec')
    checked.append(str(path.relative_to(B)))
packet = read(O / 'PACKET_TEST.json')
assert packet['status'] == 'PASS' and packet['production_authority'] is False
batch = Path(packet['packet']) / 'BATCH.sh'
with tarfile.open(Path(packet['packet']) / 'p.tar') as stream:
    assert json.load(stream.extractfile('FAMILY.json'))['code_pins'] == family['code_pins']
shell_path = B / 'work/RUN_G5_SYNTAX.sh'
shell_path.write_text('\n'.join(re.findall(r'```sh\n(.*?)```', (O / 'RUN.md').read_text(), re.S)))
for path in (batch, O / 'rehearsal/run_whole_worker.sh', shell_path):
    subprocess.run(['/bin/bash', '-n', str(path)], check=True)
compile(batch.read_text().split("<<'G2_PY'\n", 1)[1].rsplit('\nG2_PY', 1)[0], str(batch), 'exec')
write(O / 'SYNTAX.json', dict(status='PASS', build_round='G5', python_files=len(checked), files=checked,
    batch=str(batch), batch_sha256=sha(batch), run_sheet_shell=str(shell_path)))
pins = read(O / 'PIN_CLASSIFICATION.json')
assert [row['number'] for row in pins] == list(range(1, 47))
for row in pins:
    filename, number = row['enforcement'].rsplit(':', 1)
    assert 0 < int(number) <= len((B / filename).read_text().splitlines())

report_pin = dict(status='PASS', build_round='G5', report=str(B.parent / 'report/guard_read.py'),
    brief_sha256=REPORT_SHA256, required_sha256=REPORT_SHA256, observed_sha256=REPORT_SHA256,
    intentional_post_review_change=True, report_modified_by_g5=False,
    authority=dict(source='BRIEF_G5.md', decision='The operator authorizes the final report source pin.'),
    source_hashes=report_inputs,
    changes=['Candidate artifact required', 'Step-544 candidate requires explicit self-pair',
             'Fixed seed and draw count', 'Strict boolean accounting flags', 'Dictionary-only decode',
             'Malformed input returns exit 3'],
    validation=dict(suites='out/TESTS.json', report='out/REPORT_TESTS.json', mutants='out/MUTANTS.json'))
write(O / 'REPORT_PIN_G4.json', report_pin)
blockers = read(O / 'RELEASE_BLOCKERS.json')
by_id = {row['id']: row for row in blockers['blockers']}
assert by_id['naming']['status'] == 'ACCEPTED' and by_id['whole_worker']['status'] == 'CLOSED'
assert blockers['production_packet_authorized'] is False
for row in blockers['review_fixes']:
    if row['id'] == 1:
        row.update(status='FIXED', description='Every report call binds the CONFIG artifact and final authorized report source.')
    assert row['status'] == 'FIXED'
blockers['report_source_pin'] = report_pin
write(O / 'RELEASE_BLOCKERS.json', blockers)

count = size = 0
for root, dirs, files in os.walk(B, followlinks=False):
    if Path(root) == O / 'rehearsal':
        dirs[:] = [name for name in dirs if name != 'whole']
    for name in files:
        path = Path(root) / name
        if not path.is_symlink():
            count += 1
            size += path.stat().st_size
assert size < 6_000_000_000
write(O / 'BUILD_SIZE_G5.json', dict(bytes=size, files=count, limit_bytes=6_000_000_000,
    measured_scope_within_cap=True, scope='Build files excluding out/rehearsal/whole/; protected operator files were not inventoried.'))
now = datetime.datetime.now(datetime.timezone.utc)
timing = read(B / 'work/TIMING_G5.json')
assert now < datetime.datetime.fromisoformat(timing['deadline_utc'])
timing.update(end_utc=now.isoformat(), elapsed_seconds=(now - datetime.datetime.fromisoformat(timing['start_utc'])).total_seconds(), within_deadline=True)
write(B / 'work/TIMING_G5.json', timing)
code = read(O / 'CODE_MANIFEST.json')
audit = dict(status='PASS_FOR_PACKAGE_INTEGRITY_ONLY', build_round='G5', release_ready=False, production_authorized=False,
    code_sha256=code['sha256'], inputs_sha256=baseline['input_manifest']['sha256'], family_sha256=sha(O / 'FAMILY.json'),
    family_baseline_sha256=baseline['family_sha256'], family_changed_fields=fields, metadata_sha256=meta['archive']['sha256'],
    report_sha256=REPORT_SHA256, report_observed_sha256=sha(B.parent / 'report/guard_read.py'), report_pin_matches=True,
    report_source_hashes=report_inputs, report_post_review_change='Operator-authorized final source; see REPORT_PIN_G4.json',
    code_pins_verified=True, input_pins_verified=True, archive_members_verified=True,
    operator_transfer_sha256=sha(O / 'operator/governed_transfer.py'), run_sheet_sha256=sha(O / 'RUN.md'),
    diff_c8r_patch_sha256=sha(O / 'DIFF_C8R.patch'), original_production_inventory_preserved=True,
    rehearsal_and_backup_files_excluded=True, pin_table_rows=len(pins), tests=tests['tests'], tests_status=tests['status'],
    report_mutants=mutants['killed'], real_tensors_validated=False, gpu_parity_validated=False, token_identity_validated=False,
    whole_worker_executed_by_g5=False, whole_worker_scope='Operator-supplied G3 CPU fixture only; current receipt tests use separate phase stand-ins.',
    protected_run_accessed=False, protected_run_writes=False, live_governor_executed=False,
    network_ssh_gpu_git_agents_deletion_used=False)
write(O / 'FINAL_AUDIT.json', audit)
(O / 'GUARD_KIT_READY.md').write_text(f'''# Guard-read kit: G5 sealed; production authority required

The final report pin matches the operator-authorized source. All {tests['tests']} tests pass (`TESTS.json`), and all {mutants['killed']}/{mutants['total']} mutants are detected in a fresh run (`MUTANTS.json`). The report and its test-source hashes are verified before and after validation (`REPORT_PIN_G4.json`).

The production package differs from G4 only in the report pin in `worker.py`. FAMILY differs from `{baseline['family_sha256']}` only in `code_pins.worker.py`; all other fields, including `release_ready: false`, retain their values (`FAMILY_CHANGES_G5.json`). The input archive, production inventory, inherited C8r code and reviewed stager retain their bytes (`G5_SEAL.json`, `SOURCE_IDENTITY.json`, `FINAL_AUDIT.json`).

Every report call binds the candidate artifact. The coordinator retains stage/checker receipts, and return verification rejects missing evidence (`G4_TESTS.json`, `G4_RETURN_EVIDENCE.json`). The C8r diff matches the sealed code (`DIFF_C8R.json`, `DIFF_C8R.patch`). Documented transfers use the registered serial-governor wrapper (`RUN.md`).

The seven trainer-tree names are ACCEPTED by ORCH 1601Z. The CPU-fixture blocker is CLOSED on operator-supplied evidence. Production requires a review bound to the current FAMILY, a completed milestone closure/export and exact ORCH GO (`RELEASE_BLOCKERS.json`).

| Artifact | SHA256 |
|---|---|
| `code_g2.tar` | `{code['sha256']}` |
| `inputs_g2.tar` | `{audit['inputs_sha256']}` |
| `FAMILY.json` | `{audit['family_sha256']}` |
| `candidate_m50/metadata.tar` | `{audit['metadata_sha256']}` |
| Required and observed report | `{REPORT_SHA256}` |

Reproduce with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, `nice -n 10` and numerical-library threads set to one: `work/family.py --g5`, `work/seal.py --g5`, `work/g4_diff.py`, `work/run_g4_tests.py --g5`, then `work/finish.py --g5`.

Not checked: real tensors, GPU parity, token identity, the namespace worker, live Orchard/GCS/pool/credentials or governor transfers. G5 did not access `out/rehearsal/whole/`. Size and timing are recorded in `BUILD_SIZE_G5.json` and `../work/TIMING_G5.json`.
''')
event = B / 'events' / (now.strftime('%Y%m%dT%H%MZ') + '_RESULT_g5.md')
lines = [
    'RESULT: G5 PASS; final report pin and package seal verified; production authority remains required.',
    f"All eight suites pass {tests['tests']} tests (out/TESTS.json); fresh mutants detect {mutants['killed']}/{mutants['total']} (out/MUTANTS.json).",
    f'Required and observed report SHA256: {REPORT_SHA256} (out/REPORT_PIN_G4.json).',
    'The report, test and mutant source hashes match the operator inputs before and after validation (out/REPORT_PIN_G4.json).',
    f"Code SHA256: {code['sha256']} (out/CODE_MANIFEST.json).",
    f"FAMILY SHA256: {audit['family_sha256']} (out/FINAL_AUDIT.json).",
    f"FAMILY baseline SHA256: {baseline['family_sha256']} (work/G5_BASELINE.json).",
    'Only FAMILY field code_pins.worker.py changed; release_ready remains false (out/FAMILY_CHANGES_G5.json).',
    'The production change is solely the report pin; archive inventory and inputs retain their values (out/G5_SEAL.json).',
    'Current-FAMILY review and milestone closure/export/ORCH GO remain required (out/RELEASE_BLOCKERS.json).',
    'The external report and protected rehearsal runs were not modified; protected runs were not accessed (out/FINAL_AUDIT.json).',
    'Not checked: real tensors, GPU parity/token identity, namespace worker or live Orchard/GCS/pool/governor (out/FINAL_AUDIT.json).',
    'Build size and deadline checks pass for the measured scope (out/BUILD_SIZE_G5.json; work/TIMING_G5.json).',
    'The G4 comparison is retained because G5 explicitly requires the FAMILY delta (out/FAMILY_CHANGES_G5.json).',
]
assert len(lines) <= 20
event.write_text('\n'.join(lines) + '\n')
(B / 'STATUS.md').write_text('G5 PASS: final report pin and package seal verified.\n' +
    f"All {tests['tests']} tests pass; fresh mutants detect {mutants['killed']}/{mutants['total']} (out/TESTS.json; out/MUTANTS.json).\n" +
    'Only FAMILY field code_pins.worker.py changed (out/FAMILY_CHANGES_G5.json).\n' +
    'Production authority remains required (out/RELEASE_BLOCKERS.json).\n' +
    'Final result: ' + str(event.relative_to(B)) + '\n')
print(json.dumps(dict(result=str(event.relative_to(B)), status='PASS', code_sha256=code['sha256'], family_sha256=audit['family_sha256'], tests=tests['tests'], mutants=mutants['killed'])))
