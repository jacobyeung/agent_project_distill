VERDICT: PARTIAL Findings 1–9 are addressed behind a default-OFF switch; all permitted tests pass, but this dispatch forbids the required real-Git reruns.

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
| Unique passing tests per interpreter | 93 after patches 01–03, including 26 round-2 tests; one real-Git test is skipped. |
| Fresh-patch test executions | 720 pass; 16 skips across repeated configurations. Patch-02-only runs skip the two tests supplied by optional patch 03, as well as real Git. Combined runs skip only real Git. |
| Regression contrast | The same 26-test suite fails on the pinned installed source on both interpreters, then passes on both fixed working copies and both fresh upgrade trees. Exact failure and success outputs are linked below. |
| Fresh validation commands | 40 return their expected status; the two disabled real-Git runners intentionally return 2. Other commands return 0. |
| Python versions | Python 3.6.8 and Python 3.12.13, read from the executed interpreters. |
| Frozen coverage | 39 files / 105362 bytes by default; 41 files / 120931 bytes with optional shell copies. Original/default filter output is byte-identical. |
| Workspace before final report | 544476927 bytes in 259170 local entries; 422634303488 bytes free on scratch. This includes retained fixtures. |
| Limits (configuration) | Eight-thread environment limits; no CUDA devices; niceness 10 or lower priority; workspace cap 3 GB and memory cap 30 GB. Memory peak was not measured. |
| Production access | Eight named files read and hashed: seven owner tools and the hourly script. No installed writes, live Git, SSH, service changes, or model calls. |

Validation ran on trinity-1-18. Start: 2026-11-19 10:08:40 UTC. Deadline: 2026-11-19 12:08:40 UTC.
Report time: Thu Nov 19 10:25:11 UTC 2026. These are stdlib tools/tests; no torch or other framework behavior is used.

## Review round 2: finding -> fix -> test

| Finding | Fix or decision | Test |
|---|---|---|
| 1 | Origin push failure prints a STOP notice requiring the user before the hourly run; it neither pushes home nor writes a receipt. This is the review's minimal mitigation; the local commit remains. | LandingFailures.test_f1_origin_rejection_requires_user_and_never_pushes_home |
| 2 | Add/commit/copy errors reset only the kit path in the index and verify a clean index. The refusal explains how to inspect HEAD and move an untracked kit aside; failed cleanup requires the user before the hourly. | LandingFailures.test_f2_failed_commit_unstages_only_kit; test_f2_failed_add_unstages_only_kit; test_f2_partial_copy_explains_recovery_without_staging; test_f2_reset_failure_requires_user_before_hourly |
| 3 | Resolved test destinations cannot overlap production state, clone, or local state events; a broad test root and a symlink cannot bypass the checks. | TestIsolation: four test_f3_* methods |
| 4 | The binding parser recognizes bullets, quotes, bold labels, tables, backticks, and SHA-256. Every binding must match, even with owner --bind-sha; empty and conflicting fields refuse. | BindingAndVerdicts.test_f4_formatted_contradictory_hashes_cannot_hide_behind_owner_binding; test_f4_matching_formatted_bindings_authorize_and_conflicts_refuse |
| 5 | Negative tokens are uppercase whole alphabetic words; later VERDICT labels are case-sensitive. Ordinary prose passes. Quoted uppercase NO-GO still refuses, preserving the required negative-token policy. | BindingAndVerdicts.test_f5_ordinary_prose_does_not_override_accepting_verdict; test_f5_explicit_negative_tokens_still_refuse_even_when_quoted |
| 6 | Recovery event names include the observation time and recovered incident kinds, so split stale/failed recovery at one verified timestamp emits both events. | HealthRegressions.test_f6_split_stale_and_failed_recovery_emits_both_results |
| 7 | Health checks last_failed_run before scanning hourly BLOCKERs and records either decision. A consumer moving a previously observed BLOCKER cannot cause a duplicate. | HealthRegressions.test_f7_own_blocker_is_read_once_even_after_consumer_moves_it; test_f7_absent_own_blocker_is_checked_once_per_failure |
| 8 | dry_count checks every ancestor below the orchestration root, including multi-component substring exclusions and MAXDIR. | CoverageAndFixtureSafety.test_f8_nested_excluded_ancestor_has_no_hourly_coverage; existing CoverageTests |
| 9 | Owner/filter tests use validated temporary roots under /scratch or /tmp and reject unsafe roots before writes. They never default to the installed checkout. Scratch-only integration tests skip when the temporary root is /tmp. | CoverageAndFixtureSafety: four test_f9_* methods; Documentation.test_f9_default_tmp_root_skips_scratch_integration_before_writes |
| 10 (INFO) | The owner guide states installed status, node-local receipts, absolute queue paths and node scope, dry-run locking, and the implemented verdict rules. | Documentation.test_f10_guide_matches_installation_receipts_queue_and_dry_lock |
| 11 (INFO) | Real-Git reruns are not executed: the current dispatch explicitly forbids Git and supersedes the earlier round's exception. The unchanged runner remains available for an authorized owner. | The runner's disabled guard is exercised under both interpreters; real-Git unittest is explicitly skipped. No current real-Git proof is claimed. |
| 12 (INFO) | EOFError, zlib.error and LZMAError become REFUSED; non-object KIT.json refuses cleanly. The Python 3.6 surviving-grandchild timeout problem remains: changing process-tree termination exceeds the small error-handling fix and needs authorized integration validation. | MalformedInputs: three test_f12_* methods. The subprocess timeout/grandchild case is not tested or fixed. |
| 13 (INFO) | The existing lock, archive/filter/scanner safeguards, branch/refspec constraints, receipts, package override and default filter behavior are rechecked by the permitted suites. Live remote and real-Git claims remain unverified this round. | Owner/package/filter suites on both interpreters; syntax, in-memory compilation, supplied-log health samples, patch/source equivalence and input hashes. |

