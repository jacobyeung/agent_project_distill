# PH2GATE report
CPU gate PASS; GPU execution is NOT LAUNCH-READY. No GPU inference ran.
All work stayed in this copy on trinity-1-18; no network, SSH, Git, process killing or deletions.
Bars: 166be15bcd56f303b9b032bab84712264a687bc073b791251b57b814e515d774, unchanged.
The launcher, direct scorer, aggregate and GPU entry points check bars before writes and refuse existing scored outputs.
Capture admission checks work/part2_caps plus out/part2; aggregation reads those captures but requires a clean out/part2.
The CPU launcher uses one process to avoid shard-admission races. All active launchers resolve to this copy.
Fixture pin keys now name local files; historical producer bytes live in work/fixture_sources/*.txt. Every pinned hash is preserved.
Tests PASS: part 1 26/26; part 2 20/20 (original 14 plus six guard tests, including wrapper paths/options and no file/directory writes).
Independent read-only review accepted the guard fixes; GPU-launch limitations remain below.
CPU step 1 PASS: P0 parity 42/42 rows on five captures, 1,037/1,037 across all captures.
CPU step 2 PASS: recall raw/pooled 1,804/1,883; after lifting, raw/best-single/pooled 1,757/1,828/1,856.
CPU step 3 PASS: 23 alias calls, 66 pools, zero refusals or survival/identity/table/builder failures.
CPU step 4 PASS: 209 captures, 192 rooms, 1,037 training rows; rooms remain disjoint across folds.
Part 2 CPU fixture PASS: two freshly priced captures; fresh aggregate over 209 copied synthetic captures reproduces W_cf on 1,037 rows.
Fixture aggregate bars: exact PASS; new/retention FAIL. These synthetic results are plumbing checks, not GPU evidence.
STEP5 FAIL (GPU required): CPU invocation exits 1 with “part 2 needs CUDA”; no STEP5.json was fabricated. GPU pool pass NOT RUN.
CPU-number command: `env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 nice -n 10 python -B verify_cpu.py`; CPU_VALIDATION.json records every child command, exit code and evidence SHA.
GPU checks FAIL: no placement/card/node verification, no two empty nvidia-smi readings 300 s apart, no enforced vnice, no timeout using remaining budget.
The 1.2 GPU-h check occurs after captures; a stalled call can exceed it. Timing excludes tower loading and STEP5; the ten-capture projection drops new phrases first.
STOP/KILLED markers now refuse reruns, but abrupt kills create no marker automatically; unmarked partial passes can resume. Do not launch until an external guard fixes this.
Output confinement FAIL: GPU OUT is out/pool_part2, but TIMING_RECEIPT.json goes to out/; no GPU launcher confines caches. See GPU_LAUNCH_AUDIT.json.
Staging command: `bash sb_mask_phrase/run.sh part2/staging.py`; exact paths, bytes and SHA256 are in STAGING_PART2.tsv and STAGING_PART2.json.
GPU payload: 7,129 files, 5,306,616,193 bytes; every listed file and expected pin verified PASS; no missing payload input.
Payload: frames 6,688/1,838,158,527 bytes; checkpoint 1/3,450,062,241; SAM source 193/4,739,916; reader source 234/3,295,967.
Payload continued: plan inputs 8/8,029,307; entrypoints 3/22,878; source receipt 1/1,123; STEP5 raw cache 1/2,306,234.
The payload excludes the existing SAM3 Python environment and CPU pricing dependencies; their paths remain prerequisites, not a claim of a self-contained deployment.
Default: 1,540 calls × 32 frames × 0.064 GPU-s / 3,600 = 0.876089 GPU-h; --all-aliases: 2,004 calls = 1.140053 GPU-h.
These estimates use the v3 spec's teacher rate and exclude encoding, loading and STEP5; both share the 1.2 GPU-h cap.
Package command: `bash package.sh`; out/sb_ph2gate.tar and out/sb_ph2gate.tar.sha256. Stale nested archives, bytecode, caches and planted refusal-test trees are excluded.
