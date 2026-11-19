# Owner handover

The delivery fixes review-round-3 findings 1–5 behind `LCS_REVIEW2_FIXES=1`, default OFF.
Only `land_kit.py`, `sync_health.py`, and `dry_count.py` differ from the installed base.
`INSTALLED_CHANGES.json` gives the exact installed paths and base/new SHA256 values.
The installed copies, wrappers, hourly script and running services have not been changed here.

Before installation, the authorized lane must run the real-Git command below on both interpreters.
The suite covers a successful landing, hourly pathspec isolation, a failed commit, and origin rejection.
The coordinator's available happy-path evidence is recorded in `REPORT.md`; it does not prove
the two new failure cases. This dispatch forbids Git, so their execution remains pending.

```bash
(
set -e
L=/scratch/jjyeung/orch_n30/so_git
mkdir -p "$L/work/realgit_round3_lane"
for PY in /usr/bin/python3 /scratch/jjyeung/envs/p1cpu/bin/python; do
  LCS_RUN_REAL_GIT_TESTS=1 LCS_REVIEW2_FIXES=1 \
    LCS_REAL_GIT_WORK="$L/work/realgit_round3_lane" LCS_PYTHON="$PY" \
    bash "$L/work/review_round3_source/tests/run_real_git_owner.sh"
done
)
```

Expect three tests, no skips, and `LCS_REVIEW2_FIXES=1` in the runner output. Stop on any
failure; do not retry killed work. The command uses only throwaway local bare remotes.

Check each installed preimage hash, stage each replacement as a temporary file in the same
directory, then rename it atomically over the target. Only the lane owner installs.
Replacement Python files load on the next health tick. The owning orchestrator must arrange
a restart only to change the loop environment to include `LCS_REVIEW2_FIXES=1`.
Keep the relevant `LCS_ENABLE_*` flag enabled as described in `GIT_OWNER.md`.

On an origin refusal, the local commit remains: contact the user before the hourly can push it.
On a handled add/commit failure, the tool clears only kit staging and checks the index.
Inspect HEAD before moving an untracked kit aside. A killed process or failed cleanup needs
the user before the hourly. The tool neither stops services nor rewrites history.

Patches 01–03 rebuild the full package from supplied inputs. Patch 04 independently upgrades
the pinned installed package and its tests/docs to the same delivery. Patch 05 independently
upgrades the reviewed round-2 delivery to this delivery. Choose one owner upgrade route;
do not apply patches 04 or 05 after the cumulative patch 02. `PATCH_BASES.json` pins all inputs.

## Review round 3: finding -> fix -> test

| Finding | Fix | Test or remaining validation |
|---|---|---|
| 1 | Refuse REJECTED, REJECTION and NO-GOOD; restore the round-1 REJECTED assertion. Mixed-case conditional verdict labels also refuse. | VerdictAndBindingTests.test_f1_*; ReviewTests.test_negative_anywhere_is_refused |
| 2 | Recognize numbered lists, headings, underscore/backtick labels, up to two leading words and equals separators; contradictory bindings always refuse. | VerdictAndBindingTests.test_f2_* |
| 3 | Record the switch value, including unset/empty. Add isolated pre-commit and pre-receive hook cases for failed staging and origin rejection. | RunnerEvidenceTests.test_f3_* passes without Git. RealGitOwnerTests.test_failed_commit_* and test_origin_rejection_* await authorized Git execution. |
| 4 | Check all fetch and push URLs for origin/home before clone mutation; resolve local paths and symlinks inside the test boundary. | RemoteBoundaryTests.test_f4_* covers external URLs, symlink escape, relative paths, multiple push destinations and no-Git dry runs. |
| 5 | Apply SUBSTR to full orchestration-relative paths for hourly totals; retain raw filter counts. Refuse ambiguous deduplicated output and request the lane root. | NestedCoverageTests.test_f5_* compares nested out/ counts with whole-tree selection and checks the duplicate-representative refusal. |

## Review round 2: finding -> fix -> test

