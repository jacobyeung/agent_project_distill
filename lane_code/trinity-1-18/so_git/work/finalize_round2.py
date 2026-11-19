"""Write the final evidence-based report and manifest; never execute Git."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
EVIDENCE = OUT / 'evidence'
commands = json.loads((EVIDENCE / 'round2_commands.json').read_text())
validation = json.loads((EVIDENCE / 'round2_validation_result.json').read_text())
assert validation['all_expected_exits'] and validation['git_invocations'] == 0
assert len(commands) == validation['commands']
assert all(c['exit_code'] == c['expected_exit_code'] for c in commands)
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())
changes = json.loads((OUT / 'INSTALLED_CHANGES.json').read_text())
rows = json.loads((L / 'work/round2_findings.json').read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
print(now, flush=True)
input_hashes = json.loads((L / 'work/review_round2_base/MANIFEST.json').read_text())['input_sha256']
assert {n: digest(L / 'in' / n) for n in input_hashes} == input_hashes
installed_pins = json.loads((EVIDENCE / 'round2_installed_base.json').read_text())
for path, record in installed_pins.items():
    assert digest(Path(path)) == record['sha256'], 'installed file changed: ' + path
(EVIDENCE / 'round2_readonly_verification.txt').write_text(
    'INPUT_HASHES_UNCHANGED true\nINSTALLED_OWNER_FILES_UNCHANGED 7\nINSTALLED_HOURLY_UNCHANGED true\n')

# One local metadata-only inventory; no symlink traversal or file-content reads.
workspace_bytes = 0
workspace_files = 0
for parent, dirs, files in os.walk(str(L), followlinks=False):
    for name in files:
        info = os.lstat(os.path.join(parent, name))
        workspace_bytes += info.st_size
        workspace_files += 1
        assert workspace_files < 300000, 'bounded workspace inventory exceeded 300000 files'
disk = os.statvfs(str(L))
resources = dict(utc=now, measured_workspace_bytes=workspace_bytes, measured_workspace_files=workspace_files,
                 measured_scratch_available_bytes=disk.f_bavail * disk.f_frsize,
                 scope='One local metadata inventory before final report/manifest writes; symlinks not followed.',
                 memory_peak='not measured', configured_memory_limit_bytes=30000000000,
                 configured_thread_limit=8, torch_used=False)
assert workspace_bytes < 3000000000
assert resources['measured_scratch_available_bytes'] > 200000000000
(EVIDENCE / 'round2_resources.json').write_text(json.dumps(resources, indent=2) + '\n')

test_results = {}
for command in commands:
    output = (OUT / command['exact_output']).read_text()
    match = re.search(r'^Ran (\d+) tests? in ([0-9.]+)s$', output, re.M)
    if match:
        assert re.search(r'^OK(?: \(skipped=\d+\))?$', output, re.M)
        skip = re.search(r'^OK \(skipped=(\d+)\)$', output, re.M)
        skipped = int(skip[1]) if skip else 0
        test_results[command['label']] = dict(run=int(match[1]), passed=int(match[1]) - skipped,
                                             skipped=skipped, seconds=float(match[2]))
passes = sum(r['passed'] for r in test_results.values())
skips = sum(r['skipped'] for r in test_results.values())
unique = set()
for label in ('owner_optional_enabled_py312', 'pkg_py312'):
    c = next(c for c in commands if c['label'] == label)
    unique.update(re.findall(r'^(test_\w+) \(([^)]+)\) \.\.\. ok$', (OUT / c['exact_output']).read_text(), re.M))
assert len(unique) == test_results['owner_optional_enabled_py312']['passed'] + test_results['pkg_py312']['passed']

regression_evidence = {}
for mode in ('base', 'source'):
    for tag in ('py36', 'py312'):
        record = json.loads((EVIDENCE / ('round2_regressions_' + mode + '_' + tag + '.json')).read_text())
        output = (OUT / record['exact_output']).read_text()
        assert record['exit_code'] == (1 if mode == 'base' else 0)
        if mode == 'source':
            assert re.search(r'^Ran 26 tests in ', output, re.M) and re.search(r'^OK$', output, re.M)
        regression_evidence[mode + '_' + tag] = record

report = f'''VERDICT: PARTIAL Findings 1–9 are addressed behind a default-OFF switch; all permitted tests pass, but this dispatch forbids the required real-Git reruns.

The fixed files are in `out/tools/`. Exactly three installed files change: `land_kit.py`,
`sync_health.py`, and `dry_count.py`. Enable the fixes with `LCS_REVIEW2_FIXES=1` alongside
the relevant `LCS_ENABLE_*` flag. The installed copies and `lane_code_sync.sh` remain unchanged.
Finding 1 uses the review's minimal STOP-and-contact-the-user mitigation; it does not prevent
a rejected commit from remaining on local lane-code. Finding 2 clears kit staging on a handled
failure and verifies a clean index, without rewriting history or deleting working files.

## Numbers

All results below are measured unless identified as configuration. No performance estimate is claimed.

| Measurement | Result |
|---|---|
| Unique passing tests per interpreter | {len(unique)} after patches 01–03, including 26 round-2 tests; one real-Git test is skipped. |
| Fresh-patch test executions | {passes} pass; {skips} skips across repeated configurations. Patch-02-only runs skip the two tests supplied by optional patch 03, as well as real Git. Combined runs skip only real Git. |
| Regression contrast | The same 26-test suite fails on the pinned installed source on both interpreters, then passes on both fixed working copies and both fresh upgrade trees. Exact failure and success outputs are linked below. |
| Fresh validation commands | {len(commands)} return their expected status; the two disabled real-Git runners intentionally return 2. Other commands return 0. |
| Python versions | Python 3.6.8 and Python 3.12.13, read from the executed interpreters. |
| Frozen coverage | 39 files / 105362 bytes by default; 41 files / 120931 bytes with optional shell copies. Original/default filter output is byte-identical. |
| Workspace before final report | {workspace_bytes} bytes in {workspace_files} local entries; {resources['measured_scratch_available_bytes']} bytes free on scratch. This includes retained fixtures. |
| Limits (configuration) | Eight-thread environment limits; no CUDA devices; niceness 10 or lower priority; workspace cap 3 GB and memory cap 30 GB. Memory peak was not measured. |
| Production access | Eight named files read and hashed: seven owner tools and the hourly script. No installed writes, live Git, SSH, service changes, or model calls. |

Validation ran on trinity-1-18. Start: 2026-11-19 10:08:40 UTC. Deadline: 2026-11-19 12:08:40 UTC.
Report time: {now}. These are stdlib tools/tests; no torch or other framework behavior is used.

## Review round 2: finding -> fix -> test

| Finding | Fix or decision | Test |
|---|---|---|
'''
for row in rows:
    report += '| ' + ' | '.join(row) + ' |\n'
report += '''
## Installed replacements

The base hashes were read from the installed files and match the reviewed delivery exactly.
The final read-only check confirms that the installed files still have those base hashes.
Paths and both hashes are recorded in [INSTALLED_CHANGES.json](INSTALLED_CHANGES.json).

| Installed file under `orch_n30/tools/` | New SHA256 |
|---|---|
'''
for record in changes['changes']:
    report += '| [' + Path(record['installed_path']).name + '](' + record['delivery_path'] + ') | `' + record['new_sha256'] + '` |\n'
report += '''
The unchanged files are `land_kit.sh`, `sync_health.sh`, `sync_health_loop.sh`, `dry_count.sh`,
and `lane_code_sync.sh`. The hourly script is not delivered as a changed production file.
The four owner wrappers in `out/tools/` remain byte-identical to their installed copies.
No deployment was performed. [HANDOVER.md](HANDOVER.md) identifies the remaining owner actions;
[GIT_OWNER.md](GIT_OWNER.md) explains operation and recovery.

## Patches and base pins

Patches 01–03 apply to fresh copies of the named supplied inputs. Patch 04 is an alternative
upgrade from the pinned reviewed package, including its tests/docs; do not apply it after the
regenerated 02/03. Every patch was applied with `patch --batch --fuzz=0 -p1` after checking
each preimage. Both owner package routes reproduce the delivered tools, tests, and guides exactly.

Base pins are per-file SHA256 values plus a deterministic hash of each patch's preimage map.
Absent files are recorded as null. No Git commit ID is claimed or queried.
[PATCH_BASES.json](PATCH_BASES.json) contains every preimage/postimage and the pin calculation;
[MANIFEST.json](MANIFEST.json) hashes the delivery and records current validation status.

| Patch | Switch and scope | SHA256 | Base pin SHA256 |
|---|---|---|---|
'''
descriptions = {
    '01': '`R1315_PKG`, unset preserves the supplied default; package tests included.',
    '02': '`LCS_ENABLE_*` and `LCS_REVIEW2_FIXES`, default OFF; cumulative tools/tests/guides.',
    '03': '`LCS_INCLUDE_SHELL_COPIES`, default OFF; optional filter and tests.',
    '04': '`LCS_REVIEW2_FIXES`, default OFF; alternative installed-package upgrade and tests.'}
for name, record in sorted(pins.items()):
    assert digest(OUT / 'patches' / name) == record['patch_sha256']
    report += '| [' + name + '](patches/' + name + ') | ' + descriptions[name[:2]] + ' | `' + record['patch_sha256'] + '` | `' + record['base_pin_sha256'] + '` |\n'
report += '''
Default-OFF production branches retain the installed behavior. Default and enabled owner suites
both pass; the optional filter's default output matches the supplied filter byte for byte.
The input files, hourly fixture, wrappers, package source/test, and unchanged production files
are pinned separately. New production behavior requires the explicit switch. Test-root safety
changes apply unconditionally to tests so an ordinary test import cannot seed the installed tree.

## Exact commands and outputs

The serial drivers are `work/run_round2_regressions.py` and `work/validate_round2.py`.
The complete [command ledger](evidence/round2_commands.json) gives UTC time from `date -u`,
argv, working directory, relevant environment, expected/actual exit status, and exact combined
stdout/stderr for every command. Test runs set `LCS_TEST_WORK` and `TMPDIR` under this workspace.
`LCS_RUN_REAL_GIT_TESTS=0` prevents Git integration, and a PATH guard records unexpected Git
attempts; none occurred. No result from an earlier real-Git run is used as current proof.

The test command for each interpreter is `nice -n 10 <python> -I -s -B -m unittest discover
-s tests -v`, with default/enabled switch values recorded in the ledger. Package tests use
`nice -n 10 <python> -I -s -B -m unittest -v`. The upgrade regression command adds
`-p test_review_round2.py`. The same regression command runs against the pinned base for the
failure demonstration. Each command uses the corresponding fresh patch tree as its cwd.

| Regression run | Exit | Exact combined output | Exact argv/environment |
|---|---|---|---|
'''
for label, record in regression_evidence.items():
    stem = 'evidence/round2_regressions_' + label
    report += '| ' + label + ' | ' + str(record['exit_code']) + ' | [output](' + stem + '.txt) | [command](' + stem + '.json) |\n'
report += '\nFresh validation root: `' + validation['root'] + '`.\n\n'
report += '| Command/check | Exit | Exact output |\n|---|---|---|\n'
for command in commands:
    report += '| `' + command['label'] + '` | ' + str(command['exit_code']) + ' | [output](' + command['exact_output'] + ') |\n'
report += '''
The exact unittest summary lines below are excerpts; each linked output above retains the
full test-by-test output without truncation.

'''
for label in test_results:
    command = next(c for c in commands if c['label'] == label)
    raw = (OUT / command['exact_output']).read_text()
    summary = re.search(r'^Ran \d+ tests? in [0-9.]+s\n\nOK[^\n]*', raw, re.M)[0]
    report += '`' + label + '`:\n\n```text\n' + summary + '\n```\n\n'
report += '''## Verification of fixes relied on from round 1

The existing tests recheck Python 3.6 APIs, strict first-line verdicts, independent identities,
archive binding, every filter omission, exact size caps, deduplication, secret scanning, scanner
omissions, malicious archive paths/types, metadata, flock wait/acquisition, the 600-second default,
maintenance/prompt flags, inherited Git selectors, dirty-index refusals, both remote verifications,
receipts, persistent health delivery and replay, legacy state migration, lock-skip evidence,
coverage rules, and health-loop error/signal handling. Package tests recheck override validation,
the unchanged default, default collectors under an override, and checkout cleanliness.
The declared hourly add pathspec is checked against the unchanged fixture.

These tests use real filesystem/filter/scanner/lock behavior and a command double for Git.
Actual Git index semantics, remote publication, commit metadata, and the hourly committed-kits
tree proof require the real-Git test; those claims are not reverified under this dispatch.

## What could go wrong and how to notice

- An origin content rejection still strands a local commit. The new STOP refusal includes its
  SHA and requires the user before the hourly can repeat the failure and advance home. The tool
  neither stops the hourly nor rewrites history. This deliberately implements the review's
  minimal mitigation rather than the optional commit-tree redesign.
- Index cleanup can fail, or a killed process can bypass cleanup. The handled failure prints
  STOP and requires the user before the next hourly. A normal cleanup failure must never be
  treated as a successful landing. There is no receipt until both remotes verify.
- A timeout can occur after a commit or push completed. The owner must inspect HEAD and remotes
  before moving any working directory or repeating an operation. No retry runs in the tool.
- The Python 3.6 timeout handler kills only its immediate child and calls `communicate()` without
  another timeout (`/usr/lib64/python3.6/subprocess.py:426–428`, read directly in this round).
  A surviving grandchild holding pipes can hold the owner lock longer than 300 seconds. Repeated
  hourly lock-skip messages or a stale event expose the symptom; this case remains unresolved.
- A consumer that moves the hourly BLOCKER before health first observes it can still cause a
  duplicate health BLOCKER. After the first decision, the recorded run key prevents rescanning
  or duplication. The hourly script is unchanged, so this earlier window cannot be closed by
  writing its own delivery journal here.
- A process crash between writing an event and saving its delivery acknowledgement can still
  replay an undelivered event. Delivered entries are not reread or recreated after consumers move them.
- With `LCS_REVIEW2_FIXES` unset, installed behavior remains active, including the reported issues.
  The owner must set the switch for each tool and the loop environment. The owning orchestrator
  controls loop restarts. This task did not stop or replace any running service.
- Audit and test fixtures remain on scratch under the no-deletion rule. The local size measurement
  remains below 3 GB. Actual sb/so lane inventories and remote-stage shell-copy opt-in are not
  established by the supplied mirror; the owner must check actual local lane folders.

## What is not done

The required current-tool real-Git reruns, including finding 11 and the real index/tree/remote
proofs in the report, are not executed because the current dispatch explicitly says “No git”.
That ruling controls this round; the earlier fix-round exception is not reused. The disabled
runner is checked and its exact refusal is recorded. This is why the verdict is PARTIAL.

The optional commit-tree redesign for finding 1 and the process-tree timeout redesign in
finding 12 are not implemented. The report and handover state their remaining risks. No other
LOW finding is deferred. Production installation, loop activation, live-node smoke tests and
remote publication are owner actions outside this read-only production scope.

The no-archaeology and summary skills guide this report. The requested finding mapping and
before/after regression evidence are retained because they establish what each fix proves.
Internal operational details are included because this is the requested owner handover.
'''
(OUT / 'REPORT.md').write_text(report)

manifest = dict(created_utc=now, verdict='PARTIAL', input_sha256=input_hashes,
    review_verdict=dict(path='/scratch/jjyeung/orch_n30/so_cr_git2/REVIEW_VERDICT.md',
                        sha256=digest(Path('/scratch/jjyeung/orch_n30/so_cr_git2/REVIEW_VERDICT.md'))),
    patches={name: dict(sha256=record['patch_sha256'], base_pin_sha256=record['base_pin_sha256'],
                       bytes=(OUT / 'patches' / name).stat().st_size) for name, record in pins.items()},
    base_pin_format='SHA256 of sorted compact JSON mapping patch paths to preimage SHA256 or null',
    installed_changes=changes, installed_copies_modified=False, real_git_executed=False,
    production_deployed=False, live_services_modified=False, validation=validation,
    test_results=test_results, final_fresh_patch_passed_executions=passes,
    final_fresh_patch_skipped_executions=skips, unique_passing_tests_per_interpreter=len(unique),
    before_after_regressions=regression_evidence,
    defaults=dict(LCS_REVIEW2_FIXES='OFF', LCS_ENABLE_KIT_LANDING='OFF', LCS_ENABLE_SYNC_HEALTH='OFF',
        LCS_ENABLE_DRY_COUNT='OFF', LCS_INCLUDE_SHELL_COPIES='OFF', LCS_LOCK_TIMEOUT='600',
        R1315_PKG='unset preserves supplied default'),
    resources=resources, current_evidence_prefix='evidence/round2_',
    retained_evidence_note='Other evidence files are retained from supplied delivery and are not current validation.',
    artifacts={str(p.relative_to(OUT)): dict(bytes=p.stat().st_size, sha256=digest(p))
               for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'})
(OUT / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(now + ': PARTIAL delivery complete. Findings 1–9 addressed; 10 and small error cases in 12 addressed. '
    + str(len(unique)) + ' unique permitted tests pass per interpreter; ' + str(passes) + ' fresh-patch passes, '
    + str(skips) + ' explicitly explained skips. Four patches and base pins verified; exactly three installed tool changes listed. '
    'Installed files/hourly unchanged. Real-Git reruns and subprocess-grandchild timeout repair remain uncompleted; see out/REPORT.md.\n')
print('REPORT_AND_MANIFEST_WRITTEN', json.dumps(dict(unique_passes_per_interpreter=len(unique),
      fresh_patch_passes=passes, skipped_executions=skips, workspace_bytes=workspace_bytes)))
