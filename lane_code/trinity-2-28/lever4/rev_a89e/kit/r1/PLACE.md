<!-- boot-order -->
The boot gate imports all 411 audited modules before staging any checkpoint, weight or frame. It stages CPython from runtime group 0, the base environment from group 1, `v/py` and its overlay from input 3, and policy from input 4. Pre-bulk authenticated source bytes total **10,237,341,493**, including **3,833,173** package bytes. Runtime group 0's other members and all bulk inputs follow a successful boot receipt.

The pool probe writes and fsyncs 131,072 random bytes, verifies their SHA256, and reserves 131,104 bytes including the ledger write. Both CPU guards in `a/5.py` and the pre-submission receipt check `a/9.py` read `WRITE_TEST_BYTES` from the sealed pool writer `orchard_h10/vendor/return_io.py`; the guards also verify the retained file, receipt hash, ledger charge and guarded helper. The cumulative pool and metadata budgets remain unchanged.

The CPU check of `a38bd627f901e` failed because the build changed only one side of a constant. The previous `revision8.py:49` replaced `4*1024**2` with `131072` in `return_io.py`, so the guarded write test wrote 128 KiB, while `a/5.py:53` (`out/WT_OLD_5.py:53`, from `inspect/a_5.py:49`) still required 4 MiB and raised at line 54. The mismatch was deterministic; no job ID, node, time, path, token or sibling placement entered it. The receipt is not written by placement: each CPU check creates a fresh `wpool/<token>/.wtest` under its own job-local temporary root through `orchard_results.write_test` and the guarded `return_io.py test` subprocess, then compares it at once. The second guard (`out/WT_OLD_5.py:77`) and `a/9.py:23`, which `o_check_sub.sh` runs on `CPU.json` before the GPU submit, pinned the same stale 4 MiB and would have failed next. Local tests missed all three because they called the operator directly, stopped at boot, or fed `a/9.py` no real CPU receipt.

`tests/test_write_receipt.py` runs the delivered `BATCH.sh` CPU route with job IDs that differ from 173995, a fresh pool, and three spent sibling placements, then runs `a/9.py` on the resulting `CPU.json` as `o_check_sub.sh` does. Remote staging and model execution use tiny fixtures; the pool writer, reservation ledger, guarded subprocess, bootstrap dispatch, receipt check and authenticated fetch are real. The old `a/5.py` and the old `a/9.py` line both reject the new receipt. Wrong receipt sizes, changed evidence sizes or hashes, exhausted budgets, changed settings and later preparation failures all fail with bounded diagnostics.

`a/30.json` records the CPU failure, the failed check's name, and up to 16 comparisons, with each expected/found value bounded to 2,048 characters. Supervisor recovery returns the matching job/plan record as `metadata/30.json`, alongside boot status and the traceback. When the exception follows a passed comparison, `failed_check` is null and `comparison_status` says so. A failed pool subprocess records its expected and actual exit status and bounded stderr. A failed `a/9.py` size check prints the expected and found sizes.

`tests/test_vpy.py` separately checks all 411 imports through the real pinned archives, production capture and namespace argv. The host bwrap executable, scratch bindings and sleeping watcher helper are substituted. New fixtures remain in the approved sibling directory; no files are deleted.

Token `a89e8fdab55d4` supersedes the placed tokens `a6f198d3c7b20`, `a7e29d4c8f103`, `a38bd627f901e` and `a4282fee306d6` and the unplaced interim build `ad07f53341bc0`; placement and submission use fresh paths and one-use locks.

<!-- /boot-order -->

<!-- debug-partition -->
## Debug partition

Both allocations go to Orchard's `debug` partition under `debug_qos`, because another project's job holds the account's `general` slot. `debug_partition.py` defines `PARTITION`, `QOS` and the lane's job-name prefix `a15_cot_ap`. The build writes them into the submission contract (`orchard_h10/common.py`, `submit_argv`), the retained template launcher (`orchard_h10/vendor/orchard_launcher.py`: `submit_argv`, `queue_admission`, `submit`) and the queue check in `orchard/o_check_sub.sh` and `orchard/o_sub_hand.sh`. The GPU job replaces `--partition=general` with `--partition=debug --qos=debug_qos` and keeps every other flag: account, one node and task, 16 CPUs, 200G, the exclusion, `--time=00:50:00` (debug allows one hour), `--signal=B:USR1@120`, `--no-requeue`, `--export=NONE`, the output and error paths, `--chdir=/tmp` and the job name. The CPU check sends the same flags without `--gres=gpu:1`.

