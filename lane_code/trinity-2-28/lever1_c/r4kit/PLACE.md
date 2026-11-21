The delivery preserves the frozen 580 prompts, greedy decoding, 64-token cap and first-call-opening stop. No tool response is served. The checkpoint is step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`.

Token: `2d1983684f183`. Superseded tokens: `f68a2d7c903be` (placed destination exists; CPU submission marker spent), `87f4ae5c2f44f` (placed destination exists; CPU submission marker spent; GPU marker used by job 173990) and `baf58c689fca5` (placed destination exists; CPU and GPU submission markers spent; GPU marker used by job 174087). Job: `a15_cot_ap2d1983684f183`.
Delivery: **4,318,129 bytes**, SHA-256 `d18d1524465ce7cb6aaaeece1ba9fbb19672dc5b6ed626ca9de1e26a513f42d9`.
Frozen SHA-256: `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`.

The lane places and submits; this builder ran only local CPU checks. Use the existing approved transport to place `out/delivery.tgz` at `/project/community/jjyeung/okh7/ad2d1983684f183/0.tgz`. The checkpoint, environment and frame archives already on Orchard remain pinned and are reused.

Place and authenticate once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap2d1983684f183
D=/project/community/jjyeung/okh7/ad2d1983684f183/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 4318129
assert hashlib.sha256(src.read_bytes()).hexdigest() == 'd18d1524465ce7cb6aaaeece1ba9fbb19672dc5b6ed626ca9de1e26a513f42d9'
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

The CPU preflight uses the assigned ext4 job_tmp bind at `/tmp`; it refuses tmpfs before copying archives. It hashes all staged inputs, checks head metadata and meta model shapes, and exercises the processor on two prompts. It loads no resident full-model weights. Before any bulk staging, the boot gate of both CPU and GPU jobs runs the delivered batched cache merge on a tiny native hybrid model in the pinned interpreter (`execution.boot.batch_selfcheck`); a merge incompatible with the installed transformers fails there with zero bulk bytes. The CPU worker has a 32 GiB address-space ceiling and a 110 GiB non-reclaimable-memory stop. Missing memory.stat or memory.current falls back to process-tree RSS. The production peak remains unmeasured. `DEBUG.md` records the cause analysis and evidence.

Submit the CPU preflight once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap2d1983684f183
/usr/bin/python3 -I -s -B "$P/3.py" cpu
```

After the CPU job finishes, fetch its success or failure return explicitly:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap2d1983684f183
R=/project/community/jjyeung/okh7/af2d1983684f183c
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" c
```

After a successful CPU preflight, submit the GPU job once. The controller itself requires the successful CPU receipt and matching package, payload and frozen hashes before submission:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap2d1983684f183
/usr/bin/python3 -I -s -B "$P/3.py" submit
```

The resource arguments fix general, one GPU, 16 CPUs, 200G, 30 minutes, `--exclude=orchard-community-4` and `--no-requeue`. Both modes use the same `--export=A_M=...` policy, `--chdir=/tmp`, output/error paths under `/tmp`, 30-minute limit, 200G request, sanitized submission environment and `4.sh` entry into `/usr/bin/python3 -I -s -B 3.py work`. The only submission differences are `A_M=c` versus `A_M=g` to select the workload and `--gres=gpu:1` for GPU mode. Inside the namespace, CPU hides CUDA, uses a 32 GiB address-space cap and a 110 GiB non-reclaimable-memory stop, and returns after processor checks; GPU exposes its assigned device, loads the full model and uses a 180 GiB stop. These differences keep preflight light while checking the same staging and launch path. Submission-attempt markers prevent duplicate submissions. A killed job must not be retried without the user's answer.

