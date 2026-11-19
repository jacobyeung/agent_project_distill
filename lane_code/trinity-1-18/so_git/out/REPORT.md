VERDICT: DONE Fixed review-round-4 findings 1–5 and validated every permitted suite on Python 3.6.8 and 3.12.13.

Only `land_kit.py` changes against the installed round-3 tools. The production checks require
`LCS_REVIEW2_FIXES=1`, default OFF. `out_round3/` preserves the complete pre-edit delivery.
The health loop already has the switch enabled; this update requires no loop restart.

## Measured results

Every number below is measured here or read from the named coordinator logs; none is estimated.

| Check | Result |
|---|---|
| Full owner suite, each interpreter, switch `0` and `1` | 109 tests, 0 failures, 3 real-Git skips per run |
| New round-4 regressions against installed round-3 files | 11 tests, 25 expected failures per interpreter |
| New round-4 regressions against fixed files | 11 tests, 0 failures, 0 skips per interpreter |
| Round-2 / round-3 regression suites on the current upgrade | 26 / 12 tests, 0 failures, 0 skips per interpreter |
| Configurable-package suite | 10 tests, 0 failures, unchanged test checkout per interpreter |
| Optional shell-copy filter suite | 2 tests, 0 failures per interpreter; both option values exercised |
| Switch-off comparisons against round-1 and round-3 tools | 27,000 review inputs per interpreter, 0 differences; 7 root-gate folders, 0 differences |
| Patch reconstruction | 6 patches apply with exact preimage pins and zero fuzz; all 3 alternative owner upgrades reproduce the cumulative files |
| lzma preflight | Both interpreters print `LZMA_IMPORT_OK` |
| Recorded real-Git evidence | `work/realgit4_by_swarm_opt/`: 3 tests, 0 skips per interpreter, `rc=0` |
| Workspace storage at Thu Nov 19 12:51:41 UTC 2026 | 2,799,697,920 allocated bytes; 1,212,251,040 logical bytes; both below 3,000,000,000 |

The owner suite includes both optional-filter tests. The supplied filter's default selection
also matches the delivered optional filter byte for byte on the frozen coverage fixture:
39 files / 105,362 bytes by default; 41 files / 120,931 bytes with shell copies enabled.
The test runner used local retained fixtures under this workspace, disabled GPUs, eight-thread
environment limits, and `nice -n 10`. Peak RAM was not measured. These tools and tests use the
standard library; no Torch/framework behavior or paid/network service is involved.

## Review round 4: finding -> fix -> test

| Finding | Fix | Before/after evidence |
|---|---|---|
| 1 LOW: title-case negative verdicts pass | Case-insensitive negative Verdict/Status labels and leading No-Go refuse. Ordinary prose, title-case prose, and `Verdict: see above` still pass. | `ReviewTests.test_f1_title_case_negative_verdicts_refuse` fails before and passes after; `test_f1_prose_and_references_remain_accepted` passes on both. All six review examples are included. |
| 2 LOW: archive-hash formats bypass owner binding | Check every 64-hex token on lines naming SHA256/SHA-256 and archive/.tar/.tgz. Check sha256sum lines and subsequent rows of Archive/SHA256 pipe tables. A mismatch refuses even with owner binding; these backstops never grant binding. | `ReviewTests.test_f2_all_listed_conflicting_formats_refuse` and `test_f2_line_backstop_checks_every_hash_and_sha_spelling` fail before and pass after. Matching hashes, case folding, binding requirements, and table termination are also tested. |
| 3 LOW: nested dry-count tests fail outside the orchestration tree | Add the existing two-line location guard to both integration tests. | `CoveragePortabilityTests.test_f3_nested_coverage_skips_outside_orchestration_before_writes` fails before and passes after: exactly two skips and no attempted writes. The two real integration cases pass inside the workspace. |
| 4 INFO: leading tilde URLs and lzma dependency | Refuse a leading `~` in every fetch/push URL for both test remotes. Keep `import lzma` and document the owner's preflight. | `RemoteTests.test_f4_leading_tilde_fetch_and_push_refuse_before_mutation` and `DocumentationTests.test_f4_lzma_owner_preflight_is_explicit` fail before and pass after. All 16 remote/direction/tilde combinations pass after; `./~repo.git` stays accepted. Both interpreters pass the import check. |
| 5 INFO: stale report/guide/handover | State the passed realgit4 hook evidence, installed round-3 base, enabled health loop, and actual dry-count refusal condition. Provide the realgit5 command. | `DocumentationTests.test_f5_hook_evidence_and_new_runner_are_current` fails before and passes after. The separate report regression checks the report against the same current facts. |

