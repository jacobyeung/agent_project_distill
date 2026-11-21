The delivery preserves the frozen 580 prompts, greedy decoding, 64-token cap and first-call-opening stop. No tool response is served. The checkpoint is step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`.

Token: `f68a2d7c903be`. Job: `a15_cot_apf68a2d7c903be`.
Delivery: **4,255,483 bytes**, SHA-256 `233ee0816bc9a6e39c999519cbe0944a1b024518c1c0e61a7925b043254dbd66`.
Frozen SHA-256: `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`.

The lane places and submits; this builder ran only local CPU checks. Use the existing approved transport to place `out/delivery.tgz` at `/project/community/jjyeung/okh7/adf68a2d7c903be/0.tgz`. The checkpoint, environment and frame archives already on Orchard remain pinned and are reused.

Place and authenticate once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apf68a2d7c903be
D=/project/community/jjyeung/okh7/adf68a2d7c903be/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 4255483
assert hashlib.sha256(src.read_bytes()).hexdigest() == '233ee0816bc9a6e39c999519cbe0944a1b024518c1c0e61a7925b043254dbd66'
dest.mkdir(mode=0o700)
with tarfile.open(src) as archive:
    seen = set(); total = 0
    for entry in archive:
        rel = PurePosixPath(entry.name)
        assert entry.isfile() and not rel.is_absolute() and '..' not in rel.parts
        assert entry.name not in seen
        seen.add(entry.name); total += entry.size
        assert total <= 32*1024**2 and total+src.stat().st_size <= 20000000
        target = dest/entry.name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with target.open('xb') as output:
            output.write(archive.extractfile(entry).read())
        target.chmod(0o600)
(dest/'a').mkdir(mode=0o700)
for name, pin in json.loads((dest/'0.json').read_text())['files'].items():
    raw = (dest/name).read_bytes()
    assert len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']
print('OK')
PYPLACE
/usr/bin/python3 -I -s -B "$P/3.py" check
```

The CPU preflight uses the assigned ext4 job_tmp bind at `/tmp`; it refuses tmpfs before copying archives. It hashes all staged inputs, checks head metadata and meta model shapes, and exercises the processor on two prompts. It loads no resident full-model weights. The CPU worker has a 32 GiB address-space ceiling and a 110 GiB non-reclaimable-memory stop. Missing memory.stat or memory.current falls back to process-tree RSS. The production peak remains unmeasured. `DEBUG.md` records the cause analysis and evidence.

Submit the CPU preflight once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apf68a2d7c903be
/usr/bin/python3 -I -s -B "$P/3.py" cpu
```

After the CPU job finishes, fetch its success or failure return explicitly:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apf68a2d7c903be
R=/project/community/jjyeung/okh7/aff68a2d7c903bec
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" c
```

After a successful CPU preflight, submit the GPU job once. The controller itself requires the successful CPU receipt and matching package, payload and frozen hashes before submission:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apf68a2d7c903be
/usr/bin/python3 -I -s -B "$P/3.py" submit
```

The resource arguments fix general, one GPU, 16 CPUs, 200G, 30 minutes, `--exclude=orchard-community-4` and `--no-requeue`. Both modes use the same `--export=A_M=...` policy, `--chdir=/tmp`, output/error paths under `/tmp`, 30-minute limit, 200G request, sanitized submission environment and `4.sh` entry into `/usr/bin/python3 -I -s -B 3.py work`. The only submission differences are `A_M=c` versus `A_M=g` to select the workload and `--gres=gpu:1` for GPU mode. Inside the namespace, CPU hides CUDA, uses a 32 GiB address-space cap and a 110 GiB non-reclaimable-memory stop, and returns after processor checks; GPU exposes its assigned device, loads the full model and uses a 180 GiB stop. These differences keep preflight light while checking the same staging and launch path. Submission-attempt markers prevent duplicate submissions. A killed job must not be retried without the user's answer.

Fetch the GPU success or failure return:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apf68a2d7c903be
R=/project/community/jjyeung/okh7/aff68a2d7c903be
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" g
```