Fetch the GPU success or failure return:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap2d1983684f183
R=/project/community/jjyeung/okh7/af2d1983684f183
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" g
```

The authenticated archive is `$R/0.tgz`; its receipt is `$R/1.json`. JSON receipts and result lines use `{"a0":"<hex bytes>"}`. Return members are paired results `0.jsonl`, summary `1.json`, optional controller traceback `2.json`, per-batch timings `3.jsonl`, and worker failure diagnostics `4.json` (traceback when available, exact return code/signal, last stage, peak host RSS, GPU max allocated bytes, and hex-packed stdout/stderr tails at each execution layer). Tracebacks retain the last 200 lines, capped at 24,000 ASCII bytes; closure failures preserve full lines and separate full entry/exception fields, while other failures cap lines at 120 characters before packing. Controller and worker errors have separate files so both survive. The saved `0.stream` is hex-packed; the original framed protocol still authenticates the archive in memory. Both expanded and compressed returns are capped at 2 MB. A result-budget overflow returns a capped failure; it never publishes an oversized archive. A one-use reservation ledger caps cumulative project writes, including interrupted attempts and both fetches; retries cannot consume new slots. Every completed arm pair is flushed and synced immediately; an interrupted final pair is omitted during finalization. The scorer decodes envelopes locally. Decode diagnostics only after bringing the archive back locally:

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

All **52 CPU tests pass**. They include eleven injected failures in each of CPU and GPU modes followed by real fetch, real delivered-worker subprocess failures with locally decoded tracebacks, SIGKILL/SIGTERM/hard-exit/deadline diagnostics through real fetch in both modes, active-mount checks and metadata-only head loading, bounded diagnostic and output scans, slow/fast batch admission with fetched timing records, interrupted-pair retention, the real staging allowance, native batch parity, and the actual CPU runtime/restore with tiny pinned inputs and processor doubles. `out/FIX_CHECKS.json` records every file scanned during that rehearsal. Expanded delivery: 15,640,595 bytes; inner payload: 13,434,414 bytes, both below 32 MiB.

`NAMING_AUDIT.json` records opaque physical source names and raw/JSON-decoded output scans. Logical names and generated text are decoded only in memory. Its remaining exceptions cover fixed kernel/CUDA interfaces, immutable external runtime/model assets, and native cache internals confined to the ephemeral job directory; each has a stated reason. Production GPU cache contents were not exercised here.

Reproduce locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_imports.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_boot.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_pinned.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_pinned_batch.py
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

Delivery plus extraction actually uses **19,958,724 bytes**. Placement checks that sum before each extracted-file write. Each return is capped at 2 MB. Each fetch reserves 8 MB before creating files: at most 2 MB for its archive, about 5.34 MB for hex/base64 transport, and bounded receipts. The transport's `.partial` and final archive are hard links to the same bytes.

The locked ledger reserves writes before they occur. Each mode gets one finalization and one fetch; interrupted reservations remain spent. Metadata has a separate byte cap, and the ledger permits at most 128 entries. Oversized returns become capped failures. Repeated fetches and excess metadata writes fail before writing their outputs.

Bulk staging, extracted assets, caches and stream journals use only the assigned **ext4 job_tmp at `/tmp`**. The controller rejects tmpfs before bulk copying. Slurm bootstrap logs also use `/tmp`; no logs are written to `/project`. Both package levels pass the existing 32 MiB extraction allowance.

Every library cache and temporary directory points to an opaque numbered directory under the job root, including HOME, all XDG locations, Hugging Face, PyTorch/Inductor/extensions, Triton, CUDA, kernel, Matplotlib, Numba, CuPy, TileLang and FlashInfer caches. The controller sets the environment before staging; CPU and GPU launches reset the same overrides before imports. Hugging Face stays offline with telemetry disabled; CUDA and PyTorch kernel disk caches are disabled. Python bytecode and experiment tracking are disabled. No caller cache override survives.

The worker namespace exposes only this job's temporary directory and cannot see `/project`. Orchard removes the ext4 job_tmp with the job; native cache files never enter a return or fetch. `out/CACHE_CHECKS.json` lists every file written outside the job directory during a fresh-process CPU rehearsal with native libc writable-open auditing, Python mutation auditing and a complete public-tree inventory. The only files are the fixed budgeted package, ledger, CPU return and fetch allowlist; the unexpected-file list is empty. The rehearsal uses tiny authenticated inputs and processor/RGB/head-shape doubles. GPU cache contents remain unexecuted, with the same cache-location policy tested in both modes.

The GPU job requests **200G (200 GiB)**. Its conservative planning peak is **187 GB (174.2 GiB)**: approximately 96 GB host RSS from the old full-load preflight, 71 GB of potentially charged staged-file page cache, and 20 GB for batch buffers and overhead. The full-model GPU peak remains unmeasured.

Both supervisors poll the guarded figure every 50 ms and stop at **180 GiB (GPU)** or **110 GiB (CPU)**. The exact formula is `max(0, memory.current - min(active_file + inactive_file, max(0, file - shmem)))`. Equivalently, subtract both file LRUs and add back only their overlap with shmem. Linux file LRUs normally exclude shmem, so adding all shmem again would double-count it; the file-minus-shmem bound also protects counters that include it. Without the file/shmem pair, subtract the file LRUs directly. Missing or incomplete memory.stat/current falls back to process-tree RSS. Staging phases use the same guard. Every authenticated return records `peak_tree_rss_bytes`, `peak_cgroup_current_bytes`, `cgroup_memory_peak_bytes` (null if unavailable), and `peak_guarded_bytes`; sampled peaks merge across supervisors and staging. memory.peak is the kernel cgroup lifetime high-water, not a reset per-job counter. The guard retains 20 GiB of non-reclaimable-memory headroom under the request. The controller returns the memory-stop reason and both stream tails. External node/controller death or a spike faster than polling can still prevent finalization.

Every batch records host RSS high-water and GPU max allocated bytes. Every return includes the final observations. A 200 ms sampler covers model loading; abrupt death returns the last sampled GPU peak with `gpu_peak_complete=false`, while wait4 supplies peak host RSS. Normal completion and Python exceptions record the final CUDA peak. CPU and pre-CUDA failures report zero GPU allocation with `gpu_measured=false`.

Controller, namespace-supervisor and worker output enters opaque hex `8.log`/`9.log` journals as bytes arrive. Each stream admits at most 262,144 raw bytes; overflow fails the job. Every return carries **16,000-byte stdout and stderr tails**. Success, partial results, early failures in both modes, memory stops and log overflow pass real fetch. `out/FIX_CHECKS.json` records this evidence.

The extractor preserves every native interpreter/package path. Opaque translation applies only to authored `c/` and `v/` source trees (`src/storage.py:108`). The existing native-runtime ABI exception covers the unchanged pinned external files; no new public names or exceptions are introduced. The memory guard and FROZEN.json remain unchanged.

The CPU import regression verifies all 4,806 local pinned interpreter files after the real extractor, checks 36,009 package paths, reproduces the old missing `keyword` failure, and replays the recorded worker import closure in a fresh staged interpreter with `-X importtime`. The worker reaches `restore` without loading checkpoint weights. Namespace test mode: production namespace. This test uses local p1cpu packages. `tests/test_pinned.py` separately boots the exact delivery with the authenticated Orchard interpreter, base environment and a4 overlay in the production namespace, with CUDA hidden and no package doubles. `IMPORTS.md` and `out/IMPORT_CHECKS.json` record the exact evidence and limits.

Both CPU and GPU jobs follow this order: authenticate and materialize the package; stream only the complete CPython tree from runtime group 0; stage the group 1 environment, a4 entry/overlay and bwrap; run the real worker's import closure through the production interpreter, namespace, environment and cwd; require its boot receipt; then stage all remaining archives and run the workload. Group 0's other members and all of group 2, the checkpoint, base assets, frames and preparation inputs wait for boot success. The streamed mixed archive is authenticated in full but never copied before boot.

Pre-bulk bytes: 104,949,562 CPython file bytes; 8,612,076,000 environment/overlay archives plus bwrap; 2,153,128 package archive bytes; total **8,719,178,690 bytes** copied or selectively materialized. Authentication also reads the 1,621,422,080-byte mixed interpreter archive without staging its other members. The environment and overlay expand to another 8,530,064,849 file bytes; the package expands to 13,434,414 bytes plus materialized private sources. These are separate source-transfer and expansion counts, not a measured disk high-water.

Local successful pre-bulk checks took 4.207–4.249 seconds with tiny staging fixtures and read-only local runtime binds. The superseded package reached the Orchard boot gate in 164.381 seconds with zero bulk bytes; successful revised production staging time remains unmeasured. Each return records its timing in `execution.boot.pre_bulk_seconds`, alongside bytes, mode, interpreter, cwd, closure digest and import duration. Boot uses the existing 600-second staging deadline. The overall forecast retains its existing staging allowance. The revised CPU replay time measures boot after local extraction.

The recorded closure contains **3,228 CPU modules** and **3,229 GPU modules**, compared with 1,167 importable modules in the prior 1,170-entry inventory. `tests/trace_worker.py` runs the delivered `runtime.run` on CPU with `sys.addaudithook('import')`, through real restore/meta shape checking, processor construction, model loading with tiny native weights, routed prompt preparation and the first eight-row batch. `tests/record_import_closure.py` unions the successful runtime inventory with `tests/import_baseline.json` and applies the per-entry exclusions in `tests/pinned_exclusions.json`; `IMPORT_CLOSURE.json` records every module, digest and exclusion. `src/runtime.py:113` imports every required module before bulk staging. No AST/source scan derives this closure.

CPU replay excludes `fla`, `triton` and `causal_conv1d`. GPU replay requires `triton` before bulk. `fla` and `causal_conv1d` are optional GPU kernels (`IMPORT_CLOSURE.json:gpu_optional`): GPU boot records each one's `find_spec` result, origin and expected PyTorch fallback in `optional_modules` and never fails on its absence. Neither ships in the pinned environment, and base read D400 ran with both fallbacks. Trace harness aliases, local test modules, generated Cython/PyTorch runtime helpers and unsuccessful optional import probes are listed individually with reasons in `IMPORT_CLOSURE.json:exclusions`. Native aliases are imported after their canonical modules. The trace uses tiny tokenizer/RGB/checkpoint boundaries; full-checkpoint GPU execution remains unmeasured.

The seven boot tests use the delivered worker, the exact pinned `v/py` and `v/boot.py`, both production supervisors, the production namespace constructor with local runtime fixture binds, and real finalization/fetch. In both modes, omitting the lazy `student_pilot.carrier_c1_canary` module fails with **zero bulk bytes staged**, and its traceback survives authenticated fetch. A GPU-mode boot without `fla` and `causal_conv1d` passes and records both as absent; a GPU-mode boot without `triton` fails at boot naming `triton`, with zero bulk bytes. `out/BOOT_CHECKS.json` pins these checks to this delivery. These fetch tests use local p1cpu libraries. The pinned-environment CPU boot also passes; full-checkpoint GPU execution remains unmeasured.

The pinned CPU boot passes all 3,228 required imports in 10.287 seconds with zero bulk bytes and no package doubles. The pinned GPU-mode boot, with CUDA hidden, imports those modules plus `triton` in 10.189 seconds and records `fla` and `causal_conv1d` as absent with the PyTorch fallback expected. The pre-bulk archives were authenticated and extracted under `tmp/pinned/`; `out/PINNED_ARCHIVES.json` records their pins. The environment uses Pillow 13.0.0, NumPy 2.3.5 and Torch 2.13.0+cu130. `out/PINNED_CHECKS.json` pins the successful replay to this delivery.

The failed entry was `PIL._typing`: the pinned `PIL/_typing.py:8` imports `numbers._IntegralLike` unconditionally, while `PIL/Image.py:207–214` places that helper inside a disabled `if TYPE_CHECKING` branch. The local copy guards the numbers import. Every dropped entry and its pinned-environment reason is recorded in `tests/pinned_exclusions.json` and `IMPORT_CLOSURE.json:pinned_drops`: 110 drops reduce the CPU closure from 3,338 to 3,228 and the GPU closure from 3,341 to 3,229. The three CUDA-only exclusions are unchanged. Imports use normal module names with runtime typing semantics; no library or interpreter bytes are patched.

Closure failures retain the entry and full exception in both the worker diagnostic and boot receipt. The typing-helper regression verifies that an exception longer than 120 characters survives authenticated fetch, with zero bulk staging. Tokens `f68a2d7c903be`, `87f4ae5c2f44f` and `baf58c689fca5` are superseded by `2d1983684f183` because placement cannot overwrite their destinations and their submission markers are spent.

GPU job 174087 (token `baf58c689fca5`) booted, loaded the model (26.1 GB GPU) and failed in batch 0 after 16.8 seconds: `10.py:23` called the frozen `carrier_c1_batch_decode.merge_caches`, whose line 43 reads `.shape` from each linear-attention state. Pinned transformers 5.19.0 stores `LinearAttentionLayer.conv_states` and `recurrent_states` as `{state_idx: tensor}` dicts with per-index `is_*_initialized` and `has_previous_state` dicts (`cache_utils.py:950-957`); local 5.12.1 stores tensors and booleans, so local tests passed. The frozen module stays unchanged (FROZEN.json pins it). `src/batch.py` now owns `merge_caches` and `select_cache_rows`: it concatenates every state index, copies the flag and kernel-size dicts per merged layer, rejects mismatched flags, past-recording layers, static, sliding and offloaded caches, and still handles the tensor form. Decoding semantics are unchanged. In the pinned interpreter on CPU (`tests/test_pinned_batch.py`, `out/PINNED_BATCH_CHECKS.json`), the previous delivery reproduces the production traceback exactly; the new delivery matches serial decoding token for token in eight unequal-length rows, with EOS, 64-token-cap and first-call-opening stops and mid-batch row removal, and the boot self-check passes while the frozen merge fails it. The orchestrator-requested CPU run of the real first batch with step-400 weights did not run: the export weights (18.8 GB of bf16 shards, 2.76 GB heads.pt) and the frame archive are not on trinity-2-28; only their metadata is (`out/REAL_BATCH_CPU.json`).

GPU job 173990 (token `87f4ae5c2f44f`) failed at the boot gate on `causal_conv1d` with zero bulk bytes. `build.py` serializes `2.json` with sorted keys, so the worker tried `causal_conv1d` before `fla` and `triton`; neither of those was attempted. `fla` would also have failed: no `fla` package exists in runtime group 1, a4, a2 or a3 (only `cudnn/fla` and `vllm/third_party/flash_linear_attention` subpackages), and D400's `worker.log` lines 6–9 report the `flash-linear-attention` and `causal_conv1d` fallbacks. Transformers 5.19 resolves both kernels when `modeling_qwen3_5` is imported (`integrations/hub_kernels.py:984–1014`) and otherwise uses its PyTorch reference implementation; `kernels` is not installed, so no hub download is attempted.
