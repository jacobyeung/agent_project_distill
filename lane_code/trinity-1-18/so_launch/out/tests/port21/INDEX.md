# Build 21 evidence

All paths below contain exact output, not inferred results. Tests use build 21 seal `b262e7a7`.

- [OFF comparisons](off_identity.txt) ran before ON suites; [retained harness-error output](off_identity.harness_error.txt).
- [Machine-readable test commands and exits](suite_summary.json).
- [Ordered delivered-patch application](recommended.apply.txt).
- [Artifact audit](artifact_audit.json): complete base/result identities, patch scope, syntax, size and backup checks.
- [Known native fixture comparison](known_failure_comparison.txt).
- [READY read-only fixture links](fixture_links.json).

- [03_checkpoint_verify_memo.diff: initial build-20 patch trial](03_checkpoint_verify_memo.diff.initial.txt); [fresh build-21 delivery application](03_checkpoint_verify_memo.diff.delivery.txt).
- [04_launch_phase_timing.diff: initial build-20 patch trial](04_launch_phase_timing.diff.initial.txt); [fresh build-21 delivery application](04_launch_phase_timing.diff.delivery.txt).
- [02_parallel_frame_sha.diff: initial build-20 patch trial](02_parallel_frame_sha.diff.initial.txt); [fresh build-21 delivery application](02_parallel_frame_sha.diff.delivery.txt).

- [03_checkpoint_verify_memo.test_checkpoint_verify_memo](03_checkpoint_verify_memo.test_checkpoint_verify_memo.txt), exit 0.
- [04_launch_phase_timing.test_launch_phase_timing](04_launch_phase_timing.test_launch_phase_timing.txt), exit 0.
- [02_parallel_frame_sha.test_parallel_frame_sha](02_parallel_frame_sha.test_parallel_frame_sha.txt), exit 0.
- [01_diagnostic.test_prepared_input_cache](01_diagnostic.test_prepared_input_cache.txt), exit 0.
- [01_diagnostic.test_prepared_cache_wrapper](01_diagnostic.test_prepared_cache_wrapper.txt), exit 0.
- [recommended.test_checkpoint_verify_memo](recommended.test_checkpoint_verify_memo.txt), exit 0.
- [recommended.test_launch_phase_timing](recommended.test_launch_phase_timing.txt), exit 0.
- [recommended.test_parallel_frame_sha](recommended.test_parallel_frame_sha.txt), exit 0.
- [combined_diagnostic.test_checkpoint_verify_memo](combined_diagnostic.test_checkpoint_verify_memo.txt), exit 0.
- [combined_diagnostic.test_launch_phase_timing](combined_diagnostic.test_launch_phase_timing.txt), exit 0.
- [combined_diagnostic.test_parallel_frame_sha](combined_diagnostic.test_parallel_frame_sha.txt), exit 0.
- [combined_diagnostic.test_prepared_input_cache](combined_diagnostic.test_prepared_input_cache.txt), exit 0.
- [combined_diagnostic.test_prepared_cache_wrapper](combined_diagnostic.test_prepared_cache_wrapper.txt), exit 0.
- [native_baseline](native_baseline.txt), exit 0.
- [native_recommended](native_recommended.txt), exit 0.
- [native_combined_diagnostic](native_combined_diagnostic.txt), exit 0.
- [native_recommended_on](native_recommended_on.txt), exit 0.
- [extra_probes](extra_probes.txt), exit 0.

- [Round 1 delivery contracts](review_round1_contracts.txt): six tests, OK.
- [Round 2 delivery contracts](review_round2_contracts.txt): five tests, OK.

Contract commands, after `source work/fix2_env.sh` and setting `TEST_TMP_ROOT`, `TMPDIR`, and `LANE_TEST_OUTPUT` to `$L/work/port21/tmp`:

```bash
REVIEW_TREE="$L/work/port21/combined_diagnostic" nice -n 10 "$PY" -I -s -B work/test_review_round1_delivery.py
REVIEW_TREE="$L/work/port21/combined_diagnostic" nice -n 10 "$PY" -I -s -B work/test_review_round2_delivery.py
```
