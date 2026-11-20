The delivery below uses the approved 50-minute allocation and a 30-minute worker cap. Its forecast is 23.75 worker minutes and 37.75 allocation minutes, leaving 6.25 and 12.25 minutes of headroom. Placement and submission remain with the authorized lane.

The lane can place the depth package at `/project/community/jjyeung/a6f198d3c7b20`. This builder has not placed or submitted the package. The production fetch path has passed a local injected-failure test.

| Artifact | Bytes |
| --- | ---: |
| `out/delivery.tgz` | 3,715,001 |
| Expanded inner payload (32 MiB limit) | 30,865,034 |
| Installed package files | 4,064,775 |
| Installed `BUILD.json` | 59,356 |
| Streamed `orchard/o_place.sh` | 5,037,629 |
| Conservative delivery + installed files + descriptor | 7,839,132 |

Delivery SHA256: `15f344079a052891137d1fd28ec9a20c4f8a41b60f92af624fdd96dcccf2b548`.

The job uses `a15_cot_apa6f198d3c7b20`, general, `--gres=gpu:1`, `--cpus-per-task=16`, `--mem=200G`, and `--exclude=orchard-community-4`. The worker checks for an H100 before model loading. The inherited submission checker requires a minimum 50-minute allocation. The worker has a 30-minute cap and a deadline 270 seconds before allocation end; termination and reaping allow at most another 25 seconds. Staging and work share a deadline 240 seconds before allocation end. Capture publication stops 90 seconds before allocation end, normal publication stops 10 seconds before it, and the failure-receipt fallback stops two seconds before it. Every transfer uses the remaining time in its window. The forecast is 23.75 worker minutes and 37.75 allocation minutes. This includes 16.75 minutes of T1 replay, six minutes for shared loading, one minute for indexed RGB extraction and telemetry, ten minutes for shared staging, and four minutes for publication. The allowances are unmeasured.

After re-review, run these commands from the authorized lane holding this directory. Wait for each background script's printed log to report completion before starting its dependent step. Check job status at most once per minute. The scripts refuse an existing destination and use one-use submission locks; do not retry a killed or failed command automatically.

