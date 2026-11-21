**GO AFTER FIXES — make late sink failures fatal and return their cause through production fetch.**

Read-only sandbox; review provided here instead of `REVIEW_R1.md`. Paths below are relative to `/scratch/jjyeung/orch_n30/lever1_c/r1/`; `P/` means `out/delivery.tgz → 0.tgz`.

- **Blocker reproduced:** `runtime/b.py:53` assigns the child’s successful status to `rc=0`. If sink cleanup then raises, the handler records the exception but leaves `rc` unchanged; line 65 returns success. My read-only mocked replay produced **`late sink failure`, supervisor return 0**. The sealed supervisor contains this same code.
- Sink cleanup can raise for drain errors, drain timeout, or diagnostic-save failure (`runtime/e.py:63–66`). Existing tests inject startup/premature drain failure but do not isolate cleanup failure after a successful child (`tests/test_review10.py:25–46`).
- **Required fix:** set a nonzero status for supervisor/sink exceptions and ensure production fetch reports that failure even when the child already published a successful receipt. Current recovery accepts an existing authenticated receipt without checking its failure status (`runtime/b.py:73–80`); shell recovery rejects a zero terminal status (`runtime/f.py:7–9`). Add a successful-child/late-sink-failure regression through production fetch, then reseal and revalidate.

The original review-10 submission defects are fixed:

- Submission pre-creates durable regular files, rejects nonregular/oversized targets without blocking, and calls `sbatch` directly; no FIFO or collector remains (`runtime/c.py:13–23`).
- Both layers preserve submission failure, including numeric job-ID output (`runtime/c.py:23`; `P/8.py:86–92`).
- Sealed `BATCH.sh:2–6` sets the cap first and installs exit-code/failing-line traps. Output paths survive the job. My delivered/embedded source scan found no `/dev/null` output route; its sole occurrence is a system-read allowlist.
- Recorded first-line, extraction, missing-USER and overflow failures return causes through production fetch (`out/BOOTSTRAP_CHECKS.json:1`; `out/REVIEW9_CHECKS.json:1`; `out/REVIEW10_CHECKS.json:1`, decoded a0 records).

CPU/GPU submission comparison (`P/8.py:75–86`; `P/orchard_h10/common.py:64–74`):

| Setting | CPU | GPU |
|---|---|---|
| Partition | general | general |
| GRES | omitted | gpu:1 |
| Time / export / chdir | 00:50:00 / NONE / `/tmp` | identical |
| Submission environment | fixed PATH; caller HOME and USER | identical |
| Entry | same sealed BATCH.sh; CPU branch | same bytes; GPU branch |

Other request flags and output handling match. Scheduler GPU assignment selects the branch (`out/REVIEW8_CHECKS.json:1`).

Environment reads and sources:

- **A_N, A_T, A_I, A_C:** validated receipt and authenticated digests (`runtime/a.py:7–16`; `P/orchard_h10/job.py:193,213,217`).
- **SLURM_JOB_ID, SLURM_JOB_GPUS, CUDA_VISIBLE_DEVICES:** scheduler; **SLURM_JOB_START_TIME/END_TIME:** scheduler or explicit clock defaults (`P/orchard_h10/job.py:192–195`; vendor `orchard_job.py:113–115`; `runtime/b.py:67,71`).
- **HOME, USER, PATH, TMPDIR, filtered SLURM_\*:** submission/login environment and explicit job-local environment construction (`P/8.py:78`; vendor `orchard_job.py:146–153`; `P/orchard_h10/common.py:110`).
- **PATH, LD_LIBRARY_PATH, B8_DELAY:** conditional inheritance; **XDG_CACHE_HOME, HF_HOME, TRITON_CACHE_DIR, TORCHINDUCTOR_CACHE_DIR, TORCH_HOME:** runner-created cache directories (`P/orchard_h10/runner.py:88–93`; `P/g/w.py:32–33`).
- **A_TRACE_RUNNER, A_JOB_ROOT, A_JOB_CONFIG:** conditional tracing wrapper (`P/orchard_h10/vendor/orchard_results.py:38–40`).
- The complete per-read inventory, including retained serving branches, defaults and environment-copy expressions, contains **373 references** with file/line/source details (`out/ENVIRONMENT_INVENTORY.json:1`).

Other gates retain supporting evidence:

- **Storage/budget:** ext4 `/dev/` filesystem and assigned `job_tmp/<job ID>` required before bulk staging; documented **48,000,000-byte total `/project` allowance** (`P/orchard_h10/vendor/orchard_job.py:80–87`; `P/orchard_h10/job.py:210–221`; `PLACE.md:106–120`; `REPORT.md:10`).
- **Allocation/deadlines:** 3,000-second allocation, 1,800-second worker cap and bounded publication windows (`out/VALIDATION.json:221–249`).
- **Capture ordering, telemetry, bounded tracebacks, naming and no labels:** current-hash evidence remains passing (`out/FAILURE_CHECKS.json:1`; `out/FIX_CHECKS.json:1`).
- **150-item parity and cells a–g:** gate remains before intervention evaluation (`relift.py:238–257`; `tests/test_all.py:95–105`).
- **Vendor/import integrity:** 26 vendor files, zero unresolved imports (`runtime/s.py:18`; `out/VALIDATION.json:154–161`). I verified **15 package pins, 345 payload pins, and all referenced suite/evidence hashes**.

Validation records **64 tests, passed=true**, but misses the reproduced blocker (`out/VALIDATION.json:2–13`).
PLACE, REPORT and BUILD agree: **a6f198d3c7b20**, **3,736,824 bytes**, SHA256 **`7e80b0e550709952985e80a9a148f5ff9f134fb60a9ae61e3bf7586fef6cdf68`** (`PLACE.md:7–14`; `REPORT.md:3–4`; `out/BUILD.json:348–349`).