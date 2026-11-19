VERDICT: PARTIAL Requested fixes are implemented; final frozen-tree validation is pending workspace-cap approval.

The wrapper audits opaque operational names, checks real package rows and executes login placement/fill/public checks under Python 3.6.8. It plans all phases before transport, limits each call with timeout, throttles the stream to 8,000,000 bytes/s and polls CPU completion locally. Optional token builders are added files and preserve native sources.

Measured development results: three targeted Python 3.6/state regressions passed; D default deliveries matched all 5,272,526 bytes; the explicit D full build and native sealed-asset release checker passed. The supplied native mirror has a pre-existing `score_d.py` mismatch against its embedded copy. Full native-checker validation uses a coherent fixture of the authenticated embedded assets.

The workspace measured 3,486,240,768 allocated bytes and 3,278,898,187 apparent bytes before final validation. Lossless fixture compression awaits the user answer required by the Trinity heavy-I/O rule. Final tests and patch hashes will replace this pending report after validation.

No ssh, Slurm, GPU, Git, deletion or paid model API operation ran. Authenticated full r10 source deliveries, step-600 export/dependency mirrors and a fresh Trinity token ledger remain absent. Live Orchard staging, restore/RGB rehearsal, GPU execution and trainer-rank stop/checkpoint/export proofs remain unvalidated.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression test |
|---|---|---|
| 1 | Audit operational names; keep private bytes separate; check containment and stale identities. | `test_F01_*` |
| 2 | Plan every phase before the first transfer. | `test_F02_real_submit_preflight_fails_before_place`, `test_all_plans_every_phase_before_any_remote_execution` |
| 3 | Bound every ossh call with timeout; submit CPU, poll locally, then submit GPU. | `test_F03_short_calls_and_F10_accounting_error_budget`, local transport stub |
| 4 | Apply both patches and compare every delivered source hash. | `test_delivery.py`: `F04_PATCH_EQUALS_TESTED_SOURCE_PASS` |
| 5 | Replace the old CPU job name as well as its package path; reject residual old tokens. | `test_fixed_token_operational_adapter_is_explicit` |
| 6 | Check top-level read metadata and reject a duplicate-layout zero-row gate. | `test_F06_*` |
| 7 | Add token-enabled builders in `so_pack_builders/`; preserve native originals. | `test_delivery.py` and native `check_release_d.py` fixture |
| 8 | Execute login placement, exact fill and public check with real Python 3.6.8. | `test_F08_real_python36_login_runtime`, `test_F09_dropped_env_through_real_python36_fill_probe` |
| 9 | Plant import and archive defects through probe wiring. | `test_F09_*` |
| 10 | Reject every non-running terminal state; tolerate fewer than three consecutive accounting errors. | `test_F10_*`, `test_F03_*` |
| 11 | Apply extra terms to the remote package path and fill argv. | `test_F11_custom_terms_cover_remote_path_and_fill_argv` |
| 12 | Cap the complete transport stream at 8,000,000 bytes/s. | `test_transport_stream_with_local_copy_stub_and_no_retry` |
| 13 | Check a SHA-pinned Trinity ledger before an explicit-token build. | `test_F13_ledger_reuse_rejected_before_builder` |
| 15 | State remote dependencies and signal-delivery limits explicitly. | `test_delivery.py`: `F15_DOCUMENTED_REMOTE_CONTRACT_PASS` |
