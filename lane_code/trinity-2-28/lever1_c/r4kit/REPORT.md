The delivery passes **42 local CPU tests**, including staged-interpreter imports and forced early failures in both modes through real authenticated fetch. No placement, submission, network access or GPU execution occurred.

Token: `f68a2d7c903be`. Job: `a15_cot_apf68a2d7c903be`.
Delivery: **4,255,483 bytes**. SHA-256: `233ee0816bc9a6e39c999519cbe0944a1b024518c1c0e61a7925b043254dbd66`.
Frozen SHA-256: `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`. FROZEN.json and the checkpoint pin remain unchanged.

Both streams now reach every return. The controller, namespace supervisor and worker capture output as it arrives; success, partial, failure and overflow cases pass fetch. CPU/GPU memory-stop tests return their failure reason, RSS and stream fields. CUDA telemetry uses a CPU double in tests; production GPU memory remains unmeasured.

CPU and GPU submissions use the same export policy, sanitized environment, chdir, output paths and entry script. Only the `A_M` mode value and GPU `--gres=gpu:1` differ. Both request 200G and 30 minutes. The constructor regression compares complete argument lists, script bytes and environments.

CPU preflight disables CUDA, caps address space at 32 GiB and guarded memory at 110 GiB, validates metadata and two processor batches, and skips resident full-model loading. GPU mode exposes its assigned device, loads the checkpoint and stops at 180 GiB guarded memory. Both use the same staging and namespace path.

The frozen 580 prompts, greedy 64-token limit, first-opening stop and unserved tools remain intact. Native tiny-model batch parity, opaque-source loading, naming scans, staging limits and interrupted-pair retention pass. The actual scorer accepts successful, partial and failed archives produced by real finalization and fetch.

The central timing forecast remains **1367.2 seconds (22.79 minutes)** with **20.51% headroom**. It assumes an unmeasured 2x batch-forward cost. The all-64-token forecast is 1694.2 seconds. Batch admission uses observed timings; incomplete runs receive no gate verdict.

Evidence: `out/test_probe.log`, `out/test_fixes.log`, `out/FIX_CHECKS.json`, `out/FIX3_CHECKS.json`, `out/CACHE_CHECKS.json`, `NAMING_AUDIT.json`, `FORECAST.json` and `BUILD.json`. `PLACE.md` contains exact operator commands. Full-checkpoint GPU numerical parity remains untested.

The aggregate `/project` write ceiling is **44,000,000 bytes (44 MB)** for the entire CPU-plus-GPU lifecycle, below 50 MB per job.

| Component | Reserved bytes |
| --- | ---: |
| Delivery plus extraction | 20,000,000 |
| CPU and GPU returns, including receipts | 6,000,000 |
| Both fetched archives, hex transport streams and receipts | 16,000,000 |
| Operator metadata and reservation ledger | 2,000,000 |
| Logs on `/project` | 0 |
| **Total** | **44,000,000** |

Delivery plus extraction actually uses **19,531,423 bytes**. Placement checks that sum before each extracted-file write. Each return is capped at 2 MB. Each fetch reserves 8 MB before creating files: at most 2 MB for its archive, about 5.34 MB for hex/base64 transport, and bounded receipts. The transport's `.partial` and final archive are hard links to the same bytes.

The locked ledger reserves writes before they occur. Each mode gets one finalization and one fetch; interrupted reservations remain spent. Metadata has a separate byte cap, and the ledger permits at most 128 entries. Oversized returns become capped failures. Repeated fetches and excess metadata writes fail before writing their outputs.

Bulk staging, extracted assets, caches and stream journals use only the assigned **ext4 job_tmp at `/tmp`**. The controller rejects tmpfs before bulk copying. Slurm bootstrap logs also use `/tmp`; no logs are written to `/project`. Both package levels pass the existing 32 MiB extraction allowance.

Every library cache and temporary directory points to an opaque numbered directory under the job root, including HOME, all XDG locations, Hugging Face, PyTorch/Inductor/extensions, Triton, CUDA, kernel, Matplotlib, Numba, CuPy, TileLang and FlashInfer caches. The controller sets the environment before staging; CPU and GPU launches reset the same overrides before imports. Hugging Face stays offline with telemetry disabled; CUDA and PyTorch kernel disk caches are disabled. Python bytecode and experiment tracking are disabled. No caller cache override survives.

The worker namespace exposes only this job's temporary directory and cannot see `/project`. Orchard removes the ext4 job_tmp with the job; native cache files never enter a return or fetch. `out/CACHE_CHECKS.json` lists every file written outside the job directory during a fresh-process CPU rehearsal with native libc writable-open auditing, Python mutation auditing and a complete public-tree inventory. The only files are the fixed budgeted package, ledger, CPU return and fetch allowlist; the unexpected-file list is empty. The rehearsal uses tiny authenticated inputs and processor/RGB/head-shape doubles. GPU cache contents remain unexecuted, with the same cache-location policy tested in both modes.