```bash
cd /scratch/jjyeung/orch_n30/lever1_c/r1
sha256sum --check --quiet SHA256SUMS
ssh orchard 'bash -s' < orchard/o_place.sh
# Wait for verified placement.
ssh orchard 'bash -s' < orchard/o_cpu.sh
# Wait for the CPU job and its authenticated CPU.json receipt to pass.
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

`build_depth.py` authenticates the exact T1 delivery and capture, preserves the 296 retained serving/evaluator source files byte for byte under opaque paths, and reseals the worker, plan, operator, batch bundle, descriptors, and scripts. It reads the named sibling inputs and writes under `r1/`. The package checks the tower source digest before large staging. It authenticates the existing shared archives once, indexes RGB offsets without extracting those frames, and materializes only capture 1. The worker runs that tower before loading the shared carrier, reuses its output for the first depth record, flushes that record, then stages each later capture on demand. Segmentation weights, receipt, source, and selector inputs have no pins, preparation settings, or extracted files. Required archive paths and file paths are already opaque; no external alias is needed.

The CPU rehearsal runs twice and scans all eight output files by name, raw content, and JSON-decoded string against the deny-list. The item copy retains exact `a0` source bytes; the copied dispatcher uses opaque source storage and passes the numeric entry test. `out/CPU_ENTRY_STUB.json` records every scanned output file and hash.

`out/VALIDATION.json` records `passed=true` for the exact delivery SHA256: 59 tests, both fresh-process import checks, all 333 Python files compiled and all seven shell scripts checked. The required suites cover the CPU rehearsal twice, scans of every produced file, capture doubles, first-write ordering, per-capture telemetry, production failure fetch, source pins and deadlines. `out/IMPORT_AUDIT.json` parses all 343 delivered and embedded Python programs, including the 296 retained sources and 26 vendor files. It walks deferred imports and literal dynamic imports, resolves nonliteral loaders through explicit targets, and lists every excluded site with its reason. Ten external packages use the unchanged authenticated T1 environment pins and T1 execution evidence; local CPU installations do not establish Orchard availability. The audit test fails on any unresolved reachable import. No live Orchard job ran.

JSON transport uses an `a0` envelope containing the exact original bytes in hexadecimal. The numeric launchers, import loader, placement/fetch scripts, and local relift CLI decode it. Package pins authenticate stored bytes; preparation and resource checks authenticate the original decoded bytes. Job-owned metadata and capture records use this transport. The runtime environment archive retains its installed third-party library layout.

Worker exceptions retain their final 200 traceback lines in `metadata/7.json`; child output, operator exceptions, allocation exceptions, preparation output, and allocation-child output use `metadata/8.json` through `12.json`. Each file uses a0-hex storage and enters the authenticated receipt archive. Lines are capped at 2,048 characters. Decode locally with `runtime/j.py`. Abrupt process death cannot supply a Python traceback; the parent retains available child output and its failure receipt.

The delivered CPU rehearsal verifies the original tower source digest and dynamic imports before exercising its CPU weight doubles.

Capture receipts in `metadata/5.json` update once per second and after phase changes. Each row contains capture identity, elapsed seconds, sampled capture RSS peak, exact cumulative process RSS high-water mark, GPU maximum allocated bytes since capture start, and status. `metadata/13.json` retains the last 200 bounded log entries. Both use atomic a0-hex writes. Phase codes are 0 (binding/staging), 1 (first tower), 2 (shared carrier load), 3 (prefill/geometry), and 4 (publication to the depth file). The first capture includes shared worker startup; later captures include their RGB staging. Abrupt death can lose up to one heartbeat, and sampled RSS can miss shorter peaks; the cumulative kernel high-water mark remains exact at each snapshot.

The shared environment, step-544 carrier/private-head weights, tower weights, processor assets, and their authentication remain up front. They are required to compute the first served scale. Existing multipart tar archives must be fully authenticated once, including any co-packaged later RGB bytes; later RGB rasters are neither extracted nor decoded until their own capture. A missing/corrupt vendor tree fails before those archives. The full tower/GPU path cannot be guaranteed to fail within two minutes of allocation start without measuring shared staging; no such timing has been claimed.

The production failure-fetch regression injects a worker exception, publishes real local pool receipts, runs the unchanged Python block from `orchard/o_fetch.sh` and the delivered numeric fetch entry with a local pool binding, then decodes `metadata/7.json` from fetched `0.tgz`. It validates package pins, plan, both receipts, and inner identity. `out/FAILURE_CHECKS.json` records the delivery hash and fetched artifact. Cloud transport is disabled for this local test.

The forecast is 1,005.01 seconds of measured T1 replay, 360 seconds for shared loading, 60 seconds for indexed RGB staging/telemetry, 600 seconds for shared archive staging and 240 seconds for publication: 2,265.01 seconds total. The allowances are unmeasured. The 30-minute worker cap leaves 374.99 seconds beyond the worker forecast. Even a worker that consumes the full cap fits with the staging and publication allowances in 44 minutes, leaving six allocation minutes; the forecast does not justify raising the cap to 35 minutes.

For allocation end E = start + 3,000 seconds (bounded by SLURM_JOB_END_TIME), the worker stops at min(worker start + 1,800, E − 270). Its latest stop is minute 45:30; staging/work end by 46:00; capture publication ends by 48:30; normal publication ends by 49:50; the fallback receipt ends by 49:58. All subprocess and pool transfers use the time remaining in their window. `out/BUDGET_CHECK.json` records these windows and the 734.99-second allocation margin.

The batch first routes stdout/stderr through a pipe into the independently capped hex sink `a/20` (131,072 bytes), recording truncation in `a/22` (two bytes). The shell and supervisor keep their 524,288-byte file-size limit; ERR/EXIT traps append status and line number to `a/21`. The supervisor gives the bulk worker bounded pipe descriptors before restoring that child's file-size limit for job-disk staging. Recovery modules execute inside the protected block and build returns on the assigned job disk.

Slurm writes to FIFO `a/19`, which stores zero file bytes. The submission process opens its reader before `sbatch --wait`, drains into `a/24` (131,072 bytes), and records truncation in `a/25` (two bytes). It stays alive during queueing and execution, drains pending bytes at job completion, and joins the reader. CPU and GPU submissions serialize through `a/28`; no collector daemon is created. Keep the existing submission session alive until it completes. The background script prints its job ID after completion, including a failed job that Slurm accepted. The retained vendor launcher uses this same output route.

`out/REVIEW9_CHECKS.json` scans all delivered files, nested archives, embedded code and shell scripts for discard routes, and overflows both channels through direct file descriptors. The scheduler test writes 128 MiB across two submissions; the supervisor test writes 64 MiB and then passes the authenticated production failure fetch. Both sinks remain at 128 KiB, and truncation markers persist. The diagnostic bound, including a full trap file, is 786,436 bytes. The only `/dev/null` source literal is an unchanged serving policy's system-read allowlist; no submission flag or redirection uses it.

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

CPU and GPU submission call the same packaged `submit` function and send identical `BATCH.sh` bytes, environment, `--export=NONE`, `--chdir=/tmp`, append output paths, signal, time, memory, CPU count, account, partition and exclusion. The sole Slurm flag difference is omission of `--gres=gpu:1` for CPU. The identical bootstrap selects rehearsal when the scheduler assigns no GPUs; otherwise it validates the CPU proof, restores A_N/A_T/A_I/A_C from the receipt and invokes real `job.main`.

`out/BOOTSTRAP_CHECKS.json` exercises real `job.main`, ext4 admission and job environment creation with no inherited A_* values. Only Orchard filesystem bindings, mount observations, cloud transport and external bulk staging are substituted locally. First-line, extraction, missing-USER and oversized-publication failures must return their causes through the production fetch. `out/REVIEW8_CHECKS.json` records submission equivalence, persistent diagnostics and budget rejection before writes. `out/ENVIRONMENT_INVENTORY.json` lists every environment reference in a conservative superset of all delivered serving sources and embedded programs, with source lines, expressions, available keys and provisioning/default sources. Third-party internals belong to the pinned runtime environment.