| Finding | Current behavior | Test or limit |
|---|---|---|
| 1 | Origin push failure prints a STOP notice requiring the user before the hourly run; it neither pushes home nor writes a receipt. This is the review's minimal mitigation; the local commit remains. | LandingFailures.test_f1_origin_rejection_requires_user_and_never_pushes_home |
| 2 | Add/commit/copy errors reset only the kit path in the index and verify a clean index. The refusal explains how to inspect HEAD and move an untracked kit aside; failed cleanup requires the user before the hourly. | LandingFailures.test_f2_failed_commit_unstages_only_kit; test_f2_failed_add_unstages_only_kit; test_f2_partial_copy_explains_recovery_without_staging; test_f2_reset_failure_requires_user_before_hourly |
| 3 | Resolved test destinations cannot overlap production state, clone, or local state events; a broad test root and a symlink cannot bypass the checks. | TestIsolation: four test_f3_* methods |
| 4 | Formatted Seal/SHA256 metadata must match, including extended labels and separators. | BindingAndVerdicts.test_f4_formatted_contradictory_hashes_cannot_hide_behind_owner_binding; test_f4_matching_formatted_bindings_authorize_and_conflicts_refuse |
| 5 | Ordinary lowercase prose passes; uppercase negative tokens and uppercase continuations refuse. Conditional verdict labels refuse in any case. | BindingAndVerdicts.test_f5_ordinary_prose_does_not_override_accepting_verdict; test_f5_explicit_negative_tokens_still_refuse_even_when_quoted |
| 6 | Recovery event names include the observation time and recovered incident kinds, so split stale/failed recovery at one verified timestamp emits both events. | HealthRegressions.test_f6_split_stale_and_failed_recovery_emits_both_results |
| 7 | Health checks last_failed_run before scanning hourly BLOCKERs and records either decision. A consumer moving a previously observed BLOCKER cannot cause a duplicate. | HealthRegressions.test_f7_own_blocker_is_read_once_even_after_consumer_moves_it; test_f7_absent_own_blocker_is_checked_once_per_failure |
| 8 | Ancestor/MAXDIR gates and full-path SUBSTR checks determine hourly counts for nested folders. | CoverageAndFixtureSafety.test_f8_nested_excluded_ancestor_has_no_hourly_coverage; existing CoverageTests |
| 9 | Owner/filter tests use validated temporary roots under /scratch or /tmp and reject unsafe roots before writes. They never default to the installed checkout. Scratch-only integration tests skip when the temporary root is /tmp. | CoverageAndFixtureSafety: four test_f9_* methods; Documentation.test_f9_default_tmp_root_skips_scratch_integration_before_writes |
| 10 (INFO) | The owner guide states installed status, node-local receipts, absolute queue paths and node scope, dry-run locking, and the implemented verdict rules. | Documentation.test_f10_guide_matches_installation_receipts_queue_and_dry_lock |
| 11 (INFO) | Real-Git failure cases are delivered for the authorized lane; this dispatch executes no Git. | Disabled-runner guard and switch logging pass; the Git-dependent tests remain skipped. |
| 12 (INFO) | EOFError, zlib.error and LZMAError become REFUSED; non-object KIT.json refuses cleanly. The Python 3.6 surviving-grandchild timeout problem remains: changing process-tree termination exceeds the small error-handling fix and needs authorized integration validation. | MalformedInputs: three test_f12_* methods. The subprocess timeout/grandchild case is not tested or fixed. |
| 13 (INFO) | The existing lock, archive/filter/scanner safeguards, branch/refspec constraints, receipts, package override and default filter behavior are rechecked by the permitted suites. Live remote and real-Git claims remain unverified this round. | Owner/package/filter suites on both interpreters; syntax, in-memory compilation, supplied-log health samples, patch/source equivalence and input hashes. |

## Remaining limits

The health monitor cannot recognize an hourly BLOCKER consumed before its first observation.
Python 3.6 subprocess timeouts may wait on a surviving grandchild's pipes. Both supported
interpreters provide `_lzma`; the unconditional lzma import still requires it in any other
production interpreter. No framework behavior is used by these stdlib tools.
The explicit round-by-round mapping is retained because the dispatch requires it.