The authenticated archive is `$R/0.tgz`; its receipt is `$R/1.json`. JSON receipts and result lines use `{"a0":"<hex bytes>"}`. Return members are paired results `0.jsonl`, summary `1.json`, optional controller traceback `2.json`, per-batch timings `3.jsonl`, and worker failure diagnostics `4.json` (traceback when available, exact return code/signal, last stage, peak host RSS, GPU max allocated bytes, and hex-packed stdout/stderr tails at each execution layer). Tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes before packing. Controller and worker errors have separate files so both survive. The saved `0.stream` is hex-packed; the original framed protocol still authenticates the archive in memory. Both expanded and compressed returns are capped at 2 MB. A result-budget overflow returns a capped failure; it never publishes an oversized archive. A one-use reservation ledger caps cumulative project writes, including interrupted attempts and both fetches; retries cannot consume new slots. Every completed arm pair is flushed and synced immediately; an interrupted final pair is omitted during finalization. The scorer decodes envelopes locally. Decode diagnostics only after bringing the archive back locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - out/return.tgz <<'PYDIAG'
import json, sys, tarfile
with tarfile.open(sys.argv[1]) as archive:
    for name in ('2.json', '4.json', '3.jsonl'):
        if name not in archive.getnames():
            continue
        for line in archive.extractfile(name):
            value = json.loads(bytes.fromhex(json.loads(line)['a0']))
            print(name, value.get('traceback', value))
PYDIAG
```

Bring the small archive back through the lane's approved transport, save it as `out/return.tgz`, and run:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B score.py out/return.tgz --out out/call_rates.json
```

The scorer uses 10,000 paired room-bootstrap draws, seed 20261120. REVSI call rate at least 95% means no change; otherwise the lane reports to the orchestrator. It gives no verdict for incomplete pairs. Arm D stays closed.

The central forecast is **1367.2 seconds (22.79 minutes)**, including 395.0 seconds of measured D400 overhead. The worker estimate is **972.1 seconds**. This leaves **20.51% headroom** before the effective 1,720-second cutoff. Worker execution also has a 1,500-second cap. Staging has a 600-second total cap and 300-second step caps; submission has a 60-second timeout; worker launch uses the remaining deadline; finalization reserves up to 50 seconds.

Eight-row batches retain serial video prefills, then left-pad and merge the native hybrid caches for greedy token forwards. Prompts remain pair-interleaved. The forecast assumes each eight-row token forward costs twice a serial forward and both arms open as early as D400. GPU throughput, memory use and full-checkpoint numerical parity remain unmeasured. The all-64-token estimate is 1694.2 seconds and assumes the same unmeasured cost. Each admitted batch records preparation, prefill, slowest synchronized token-step and total time, plus complete-pair counts. Admission requires a full batch estimate plus 10 seconds: initially 60 seconds; thereafter the maximum of 60 seconds, 1.25 times observed batch duration, and 1.25 times (preparation + prefill + 64 slowest token steps). The worker stops admitting batches if that estimate will not fit. An unexpected slowdown can still interrupt a batch; only complete pairs are returned. The tiny native CPU model produced identical tokens for eight unequal-length prompts, including EOS and 64-token stops. `FORECAST.json` records the model and its limits.

All **42 CPU tests pass**. They include eleven injected failures in each of CPU and GPU modes followed by real fetch, real delivered-worker subprocess failures with locally decoded tracebacks, SIGKILL/SIGTERM/hard-exit/deadline diagnostics through real fetch in both modes, active-mount checks and metadata-only head loading, bounded diagnostic and output scans, slow/fast batch admission with fetched timing records, interrupted-pair retention, the real staging allowance, native batch parity, and the actual CPU runtime/restore with tiny pinned inputs and processor doubles. `out/FIX_CHECKS.json` records every file scanned during that rehearsal. Expanded delivery: 15,275,940 bytes; inner payload: 13,101,240 bytes, both below 32 MiB.

`NAMING_AUDIT.json` records opaque physical source names and raw/JSON-decoded output scans. Logical names and generated text are decoded only in memory. Its remaining exceptions cover fixed kernel/CUDA interfaces, immutable external runtime/model assets, and native cache internals confined to the ephemeral job directory; each has a stated reason. Production GPU cache contents were not exercised here.

Reproduce locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_imports.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_boot.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B finish.py
```

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
