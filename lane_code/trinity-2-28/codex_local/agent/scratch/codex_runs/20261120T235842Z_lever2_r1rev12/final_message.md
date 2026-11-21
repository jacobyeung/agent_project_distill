**GO.** The late sink failure fix is sealed and covered by production-fetch regressions. No blocking regression found.

The sandbox is read-only; this message is the review. Paths below are relative to `/scratch/jjyeung/orch_n30/lever1_c/r1/`; `P/` denotes `out/delivery.tgz → 0.tgz`.

- **Late sink failure:** every supervisor exception sets `rc=1`; recovery replaces an existing success receipt and retains the exception independently of diagnostic-save success (`runtime/b.py:56–107`). I verified that the sealed supervisor function matches this source exactly.
- **Regression coverage:** a child publishes an authenticated COMPLETE receipt and exits zero before sink cleanup fails (`tests/local_bootstrap.py:27–59,118–120`). Drain-error, timeout, and persistent-save-error cases all fetch FAILED with the cause (`tests/test_review11.py:21–45`; `out/REVIEW11_CHECKS.json:1`).
- **Durable output:** submission creates regular, bounded `a/19`, `a/24`, and `a/21` before `sbatch` (`runtime/c.py:13–23`). Sealed `BATCH.sh:2–6` applies the limit first and installs exit-code/failing-line traps. The delivered/embedded route audit reports no discarded stdout/stderr routes (`out/REVIEW9_CHECKS.json:1`).
- **Early failure:** first-line exceptions, extraction failure, and missing USER return their causes through production fetch (`out/BOOTSTRAP_CHECKS.json:1`). These are local CPU injections using production code with filesystem/scheduler/transport substitutions.

CPU/GPU comparison (`P/8.py:75–86`; `P/orchard_h10/common.py:64–74`; `out/REVIEW8_CHECKS.json:1`):

| Setting | CPU check | GPU job |
|---|---|---|
| Partition | general | general |
| GRES | omitted | gpu:1 |
| Time | 00:50:00 | identical |
| Export / chdir | NONE / `/tmp` | identical |
| Submission environment | fixed PATH; caller HOME and USER | identical |
| Entry script | sealed BATCH.sh; CPU branch | identical bytes; GPU branch |

Scheduler GPU assignment selects the branch. Other request flags and output handling match.

Environment reads and provisioning:

- **A_N, A_T, A_I, A_C:** validated CPU receipt supplies `1`, `3000`, inputs digest, and CPU-receipt digest (`runtime/a.py:5–16`; `P/orchard_h10/job.py:193,213,217`).
- **SLURM_JOB_ID, SLURM_JOB_GPUS, CUDA_VISIBLE_DEVICES:** scheduler; **SLURM_JOB_START_TIME/END_TIME:** scheduler with explicit clock defaults (`P/orchard_h10/job.py:192–195`; vendor `orchard_job.py:113–115`; `runtime/b.py:73,77`).
- **HOME, USER, PATH, TMPDIR and filtered SLURM_\*:** submission/login environment, then explicit job-local environment construction (`P/8.py:78`; vendor `orchard_job.py:142–153`; `P/orchard_h10/common.py:110`).
- **PATH, LD_LIBRARY_PATH, B8_DELAY:** conditional inheritance. **XDG_CACHE_HOME, HF_HOME, TRITON_CACHE_DIR, TORCHINDUCTOR_CACHE_DIR, TORCH_HOME:** runner-created directories (`P/orchard_h10/runner.py:88–93`; `P/g/w.py:32–33`).
- **A_TRACE_RUNNER, A_JOB_ROOT, A_JOB_CONFIG:** conditional tracing wrapper (`P/orchard_h10/vendor/orchard_results.py:38–40`).
- The complete per-read list, including retained serving branches, environment-copy expressions, defaults, and provisioning sources, contains **373 references** (`out/ENVIRONMENT_INVENTORY.json:1`); its recorded hash matches.

Remaining gates:

- **Storage:** bulk staging requires an ext4 `/dev/` mount assigned as `job_tmp/<job ID>` before staging (`P/orchard_h10/vendor/orchard_job.py:80–87`; `P/orchard_h10/job.py:210–221`). The kit documents this and a **48,000,000-byte total `/project` allowance**, below 50 MB (`PLACE.md:106–120`; `REPORT.md:10`).
- **Allocation:** 3,000 seconds; worker cap 1,800 seconds; staging, capture, normal-return, and fallback deadlines remain bounded (`PLACE.md:96`; `out/VALIDATION.json:230–266`).
- **Integrity:** 26 vendor files remain enforced (`runtime/s.py:18`); import audit has zero unresolved imports (`out/VALIDATION.json:162–170`). I independently verified **15 package pins and 345 payload pins**.
- **Capture 1 first, telemetry, bounded tracebacks, naming across Orchard-visible surfaces, and no labels:** current-delivery checks remain passing (`out/FIX_CHECKS.json:1`; `out/FAILURE_CHECKS.json:1`; `PLACE.md:76–88`).
- **150-item parity gate and cells a–g:** regression coverage remains passing; intervention evaluation follows the parity gate (`relift.py:238–257`; `tests/test_all.py:95–105`).
- **Validation:** `passed=true`, **67 tests**, two import checks, exact delivery hash (`out/VALIDATION.json:2–13,105`). I verified all referenced suite-source, log, and evidence hashes; I did not rerun write-producing suites.
- **Artifact agreement:** PLACE, REPORT, BUILD, and the actual archive agree: token **a6f198d3c7b20**, **3,737,273 bytes**, SHA256 **`9ac72506077fb4ca0ce24b4c691e076c748d6c9d9c2f6e67e71de821b0f42b0e`** (`PLACE.md:7–14`; `REPORT.md:3–4`; `out/BUILD.json:348–349`).