The review lists six inline hash formats and one column-table format; all seven are explicit
regression cases. Additional cases cover SHA-256, `.tgz`, uppercase hashes, a correct hash
followed by a different hash, and a later conflicting table row. The backstop intentionally
checks every hash in an archive-hash table, so an unrelated source hash in another column also
refuses. A non-table paragraph ends that table context.

The portability regression substitutes a synthetic outside-orchestration path and forbids
`mkdir`; it never writes outside the authorized workspace. Normal dry-count integration still
runs in the actual orchestration tree. When no root gate excludes a folder, dry_count refuses
if any selected path is pruned and either duplicates are nonzero or their count is unavailable.
It does not determine whether the pruned path itself was duplicated.

## Delivery and installation

`INSTALLED_CHANGES.json` uses the user-confirmed installed round-3 package as its base.
The preserved files match the supplied prefixes. Their full hashes are pinned, without
reading or modifying the installed tree during this dispatch.

- `land_kit.py`: `c7b80359e75be1943b4ecbc52688e8243adabcd7f626d567a2e598468417076c` -> `29dd347d33b285453cd3bbddc7e630c01af64fa178c007db9edac913ea5f977f`.
- `sync_health.py` remains `f4b0cc8328e1044b9f3d26721891ce683fc9636a240e8a9d077ac26d5bcd4f54`.
- `dry_count.py` remains `14fd0d4492ac8aaafa6ffd6e13aa4d85c5636aa2dd8803e7055e248ed3ce54b0`.
- Wrappers, `lane_code_sync.sh`, filter/scanner inputs, and running services are unchanged.

The owner runs `python3 -I -c 'import lzma'` on trinity-3-30 in the wrapper's environment,
and checks `LCS_PYTHON` too if configured. The retained unconditional import requires `_lzma`
even when the review switch is off. Its absence fails closed with a startup traceback.
The owner checks the installed preimage, stages `land_kit.py` as a temporary file in the same
directory, verifies its delivered hash, and renames it atomically over the installed target.

| Patch | Base and verification |
|---|---|
| [01_pkg_configurable.diff](patches/01_pkg_configurable.diff) | Supplied remediation input; package suite, 10 tests per interpreter. |
| [02_owner_tools.diff](patches/02_owner_tools.diff) | Supplied owner inputs; adds current tools/tests/docs. Full owner suite runs on this tree after patch 03. |
| [03_shell_copy_coverage_optional.diff](patches/03_shell_copy_coverage_optional.diff) | Supplied filter; option OFF matches the input, option ON and size/path limits pass both filter tests. |
| [04_installed_owner_review2.diff](patches/04_installed_owner_review2.diff) | Alternative upgrade from pinned round-1 files; every resulting owner tool/test/doc matches the full-suite-tested cumulative tree. |
| [05_reviewed_owner_round3.diff](patches/05_reviewed_owner_round3.diff) | Alternative upgrade from pinned round-2 files; the same exact-byte equivalence holds. |
| [06_installed_owner_round4.diff](patches/06_installed_owner_round4.diff) | Current installed round-3 upgrade, including regression tests and docs; round-2, round-3, and round-4 suites run on this reconstructed tree. |

Choose one owner upgrade route. Do not stack patches 04, 05, or 06 with cumulative 02+03.
[PATCH_BASES.json](PATCH_BASES.json) pins each patch, each preimage, and each resulting file;
[source equivalence](evidence/round4_source_equivalence.txt) records the reconstruction checks.
The full current suite covers each distinct test on both interpreters and in both review-switch
modes. Identical reconstructed trees share that full-suite result rather than retaining another
copy of every large fixture, keeping this workspace below its storage limit.

