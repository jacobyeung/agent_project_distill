# Step-600 release procedure

Use the root `pack.py` with its sibling `pack_probes.py`. Apply the two patches as described in `PATCHES.md`. Patch 02 adds builder copies under `so_pack_builders/`; it leaves native builders and their embedded operational assets byte-identical.

Fill `config_step600.example.json` with authenticated source deliveries, the complete step-600 binding, ordered export/preparation/dependency mirrors, source-script SHA256 values and a fresh SHA-pinned Trinity ledger snapshot. Keep the workspace and mirrors on `/scratch`. Point `builder.path` at the optional builder copy and enable `builder.explicit_token_switch` for a token chosen in advance. Its environment switch defaults off.

```sh
nice -n 10 env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/pack.py" all --enable --config "$L/work/600.json" --yes --token TOKEN
```

This command builds, checks and prints the planned ossh commands. Production execution additionally requires `--execute-remote`. Every local check and every script preflight finishes before placement. Transport uses `pv -L 8000000` and `timeout 300`. CPU submission returns promptly; Trinity polls through short calls at intervals of at least 60 seconds. GPU submission requires COMPLETED, the native CPU receipt and all sealed submit guards. Failed transport and submission attempts are never retried automatically.

Choose a token matching `[a-f][0-9a-f]{10,15}` that is absent from the Trinity ledger. The job name is `a15_cot_apTOKEN`. Operational names, paths, argv, environment values and Slurm comments must be opaque. Private archive contents and code comments are excluded from term scanning; stale identities are checked in every decoded archive and bundle. Placement creates 0700 directories and 0600 files; every phase sets umask 077.

The login path uses `/usr/bin/python3` 3.6.8. The job payload uses Python 3.12. Local checks do not create the allocated `a/c/CPU.json`. Missing authenticated inputs block release. This delivery does not certify the live Slurm environment, full restore/RGB staging, H100 execution or trainer-rank checkpoint/export behavior. The supplied native mirror also has a pre-existing `score_d.py`/embedded-asset mismatch; the sealed-asset checker fixture is documented in `REPORT.md`.

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
