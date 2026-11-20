The delivery passes **35 local CPU tests**, including forced early failures in both modes through real authenticated fetch. No placement, submission, network access or GPU execution occurred.

Token: `e71c940a6b283`. Job: `a15_cot_ape71c940a6b283`.
Delivery: **4,250,122 bytes**. SHA-256: `3ca1fd77d3cd021210bae2ef31d0c323bd3d8bd0d1cf3e2b5df12410c91232af`.
Frozen SHA-256: `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`. FROZEN.json and the checkpoint pin remain unchanged.

Both streams now reach every return. The controller, namespace supervisor and worker capture output as it arrives; success, partial, failure and overflow cases pass fetch. CPU/GPU memory-stop tests return their failure reason, RSS and stream fields. CUDA telemetry uses a CPU double in tests; production GPU memory remains unmeasured.

CPU and GPU submissions use the same export policy, sanitized environment, chdir, output paths and entry script. Only the `A_M` mode value and GPU `--gres=gpu:1` differ. Both request 200G and 30 minutes. The constructor regression compares complete argument lists, script bytes and environments.

CPU preflight disables CUDA, caps address space at 32 GiB and charged memory at 110 GiB, validates metadata and two processor batches, and skips resident full-model loading. GPU mode exposes its assigned device, loads the checkpoint and stops at 180 GiB charged memory. Both use the same staging and namespace path.

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

Delivery plus extraction actually uses **19,506,279 bytes**. Placement checks that sum before each extracted-file write. Each return is capped at 2 MB. Each fetch reserves 8 MB before creating files: at most 2 MB for its archive, about 5.34 MB for hex/base64 transport, and bounded receipts. The transport's `.partial` and final archive are hard links to the same bytes.

The locked ledger reserves writes before they occur. Each mode gets one finalization and one fetch; interrupted reservations remain spent. Metadata has a separate byte cap, and the ledger permits at most 128 entries. Oversized returns become capped failures. Repeated fetches and excess metadata writes fail before writing their outputs.

Bulk staging, extracted assets, caches and stream journals use only the assigned **ext4 job_tmp at `/tmp`**. The controller rejects tmpfs before bulk copying. Slurm bootstrap logs also use `/tmp`; no logs are written to `/project`. Both package levels pass the existing 32 MiB extraction allowance.

Every library cache and temporary directory points to an opaque numbered directory under the job root, including HOME, all XDG locations, Hugging Face, PyTorch/Inductor/extensions, Triton, CUDA, kernel, Matplotlib, Numba, CuPy, TileLang and FlashInfer caches. The controller sets the environment before staging; CPU and GPU launches reset the same overrides before imports. Hugging Face stays offline with telemetry disabled; CUDA and PyTorch kernel disk caches are disabled. Python bytecode and experiment tracking are disabled. No caller cache override survives.

The worker namespace exposes only this job's temporary directory and cannot see `/project`. Orchard removes the ext4 job_tmp with the job; native cache files never enter a return or fetch. `out/CACHE_CHECKS.json` lists every file written outside the job directory during a fresh-process CPU rehearsal with native libc writable-open auditing, Python mutation auditing and a complete public-tree inventory. The only files are the fixed budgeted package, ledger, CPU return and fetch allowlist; the unexpected-file list is empty. The rehearsal uses tiny authenticated inputs and processor/RGB/head-shape doubles. GPU cache contents remain unexecuted, with the same cache-location policy tested in both modes.

The GPU job requests **200G (200 GiB)**. Its conservative planning peak is **187 GB (174.2 GiB)**: approximately 96 GB host RSS from the old full-load preflight, 71 GB of potentially charged staged-file page cache, and 20 GB for batch buffers and overhead. The full-model GPU peak remains unmeasured.

Both supervisors poll charged memory every 50 ms and stop their child at **180 GiB (193,273,528,320 bytes)**, leaving 20 GiB below the request. Staging phases also check memory. Missing production counters cause a failure. The controller returns the memory-stop reason and both stream tails. External node/controller death or a spike faster than polling can still prevent finalization.

Every batch records host RSS high-water and GPU max allocated bytes. Every return includes the final observations. A 200 ms sampler covers model loading; abrupt death returns the last sampled GPU peak with `gpu_peak_complete=false`, while wait4 supplies peak host RSS. Normal completion and Python exceptions record the final CUDA peak. CPU and pre-CUDA failures report zero GPU allocation with `gpu_measured=false`.

Controller, namespace-supervisor and worker output enters opaque hex `8.log`/`9.log` journals as bytes arrive. Each stream admits at most 262,144 raw bytes; overflow fails the job. Every return carries **16,000-byte stdout and stderr tails**. Success, partial results, early failures in both modes, memory stops and log overflow pass real fetch. `out/FIX_CHECKS.json` records this evidence.
