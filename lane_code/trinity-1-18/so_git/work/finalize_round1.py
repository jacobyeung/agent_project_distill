"""Write the outcome report and hash manifest from recorded validation evidence."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
EV = OUT / 'evidence'
commands = json.loads((EV / 'round1_commands.json').read_text())
result = json.loads((EV / 'round1_validation_result.json').read_text())
root = Path(result['root'])
assert len(commands) == 29 and all(c['exit_code'] == 0 for c in commands)
when = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
print(when)
size_output = subprocess.check_output(['nice', '-n', '10', 'du', '-sb', str(L)], universal_newlines=True)
usage = shutil.disk_usage(str(L))
resources = dict(utc=when, command=['nice', '-n', '10', 'du', '-sb', str(L)],
                 exact_output=size_output, workspace_bytes=int(size_output.split()[0]),
                 scratch_available_bytes=usage.free)
(EV / 'round1_resources.json').write_text(json.dumps(resources, indent=2) + '\n')

tests = [c for c in commands if c['label'].startswith(('owner_', 'pkg_', 'realgit_runner_'))]
test_counts = {}
for c in tests:
    text = (OUT / c['exact_output']).read_text()
    count, seconds = re.search(r'^Ran (\d+) tests? in ([0-9.]+)s$', text, re.M).groups()
    assert re.search(r'^OK$', text, re.M) and 'skipped' not in text
    test_counts[c['label']] = dict(tests=int(count), seconds=seconds)
unique = set()
for label in ('owner_optional_py312', 'pkg_py312'):
    c = next(c for c in tests if c['label'] == label)
    text = (OUT / c['exact_output']).read_text()
    unique.update(re.findall(r'^([a-z_0-9]+) \(([^)]+)\) \.\.\. ok$', text, re.M))
assert len(unique) == 68
assert sum(v['tests'] for v in test_counts.values()) == 250

rows = [
('1', 'Both tools and all owner/filter/real-Git tests use Python 3.6 APIs; the health path also avoids `is_relative_to`.',
 '`test_shell_wrapper_default_system_python`, `test_dry_count_default_system_python`, and both complete interpreter runs pass.'),
('2', 'The first nonempty line must be an unindented supported `VERDICT:`. Any negative token refuses; a conditional review cannot upgrade itself.',
 '`ReviewTests` covers supported forms, first-line placement, negative text anywhere, conditional/in-file GO, and unknown verdicts.'),
('3', 'A matching Seal/SHA256 or explicit owner `--bind-sha` is required. Required owner arguments supply distinct normalized identities; metadata records the checked binding.',
 '`test_binding_required_and_all_present_fields_must_match`, `test_builder_and_reviewer_must_differ`, and each real-Git probe pass with a first-line-only review.'),
('4', 'Every omitted archive member prints as `SKIPPED`; landing requires `--allow-skips` and records the skipped list. Represented parent directories are preserved.',
 '`test_size_and_name_filter_and_duplicate_paths`, `test_all_filter_exclusions_are_reported_and_require_opt_in`, `test_exact_size_caps_are_inclusive`, and the empty-directory test cover omissions and metadata.'),
('5', 'The guide schedules kit work just after `END ok` and explains the hourly nonblocking lock. Stale events quote the latest hourly lock skip.',
 '`test_stale_event_quotes_hourly_lock_skip` checks the exact skip evidence.'),
('6', 'The journal marks successful delivery and replays only undelivered events. Delivered history does not stat/read event files; legacy journal entries migrate as delivered.',
 '`test_delivered_event_moved_by_consumer_is_not_replayed`, `test_delivered_history_does_not_touch_event_storage`, `test_only_undelivered_events_are_replayed_after_write_error`, and the legacy-journal test pass.'),
('7', 'Package tests use `tempfile.mkdtemp()` outside the checkout, independent of its location. Fixtures remain under the standing no-deletion rule.',
 '`test_default_temp_root_ignores_checkout`, both plain unittest runs, and both byte-for-byte checkout inventories pass.'),
('8', '`DEFAULT_PKG` remains in the process matcher when the epoch override is enabled; existing candidate paths remain in the list.',
 '`test_override_keeps_default_collectors_visible` and `test_override_reaches_process_matcher` pass. Both supplied copies contain only the same 34 lines; no additional callers were supplied.'),
('9', 'The real-Git test moves the tracked kit source away and edits KIT.json before the hourly add. It checks the unstaged kit paths and unchanged committed kits tree.',
 'All six real-Git proofs pass; broad `-A .` would stage the deliberately changed kit paths and fail the test.'),
('10', 'The default owner-lock wait is 600 seconds.',
 '`test_default_lock_wait_is_600_seconds` asserts the timeout passed to the real lock context.'),
('11', 'Every landing Git command disables automatic GC/maintenance. Children receive closed stdin and Git receives `GIT_TERMINAL_PROMPT=0`.',
 '`FakeGit` asserts both config arguments on every command; `test_git_children_cannot_prompt` checks stdin and the environment.'),
('12', 'Production refuses `LCS_FILTER`, `LCS_SCAN`, and `LCS_B` overrides without `LCS_TEST_ROOT`. The new event override is guarded too.',
 '`test_production_tool_overrides_refuse_before_tool_reads` checks each override before any tool resolution.'),
('13', 'dry_count accepts explicit existing folders below `/scratch/jjyeung/orch_n30/`; it refuses symlinked folders/ancestors and the whole orchestration root.',
 '`test_dry_count_refuses_symlinked_and_outside_folders` covers links, ancestor links, `/data2`, `/tmp`, and the root. Valid-folder counts still pass on both interpreters.'),
('14', 'After both heads verify, landing appends `$S/KITS_LANDED.txt` and writes a kit RESULT event. Event timestamps include microseconds to separate receipts.',
 'The landing/idempotence contract and every real-Git proof check both receipts; `test_failed_push_stops_without_retry` checks that a failed push writes neither.'),
('15', 'The loop logs ordinary check errors and continues at the next ten-minute tick. Signal exits stop for investigation under the cluster rule.',
 '`test_transient_error_is_logged_and_next_tick_runs` executes two ticks; `test_signal_exit_stops_without_automatic_rerun` checks the signal exception.'),
('16', 'GIT_OWNER.md states the strict verdict/binding rules, owner identity arguments, clean tracked-worktree requirement, 600-second wait, receipts, and loop behavior. The designated Git owner makes eff/* commits in authorized scratch lane clones under the owner lock.',
 'The applied guide matches out/ byte for byte. Exact command tests and the current real-Git outputs support its operational claims.'),
]

report = '''VERDICT: DONE Findings 1–16 are addressed; fresh patches, owner suites, and real-Git proofs pass under Python 3.6.8 and 3.12.13.

The delivery provides strict archive-bound kit landing, persistent landing receipts, health-event delivery tracking, a resilient health loop, bounded dry counts, and the package override that still detects default collectors. The owner guide names who creates eff/* commits. Production changes remain opt-in.

Validation ran on trinity-1-18. Every Git command targeted newly created throwaway repositories under this workspace's work/ directory; all remotes were local bare repositories. No production repository, network remote, service, or input file was changed. No SSH or GPU/framework computation ran.

## Measured results

| Measurement | Result |
|---|---|
| Unique tests | 68 passed on each interpreter: 58 owner/optional-filter tests, including real Git, plus 10 package tests. |
| Recorded test executions | 250 passed; no final test was skipped. Each interpreter ran patch 02 alone, patches 02+03, the standalone Git runner, and package tests. |
| Interpreter versions | `/usr/bin/python3`: Python 3.6.8; `/scratch/jjyeung/envs/p1cpu/bin/python`: Python 3.12.13. |
| Fresh validation commands | 29 returned zero, including all three patch applications with `--fuzz=0`. |
| Real Git | Six isolated end-to-end runs passed, three per interpreter. Each verified origin and home and preserved HEAD:kits despite unstaged kit edits/removal. |
| Frozen coverage | The 44-file snapshot selects 39 files / 105362 bytes by default and 41 files / 120931 bytes with optional shell copies. Default combined filter output matches the input byte for byte. |
| Package checkout | Both plain unittest runs left its file names and bytes unchanged. |
| Workspace snapshot | WORKSPACE_BYTES bytes before report generation; SCRATCH_BYTES bytes available on local scratch. [Exact measurement](evidence/round1_resources.json). |

These are measured values. No throughput or time-saving estimate is claimed. The configured monitor interval is 600 seconds and its stale threshold is 90 minutes; detection delay depends on a running loop and available local/event storage.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
'''.replace('WORKSPACE_BYTES', str(resources['workspace_bytes'])).replace('SCRATCH_BYTES', str(resources['scratch_available_bytes']))
for row in rows:
    report += '| ' + ' | '.join(row) + ' |\n'

report += '''
## Patches and owner handoff

| Patch | Contents and enablement |
|---|---|
| [01_pkg_configurable.diff](patches/01_pkg_configurable.diff) | Applies to the distill tree. `R1315_PKG=/absolute/epoch/collector` enables the override; unset keeps the current default without new validation I/O. An override must contain collect.py. The test installs at the checkout root for plain `python3 -m unittest`. |
| [02_owner_tools.diff](patches/02_owner_tools.diff) | Adds tools, owner tests, fixtures, and the [owner guide](GIT_OWNER.md). Commands require `LCS_ENABLE_KIT_LANDING=1`, `LCS_ENABLE_SYNC_HEALTH=1`, or `LCS_ENABLE_DRY_COUNT=1`; all default OFF. Existing hourly sync/filter/scanner inputs remain unchanged. |
| [03_shell_copy_coverage_optional.diff](patches/03_shell_copy_coverage_optional.diff) | Adds only `.sh.copy` behind `LCS_INCLUDE_SHELL_COPIES=1`, default OFF. Its tests support both interpreters. It changes neither caps nor directory rules. |

[MANIFEST.json](MANIFEST.json) records patch/input/delivery hashes and validation status. The patch-applied tools, tests, and docs match out/ exactly: [source check](evidence/round1_source_equivalence.txt). The selected production epoch path is `/home/jjyeung/agent_project_distill_epochs/<commit>/collector`; this delivery launches no collector.

Package tests retain temporary fixtures because the standing rule forbids deletion. Their default uses system temporary storage; these recorded runs set TMPDIR outside the checkout under work/ to confine all test writes. No cleanup command is needed to use the patches.

## Exact commands and outputs

The full command ledger records UTC time, argv, cwd, environment, exit code, and each exact combined stdout/stderr file: [round1_commands.json](evidence/round1_commands.json). The serial driver is `work/validate_round1.py`; the generator is `work/regenerate_round1.py`. It uses CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE=1, eight-thread limits, and niceness 10 or lower priority. No torch behavior is involved.

Fresh validation root: `VALIDATION_ROOT`.

'''.replace('VALIDATION_ROOT', str(root))

report += '| Command group | Exact output |\n|---|---|\n'
for c in commands:
    report += '| `' + c['label'] + '` | [' + c['exact_output'].split('/')[-1] + '](' + c['exact_output'] + ') |\n'

# Keep the complete principal test and real-Git outputs in the report itself.
for label in ('patch_apply_01', 'patch_apply_02', 'patch_apply_03',
              'pkg_py36', 'pkg_py312', 'owner_py36', 'owner_py312',
              'owner_optional_py36', 'owner_optional_py312',
              'realgit_runner_py36', 'realgit_runner_py312'):
    c = next(c for c in commands if c['label'] == label)
    report += '\n### ' + label + '\n\n'
    report += 'UTC: ' + c['utc'] + '. Exit code: 0.\n\n```bash\n'
    report += 'cd ' + shlex.quote(c['cwd']) + '\n'
    assignments = [k + '=' + shlex.quote(v) for k, v in c['environment'].items()]
    report += 'env ' + ' '.join(assignments) + ' ' + ' '.join(shlex.quote(x) for x in c['argv']) + '\n```\n\n'
    report += 'Exact combined stdout/stderr:\n\n```text\n' + (OUT / c['exact_output']).read_text() + '```\n'

report += '''
## Limits and remaining owner actions

- The owner still installs/enables the selected tools on trinity-3-30 and checks actual lane folders before expanding coverage. No trinity-3-30 session or production remote was tested here. The supplied mirror cannot establish actual sb/so inventories.
- The hourly nonblocking lock can skip a run while a kit holds it. The guide recommends landing after END ok, and stale alerts include lock-skip evidence. The kit wait itself defaults to 600 seconds.
- Pushes to two remotes and receipt writes are separate operations. A later failure can leave one or both remotes published; the command refuses, and the owner inspects the audit directory before an authorized identical rerun. Killed work is never automatically restarted.
- Delivered health events stay delivered when consumers move them. If a process dies after writing an event but before saving its delivery acknowledgement, an undelivered journal entry can replay; moving the event during that narrow interruption window can duplicate delivery. Legacy string journal entries migrate as delivered to avoid resurrecting old incidents.
- Ordinary monitoring errors remain in local health.log and the loop continues. Signal exits stop the loop for investigation. Missing/truncated logs can conservatively report stale; the reader bounds log input at 8 MiB.
- Audit directories and temporary test fixtures consume scratch and are retained under the no-deletion rule. The measured workspace remains below the 3 GB cap.
- Only the supplied 34-line recovery script and its identical mirrored copy were available. Tests cover both configured and default collector matches; no unsupplied continuation is claimed.

All requested fixes and local validation are complete. Production installation, remote publication, live-node smoke checks, and real lane inventory counts remain owner actions outside this workspace task.

The no-archaeology and summary skills govern this report. The requested review mapping is retained because it connects each finding to its fix and test; no superseded behavior is presented as current.
'''
report += '\nReport time: ' + when + '. Deadline: 2026-11-19 09:40Z.\n'
(OUT / 'REPORT.md').write_text(report)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

old = json.loads((OUT / 'MANIFEST.json').read_text())
input_hashes = {name: digest(L / 'in' / name) for name in old['input_sha256']}
assert input_hashes == old['input_sha256'], 'an input changed'
manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                input_sha256=input_hashes,
                review_verdict=dict(path='/scratch/jjyeung/orch_n30/so_cr_git/REVIEW_VERDICT.md',
                                    sha256=digest(Path('/scratch/jjyeung/orch_n30/so_cr_git/REVIEW_VERDICT.md'))),
                patches={p.name: dict(bytes=p.stat().st_size, sha256=digest(p))
                         for p in sorted((OUT / 'patches').iterdir()) if p.is_file()},
                defaults=dict(LCS_ENABLE_KIT_LANDING='OFF', LCS_ENABLE_SYNC_HEALTH='OFF',
                              LCS_ENABLE_DRY_COUNT='OFF', LCS_INCLUDE_SHELL_COPIES='OFF',
                              R1315_PKG='unset: preserve current literal default', LCS_LOCK_TIMEOUT='600'),
                real_git_executed=True, production_deployed=False,
                validated_host='trinity-1-18', interpreters={'py36': '/usr/bin/python3 (3.6.8)',
                    'py312': '/scratch/jjyeung/envs/p1cpu/bin/python (3.12.13)'},
                validation=result, test_results=test_counts, unique_tests_per_interpreter=68,
                final_test_executions=250, final_skipped_tests=0,
                artifacts={str(p.relative_to(OUT)): dict(bytes=p.stat().st_size, sha256=digest(p))
                           for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'})
(OUT / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(datetime.now(timezone.utc).isoformat() +
    ': DONE. Findings 1–16 fixed. Fresh patches and 250 test executions passed across Python 3.6.8/3.12.13; six local real-Git proofs passed. Report, exact evidence, and MANIFEST regenerated. No production deployment.\n')
print('Wrote REPORT.md and MANIFEST.json; 68 unique tests, 250 passing executions, zero final skips.')
