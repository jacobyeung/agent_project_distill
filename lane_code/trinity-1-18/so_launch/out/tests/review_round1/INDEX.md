# Review round 1 regression evidence

The behavior regressions run against a frozen copy of the pre-fix production files and the final patched files. The artifact audit checks that every frozen production file matches the exact combined tree inspected by the independent review. Every log retains its command, unittest output and exit status. Final proof uses fresh patch applications, not just the edited work tree.

| Scope | Before | After |
|---|---|---|
| Prepared cache: destination preservation, same-path topology, key names and install/report errors | [31 tests; 3 failures, 4 errors](test_prepared_input_cache.before.txt) | [31 tests; OK](test_prepared_input_cache.after.txt) |
| Wrapper: inherited lock, symlinked parent, duplicate t/u jobs, real staging matrix | [9 tests; 3 failures](test_prepared_cache_wrapper.before.txt) | [9 tests; OK](test_prepared_cache_wrapper.after.txt) |
| Memo: same-allocation invalidation and four real guard/chooser subprocesses | [10 tests; OK](test_checkpoint_verify_memo.before.txt) | [10 tests; OK](test_checkpoint_verify_memo.after.txt) |
| Timing: missing/unwritable output, recursive/parent guard events and failure status | [6 tests; 2 failures, 2 errors](test_launch_phase_timing.before.txt) | [6 tests; OK](test_launch_phase_timing.after.txt) |
| Production claims, design, key names, coverage and packaged regressions | [5 delivery contracts fail](delivery.before.txt); [native-selection contract fails](native_selection.before.txt) | [6 delivery contracts; OK](delivery.after.txt) |

The same-path and real-stage behaviors already pass on the pre-fix implementation; they establish the production constraint and cover existing correct branches. The memo integration also passes before: its defect was the report and missing coverage. The failing delivery contracts establish those omissions without inventing a memo or staging bug.

The lock-contention test uses a real held flock and scales only the requested wait to 0.1 seconds. It asserts the literal production arguments `-w 600 7`. The pre-fix symlink fixture uses an intentional three-second timeout and exits 124; the fixed recursive job exits normally. No production job was stopped.

## Final fresh applications

- [Standalone 01](../20261119T082118Z/01_prepared_input_cache.diff.txt): 31 + 9 tests, OK.
- [Standalone 02](../20261119T082118Z/02_parallel_frame_sha.diff.txt): 7 tests, OK.
- [Standalone 03](../20261119T082118Z/03_checkpoint_verify_memo.diff.txt): 10 tests, OK.
- [Standalone 04](../20261119T082118Z/04_launch_phase_timing.diff.txt): 6 tests, OK.
- [Recommended order 03, 04, 02](../20261119T082118Z/recommended.txt): 109 registered, 98 pass, 11 skip.
- [All four, with 01 last and OFF](../20261119T082118Z/combined.txt): 149 registered, 138 pass, 11 skip.
- [Manifest](../../patches/manifest.json): patch and base pins, deployment guidance and native gate SHA256.
- [Artifact audit](../final_artifact_audit.txt): exact file consistency, syntax, claims, counts, links, capacity and checksum checks.

The eleven native skips are explicit: ten tests require Gloo sockets unavailable in this sandbox, and one requires the unstaged authenticated pool receipt. They are not counted as passes. The full launch-kit and production-import modules execute, including world-4 guard/resume and shell-syntax tests.

The [input](../20261119T082118Z/known_native_failures_input.txt) and [patched](../20261119T082118Z/known_native_failures_patched.txt) expanded stale-fixture runs both report 92 tests, four failures, one error and eleven skips. The [comparison](../20261119T082118Z/known_failure_comparison.txt) confirms identical failure identities. The six-test stale admission module is outside the passing native gate.

Files named `*.fixture_trial.txt` are retained harness diagnostics and are excluded from the before/after claims above. Older timestamped logs outside this directory are archival evidence; current delivery results are the fresh applications linked here. Historical failure output is retained verbatim and does not change the OFF guidance.