## Exact commands and outputs

[The command ledger](evidence/round4_commands.json) records every exact argv, working directory,
relevant environment, UTC timestamp, expected exit, actual exit, and output path. In particular,
`LCS_RUN_REAL_GIT_TESTS=0` is set for every local test; a PATH guard rejects any Git invocation.
The three skipped owner cases are the explicitly opted-in real-Git cases. Disabled runners
return 2 by design; before-fix regressions return 1 by design. All other recorded checks pass.

The following are exact suite commands from the ledger; their working directories and
environment are part of the corresponding ledger entries.

```text
pkg_py36
nice -n 10 /usr/bin/python3 -I -s -B -m unittest -v
owner_enabled_py36
nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -v
upgrade_round2_py36
nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -p test_review_round2.py -v
upgrade_round3_py36
nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -p test_review_round3.py -v
upgrade_round4_py36
nice -n 10 /usr/bin/python3 -I -s -B -m unittest discover -s tests -p test_review_round4.py -v
pkg_py312
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest -v
owner_enabled_py312
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -v
upgrade_round2_py312
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -p test_review_round2.py -v
upgrade_round3_py312
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -p test_review_round3.py -v
upgrade_round4_py312
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m unittest discover -s tests -p test_review_round4.py -v
```

| Command | Exit | Exact output |
|---|---|---|
| `regressions_before_py36` | 1 | [output](evidence/round4_regressions_before_py36.txt) |
| `regressions_before_py312` | 1 | [output](evidence/round4_regressions_before_py312.txt) |
| `regressions_after_py36` | 0 | [output](evidence/round4_regressions_after_py36.txt) |
| `regressions_after_py312` | 0 | [output](evidence/round4_regressions_after_py312.txt) |
| `patch_apply_01` | 0 | [output](evidence/round4_patch_apply_01.txt) |
| `patch_apply_02` | 0 | [output](evidence/round4_patch_apply_02.txt) |
| `patch_apply_03` | 0 | [output](evidence/round4_patch_apply_03.txt) |
| `patch_apply_04` | 0 | [output](evidence/round4_patch_apply_04.txt) |
| `patch_apply_05` | 0 | [output](evidence/round4_patch_apply_05.txt) |
| `patch_apply_06` | 0 | [output](evidence/round4_patch_apply_06.txt) |
| `version_py36` | 0 | [output](evidence/round4_version_py36.txt) |
| `lzma_py36` | 0 | [output](evidence/round4_lzma_py36.txt) |
| `pkg_py36` | 0 | [output](evidence/round4_pkg_py36.txt) |
| `owner_default_py36` | 0 | [output](evidence/round4_owner_default_py36.txt) |
| `owner_enabled_py36` | 0 | [output](evidence/round4_owner_enabled_py36.txt) |
| `upgrade_round2_py36` | 0 | [output](evidence/round4_upgrade_round2_py36.txt) |
| `upgrade_round3_py36` | 0 | [output](evidence/round4_upgrade_round3_py36.txt) |
| `upgrade_round4_py36` | 0 | [output](evidence/round4_upgrade_round4_py36.txt) |
| `filter_suite_py36` | 0 | [output](evidence/round4_filter_suite_py36.txt) |
| `realgit_runner_disabled_py36` | 2 | [output](evidence/round4_realgit_runner_disabled_py36.txt) |
| `defaults_py36` | 0 | [output](evidence/round4_defaults_py36.txt) |
| `compile_py36` | 0 | [output](evidence/round4_compile_py36.txt) |
| `memory_smoke_py36` | 0 | [output](evidence/round4_memory_smoke_py36.txt) |
| `version_py312` | 0 | [output](evidence/round4_version_py312.txt) |
| `lzma_py312` | 0 | [output](evidence/round4_lzma_py312.txt) |
| `pkg_py312` | 0 | [output](evidence/round4_pkg_py312.txt) |
| `owner_default_py312` | 0 | [output](evidence/round4_owner_default_py312.txt) |
| `owner_enabled_py312` | 0 | [output](evidence/round4_owner_enabled_py312.txt) |
| `upgrade_round2_py312` | 0 | [output](evidence/round4_upgrade_round2_py312.txt) |
| `upgrade_round3_py312` | 0 | [output](evidence/round4_upgrade_round3_py312.txt) |
| `upgrade_round4_py312` | 0 | [output](evidence/round4_upgrade_round4_py312.txt) |
| `filter_suite_py312` | 0 | [output](evidence/round4_filter_suite_py312.txt) |
| `realgit_runner_disabled_py312` | 2 | [output](evidence/round4_realgit_runner_disabled_py312.txt) |
| `defaults_py312` | 0 | [output](evidence/round4_defaults_py312.txt) |
| `compile_py312` | 0 | [output](evidence/round4_compile_py312.txt) |
| `memory_smoke_py312` | 0 | [output](evidence/round4_memory_smoke_py312.txt) |
| `syntax_dry_count.sh` | 0 | [output](evidence/round4_syntax_dry_count.sh.txt) |
| `syntax_land_kit.sh` | 0 | [output](evidence/round4_syntax_land_kit.sh.txt) |
| `syntax_lane_code_sync.sh` | 0 | [output](evidence/round4_syntax_lane_code_sync.sh.txt) |
| `syntax_sync_health.sh` | 0 | [output](evidence/round4_syntax_sync_health.sh.txt) |
| `syntax_sync_health_loop.sh` | 0 | [output](evidence/round4_syntax_sync_health_loop.sh.txt) |
| `syntax_run_real_git_owner.sh` | 0 | [output](evidence/round4_syntax_run_real_git_owner.sh.txt) |
| `syntax_round4_lane_command.txt` | 0 | [output](evidence/round4_syntax_round4_lane_command.txt.txt) |
| `filter_original_py36` | 0 | [output](evidence/round4_filter_original_py36.txt) |
| `filter_default_py36` | 0 | [output](evidence/round4_filter_default_py36.txt) |
| `filter_optional_py36` | 0 | [output](evidence/round4_filter_optional_py36.txt) |
| `dry_count_default_py36` | 0 | [output](evidence/round4_dry_count_default_py36.txt) |
| `dry_count_enabled_py36` | 0 | [output](evidence/round4_dry_count_enabled_py36.txt) |
| `health_sample_py36_0` | 0 | [output](evidence/round4_health_sample_py36_0.txt) |
| `health_sample_py36_1` | 0 | [output](evidence/round4_health_sample_py36_1.txt) |
| `health_sample_py36_2` | 0 | [output](evidence/round4_health_sample_py36_2.txt) |
| `filter_original_py312` | 0 | [output](evidence/round4_filter_original_py312.txt) |
| `filter_default_py312` | 0 | [output](evidence/round4_filter_default_py312.txt) |
| `filter_optional_py312` | 0 | [output](evidence/round4_filter_optional_py312.txt) |
| `dry_count_default_py312` | 0 | [output](evidence/round4_dry_count_default_py312.txt) |
| `dry_count_enabled_py312` | 0 | [output](evidence/round4_dry_count_enabled_py312.txt) |
| `health_sample_py312_0` | 0 | [output](evidence/round4_health_sample_py312_0.txt) |
| `health_sample_py312_1` | 0 | [output](evidence/round4_health_sample_py312_1.txt) |
| `health_sample_py312_2` | 0 | [output](evidence/round4_health_sample_py312_2.txt) |
| `report_before_py36` | 1 | [output](evidence/round4_report_before_py36.txt) |
| `report_before_py312` | 1 | [output](evidence/round4_report_before_py312.txt) |
| `report_after_py36` | 0 | [output](evidence/round4_report_after_py36.txt) |
| `report_after_py312` | 0 | [output](evidence/round4_report_after_py312.txt) |
| `final_patch_01` | 0 | [output](evidence/round4_final_patch_01.txt) |
| `final_patch_02` | 0 | [output](evidence/round4_final_patch_02.txt) |
| `final_patch_03` | 0 | [output](evidence/round4_final_patch_03.txt) |
| `final_patch_04` | 0 | [output](evidence/round4_final_patch_04.txt) |
| `final_patch_05` | 0 | [output](evidence/round4_final_patch_05.txt) |
| `final_patch_06` | 0 | [output](evidence/round4_final_patch_06.txt) |
| `final_docs_py36` | 0 | [output](evidence/round4_final_docs_py36.txt) |
| `final_docs_py312` | 0 | [output](evidence/round4_final_docs_py312.txt) |