Before the GPU submit, the operator script runs `squeue -u jjyeung -p debug -h -o '%j|%b'` and refuses only when a job named `a15_cot_ap*` (this lane, including this package) already requests a GPU on debug. Other projects' jobs and the lane's own CPU check do not block it. The template launcher applies the same rule to its `%i|%j|%u|%T|%b` observation; `8.py submit` performs no queue check, as before.

debug allocates whole nodes (`Exclusive=NODE`), and Slurm documents that an exclusive job receives every CPU and GRES of its node, even a job that requests no GPU. Under the previous bootstrap, which chose the CPU check only when no GPU was visible, the CPU check would then have taken the GPU route and failed on the missing `a/c/CPU.json`; the GPU job's card check would have refused a multi-GPU node after staging. The bootstrap now runs the CPU check whenever no GPU is visible or the package has no `a/c/CPU.json`, and for that check it removes `SLURM_JOB_GPUS`, `SLURM_STEP_GPUS`, `SLURM_GPUS_ON_NODE` and `GPU_DEVICE_ORDINAL` and sets `CUDA_VISIBLE_DEVICES=''`. The GPU job (CPU receipt present) runs `job.main` as before; `select_cards` gives the worker the first visible GPU, and `metadata/CARDS.json` records the selected and the assigned lists. On a node that exposes only the requested GPU, both changes are no-ops.

The CPU unit's time guard reads `SLURM_JOB_START_TIME` and `SLURM_JOB_END_TIME`, which Slurm sets the same way on every partition. With E = min(start + 3,000 s, `SLURM_JOB_END_TIME`), the 00:50:00 request gives E = start + 3,000 s on debug: the worker stops by E − 360 s, the operator kills it at E − 330 s, and `CPU.json` is written before USR1 at E − 120 s. An exclusive node can give torch more than 16 threads (`os.sched_getaffinity`), which only shortens the unit; the 200G memory cgroup and the 170 GiB guard are unchanged.

`tests/test_debug_partition.py` (5 tests, `out/DEBUG_PARTITION_CHECKS.json`) checks that the argv equals the placed `a4282fee306d6` argv with only `--partition=general` replaced by partition and QoS, and that the CPU and GPU submits differ only by `--gres`. It checks the launcher's admission rule and runs the operator queue check against a stand-in `squeue` in seven cases, including a failing `squeue`. On a node that exposes four GPUs it runs the delivered CPU route (receipt and `a/9.py` pass; the operator dispatch sees no GPU) and the GPU route into `job.main`. It also checks card selection and the time guard under four end times.

Risks: that debug's exclusive allocation exposes every GPU comes from Slurm's documentation, not from an Orchard observation; the routing is correct either way. If it does, `debug_qos`'s per-user limit of 16 GPUs counts whole nodes, so other debug nodes held by the user can leave this job pending. A GPU submit through `SUBMIT.cmd` without a CPU check now runs the CPU check instead of failing.
<!-- /debug-partition -->

<!-- cpu-unit -->
## CPU real unit

The Orchard CPU check now runs the job's first real unit through the full model on CPU before it can pass. After the boot gate, staging, bundle and write-test guards, preparation and the operator rehearsal, the operator's `cpu_unit` (`a/6.py`) launches the production worker exactly as the GPU operator does: `commands()` writes `metadata/a/30.json` (action 3), and the numeric entry runs `g.w.run` with a `cpu_unit` configuration. The worker loads the full step-544 carrier and heads through `make_capped_real(..., device='cpu')` with the production loader's dtypes (bf16 base parameters, fp32 heads), runs the pinned G3T weights through `TowerG3T`/`FrozenG3TTower` on the capture's served PNGs, then runs `capture_one` (one prefill, geometry and own-depth scale) and the record encoder. Torch uses the job's CPUs (`os.sched_getaffinity`: 16 under `--cpus-per-task=16`, possibly more on an exclusive debug node).

