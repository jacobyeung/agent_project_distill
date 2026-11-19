# Owner handover

The replacement tools address findings 1–9 behind `LCS_REVIEW2_FIXES=1`, default OFF.
The required real-Git rerun remains blocked by this dispatch's explicit no-Git rule.
Do not treat the mocked command tests as proof against a real index or remote.

Replace only the three installed Python files listed in `INSTALLED_CHANGES.json` after checking
their recorded base hashes. The four shell wrappers and `lane_code_sync.sh` remain byte-identical.
This workspace has not installed files, stopped services, or published commits. The existing
tools and ten-minute health loop are installed, as stated by the supplied review; the seven
installed owner files and hourly script were independently compared with their pinned copies.

Set `LCS_REVIEW2_FIXES=1` together with the relevant `LCS_ENABLE_*` flag. An unset switch retains
the installed behavior and its limitations. The loop's owning orchestrator must arrange any
restart needed to load the new environment. `GIT_OWNER.md` gives the invocation and recovery rules.

An origin refusal leaves the local commit intact. The new STOP notice requires the user before
the hourly can repeat the origin failure and advance home. The command does not pause the hourly
or rewrite history. A failed kit commit clears only its staging; if cleanup fails or the process
is killed, user intervention is still required before the hourly. No automatic rerun is safe.

Patches 01–03 rebuild the package from the supplied input files. Patch 04 is an alternative
upgrade from the pinned review package, including its tests/docs; do not apply it after the
regenerated patch 02. `PATCH_BASES.json` pins each preimage by SHA256 and records absent files.
The installed-file list is separate because only the three tool replacements affect production.

## Review round 2: finding -> fix -> test

| Finding | Fix or decision | Regression test or remaining check |
|---|---|---|
| 1 | Origin push failure prints a STOP notice requiring the user before the hourly run; it neither pushes home nor writes a receipt. This is the review's minimal mitigation; the local commit remains. | LandingFailures.test_f1_origin_rejection_requires_user_and_never_pushes_home |
| 2 | Add/commit/copy errors reset only the kit path in the index and verify a clean index. The refusal explains how to inspect HEAD and move an untracked kit aside; failed cleanup requires the user before the hourly. | LandingFailures.test_f2_failed_commit_unstages_only_kit; test_f2_failed_add_unstages_only_kit; test_f2_partial_copy_explains_recovery_without_staging; test_f2_reset_failure_requires_user_before_hourly |
| 3 | Resolved test destinations cannot overlap production state, clone, or local state events; a broad test root and a symlink cannot bypass the checks. | TestIsolation: four test_f3_* methods |
| 4 | The binding parser recognizes bullets, quotes, bold labels, tables, backticks, and SHA-256. Every binding must match, even with owner --bind-sha; empty and conflicting fields refuse. | BindingAndVerdicts.test_f4_formatted_contradictory_hashes_cannot_hide_behind_owner_binding; test_f4_matching_formatted_bindings_authorize_and_conflicts_refuse |
| 5 | Negative tokens are uppercase whole alphabetic words; later VERDICT labels are case-sensitive. Ordinary prose passes. Quoted uppercase NO-GO still refuses, preserving the required negative-token policy. | BindingAndVerdicts.test_f5_ordinary_prose_does_not_override_accepting_verdict; test_f5_explicit_negative_tokens_still_refuse_even_when_quoted |
| 6 | Recovery event names include the observation time and recovered incident kinds, so split stale/failed recovery at one verified timestamp emits both events. | HealthRegressions.test_f6_split_stale_and_failed_recovery_emits_both_results |
| 7 | Health checks last_failed_run before scanning hourly BLOCKERs and records either decision. A consumer moving a previously observed BLOCKER cannot cause a duplicate. | HealthRegressions.test_f7_own_blocker_is_read_once_even_after_consumer_moves_it; test_f7_absent_own_blocker_is_checked_once_per_failure |
| 8 | dry_count checks every ancestor below the orchestration root, including multi-component substring exclusions and MAXDIR. | CoverageAndFixtureSafety.test_f8_nested_excluded_ancestor_has_no_hourly_coverage; existing CoverageTests |
| 9 | Owner/filter tests use validated temporary roots under /scratch or /tmp and reject unsafe roots before writes. They never default to the installed checkout. | CoverageAndFixtureSafety: four test_f9_* methods |
| 10 (INFO) | The owner guide states installed status, node-local receipts, absolute queue paths and node scope, dry-run locking, and the implemented verdict rules. | Documentation.test_f10_guide_matches_installation_receipts_queue_and_dry_lock |
| 11 (INFO) | Real-Git reruns are not executed: the current dispatch explicitly forbids Git and supersedes the earlier round's exception. The unchanged runner remains available for an authorized owner. | The runner's disabled guard is exercised under both interpreters; real-Git unittest is explicitly skipped. No current real-Git proof is claimed. |
| 12 (INFO) | EOFError, zlib.error and LZMAError become REFUSED; non-object KIT.json refuses cleanly. The Python 3.6 surviving-grandchild timeout problem remains: changing process-tree termination exceeds the small error-handling fix and needs authorized integration validation. | MalformedInputs: three test_f12_* methods. The subprocess timeout/grandchild case is not tested or fixed. |
| 13 (INFO) | The existing lock, archive/filter/scanner safeguards, branch/refspec constraints, receipts, package override and default filter behavior are rechecked by the permitted suites. Live remote and real-Git claims remain unverified this round. | Owner/package/filter suites on both interpreters; syntax, in-memory compilation, supplied-log health samples, patch/source equivalence and input hashes. |

## Remaining checks and limits

- An authorized owner must run `tests/run_real_git_owner.sh` with `LCS_RUN_REAL_GIT_TESTS=1`,
  `LCS_REVIEW2_FIXES=1`, `LCS_REAL_GIT_WORK` under authorized scratch, and each supported
  `LCS_PYTHON`. This round runs only its disabled guard; do not enable it under this dispatch.
- The health monitor cannot identify an hourly BLOCKER moved before its first observation.
  A consumer moving it in that window can still cause one duplicate health BLOCKER.
- Python 3.6 can wait past a subprocess timeout if a surviving grandchild holds its pipes.
  That process-tree issue remains; the small malformed-archive fixes do not solve it.
- Audit/test directories are retained. Test commands in `REPORT.md` place all writes under
  this workspace. With the default /tmp root, scratch-only dry-count integration tests skip.

The requested finding mapping is retained to connect decisions to evidence. Exact current
outputs and the validation limits appear in `REPORT.md` and `evidence/round2_commands.json`.