The GPU job requests **200G (200 GiB)**. Its conservative planning peak is **187 GB (174.2 GiB)**: approximately 96 GB host RSS from the old full-load preflight, 71 GB of potentially charged staged-file page cache, and 20 GB for batch buffers and overhead. The full-model GPU peak remains unmeasured.

Both supervisors poll the guarded figure every 50 ms and stop at **180 GiB (GPU)** or **110 GiB (CPU)**. The exact formula is `max(0, memory.current - min(active_file + inactive_file, max(0, file - shmem)))`. Equivalently, subtract both file LRUs and add back only their overlap with shmem. Linux file LRUs normally exclude shmem, so adding all shmem again would double-count it; the file-minus-shmem bound also protects counters that include it. Without the file/shmem pair, subtract the file LRUs directly. Missing or incomplete memory.stat/current falls back to process-tree RSS. Staging phases use the same guard. Every authenticated return records `peak_tree_rss_bytes`, `peak_cgroup_current_bytes`, `cgroup_memory_peak_bytes` (null if unavailable), and `peak_guarded_bytes`; sampled peaks merge across supervisors and staging. memory.peak is the kernel cgroup lifetime high-water, not a reset per-job counter. The guard retains 20 GiB of non-reclaimable-memory headroom under the request. The controller returns the memory-stop reason and both stream tails. External node/controller death or a spike faster than polling can still prevent finalization.

Every batch records host RSS high-water and GPU max allocated bytes. Every return includes the final observations. A 200 ms sampler covers model loading; abrupt death returns the last sampled GPU peak with `gpu_peak_complete=false`, while wait4 supplies peak host RSS. Normal completion and Python exceptions record the final CUDA peak. CPU and pre-CUDA failures report zero GPU allocation with `gpu_measured=false`.

Controller, namespace-supervisor and worker output enters opaque hex `8.log`/`9.log` journals as bytes arrive. Each stream admits at most 262,144 raw bytes; overflow fails the job. Every return carries **16,000-byte stdout and stderr tails**. Success, partial results, early failures in both modes, memory stops and log overflow pass real fetch. `out/FIX_CHECKS.json` records this evidence.

The extractor preserves every native interpreter/package path. Opaque translation applies only to authored `c/` and `v/` source trees (`src/storage.py:108`). The existing native-runtime ABI exception covers the unchanged pinned external files; no new public names or exceptions are introduced. The memory guard and FROZEN.json remain unchanged.

The CPU import regression verifies all 4,806 local pinned interpreter files after the real extractor, checks 36,009 package paths, reproduces the old missing `keyword` failure, and imports all worker import statements in a fresh staged interpreter with `-X importtime`. The worker reaches `restore` without loading checkpoint weights. Namespace test mode: production namespace. The original Orchard environment archive/boot wrapper is not local; the test reproduces its `runpy.run_path` operation and uses local p1cpu packages. `IMPORTS.md` and `out/IMPORT_CHECKS.json` record the exact evidence and limits.

Both CPU and GPU jobs follow this order: authenticate and materialize the package; stream only the complete CPython tree from runtime group 0; stage the group 1 environment, a4 entry/overlay and bwrap; run the real worker's import closure through the production interpreter, namespace, environment and cwd; require its boot receipt; then stage all remaining archives and run the workload. Group 0's other members and all of group 2, the checkpoint, base assets, frames and preparation inputs wait for boot success. The streamed mixed archive is authenticated in full but never copied before boot.

Pre-bulk bytes: 104,949,562 CPython file bytes; 8,612,076,000 environment/overlay archives plus bwrap; 2,121,649 package archive bytes; total **8,719,147,211 bytes** copied or selectively materialized. Authentication also reads the 1,621,422,080-byte mixed interpreter archive without staging its other members. The environment and overlay expand to another 8,530,064,849 file bytes; the package expands to 13,101,240 bytes plus materialized private sources. These are separate source-transfer and expansion counts, not a measured disk high-water.

Local successful pre-bulk checks took 2.263–2.269 seconds with tiny staging fixtures and read-only local runtime binds. Production pre-bulk seconds remain unmeasured; each return records them in `execution.boot.pre_bulk_seconds`, alongside bytes, mode, interpreter, cwd, closure digest and import duration. Boot uses the existing 600-second staging deadline. The overall forecast retains its existing staging allowance; it does not claim measured Orchard boot time.

The four boot tests use the delivered worker, the exact pinned `v/py` and `v/boot.py`, both production supervisors, the production namespace constructor with local runtime fixture binds, and real finalization/fetch. In both modes, an omitted private module fails with **zero bulk bytes staged**, and its traceback survives authenticated fetch. `out/BOOT_CHECKS.json` pins these checks to this delivery. The test uses local p1cpu libraries; full production-environment execution remains an Orchard check.