`metadata/33.json` (worker) and `metadata/34.json` (operator) become `CPU.json` `real_unit`. The receipt records seconds and peak RSS for the stages `bind`, `first_model`, `load`, `prefill` and `record`; shapes, dtypes and finite flags of the first-model outputs; minimum, maximum, mean and median of the served float16 plane (32×51×51) and its exact plane; the scale, the intrinsics K, the parameter count, dtypes and placement; the admission decision; and the operator's memory peaks. Parity against the GPU reference is recorded but not required: on CPU the G3T stage runs in fp32 because its bf16 autocast is CUDA-only (`tower_read.py:246`).

`real_unit.passed` requires all five stages, worker exit 0, clean output checks, no deadline or memory stop and step 544. Otherwise `a/5.py` fails the `CPU real unit passed` comparison, writes the unit receipt to `a/31.json`, and supervisor recovery returns it as `metadata/31.json` beside `metadata/30.json`. `a/9.py` (run by `o_check_sub.sh` before the GPU submit) and the GPU bootstrap both require a passing real unit.

The CPU job keeps the GPU job's flags except `--gres` and therefore its 00:50:00 allocation. With E = min(start + 3,000 s, `SLURM_JOB_END_TIME`), the worker must stop by E − 360 s and the operator kills it at E − 330 s (SIGTERM, then SIGKILL after 5 s), so `CPU.json` is written before Slurm's USR1 at E − 120 s. At worker start the admission computes need = 1.25 × (first model + load + prefill) + 60 s from measured estimates: first model 985 s for 64 frames and 325 s for 32 (measured 971 s and 312 s on 16 threads of a shared EPYC 9224 node, `out/CPU_TOWER_BENCH.json`), load 420 s, prefill 150 s. The first capture (64 frames) needs 2,004 s; the first 32-frame capture in production order (index 30) needs 1,179 s. If the first capture does not fit, the worker runs that 32-frame capture through the same code and every stage, recording `time_guard` with the numbers; if neither fits it records `over_budget`, runs index 30 anyway, and the kill deadline still preserves the receipt. The first capture fits only when everything before the unit finishes within about 10.6 minutes, so expect `time_guard`.

Memory stays under the job's 200G cgroup. The CPU worker alone sets `RLIMIT_AS` to 180 GiB; the GPU worker has no cap. The operator samples memory once a second as the cgroup's `memory.current` minus its file LRU pages, so page cache from staged archives is not charged (fallback: process-tree RSS), and SIGKILLs the worker at 170 GiB. The measured CPU first model peaked at 12.6 GB; rank 4's 9B carrier peaked at 43 GB on CPU. Worker outputs stay on the job's ext4 `/tmp` root. `CPU.json` grows by about 10 KB (400 KB cap); `a/31.json` is written only on failure (at most 100 KB). The 48,000,000-byte `/project` budget is unchanged.

`tests/test_cpu_unit.py` runs the delivered operator's `cpu_unit`, which launches the delivered worker through the operator's prefix seam with `tests/cpu_unit_fixture.py` doubles: a tiny native Qwen3.5 hybrid CarrierC1 (linear- and full-attention layers, pose and gravity heads, private depth head with its ViT copy; bf16 base as loaded in production), real tiny G3T components at 28 px, and the matching prompt batch. Real artifact manifests, `Artifact.verify`, `Audit`, `stage_capture` from the authenticated local `a2.tar`, `bind_item`, the tower run on 64 or 32 served frames, the prefill, heads, geometry, scale and record encoding are production code. Cases: admission, deadline_kill, local_first_unit, local_time_guard, memory_guard, page_cache_guard, pinned_first_unit, pinned_time_guard. The pinned cases run the production interpreter `d/v/py` (transformers 5.19.0, torch 2.13.0+cu130) in the production-shaped namespace. `tests/test_write_receipt.py` adds the real-unit failure through production fetch and `a/9.py` rejections.

