**NO-GO — gates 1 and 3 fail; gate 2 remains incompletely demonstrated.**

Read-only review; no file written. Paths below are relative to `r1/`. `P/` means a member of `out/delivery.tgz → 0.tgz`, inspected in memory.

1. **Batch output can still disappear.** GPU submission retains `--output=/dev/null --error=/dev/null` (`P/orchard_h10/common.py:72`). `BATCH.sh:3` immediately execs Python without an exit/failing-line trap. Recovery modules execute before the supervisor’s protected block (`runtime/b.py:20–31`). Child output stays in memory until capture ends (`runtime/e.py:30–47`); no persistent diagnostic file exists before startup. Add durable opaque stdout/stderr destinations and the required trap before other execution.

2. **Storage admission explicitly permits tmpfs.** `P/orchard_h10/vendor/orchard_job.py:80–87` accepts `tmpfs`, xfs and btrfs alongside ext4; checking `job_tmp` does not enforce disk-backed ext4. Bulk staging follows that admission (`P/orchard_h10/job.py:210–221`). Require ext4 on the assigned job directory before staging.

3. **The 50 MB total `/project` bound is absent.** Production publication permits 90,000,000 bytes (`P/orchard_h10/vendor/orchard_results.py:104`), and recovery creates its working return directory under `/project` (`runtime/b.py:67`). Neither PLACE nor REPORT states the required storage restriction and 50 MB total-write ceiling. `PLACE.md:12` reports only a 7,816,505-byte installation estimate. Account for diagnostics, recovery, publication and fetch copies; enforce and document the total.

4. **The A_N repair works, but the clean-environment test stops too early.** The replay identifies `KeyError: 'A_N'` ([out/REPLAY_173925.txt:12](/scratch/jjyeung/orch_n30/lever1_c/r1/out/REPLAY_173925.txt:12)). `runtime/a.py:5–14` validates the receipt and restores all four A_* values. However, the test replaces `job.main` before filesystem admission (`tests/local_bootstrap.py:29–45`), so it cannot establish every downstream environment dependency.

The orchestration environment reads and sources are:

| Reads | Source / evidence |
|---|---|
| `A_N`, `A_T`, `A_I`, `A_C` | Validated receipt, fixed card/time values and hashes; `runtime/a.py:5–14`, `P/orchard_h10/job.py:193,213,217`. |
| `SLURM_JOB_ID`, `CUDA_VISIBLE_DEVICES`, optional `SLURM_JOB_GPUS` | Scheduler; `P/orchard_h10/job.py:192,249`, `P/orchard_h10/vendor/orchard_job.py:113–115`. |
| `SLURM_JOB_START_TIME`, `SLURM_JOB_END_TIME` | Scheduler or explicit clock fallbacks; `P/orchard_h10/job.py:194–195`, `runtime/b.py:53`. |
| `USER`, `HOME` | Inherited environment; `USER` remains required, HOME becomes job-local during execution; `P/orchard_h10/vendor/orchard_job.py:99,146–153`, `P/8.py:77`. |
| `PATH`, `HOME`, `USER`, `TMPDIR`, `CUDA_VISIBLE_DEVICES`, `SLURM_*` | Filtered inheritance; `P/orchard_h10/common.py:110`, `P/orchard_h10/job.py:162`. |
| `PATH`, `LD_LIBRARY_PATH`, `B8_DELAY` | Optional inheritance; `P/orchard_h10/runner.py:88`. |
| Five cache-root variables | Runner supplies them; `P/orchard_h10/runner.py:92–93`, `P/g/w.py:32–33`. |
| `A_TRACE_RUNNER`, `A_JOB_ROOT`, `A_JOB_CONFIG` | Trace wrapper supplies them when enabled; `P/orchard_h10/vendor/trace_runtime.py:82–83`, `orchard_results.py:38–40`. |

**An exhaustive serving-path environment inventory is still missing; the table above covers orchestration, not every retained serving module.**

CPU/GPU submission comparison (`orchard/o_cpu.sh:15`; `P/orchard_h10/common.py:69–73`; `P/8.py:74–83`):

| Setting | CPU check | GPU submission |
|---|---|---|
| Partition / time / chdir | general / 50 minutes / `/tmp` | Same |
| GRES | None | `gpu:1` |
| Export | `ALL`, from a minimal environment | Packaged submit replaces `NONE` with explicit A_* exports |
| Environment | PATH, HOME, USER, empty CUDA visibility | Submit environment: PATH, HOME, USER; scheduler supplies GPU visibility |
| Entry | `a/5.py`, sequence `a/6.py` | `BATCH.sh` → embedded `0.py` → allocation job |
| Signal | No explicit warning | `USR1@120` |

Thus, **the packaged next submission does not actually use `--export=NONE`**. Align the intended route and test the complete startup under it.

Positive evidence: first-line and extraction failures pass production fetch (`out/BOOTSTRAP_CHECKS.json:14,38`). Compared with the replay package, only `9.json` changed inside the payload; runtime code, vendor files and serving sources are byte-identical. Recorded validation retains 47 tests, 26 vendor files and zero unresolved imports (`out/VALIDATION.json:12,127`), plus capture ordering, telemetry, bounded diagnostics, naming/label checks and parity/cell tests.

I independently verified delivery SHA256 **`8a73ecaa56891bb007453dbc1bdb39d5ef57e9dd089074e196a2b91d825fe123`**, package/payload pins and all 22 referenced evidence hashes. PLACE, REPORT and BUILD agree on this delivery. The 50-minute allocation, 30-minute worker cap and deadline windows remain (`PLACE.md:96`). **Passing existing validation does not clear the failed submission gates.**