## Installed replacements

The base hashes were read from the installed files and match the reviewed delivery exactly.
The final read-only check confirms that the installed files still have those base hashes.
Paths and both hashes are recorded in [INSTALLED_CHANGES.json](INSTALLED_CHANGES.json).

| Installed file under `orch_n30/tools/` | New SHA256 |
|---|---|
| [land_kit.py](tools/land_kit.py) | `1379a0d60704bf36b5bc31176181f5b03b95dab8dd516e9fc7386657de1700d9` |
| [sync_health.py](tools/sync_health.py) | `f4b0cc8328e1044b9f3d26721891ce683fc9636a240e8a9d077ac26d5bcd4f54` |
| [dry_count.py](tools/dry_count.py) | `36a5413f5ef67d82398d5a32d1b830e2578622f23fdebc5bfa6aec2e37535c4f` |

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
| [01_pkg_configurable.diff](patches/01_pkg_configurable.diff) | `R1315_PKG`, unset preserves the supplied default; package tests included. | `154af7104da86b789c175db2153a896277b851a16e0f00e6bcb767141fd170fb` | `e8444dff9fd8ee50bc091b8eb9327493d778c28c53d7ec2d0cb06e5bd780ec55` |
| [02_owner_tools.diff](patches/02_owner_tools.diff) | `LCS_ENABLE_*` and `LCS_REVIEW2_FIXES`, default OFF; cumulative tools/tests/guides. | `ddc3b5e62edfe6ed2f7608fd7d524df3c82baadb70a5ffddb3dc84c04e49a621` | `a8db3eecb984c75fe53da37ce1421aeb0538fd2b555c376788f06ba40c9786f8` |
| [03_shell_copy_coverage_optional.diff](patches/03_shell_copy_coverage_optional.diff) | `LCS_INCLUDE_SHELL_COPIES`, default OFF; optional filter and tests. | `0745706bb680537fcd3cf1543acfe0d7016a11fffb71fb56f19f6ab2d7730350` | `b2ce5bb3d3373239a2fde4e47a0ccd9040dfb83d9faa50cdc081ca4c4e0d836d` |
| [04_installed_owner_review2.diff](patches/04_installed_owner_review2.diff) | `LCS_REVIEW2_FIXES`, default OFF; alternative installed-package upgrade and tests. | `e6fdc64270ba7a1a2aa3acec0de2216f3e6aa22737a606da2ec8ad83f5bbfbc9` | `fd3df825ea1f26b7d3ec97dcc9c106c930f64507e00d7f445420e21d7ae31d74` |

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
| base_py36 | 1 | [output](evidence/round2_regressions_base_py36.txt) | [command](evidence/round2_regressions_base_py36.json) |
| base_py312 | 1 | [output](evidence/round2_regressions_base_py312.txt) | [command](evidence/round2_regressions_base_py312.json) |
| source_py36 | 0 | [output](evidence/round2_regressions_source_py36.txt) | [command](evidence/round2_regressions_source_py36.json) |
| source_py312 | 0 | [output](evidence/round2_regressions_source_py312.txt) | [command](evidence/round2_regressions_source_py312.json) |

Fresh validation root: `/scratch/jjyeung/orch_n30/so_git/work/round2_validation_nix5a90d`.