The GPU path was audited against the pinned environment (transformers 5.19.0, torch 2.13.0+cu130; the same `q/env.json` receipt under which T1 run 173662 replayed these serving sources on GPU). The boot gate imports the same 411 modules in CPU and GPU mode. `fla` and `causal_conv1d` appear only at the excluded `carrier_c1_run.fla_check` site, which the worker never calls; the pinned environment lacks both, so transformers uses its PyTorch fallbacks on either device. The worker's own code never reads cache tensors, and during this prefill the serving sources read `past_key_values` only through `get_seq_length`. Three CPU-only failures were certain and are fixed: `Monitor.begin` called `torch.cuda.reset_peak_memory_stats()`, which fails without CUDA (`runtime/m.py`); `start_tower` hard-coded `cuda:0` and `torch.cuda.synchronize()` (`runtime/w.py`); and `run` required an H100 and synchronized after each capture. The GPU worker keeps its H100 check, CUDA device, synchronization, 60-capture loop and unlimited address space.

Remaining risks: the time estimates come from a shared local EPYC 9224 node, and load and prefill for the step-544 carrier on CPU are unmeasured, so a slow Orchard node can reach `over_budget` and fail the CPU check (cost: one CPU job, no GPU job). Under `time_guard` the 64-frame first capture's G3T stage does not run on CPU in the check; the same code ran on 64 frames in the benchmark and the tiny tests. If the step-544 artifact attached an MDG head, `_prepare_decode` would call `mdg_features.expand_cache`, which reads `conv_states.shape`, while 5.19.0 stores those states as dicts; T1's success in this environment indicates the export has no MDG head, and the CPU unit would expose it before any GPU job. CPU parity with the GPU reference is not expected. Without cgroup v2 the guard falls back to process-tree RSS.
<!-- /cpu-unit -->


The delivery below uses the approved 50-minute allocation and a 30-minute worker cap. Its forecast is 23.75 worker minutes and 37.75 allocation minutes, leaving 6.25 and 12.25 minutes of headroom. Placement and submission remain with the authorized lane.

The lane can place the depth package at `/project/community/jjyeung/a89e8fdab55d4`. This builder has not placed or submitted the package. The production fetch path has passed a local injected-failure test.

| Artifact | Bytes |
| --- | ---: |
| `out/delivery.tgz` | 3,727,046 |
| Expanded inner payload (32 MiB limit) | 31,068,394 |
| Installed package files | 4,274,076 |
| Installed `BUILD.json` | 60,216 |
| Streamed `orchard/o_place.sh` | 5,054,833 |
| Conservative delivery + installed files + descriptor | 8,061,338 |

Delivery SHA256: `fc8ba8028fb6ffd735b2527bb4a44e750b3d9541a1b51bee7d27007604de6f3a`.

The job uses `a15_cot_apa89e8fdab55d4`, `--partition=debug --qos=debug_qos`, `--gres=gpu:1`, `--cpus-per-task=16`, `--mem=200G`, and `--exclude=orchard-community-4`. The worker checks for an H100 before model loading. The inherited submission checker requires a minimum 50-minute allocation. The worker has a 30-minute cap and a deadline 270 seconds before allocation end; termination and reaping allow at most another 25 seconds. Staging and work share a deadline 240 seconds before allocation end. Capture publication stops 90 seconds before allocation end, normal publication stops 10 seconds before it, and the failure-receipt fallback stops two seconds before it. Every transfer uses the remaining time in its window. The forecast is 23.75 worker minutes and 37.75 allocation minutes. This includes 16.75 minutes of T1 replay, six minutes for shared loading, one minute for indexed RGB extraction and telemetry, ten minutes for shared staging, and four minutes for publication. The allowances are unmeasured.

