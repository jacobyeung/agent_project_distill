# Checks that require Orchard

All Trinity-runnable checks and operational-script preflights finish before any transport. Missing authenticated mirrors are local prerequisites, never Orchard-only exemptions. Local receipts do not replace `a/c/CPU.json`.

| Remaining check | Orchard dependency | Failure evidence |
|---|---|---|
| Exact package location, directory permissions, actual pool/archive presence and sizes, fill and duplicate markers | Live Orchard filesystem | Login traceback, phase EXIT message and local `*_remote.log`. Placement uses mkdir without exist_ok, so a live collision stops the attempt. |
| Token uniqueness | The Trinity ledger snapshot is checked locally; only Orchard mkdir proves live uniqueness | Existing directory causes placement to fail. A stale snapshot cannot authorize overwriting it. |
| Numeric allocated job ID, node disk capacity, template/bwrap assets, namespace mounts and staging policy | Slurm allocation and node filesystem | CPU `a/4.err`, `a/4.log` and staging receipts when available; no success receipt on failure. |
| Job Python, torch/torchvision/transformers/scipy versions and CUDA libraries | Actual job venv | CPU prepare logs and native version checks. Real Python 3.6.8 login execution is already a Trinity check. |
| Full export restore, READY/settings/binding/manifest/RESTORE hashes and full-reader RGB hashes/PNG decode | Authenticated full inputs and the allocated namespace | `a/c/0.log`, `a/c/1.log`, `FULL_READER.json` and the bound native CPU receipt. Local tiny stubs do not establish restore. |
| Return pool permissions/capacity, symlink policy, general queue availability and duplicate GPU submission | Live pool and scheduler | Sealed submit stderr and the phase EXIT message. |
| sacct availability, scheduler state spelling and CPU completion | Live Slurm accounting | Each bounded poll retains its stdout/stderr. Missing/error replies tolerate at most two consecutive errors. Unknown or terminal failure states print the job ID, state and available CPU stderr tail. |
| Slurm delivery of `--signal=B:USR1@1800` to the batch shell | Scheduler signal delivery | The batch trap and stop markers show whether the signal arrived. Local trap/runner tests cover forwarding and handling, not Slurm delivery or trainer-rank exports. |
| GPU assignment/UUIDs, H100 memory/kernels, CUDA execution and node-specific bootstrap | GPU allocation | Batch EXIT capture at `a/x<job>` preserves node context, exit code and the last 60 log lines when the package directory is writable. Later failures also enter return metadata. |

Every remote call uses timeout, at most 300 seconds; no ssh session spans the CPU job. Trinity waits at least 60 seconds between sacct calls, including the final completion recheck. The overall CPU wait is at most four hours, followed by the bounded final submission call. Transport uses 8,000,000 bytes/s. Timeout or transport failure stops the attempt without retry. Three consecutive accounting errors stop polling; PENDING, RUNNING, CONFIGURING and COMPLETING are the only waiting states. COMPLETED also requires a nonempty native CPU receipt.

A4 and B5 pass the operational-name policy. Archive members inside `0.tgz`, preparation/dependency archives and decoded bundles are private; their names and contents are excluded from forbidden-term scanning. Stale identities remain a separate recursive byte check. Generated login process environments are cleared to PATH/HOME/USER and audited; native job guards check Python descendants. The native diagnostic `head` utility is shell executable syntax; its arguments and paths are audited. Code comments and log contents are not Slurm comments or log names.

Exact login placement, fill and public checks run locally under Python 3.6.8. Full-size fill/resolution remains blocked by absent authenticated export/dependency mirrors. The resolver refuses nonregular dependency members, including links; this conservative gate needs authenticated native-link handling before such an input can pass. The original r10 source deliveries and a fresh Trinity ledger are also absent. No remote place/fill, Slurm submission, GPU execution or trainer-rank export proof ran during this task.

If the batch cannot write its capture file, a failed terminal state without logs indicates a filesystem/bootstrap failure. It never counts as a successful empty return.

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