Exact unittest summary excerpts follow; the links above contain the complete outputs.

`regressions_before_py36`:

```text
Ran 11 tests in 0.291s

FAILED (failures=25)
```

`regressions_before_py312`:

```text
Ran 11 tests in 0.220s

FAILED (failures=25)
```

`regressions_after_py36`:

```text
Ran 11 tests in 2.119s

OK
```

`regressions_after_py312`:

```text
Ran 11 tests in 1.591s

OK
```

`owner_default_py36`:

```text
Ran 109 tests in 13.756s

OK (skipped=3)
```

`owner_enabled_py36`:

```text
Ran 109 tests in 13.723s

OK (skipped=3)
```

`owner_default_py312`:

```text
Ran 109 tests in 11.115s

OK (skipped=3)
```

`owner_enabled_py312`:

```text
Ran 109 tests in 11.306s

OK (skipped=3)
```

## Real-Git evidence and owner rerun

The coordinator's [Python 3.6 log](../work/realgit4_by_swarm_opt/run_py36.txt) and
[Python 3.12 log](../work/realgit4_by_swarm_opt/run_py312.txt) record 3 tests, 0 skips each,
with `LCS_REVIEW2_FIXES=1`, `OK`, and `rc=0`. Both contain these exact lines:

```text
FAILED_COMMIT staging_cleared=true head_unchanged=true kit_untracked=true rerun_refused=true
ORIGIN_REJECTION stop=true home_unchanged=true origin_unchanged=true receipt_absent=true
```

