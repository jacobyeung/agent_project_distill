**NO-GO — gates 1 and 3 still fail.**

Read-only review; no file written. Paths below are relative to `/scratch/jjyeung/orch_n30/lever1_c/r1/`. `P/` denotes a member of `out/delivery.tgz → 0.tgz`, inspected in memory.

1. **Forbidden submission flags remain in the sealed delivery.** `P/orchard_h10/vendor/orchard_launcher.py:96` still contains both `--output=/dev/null` and `--error=/dev/null`. The selected submission route uses durable paths (`P/orchard_h10/common.py:72`), but the explicit “NO … anywhere” condition fails. Remove or repair the retained launcher and reseal.

2. **The claimed 48 MB total-write bound has an uncovered diagnostic path.** `BATCH.sh:2–4` redirects stdout/stderr and sets a soft size limit, but `BATCH.sh:8` immediately restores Python’s limit to the hard limit ([build_depth.py:200](/scratch/jjyeung/orch_n30/lever1_c/r1/build_depth.py:200)). Direct writes through inherited stdout/stderr bypass the metadata ledger, which wraps subsequent file opens ([runtime/q.py:35](/scratch/jjyeung/orch_n30/lever1_c/r1/runtime/q.py:35)). The scheduler’s `a/19` also lacks a demonstrated cap. Keep startup/supervisor output behind an independently bounded sink and test overflow. The shell-header and child-capture tests do not cover this gap (`tests/test_review8.py:59–80`).

The other review-8 repairs are supported:

- **Durable diagnostics:** `BATCH.sh:2` opens opaque `a/20` first; line 4 installs ERR/EXIT records. Recovery loads inside the protected block (`runtime/b.py:22`). First-line, missing-USER and extraction causes pass production fetch (`out/BOOTSTRAP_CHECKS.json:18,42,147`).
- **Disk admission:** only ext4 backed by `/dev/` on the assigned `/tmp` job mount passes (`P/orchard_h10/vendor/orchard_job.py:80–87`), before bulk staging (`P/orchard_h10/job.py:210–221`). Recovery works under the job directory (`runtime/b.py:76–77`).
- **Documented budget:** PLACE states ext4 and the 48,000,000-byte breakdown (`PLACE.md:100–114`); REPORT agrees (`REPORT.md:8–10`). Metadata and pool reservations exist, but do not close finding 2.
- **Clean startup:** the test now executes real `job.main`, filesystem admission and environment creation; external staging remains substituted (`tests/local_bootstrap.py:29–63`; `out/BOOTSTRAP_CHECKS.json:9–15`).

CPU/GPU comparison (`out/REVIEW8_CHECKS.json:34–81`):

| Setting | CPU | GPU |
|---|---|---|
| Partition / time / export / chdir | general / 00:50:00 / NONE / `/tmp` | Identical |
| GRES | Omitted | `gpu:1` |
| Submission environment | Fixed PATH; HOME and USER | Identical |
| Entry | Same sealed BATCH.sh; CPU branch | Same bytes; GPU branch |
| Other flags | Account, CPUs, memory, exclusion, signal, output paths | Identical |

Environment reads and sources are recorded individually in [ENVIRONMENT_INVENTORY.json](/scratch/jjyeung/orch_n30/lever1_c/r1/out/ENVIRONMENT_INVENTORY.json:1), including retained-source reads. The orchestration sources are:

| Variables | Source |
|---|---|
| A_N, A_T, A_I, A_C | Validated receipt restoration; `runtime/a.py:7–16` |
| SLURM_JOB_ID, SLURM_JOB_GPUS, CUDA_VISIBLE_DEVICES | Scheduler; `P/orchard_h10/vendor/orchard_job.py:113–115` |
| SLURM_JOB_START_TIME, SLURM_JOB_END_TIME | Scheduler or explicit clock defaults; `P/orchard_h10/job.py:194–195` |
| USER, HOME, PATH, TMPDIR; filtered SLURM_* | Login/submission environment, then job-local construction; `P/8.py:78`, `P/orchard_h10/common.py:110`, vendor `orchard_job.py:146–153` |
| PATH, LD_LIBRARY_PATH, B8_DELAY | Optional filtered inheritance; `P/orchard_h10/runner.py:88` |
| XDG_CACHE_HOME, HF_HOME, TRITON_CACHE_DIR, TORCHINDUCTOR_CACHE_DIR, TORCH_HOME | Runner-created directories; `P/orchard_h10/runner.py:92–93`, `P/g/w.py:32–33` |
| A_TRACE_RUNNER, A_JOB_ROOT, A_JOB_CONFIG | Optional trace wrapper; vendor `orchard_results.py:38–40` |

Recorded regression evidence retains 50-minute allocation/deadlines and the 30-minute worker cap (`out/FIX_CHECKS.json:54`), capture-1 ordering and telemetry (`out/FAILURE_CHECKS.json`), bounded captured tracebacks (`runtime/e.py:10–20`), naming/label checks (`out/FIX_CHECKS.json:19,66,76`), and parity/cells a–g (`PLACE.md:57`; `tests/test_all.py:95–138`). Startup diagnostics remain the exception identified above.

I verified all 13 package pins, 346 payload pins, and referenced suite/evidence hashes. Validation records **55 tests, passed=true**, 26 vendor files and zero unresolved imports (`out/VALIDATION.json:2–13,136–143`). PLACE, REPORT and BUILD agree on token **a6f198d3c7b20**, **3,719,932 bytes**, SHA256 **bb5315a268af467e2015a590f9fbe383e604e22c9accb1f40cc5e0b81fb0f2a4**.