After re-review, run these commands from the authorized lane holding this directory. Wait for each background script's printed log to report completion before starting its dependent step. Check job status at most once per minute. The scripts refuse an existing destination and use one-use submission locks; do not retry a killed or failed command automatically.

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
sha256sum --check --quiet SHA256SUMS
ssh orchard 'bash -s' < orchard/o_place.sh
# Wait for verified placement.
ssh orchard 'bash -s' < orchard/o_cpu.sh
# Wait for the CPU job (up to 50 minutes; it ends with the CPU real unit) and its authenticated CPU.json receipt to pass.
ssh orchard 'bash -s' < orchard/o_sub_hand.sh
# Wait for the GPU job to finish.
ssh orchard 'bash -s' < orchard/o_fetch.sh
# Wait for the authenticated fetch into the package's a/f directory.
mkdir -p returned
ssh orchard 'bash -s' < orchard/o_get.sh | pv -q -L 8000000 > returned/receipts.tgz
tar -xzf returned/receipts.tgz -C returned
```

`returned/4.json` is the depth upload receipt: URI, immutable generation, SHA256, size, and verification status. `returned/5.json` contains camera/scale parity. The small `returned/0.tgz` contains normal job receipts. Failed camera/scale parity does not suppress the depth return.

Retrieve the depth gzip through the lane's governed stream, using `returned/4.json`. Expected compressed size is 40 MB; the conservative budget is 80 MB and the enforced cap is 1,000,000,000 bytes. The supplied transport uses one GCS stream, an 8 MiB/s throttle, and the direct InfiniBand destination on trinity-2-28. It creates only `r1/returned/0.gz`, refuses overwrite, and verifies bytes and SHA256.

From the authorized transport session on trinity-3-30, with the script and receipt available locally:

```bash
bash orchard/pull_depth.sh returned/4.json
```

This prints a stopped process-group ID. The governor must register and resume that group before any bytes move. No governor API is assumed. The builder did not run this script. Internet ingress shares the user's cluster allowance; coordinate it with other streams.

After the authenticated return lands on this node:

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B relift.py \
  --depth returned/0.gz --receipt returned/4.json --out out/RELIFT.json
```

The CLI first checks all 150 items at the registered 0.00 m printed-gap tolerance. Each of the two operands inherits its item's gap-match flag; at least 95% must match. Failed parity writes a STOP result and evaluates no intervention cells. Missing depth writes `depth return missing` and exits successfully. `--half-only` explicitly tests float16-only sensitivity under the same gate; the default reconstructs the exact served depth from float16 plus its lossless residual.

