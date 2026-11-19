"""Write the review report and hash manifest from recorded evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
OUT = L / 'out'
commands = json.loads((OUT / 'evidence/round3_commands.json').read_text())
final_commands = json.loads((OUT / 'evidence/round3_final_commands.json').read_text())
validation = json.loads((OUT / 'evidence/round3_validation_result.json').read_text())
final = json.loads((OUT / 'evidence/round3_final_result.json').read_text())
resources = json.loads((OUT / 'evidence/round3_resources.json').read_text())
installed = json.loads((OUT / 'INSTALLED_CHANGES.json').read_text())
pins = json.loads((OUT / 'PATCH_BASES.json').read_text())
findings = json.loads((L / 'work/round3_findings.json').read_text())
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()

def summary(row):
    raw = (OUT / row['exact_output']).read_text()
    match = re.search(r'Ran (\d+) tests? in .*\n\nOK(?: \(skipped=(\d+)\))?', raw)
    return (int(match[1]), int(match[2] or 0)) if match else None

totals = [summary(row) for row in commands if summary(row)]
passed = sum(n - skipped for n, skipped in totals)
skipped = sum(s for n, s in totals)
by_label = {row['label']: row for row in commands}
unique = sum(n - skip for n, skip in (summary(by_label['pkg_py36']),
                                     summary(by_label['owner_optional_enabled_py36'])))
report = '''VERDICT: DONE Findings 1–5 are fixed and all permitted suites pass on both Python versions; the real-Git failure cases are delivered for the authorized lane.

The replacements are in `out/tools/` and require `LCS_REVIEW2_FIXES=1`, default OFF.
Exactly three installed files change: `land_kit.py`, `sync_health.py`, and `dry_count.py`.
The installed files and hourly `lane_code_sync.sh` were read-only throughout this task.
No Git, SSH, deployment, service stop, GPU work, or model API call ran.

## Numbers

All test and byte counts below are measured. Resource caps and switch defaults are configuration,
not measurements. No estimated performance result is claimed.

| Measurement | Result |
|---|---|
| Unique permitted tests per interpreter | ''' + str(unique) + ''' pass: owner/filter suites plus package-path tests. |
| Full owner suite | 98 tests under each interpreter and switch setting: 95 pass, 3 real-Git tests skip. |
| Core owner suite without optional patch 03 | 96 tests: 91 pass, 5 skip (3 real-Git cases and 2 optional-filter checks). |
| Fresh-patch successful test executions | ''' + str(passed) + ''' pass; ''' + str(skipped) + ''' skips across the recorded configurations. |
| Round-3 regression contrast | Same 12 tests on both interpreters: frozen pre-fix tools produce 28 failing assertions and 9 errors; fixed tools pass all 12. Subtests account for multiple failures per test. |
| Switch-off differential | 2079 generated review inputs and 7 existing root-gate folders per interpreter; 0 differences from pinned installed behavior. |
| Validation commands | ''' + str(len(commands)) + ''' expected exits; disabled real-Git runners return 2, all others return 0. Final packaging adds ''' + str(len(final_commands)) + ''' successful checks. |
| Interpreters | Python 3.6.8 and Python 3.12.13, read from the executed binaries. |
| Frozen coverage | Default: 39 files / 105362 bytes; shell-copy opt-in: 41 files / 120931 bytes. Original/default filter output is byte-identical. |
| Local workspace inventory | ''' + str(resources['measured_workspace_bytes']) + ''' bytes across ''' + str(resources['measured_workspace_entries']) + ''' entries before final report/manifest writes; below the configured 3 GB cap. |
| Scratch free space | ''' + str(resources['measured_scratch_available_bytes']) + ''' bytes at that inventory. |
| Load configuration | Niceness 10; eight-thread environment limits; no CUDA devices. Memory peak was not measured; configured cap is 30 GB. |

Host: trinity-1-18. First recorded task time: 2026-11-19 11:42:16 UTC.
Report time: ''' + now + '''. These tools and tests use the standard library; no torch or framework behavior is relied on.

## Review round 3: finding -> fix -> test

| Finding | Fix | Regression or remaining check |
|---|---|---|
'''
report += ''.join('| ' + ' | '.join(row) + ' |\n' for row in findings)
report += '''
The round-1 `REJECTED` test again refuses under both switch settings. Its reviewed lowercase-prose
exceptions remain; no test permits uppercase `REJECTED`, `REJECTION`, or `NO-GOOD`.
All production fixes fit below about 30 added lines per finding and reuse the explicit switch.
No finding from 1–5 is deferred. Finding 3's Git-dependent execution is assigned to the lane,
as required by this dispatch; the disabled-runner regression proves only logging and guarding.

INFO 6 is addressed in `GIT_OWNER.md`: verdict/binding formats, nested coverage and health-loop
reload behavior match the code. INFO 7's installation note uses temporary files plus atomic rename.
The unconditional `lzma` import remains: both tested interpreters provide it, and removing that
dependency is outside the requested findings. Other production interpreters still need `_lzma`.

## Installed replacements

The following filenames are under
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/`.
[INSTALLED_CHANGES.json](INSTALLED_CHANGES.json) records full paths and both hashes.
Eight named installed files were hashed before and after validation; all retain their pinned base bytes.

| Installed file | New SHA256 |
|---|---|
'''
for row in installed['changes']:
    report += '| [' + Path(row['installed_path']).name + '](' + row['delivery_path'] + ') | `' + row['new_sha256'] + '` |\n'
report += '''
The four shell wrappers and hourly script are unchanged. `sync_health.py` includes the required
round-2 fixes already in the reviewed delivery; this round changes its tests/docs, not its bytes.
Only the owner installs the replacements. Stage each file in its destination directory and rename
it atomically. Replacement Python files load on the next health tick; changing the loop's switch
requires its owning orchestrator to restart the environment. No restart was performed here.

## Patches, base pins and validation

Patches 01–03 build from the supplied inputs. Patch 04 independently upgrades the pinned installed
package and its tests/docs. Patch 05 independently upgrades the frozen reviewed round-2 delivery.
Choose one owner route; do not apply 04 or 05 after cumulative patch 02.
Every patch contains its relevant tests and applies with `patch --batch --fuzz=0 -p1`.
[PATCH_BASES.json](PATCH_BASES.json) records absent paths, every preimage/postimage SHA256,
and the SHA256 of the sorted compact JSON preimage map. No Git base ID is claimed.

| Patch | Validation | Patch SHA256 | Base pin SHA256 |
|---|---|---|---|
'''
tests = {'01': 'Package suite on both interpreters', '02': 'Full core suite, switch off/on, both interpreters',
         '03': 'Full optional suite, switch off/on, both interpreters',
         '04': 'Round-2 and round-3 regressions, both interpreters',
         '05': 'Round-3 regressions, both interpreters'}
for name, record in pins.items():
    report += '| [' + name + '](patches/' + name + ') | ' + tests[name[:2]] + ' | `' + record['patch_sha256'] + '` | `' + record['base_pin_sha256'] + '` |\n'
report += '''
Final patch applications verify every current payload against `out/`. The delivered tools/tests
and the lane's source tree match the fully tested tree byte for byte; the final packaging checks
also cover the complete current docs. See [final verification](evidence/round3_final_result.json)
and [lane source hashes](evidence/round3_lane_source_hashes.json).

The default production branches retain pinned installed behavior. The shell-copy filter switch
and `R1315_PKG` package override also remain default OFF/unset. Raw inputs are unmodified.

## Exact commands and outputs

The full [command ledger](evidence/round3_commands.json) records each argv, cwd, UTC timestamp,
relevant environment and exit code. [Final commands](evidence/round3_final_commands.json) record
the current patch applications, switch-off comparisons and lane-command syntax check.
The serial drivers are `work/run_round3_regressions.py`, `work/validate_round3.py`, and
`work/final_check_round3.py`. All writes use this workspace. `LCS_RUN_REAL_GIT_TESTS=0`
and a PATH guard prevent accidental Git; the guard recorded zero attempts.

For each `/usr/bin/python3` and `/scratch/jjyeung/envs/p1cpu/bin/python`, suite commands are:

```text
nice -n 10 <python> -I -s -B -m unittest -v
nice -n 10 <python> -I -s -B -m unittest discover -s tests -v
nice -n 10 <python> -I -s -B -m unittest discover -s tests -p test_review_round2.py -v
nice -n 10 <python> -I -s -B -m unittest discover -s tests -p test_review_round3.py -v
```

The package command runs in the fresh distill tree. Owner commands run in the fresh owner or
upgrade tree with `LCS_TEST_WORK` and `TMPDIR` under this workspace. Default runs set
`LCS_REVIEW2_FIXES=0`; enabled runs set it to `1`. Switch-unset differential checks remove it.
The exact paths and environments are in the ledgers. Full validation tree:
`''' + validation['root'] + '''`.

| Regression contrast | Exit | Exact output | Exact argv/environment |
|---|---|---|---|
'''
for mode in ('before', 'after'):
    for tag in ('py36', 'py312'):
        name = 'round3_regressions_' + mode + '_' + tag
        row = json.loads((OUT / 'evidence' / (name + '.json')).read_text())
        report += '| ' + mode + '_' + tag + ' | ' + str(row['exit_code']) + ' | [output](' + row['exact_output'] + ') | [command](evidence/' + name + '.json) |\n'
report += '\n| Validation command | Exit | Exact output |\n|---|---|---|\n'
for row in commands + final_commands:
    report += '| `' + row['label'] + '` | ' + str(row['exit_code']) + ' | [output](' + row['exact_output'] + ') |\n'
report += '\nExact unittest summary excerpts (full outputs are linked above):\n'
for label in ('pkg_py36', 'pkg_py312', 'owner_optional_default_py36', 'owner_optional_enabled_py36',
              'owner_optional_default_py312', 'owner_optional_enabled_py312',
              'incremental_regressions_py36', 'incremental_regressions_py312'):
    raw = (OUT / by_label[label]['exact_output']).read_text()
    report += '\n`' + label + '`\n\n```text\n' + '\n'.join(raw.splitlines()[-4:]) + '\n```\n'

report += '''
## Exact real-Git command for the lane

This command is delivered, not executed by this agent. The authorized lane runs it serially
under both interpreters. The source tree is pinned in `evidence/round3_lane_source_hashes.json`
and matches the tested delivery; each case creates new local bare remotes and its own clone.

```bash
''' + (L / 'work/round3_lane_command.txt').read_text() + '''```

Expect `LCS_REVIEW2_FIXES=1`, three tests, zero skips, and `OK` under each interpreter.
The hook cases assert a clean index, unchanged HEAD and an untracked kit after commit failure;
the rerun must refuse as not fully tracked. Origin rejection must print STOP, preserve both
remote refs, and leave no landing receipt or RESULT event. No killed work is automatically retried.

The coordinator's supplied logs at
`work/realgit3_by_swarm_opt/run_py36.txt` and `run_py312.txt` record one successful real-Git
happy-path test each at 2026-11-19T10:59:42Z, including matching remote refs and hourly kit-tree
preservation. They do not record the switch value and do not exercise either failure hook.
They therefore do not validate the new failure cases or this final delivery.

## Review round 2: finding -> fix -> test

The current mapping is included because the binding fix-round prompt requires it.
'''
handover = (OUT / 'HANDOVER.md').read_text()
report += handover.split('## Review round 2: finding -> fix -> test\n', 1)[1].split('## Remaining limits', 1)[0]
report += '''
## What could go wrong and how we would notice

- An origin refusal leaves the local commit intact. STOP requires the user before the hourly
  can repeat the failure and advance home. The tool does not stop the hourly or rewrite history.
- A handled commit failure clears only the kit's index paths. A killed process or failed cleanup
  can still leave staging; its STOP/refusal requires user intervention before the hourly.
- The new real-Git hook cases are unexecuted here. Their absence is visible as three skipped
  real-Git tests; the authorized lane must obtain zero skips before treating them as verified.
- Test-mode remote checks reject protocol URLs and paths outside the boundary, including extra
  push URLs and symlink escapes. A refusal occurs before clone mutation; `--dry` still uses no Git.
- A review whose hash format lies outside the documented grammar still relies on the owner's
  explicit `--bind-sha` attestation. The owner must read it. Table headers resembling binding
  fields can refuse conservatively rather than authorize an ambiguous review.
- Nested coverage can become ambiguous when contextual pruning follows deduplication. The
  counter returns a refusal and asks for the containing lane root instead of reporting a false count.
- A health BLOCKER consumed before the first observation can still produce a duplicate incident.
  Python 3.6 subprocess timeout handling can still wait for a surviving grandchild's pipes.
- An interpreter without `_lzma` can fail at import. Both supported interpreters pass; deployment
  to a different interpreter requires its own import check.

## What is not done

No required finding from 1–5 is left without its code/test change. The lane must execute the
new real-Git failure cases; this dispatch explicitly forbids that execution. Production installation,
environment activation, live-node smoke tests, remote publishing and service restarts are not done.
The INFO-only lzma portability change and Python 3.6 process-tree timeout redesign are not included.

The requested review mappings and before/after regression contrast are the only retained revision
comparisons; they connect each required finding to evidence. The no-archaeology writing skill
was applied to the guide, handover and report.
'''
(OUT / 'REPORT.md').write_text(report)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

artifacts = {}
for path in sorted(OUT.rglob('*')):
    if path.is_file() and path != OUT / 'MANIFEST.json':
        raw = path.read_bytes()
        artifacts[str(path.relative_to(OUT))] = dict(bytes=len(raw), sha256=sha(raw))
manifest = dict(utc=now, artifacts=artifacts, patches=pins, installed_changes=installed,
                validation=validation, final_verification=final, resources=resources,
                unique_permitted_tests_per_interpreter=unique,
                fresh_patch_passed_executions=passed, fresh_patch_skips=skipped,
                real_git_executed_by_this_agent=False, real_git_failure_validation_pending=True,
                current_evidence_prefix='evidence/round3_',
                note='Other evidence files are retained audit records and are not current validation claims.')
(OUT / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
(L / 'work/STATUS.md').write_text(now + ': DONE. Findings 1–5 fixed; ' + str(unique) +
    ' unique permitted tests pass on each interpreter. Five patches, final hashes, report and lane real-Git command delivered. No installed writes or Git. Lane failure-hook execution remains pending by dispatch.\n')
print(now)
print('REPORT_WRITTEN', len(report.encode()), 'bytes')
print('MANIFEST_ARTIFACTS', len(artifacts))
print('UNIQUE_PERMITTED_TESTS_PER_INTERPRETER', unique)
print('FRESH_PATCH_PASS_EXECUTIONS', passed, 'SKIPS', skipped)