| Command/check | Exit | Exact output |
|---|---|---|
| `version_py36` | 0 | [output](evidence/round2_version_py36.txt) |
| `version_py312` | 0 | [output](evidence/round2_version_py312.txt) |
| `patch_apply_01` | 0 | [output](evidence/round2_patch_apply_01.txt) |
| `patch_apply_02` | 0 | [output](evidence/round2_patch_apply_02.txt) |
| `pkg_py36` | 0 | [output](evidence/round2_pkg_py36.txt) |
| `pkg_py312` | 0 | [output](evidence/round2_pkg_py312.txt) |
| `owner_default_py36` | 0 | [output](evidence/round2_owner_default_py36.txt) |
| `owner_enabled_py36` | 0 | [output](evidence/round2_owner_enabled_py36.txt) |
| `owner_default_py312` | 0 | [output](evidence/round2_owner_default_py312.txt) |
| `owner_enabled_py312` | 0 | [output](evidence/round2_owner_enabled_py312.txt) |
| `patch_apply_03` | 0 | [output](evidence/round2_patch_apply_03.txt) |
| `owner_optional_default_py36` | 0 | [output](evidence/round2_owner_optional_default_py36.txt) |
| `owner_optional_enabled_py36` | 0 | [output](evidence/round2_owner_optional_enabled_py36.txt) |
| `realgit_runner_disabled_py36` | 2 | [output](evidence/round2_realgit_runner_disabled_py36.txt) |
| `owner_optional_default_py312` | 0 | [output](evidence/round2_owner_optional_default_py312.txt) |
| `owner_optional_enabled_py312` | 0 | [output](evidence/round2_owner_optional_enabled_py312.txt) |
| `realgit_runner_disabled_py312` | 2 | [output](evidence/round2_realgit_runner_disabled_py312.txt) |
| `patch_apply_04` | 0 | [output](evidence/round2_patch_apply_04.txt) |
| `upgrade_regressions_py36` | 0 | [output](evidence/round2_upgrade_regressions_py36.txt) |
| `upgrade_regressions_py312` | 0 | [output](evidence/round2_upgrade_regressions_py312.txt) |
| `syntax_dry_count.sh` | 0 | [output](evidence/round2_syntax_dry_count.sh.txt) |
| `syntax_land_kit.sh` | 0 | [output](evidence/round2_syntax_land_kit.sh.txt) |
| `syntax_lane_code_sync.sh` | 0 | [output](evidence/round2_syntax_lane_code_sync.sh.txt) |
| `syntax_sync_health.sh` | 0 | [output](evidence/round2_syntax_sync_health.sh.txt) |
| `syntax_sync_health_loop.sh` | 0 | [output](evidence/round2_syntax_sync_health_loop.sh.txt) |
| `syntax_run_real_git_owner.sh` | 0 | [output](evidence/round2_syntax_run_real_git_owner.sh.txt) |
| `compile_py36` | 0 | [output](evidence/round2_compile_py36.txt) |
| `memory_smoke_py36` | 0 | [output](evidence/round2_memory_smoke_py36.txt) |
| `compile_py312` | 0 | [output](evidence/round2_compile_py312.txt) |
| `memory_smoke_py312` | 0 | [output](evidence/round2_memory_smoke_py312.txt) |
| `filter_original` | 0 | [output](evidence/round2_filter_original.txt) |
| `filter_default` | 0 | [output](evidence/round2_filter_default.txt) |
| `filter_optional` | 0 | [output](evidence/round2_filter_optional.txt) |
| `dry_count_default_py36` | 0 | [output](evidence/round2_dry_count_default_py36.txt) |
| `dry_count_enabled_py36` | 0 | [output](evidence/round2_dry_count_enabled_py36.txt) |
| `dry_count_default_py312` | 0 | [output](evidence/round2_dry_count_default_py312.txt) |
| `dry_count_enabled_py312` | 0 | [output](evidence/round2_dry_count_enabled_py312.txt) |
| `health_sample_0` | 0 | [output](evidence/round2_health_sample_0.txt) |
| `health_sample_1` | 0 | [output](evidence/round2_health_sample_1.txt) |
| `health_sample_2` | 0 | [output](evidence/round2_health_sample_2.txt) |

The exact unittest summary lines below are excerpts; each linked output above retains the
full test-by-test output without truncation.

`pkg_py36`:

```text
Ran 10 tests in 0.028s

OK
```

`pkg_py312`:

```text
Ran 10 tests in 0.047s

OK
```

`owner_default_py36`:

```text
Ran 82 tests in 7.078s

OK (skipped=3)
```

`owner_enabled_py36`:

```text
Ran 82 tests in 7.514s

OK (skipped=3)
```

`owner_default_py312`:

```text
Ran 82 tests in 7.595s

OK (skipped=3)
```

`owner_enabled_py312`:

```text
Ran 82 tests in 7.937s

OK (skipped=3)
```

`owner_optional_default_py36`:

```text
Ran 84 tests in 8.449s

OK (skipped=1)
```

`owner_optional_enabled_py36`:

```text
Ran 84 tests in 8.443s

OK (skipped=1)
```

`owner_optional_default_py312`:

```text
Ran 84 tests in 7.815s

OK (skipped=1)
```

`owner_optional_enabled_py312`:

```text
Ran 84 tests in 7.673s

OK (skipped=1)
```

`upgrade_regressions_py36`:

```text
Ran 26 tests in 1.418s

OK
```

`upgrade_regressions_py312`:

```text
Ran 26 tests in 1.200s

OK
```

## Verification of fixes relied on from round 1

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