Rebuild and CPU-test locally:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build_depth.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_all.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/check_imports.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_failure.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_import_audit.py
```

`build_depth.py` authenticates the exact T1 delivery and capture, preserves the 296 retained serving/evaluator source files byte for byte under opaque paths, and reseals the worker, plan, operator, batch bundle, descriptors, and scripts. It reads the named sibling inputs and writes under `r1/`. The package checks the tower source digest before large staging. It authenticates runtime inputs before the worker import gate, then stages the bulk archives, indexes RGB offsets without extracting those frames, and materializes only capture 1. The mixed runtime archive streams only CPython before boot; its remaining members follow boot success. The worker runs that tower before loading the shared carrier, reuses its output for the first depth record, flushes that record, then stages each later capture on demand. Segmentation weights, receipt, source, and selector inputs have no pins, preparation settings, or extracted files. Required archive paths and file paths are already opaque; no external alias is needed.

The CPU rehearsal runs twice and scans all eight output files by name, raw content, and JSON-decoded string against the deny-list. The item copy retains exact `a0` source bytes; the copied dispatcher uses opaque source storage and passes the numeric entry test. `out/CPU_ENTRY_STUB.json` records every scanned output file and hash.

`out/VALIDATION.json` records `passed=true` for the exact delivery SHA256: 100 tests, both fresh-process import checks, all 335 Python files compiled and all seven shell scripts checked. The required suites cover the CPU rehearsal twice, scans of every produced file, capture doubles, first-write ordering, per-capture telemetry, production failure fetch, source pins and deadlines. `out/IMPORT_AUDIT.json` parses all 345 delivered and embedded Python programs, including the 296 retained sources and 26 vendor files. It walks deferred imports and literal dynamic imports, resolves nonliteral loaders through explicit targets, and lists every excluded site with its reason. Ten external packages use the unchanged authenticated T1 environment pins and T1 execution evidence; local CPU installations do not establish Orchard availability. The audit test fails on any unresolved reachable import. No live Orchard job ran.

JSON transport uses an `a0` envelope containing the exact original bytes in hexadecimal. The numeric launchers, import loader, placement/fetch scripts, and local relift CLI decode it. Package pins authenticate stored bytes; preparation and resource checks authenticate the original decoded bytes. Job-owned metadata and capture records use this transport. The runtime environment archive retains its installed third-party library layout.

Worker exceptions retain their final 200 traceback lines in `metadata/7.json`; child output, operator exceptions, allocation exceptions, preparation output, and allocation-child output use `metadata/8.json` through `12.json`. Each file uses a0-hex storage and enters the authenticated receipt archive. Lines are capped at 2,048 characters. Decode locally with `runtime/j.py`. Abrupt process death cannot supply a Python traceback; the parent retains available child output and its failure receipt.

The delivered CPU rehearsal verifies the original tower source digest and dynamic imports before exercising its CPU weight doubles.

Capture receipts in `metadata/5.json` update once per second and after phase changes. Each row contains capture identity, elapsed seconds, sampled capture RSS peak, exact cumulative process RSS high-water mark, GPU maximum allocated bytes since capture start, and status. `metadata/13.json` retains the last 200 bounded log entries. Both use atomic a0-hex writes. Phase codes are 0 (binding/staging), 1 (first tower), 2 (shared carrier load), 3 (prefill/geometry), and 4 (publication to the depth file). The first capture includes shared worker startup; later captures include their RGB staging. Abrupt death can lose up to one heartbeat, and sampled RSS can miss shorter peaks; the cumulative kernel high-water mark remains exact at each snapshot.

The shared environment and full worker import closure precede every checkpoint, weight, processor and frame extraction. Those bulk inputs follow only a successful boot receipt; they are required to compute the first served scale. Existing multipart tar archives must be fully authenticated once, including any co-packaged later RGB bytes; later RGB rasters are neither extracted nor decoded until their own capture. A missing/corrupt vendor tree fails before those archives. The full tower/GPU path cannot be guaranteed to fail within two minutes of allocation start without measuring shared staging; no such timing has been claimed.

The production failure-fetch regression injects a worker exception, publishes real local pool receipts, runs the unchanged Python block from `orchard/o_fetch.sh` and the delivered numeric fetch entry with a local pool binding, then decodes `metadata/7.json` from fetched `0.tgz`. It validates package pins, plan, both receipts, and inner identity. `out/FAILURE_CHECKS.json` records the delivery hash and fetched artifact. Cloud transport is disabled for this local test.

The forecast is 1,005.01 seconds of measured T1 replay, 360 seconds for shared loading, 60 seconds for indexed RGB staging/telemetry, 600 seconds for shared archive staging and 240 seconds for publication: 2,265.01 seconds total. The allowances are unmeasured. The 30-minute worker cap leaves 374.99 seconds beyond the worker forecast. Even a worker that consumes the full cap fits with staging and publication allowances in 44 minutes, leaving six allocation minutes; the forecast does not justify raising the cap to 35 minutes.

For allocation end E = start + 3,000 seconds (bounded by SLURM_JOB_END_TIME), the worker stops at min(worker start + 1,800, E − 270). Its latest stop is minute 45:30; staging/work end by 46:00; capture publication ends by 48:30; normal publication ends by 49:50; the fallback receipt ends by 49:58. All subprocess and pool transfers use the time remaining in their window. `out/BUDGET_CHECK.json` records these windows and the 734.99-second allocation margin.

Submission creates and size-checks regular files `a/19` (stdout), `a/24` (stderr), and `a/21` (trap records) before calling sbatch. It refuses symlinks, nonregular files, and files already at the 524,288-byte cap. Both launchers use these durable paths with append mode. The helper accepts only the sealed `BATCH.sh` bytes and refuses alternate batch bodies before submission. Submission calls no collector, FIFO, queue poll, or extra allocation step, and preserves sbatch's exit status even when stdout contains a numeric job ID.

The first shell command sets `ulimit -S -f 512`. ERR/EXIT traps record status, line number and job ID in `a/21`; the shell and Python supervisor retain the 524,288-byte limit. Only the bulk worker restores its limit after receiving bounded pipe output descriptors. Existing child sinks retain at most 131,072 bytes of durable output and bounded tracebacks. Every supervisor or sink exception sets a nonzero status. Recovery replaces an existing success receipt with an authenticated failure return and preserves the exception even if diagnostic saves fail.

If the shell fails before publishing a receipt, production fetch requires a nonzero terminal trap record for the requested job. The sealed recovery helper packages the bounded diagnostics into an authenticated failure return on the fetch host's local temporary disk, then runs the normal receipt validation and fetch. Overflow records `E83` plus the affected file number. The pool write probe uses 131,072 bytes, which fits beneath the supervisor's file-size cap. Shell and scheduler diagnostics occupy at most 1,572,864 bytes across the three files, below their 2 MB allowance.

`out/REVIEW9_CHECKS.json` verifies all delivered output routes, regular-file admission, overflow through inherited descriptors, and production fetch after overflow. `out/REVIEW10_CHECKS.json` verifies sink startup failure, premature sink exit, first-line exceptions inside and before the supervisor, and nonzero submission status with a numeric job ID. `out/REVIEW11_CHECKS.json` verifies production fetch after a successful child publishes an authenticated success receipt and sink cleanup then fails with a drain error, timeout, or persistent diagnostic-save error. Each fetched return reports FAILED and contains the sink exception. Tests substitute local filesystem bindings and scheduler calls; no live scheduler behavior is claimed. The only `/dev/null` source literal is a serving policy's system-read allowlist.

Before bulk staging, both allocation routes require the active kernel mount ID to identify an ext4 `/dev/` filesystem whose `/tmp` mount root contains `job_tmp/<job ID>`. tmpfs, xfs, btrfs and an unassigned `/tmp` are refused.

The total `/project` reservation is **48,000,000 bytes per job**, including placement and extraction. These are conservative write allowances, not a claim about current disk usage:

| Component | Enforced allowance (bytes) |
| --- | ---: |
| Delivery, installed package and descriptor | 10,000,000 |
| Shell and scheduler diagnostic files | 2,000,000 |
| CPU receipts and Python metadata/diagnostics, including accounting writes | 2,000,000 |
| Pool write test, publication, partial copies and receipts | 12,000,000 |
| Fetch framing, archive write, logs, receipts and extracted summaries | 20,000,000 |
| Small scheduler control files and reserve | 2,000,000 |
| **Total** | **48,000,000** |

Placement refuses totals above its allowance. `runtime/q.py` reserves cumulative package metadata bytes under a file lock before each write; pool operations reserve cumulative writes before copying, including retained write-test and partial files. Normal publication is capped at 6 MB, with a maximum 5,899,999-byte archive. Fetch refuses archives above 5.9 MB, caps transfer logs at 64 KiB and each extracted summary at 200 KB, and refuses a pre-existing fetch destination. Its stream and archive remain below the 20 MB allowance. Submission controls and the submitted shell/supervisor use 512 KiB per-file limits. Oversized publication raises into the supervisor, which publishes a small authenticated failure. Bulk payload extraction, CPU rehearsal outputs and all recovery working files remain on the job disk.

CPU and GPU submission call the same packaged `submit` function and send identical `BATCH.sh` bytes, environment, `--export=NONE`, `--chdir=/tmp`, append output paths, signal, time, memory, CPU count, account, partition and exclusion. The sole Slurm flag difference is omission of `--gres=gpu:1` for CPU. The identical bootstrap selects rehearsal when the scheduler assigns no GPUs or the package has no CPU receipt yet; otherwise it validates the CPU proof, restores A_N/A_T/A_I/A_C from the receipt and invokes real `job.main`.

`out/BOOTSTRAP_CHECKS.json` exercises real `job.main`, ext4 admission and job environment creation with no inherited A_* values. Only Orchard filesystem bindings, mount observations, cloud transport and external bulk staging are substituted locally. First-line, extraction, missing-USER and oversized-publication failures must return their causes through the production fetch. `out/REVIEW8_CHECKS.json` records submission equivalence, persistent diagnostics and budget rejection before writes. `out/ENVIRONMENT_INVENTORY.json` lists every environment reference in a conservative superset of all delivered serving sources and embedded programs, with source lines, expressions, available keys and provisioning/default sources. Third-party internals belong to the pinned runtime environment.