These logs prove the installed round-3 failure paths and the happy-path/hourly isolation case.
[The evidence record](evidence/round4_realgit4_evidence.json) pins both logs. They do not claim
to test the new round-4 parser or leading-tilde check against real Git. The complete command
for the authorized owner is in [HANDOVER.md](HANDOVER.md); it runs the frozen
`work/review_round4_source/` tree under both interpreters, logs the switch, and writes separate
logs and throwaway repositories under `work/realgit5_by_swarm_opt/`. Its shell syntax passes.

## What could go wrong and how to notice

- A legitimate review may be conservatively refused when it lists another archive SHA or an
  unrelated hash within an archive table. The refusal states `review SHA256 differs`; the owner
  must obtain an unambiguous review, not bypass it with `--bind-sha`.
- The review parser is a constrained text parser, not a complete Markdown/semantic parser.
  Unsupported layouts still need a recognized matching Seal/SHA256 or explicit owner binding.
  The owner must read the review and confirm which archive it covers.
- A test remote beginning with `~` now refuses before branch/index changes. An explicit path
  inside the test root, including `./~repo.git`, remains available for literal tilde names.
- If origin refuses a push, the local commit remains. The tool prints STOP and writes no home
  push or landing receipt. Contact the user before the hourly run. Failed commit cleanup still
  resets only kit index entries; inspect HEAD before moving an untracked kit aside.
- A killed process cannot clean its index. Python 3.6 timeouts may wait on surviving grandchild
  pipes. Neither issue is changed here; do not relaunch killed work without the user's answer.
- The health monitor cannot recognize an hourly BLOCKER consumed before its first observation.
  Its existing event/state tests pass; this package does not change health code.
- Missing `_lzma` causes a startup traceback in either switch mode. The documented owner
  preflight detects it before installation.

## What is not done

This dispatch runs no Git, SSH, deployment, or service restart. The realgit5 run and installation
are owner actions, with the exact command and atomic-install steps in the handover. Leading-tilde
refusals use FakeGit tests; actual Git tilde expansion is not claimed or relied on. No outside-tree
fixtures are created. No requested finding remains without a fix or regression check.

The requested round-4 mapping and the round-3/round-4 distinction in real-Git evidence are retained
because the user requires that audit and the evidence must name the exact source it tested.
