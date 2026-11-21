"""Recompute the local review evidence and placement instructions."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('b',ROOT/'build.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

def read(n):return json.loads((ROOT/n).read_text())
def save(n,v):(ROOT/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:return {m.name:t.extractfile(m).read() for m in t}

build=read('BUILD.json');checks=read('out/FIX_CHECKS.json');tests=read('TEST_RESULTS.json')
assert B.pin((ROOT/'out/delivery.tgz').read_bytes()) == build['delivery']
assert B.digest((ROOT/'FROZEN.json').read_bytes()) == build['frozen'] == (ROOT/'FROZEN.sha256').read_text().split()[0]
assert checks['passed'] and tests['passed']
imports=read('out/IMPORT_CHECKS.json')
assert imports['passed'] and imports['delivery']==build['delivery']
boots=read('out/BOOT_CHECKS.json')
assert boots['passed'] and boots['delivery']==build['delivery']
assert tests['delivery']==checks['delivery']==build['delivery']
trace=read('out/WORKER_IMPORT_TRACE.json')
closure=read('IMPORT_CLOSURE.json')
assert trace['passed'] and trace['source_delivery']==build['delivery']
assert closure['generator_sha256']==B.digest((ROOT/'tests/trace_worker.py').read_bytes())
assert set(closure['required_modules']) == (set(read('tests/import_baseline.json')['modules']) | set(trace['modules'])) - set(closure['exclusions']) - set(closure['gpu_only'])
assert closure['closure_sha256']==imports['closure']['closure_sha256']
assert all(c['bulk_bytes']==0 for c in boots['cases'] if c['missing'])
for case in boots['cases']:
    if not case['missing']:
        expected=set(closure['required_modules']) | (set(closure['gpu_only']) if case['mode']=='g' else set())
        assert set(case['boot']['required_modules'])==expected
        assert case['boot']['closure_sha256']==closure['closure_sha256']
build['boot']['local_pre_bulk_seconds']=[min(c['boot']['pre_bulk_seconds'] for c in boots['cases'] if not c['missing']),max(c['boot']['pre_bulk_seconds'] for c in boots['cases'] if not c['missing'])]
save('BUILD.json',build)
test_count=tests['tests']+checks['tests']+imports['tests']+boots['tests']+1
files=members((ROOT/'out/delivery.tgz').read_bytes());payload=members(files['0.tgz'])
cfg=B.storage.loads(files['2.json']);sources=B.storage.loads(files['8.bin'])
assert cfg['import_closure']==closure
assert build['boot']['closure']['cpu_modules']==closure['cpu_modules']
assert build['boot']['closure']['gpu_modules']==closure['gpu_modules']
f=read('FORECAST.json');mapping=read('PAIR_MAP.json');ids={m['source_id'] for m in mapping};positions={}
for line in (ROOT/'in/D400/ret/metadata/reads/0/metadata/journals/3/0/items.jsonl').open():
    r=json.loads(line)
    if r['id'] in ids:
        toks=r['output']['tokens'];positions[r['id']]=next(i+2 for i in range(len(toks)-1) if toks[i:i+2]==[27,1884])
steps=[max(positions[m['source_id']] for m in mapping[i:i+4]) for i in range(0,len(mapping),4)]
fixed_worker=f['model_load_s']+580*(f['per_item_other_mean_s']+f['prefill_mean_s'])
decode=sum(steps)*2*f['tool_free_decode_s_per_token'];worker=fixed_worker+decode;total=f['base_other_s']+worker
f.update(token=build['token'], delivery=build['delivery'],
    boot=build['boot'],
    interpreter_exposure=build['interpreter_exposure'],
    project_budget=build['project_budget'], gpu_memory=build['gpu_memory'],
    memory_guard=dict(formula=build['gpu_memory']['guard_formula'],fallback=build['gpu_memory']['guard_fallback'],gpu_stop_bytes=180*1024**3,cpu_stop_bytes=110*1024**3,return_fields=['peak_tree_rss_bytes','peak_cgroup_current_bytes','cgroup_memory_peak_bytes','peak_guarded_bytes']),
    submission_parity=dict(export_policy='A_M only; c/g selects mode',chdir='/tmp',entry='4.sh executes /usr/bin/python3 -I -s -B 3.py work',output='/tmp/<opaque job name>-%j.8.log and .9.log',differences=['GPU adds --gres=gpu:1','A_M=c versus A_M=g selects the preflight/read'],time='00:30:00 in both modes'),
    cpu_preflight=dict(worker_address_space_limit_bytes=32*1024**3,
        guarded_memory_stop_bytes=110*1024**3, staging_filesystem='ext4',
        tensors='meta shapes only; processor and two CPU prompt batches',
        production_measured=False, diagnostic='DEBUG.md'),
    batch_timing_return='3.jsonl: packed per-batch preparation, prefill, slowest synchronized token-step, total seconds, completed pairs, admission estimate, remaining time, host peak RSS and GPU max allocated bytes',
    batch_admission='First batch requires 60 seconds plus a 10-second reserve. Later batches require the maximum of 60 seconds, 1.25 times every observed batch elapsed time, and 1.25 times (preparation + prefill + 64 times slowest token-step seconds), plus the reserve. Whole pair batches only; estimates cannot guarantee future speed or prevent an external interruption.',
    batch_size=8,batches=len(steps),batch_forward_multiplier=2.0,
    batch_decode_ticks=sum(steps),batch_decode_s=decode,predicted_worker_s=worker,
    predicted_total_s=total,predicted_gpu_minutes=total/60,planning_gpu_minutes=30,
    effective_worker_cutoff_from_controller_start_s=1720,controller_subprocess_cutoff_s=1730,
    headroom_fraction=1-total/1720,headroom_s=1720-total,
    worker_headroom_fraction=1-worker/1500,headroom_requirement_passed=total<=.8*1720,
    all_64_token_worker_minutes=(fixed_worker+len(steps)*64*2*f['tool_free_decode_s_per_token'])/60,
    all_64_token_total_s=f['base_other_s']+fixed_worker+len(steps)*64*2*f['tool_free_decode_s_per_token'],
    formula='base overhead + model load + 580*(per-item other + serial prefill) + sum(batch maximum opening tokens)*2*serial token seconds',
    ordering='ORIG, REVSI for each item; four consecutive complete pairs per batch; final batch has two pairs',
    inference='D400 [27,1884] opening positions, duplicated across the two arms; group maxima account for unequal stops. Both arms assumed to open as early as D400.',
    batching_assumption='An eight-row token forward costs twice a serial token forward. This GPU estimate is unmeasured; CPU timing is not used as a GPU speed estimate.',
    caveat='Full-checkpoint GPU numerical parity, batch memory use, speed and ext4 sync/supervisor overhead are unmeasured. Slow openings/staging can still yield a partial return with no gate verdict.',
    cpu_parity_evidence='out/FIX_CHECKS.json:evidence.native_cpu_parity',
    code_pins={str(p.relative_to(ROOT)):B.pin(p.read_bytes()) for p in (ROOT/'src/batch.py',ROOT/'src/runtime.py',ROOT/'src/monitor.py',ROOT/'src/control.py')})
assert f['headroom_requirement_passed'];save('FORECAST.json',f)

inventory=[]
def check(text):
    hits=[w for w in B.DENY if w in text.lower()];assert not hits,(text[:90],hits)
def strings(v):
    if isinstance(v,str):check(v)
    elif isinstance(v,dict):
        for k,x in v.items():strings(k);strings(x)
    elif isinstance(v,list):
        for x in v:strings(x)
for label,container in [('delivery',files),('payload',payload)]:
    for name,raw in container.items():
        check(name)
        if name.endswith('.tgz'):continue
        check(raw.decode())
        try:strings(json.loads(raw))
        except ValueError:pass
        inventory.append(dict(scope=label,name=name,**B.pin(raw)))
source_paths={name:B.storage.mapped(name) for name in sources}
for name in source_paths.values():check(name)
for key in ('package','token'):check(cfg[key])
for group in cfg['assets']['groups']:
    for path,_,_ in group:check(path)
for archive in cfg['inputs']['archives']:
    check(archive['destination'])
    for part in archive['parts']:check(part['path'])
for pin in cfg['inputs']['files'].values():check(pin['path'])
exceptions=[
    dict(value='/dev',reason='The kernel exposes assigned accelerator devices through this fixed device namespace.'),
    dict(value='--dev-bind',reason='The existing bubblewrap namespace uses this fixed CLI option to expose kernel device nodes.'),
    dict(value='CUDA_VISIBLE_DEVICES (key only)',reason='Slurm supplies CUDA assignment through this fixed NVIDIA interface; its value is still deny-scanned.'),
    dict(value='Pinned third-party runtime archives and their installed library files: assets.groups, inputs destination d/v',
         reason='Python/native extension import and dynamic-linker ABIs require the upstream library names and contents. Authored sources use the opaque loader; no blanket environment exemption exists.'),
    dict(value='Pinned external binary checkpoints, RGBs, tokenizer/config/tensor-index files under d/b, d/m400/full_weights, d/f and their unchanged links/copies under d/e/base and d/e/full_weights; original manifest tar under d/o',
         reason='Native tokenizer/model readers and export authentication require the exact upstream vocabulary, architecture and tensor identifiers. These immutable external inputs cannot be text-renamed without changing the frozen checkpoint or breaking native readers.'),
    dict(value='Authenticated external archive bytes temporarily copied into the numeric staging directory',
         reason='These are the previously placed pinned inputs, authenticated before extraction. They retain original binary contents; retained job metadata is encoded during extraction and excluded roots are never extracted.'),
    dict(value='Library-owned cache internals under <ext4 job root>/0/<number> only',
         reason='Native cache formats may retain library identifiers. Every cache root is opaque and job-local; Orchard teardown removes it. These files are excluded from all public package/return/fetch outputs, and /project is absent from the worker namespace.')]
audit=dict(passed=True,deny_list=B.DENY,case_sensitive=False,match='literal substring',delivery=build['delivery'],token=build['token'],
    interpreter_exposure=dict(policy=build['interpreter_exposure'],new_public_names=[],new_external_exceptions=[],evidence='out/IMPORT_CHECKS.json'),
    checks=inventory,source_files=len(source_paths),renamed_source_paths=sum(a!=b for a,b in source_paths.items()),source_paths=source_paths,
    source_storage='Every authored source/resource is stored in an a0 hex envelope at a path whose components pass the deny-list. Import names and decoded program text exist only in memory; __file__ uses the opaque path.',
    json_storage='Job metadata and returned JSON/JSONL use a0 hex envelopes. Scans check raw text and JSON-decoded keys/strings (including escaped Unicode). Intentional hex payload decoding occurs only in memory or in the local scorer.',
    archive_scanning='Archive names and decompressed members are scanned recursively; compressed binary byte coincidences are not textual identifiers.',
    cpu_rehearsal=checks['evidence']['cpu_rehearsal'],remaining_external_interfaces=exceptions,
    logs='Controller, namespace supervisor and worker capture both streams as they arrive into opaque hex journals on job_tmp. Each stream keeps a 16,000-byte tail and caps its journal at 262,144 raw bytes; overflow fails the job. Every return carries both tails. Controller and worker tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes, inside a0 hex envelopes. The saved transport stream is also hex-packed.',
    cache_isolation=dict(closed=True,paths=checks['evidence']['cache_environment']['paths'],
        flags=checks['evidence']['cache_environment']['flags'],
        placement='Every cache/temp override points to <ext4 job root>/0/<number>; controller sets this before staging and launch resets every override for both modes. Inherited environment is allowlisted.',
        lifetime='The assigned ext4 job_tmp is owned and removed by Orchard job teardown. Cache files are excluded from all return/fetch member lists and are never copied to /project.',
        namespace='Only the job root is bound at its /tmp path; the worker cannot see /project. Other writable scratch/lustre aliases resolve to subdirectories of that same job root.',
        native_file_policy='Third-party cache internals may retain native identifiers only within the ephemeral job directory; public package, return and fetch names and contents retain the deny scan.',
        audited_sources=['orchard_job.environment','e2e_reader.parity.make_real write_roots','student_pilot.common kernel cache paths','step0_runtime_v1.run_cell','run_clean_offline_tests','Hugging Face constants and transformers hub','torch cpp_extension and inductor cache_dir_utils'],
        inactive_overrides='The allowlist drops STUDENT_KERNEL_CACHE_ROOT/TAG and STUDENT_MEMORY_PROBE_CACHE, so optional persistent kernel/probe overrides cannot replace the job-local paths.',
        clean_preflight=checks['evidence']['clean_preflight_writes']),
    limitations='The CPU rehearsal uses tiny pinned export inputs, a head-shape proof double, and processor/RGB doubles. The clean CPU process uses native libc writable-open auditing, Python mutation auditing and a complete public-tree inventory checked against a fixed allowlist. Direct native syscalls are outside the preload audit; no GPU execution is claimed. GPU computation and native cache contents remain unexecuted; GPU mode uses the same checked cache environment and namespace containment.')
save('NAMING_AUDIT.json',audit)
sha=build['delivery']['sha256'];size=build['delivery']['bytes'];token=build['token'];package=build['package'];frozen=build['frozen']
dest='/project/community/jjyeung/okh7/ad'+token+'/0.tgz';ret='/project/community/jjyeung/okh7/af'+token
place=f'''The delivery preserves the frozen 580 prompts, greedy decoding, 64-token cap and first-call-opening stop. No tool response is served. The checkpoint is step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`.

Token: `{token}`. Job: `a15_cot_ap{token}`.
Delivery: **{size:,} bytes**, SHA-256 `{sha}`.
Frozen SHA-256: `{frozen}`.

The lane places and submits; this builder ran only local CPU checks. Use the existing approved transport to place `out/delivery.tgz` at `{dest}`. The checkpoint, environment and frame archives already on Orchard remain pinned and are reused.

Place and authenticate once:

```bash
P={package}
D={dest}
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == {size}
assert hashlib.sha256(src.read_bytes()).hexdigest() == '{sha}'
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
P={package}
/usr/bin/python3 -I -s -B "$P/3.py" cpu
```

After the CPU job finishes, fetch its success or failure return explicitly:

```bash
P={package}
R={ret}c
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" c
```

After a successful CPU preflight, submit the GPU job once. The controller itself requires the successful CPU receipt and matching package, payload and frozen hashes before submission:

```bash
P={package}
/usr/bin/python3 -I -s -B "$P/3.py" submit
```

The resource arguments fix general, one GPU, 16 CPUs, 200G, 30 minutes, `--exclude=orchard-community-4` and `--no-requeue`. Both modes use the same `--export=A_M=...` policy, `--chdir=/tmp`, output/error paths under `/tmp`, 30-minute limit, 200G request, sanitized submission environment and `4.sh` entry into `/usr/bin/python3 -I -s -B 3.py work`. The only submission differences are `A_M=c` versus `A_M=g` to select the workload and `--gres=gpu:1` for GPU mode. Inside the namespace, CPU hides CUDA, uses a 32 GiB address-space cap and a 110 GiB non-reclaimable-memory stop, and returns after processor checks; GPU exposes its assigned device, loads the full model and uses a 180 GiB stop. These differences keep preflight light while checking the same staging and launch path. Submission-attempt markers prevent duplicate submissions. A killed job must not be retried without the user's answer.

Fetch the GPU success or failure return:

```bash
P={package}
R={ret}
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" g
```

The authenticated archive is `$R/0.tgz`; its receipt is `$R/1.json`. JSON receipts and result lines use `{{"a0":"<hex bytes>"}}`. Return members are paired results `0.jsonl`, summary `1.json`, optional controller traceback `2.json`, per-batch timings `3.jsonl`, and worker failure diagnostics `4.json` (traceback when available, exact return code/signal, last stage, peak host RSS, GPU max allocated bytes, and hex-packed stdout/stderr tails at each execution layer). Tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes before packing. Controller and worker errors have separate files so both survive. The saved `0.stream` is hex-packed; the original framed protocol still authenticates the archive in memory. Both expanded and compressed returns are capped at 2 MB. A result-budget overflow returns a capped failure; it never publishes an oversized archive. A one-use reservation ledger caps cumulative project writes, including interrupted attempts and both fetches; retries cannot consume new slots. Every completed arm pair is flushed and synced immediately; an interrupted final pair is omitted during finalization. The scorer decodes envelopes locally. Decode diagnostics only after bringing the archive back locally:

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

The central forecast is **{total:.1f} seconds ({total/60:.2f} minutes)**, including {f['base_other_s']:.1f} seconds of measured D400 overhead. The worker estimate is **{worker:.1f} seconds**. This leaves **{100*f['headroom_fraction']:.2f}% headroom** before the effective 1,720-second cutoff. Worker execution also has a 1,500-second cap. Staging has a 600-second total cap and 300-second step caps; submission has a 60-second timeout; worker launch uses the remaining deadline; finalization reserves up to 50 seconds.

Eight-row batches retain serial video prefills, then left-pad and merge the native hybrid caches for greedy token forwards. Prompts remain pair-interleaved. The forecast assumes each eight-row token forward costs twice a serial forward and both arms open as early as D400. GPU throughput, memory use and full-checkpoint numerical parity remain unmeasured. The all-64-token estimate is {f['all_64_token_total_s']:.1f} seconds and assumes the same unmeasured cost. Each admitted batch records preparation, prefill, slowest synchronized token-step and total time, plus complete-pair counts. Admission requires a full batch estimate plus 10 seconds: initially 60 seconds; thereafter the maximum of 60 seconds, 1.25 times observed batch duration, and 1.25 times (preparation + prefill + 64 slowest token steps). The worker stops admitting batches if that estimate will not fit. An unexpected slowdown can still interrupt a batch; only complete pairs are returned. The tiny native CPU model produced identical tokens for eight unequal-length prompts, including EOS and 64-token stops. `FORECAST.json` records the model and its limits.

All **{test_count} CPU tests pass**. They include eleven injected failures in each of CPU and GPU modes followed by real fetch, real delivered-worker subprocess failures with locally decoded tracebacks, SIGKILL/SIGTERM/hard-exit/deadline diagnostics through real fetch in both modes, active-mount checks and metadata-only head loading, bounded diagnostic and output scans, slow/fast batch admission with fetched timing records, interrupted-pair retention, the real staging allowance, native batch parity, and the actual CPU runtime/restore with tiny pinned inputs and processor doubles. `out/FIX_CHECKS.json` records every file scanned during that rehearsal. Expanded delivery: {build['expanded_delivery_bytes']:,} bytes; inner payload: {build['expanded_payload_bytes']:,} bytes, both below 32 MiB.

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
'''
contract=f"""
The aggregate `/project` write ceiling is **44,000,000 bytes (44 MB)** for the entire CPU-plus-GPU lifecycle, below 50 MB per job.

| Component | Reserved bytes |
| --- | ---: |
| Delivery plus extraction | 20,000,000 |
| CPU and GPU returns, including receipts | 6,000,000 |
| Both fetched archives, hex transport streams and receipts | 16,000,000 |
| Operator metadata and reservation ledger | 2,000,000 |
| Logs on `/project` | 0 |
| **Total** | **44,000,000** |

Delivery plus extraction actually uses **{build['delivery']['bytes']+build['expanded_delivery_bytes']:,} bytes**. Placement checks that sum before each extracted-file write. Each return is capped at 2 MB. Each fetch reserves 8 MB before creating files: at most 2 MB for its archive, about 5.34 MB for hex/base64 transport, and bounded receipts. The transport's `.partial` and final archive are hard links to the same bytes.

The locked ledger reserves writes before they occur. Each mode gets one finalization and one fetch; interrupted reservations remain spent. Metadata has a separate byte cap, and the ledger permits at most 128 entries. Oversized returns become capped failures. Repeated fetches and excess metadata writes fail before writing their outputs.

Bulk staging, extracted assets, caches and stream journals use only the assigned **ext4 job_tmp at `/tmp`**. The controller rejects tmpfs before bulk copying. Slurm bootstrap logs also use `/tmp`; no logs are written to `/project`. Both package levels pass the existing 32 MiB extraction allowance.

Every library cache and temporary directory points to an opaque numbered directory under the job root, including HOME, all XDG locations, Hugging Face, PyTorch/Inductor/extensions, Triton, CUDA, kernel, Matplotlib, Numba, CuPy, TileLang and FlashInfer caches. The controller sets the environment before staging; CPU and GPU launches reset the same overrides before imports. Hugging Face stays offline with telemetry disabled; CUDA and PyTorch kernel disk caches are disabled. Python bytecode and experiment tracking are disabled. No caller cache override survives.

The worker namespace exposes only this job's temporary directory and cannot see `/project`. Orchard removes the ext4 job_tmp with the job; native cache files never enter a return or fetch. `out/CACHE_CHECKS.json` lists every file written outside the job directory during a fresh-process CPU rehearsal with native libc writable-open auditing, Python mutation auditing and a complete public-tree inventory. The only files are the fixed budgeted package, ledger, CPU return and fetch allowlist; the unexpected-file list is empty. The rehearsal uses tiny authenticated inputs and processor/RGB/head-shape doubles. GPU cache contents remain unexecuted, with the same cache-location policy tested in both modes.

The GPU job requests **200G (200 GiB)**. Its conservative planning peak is **187 GB (174.2 GiB)**: approximately 96 GB host RSS from the old full-load preflight, 71 GB of potentially charged staged-file page cache, and 20 GB for batch buffers and overhead. The full-model GPU peak remains unmeasured.

Both supervisors poll the guarded figure every 50 ms and stop at **180 GiB (GPU)** or **110 GiB (CPU)**. The exact formula is `max(0, memory.current - min(active_file + inactive_file, max(0, file - shmem)))`. Equivalently, subtract both file LRUs and add back only their overlap with shmem. Linux file LRUs normally exclude shmem, so adding all shmem again would double-count it; the file-minus-shmem bound also protects counters that include it. Without the file/shmem pair, subtract the file LRUs directly. Missing or incomplete memory.stat/current falls back to process-tree RSS. Staging phases use the same guard. Every authenticated return records `peak_tree_rss_bytes`, `peak_cgroup_current_bytes`, `cgroup_memory_peak_bytes` (null if unavailable), and `peak_guarded_bytes`; sampled peaks merge across supervisors and staging. memory.peak is the kernel cgroup lifetime high-water, not a reset per-job counter. The guard retains 20 GiB of non-reclaimable-memory headroom under the request. The controller returns the memory-stop reason and both stream tails. External node/controller death or a spike faster than polling can still prevent finalization.

Every batch records host RSS high-water and GPU max allocated bytes. Every return includes the final observations. A 200 ms sampler covers model loading; abrupt death returns the last sampled GPU peak with `gpu_peak_complete=false`, while wait4 supplies peak host RSS. Normal completion and Python exceptions record the final CUDA peak. CPU and pre-CUDA failures report zero GPU allocation with `gpu_measured=false`.

Controller, namespace-supervisor and worker output enters opaque hex `8.log`/`9.log` journals as bytes arrive. Each stream admits at most 262,144 raw bytes; overflow fails the job. Every return carries **16,000-byte stdout and stderr tails**. Success, partial results, early failures in both modes, memory stops and log overflow pass real fetch. `out/FIX_CHECKS.json` records this evidence.
"""
import_contract=f'''
The extractor preserves every native interpreter/package path. Opaque translation applies only to authored `c/` and `v/` source trees (`src/storage.py:108`). The existing native-runtime ABI exception covers the unchanged pinned external files; no new public names or exceptions are introduced. The memory guard and FROZEN.json remain unchanged.

The CPU import regression verifies all {imports['runtime_files']:,} local pinned interpreter files after the real extractor, checks {imports['package_paths_checked']:,} package paths, reproduces the old missing `keyword` failure, and replays the recorded worker import closure in a fresh staged interpreter with `-X importtime`. The worker reaches `restore` without loading checkpoint weights. Namespace test mode: {imports['mode']}. The original Orchard environment archive/boot wrapper is not local; the test reproduces its `runpy.run_path` operation and uses local p1cpu packages. `IMPORTS.md` and `out/IMPORT_CHECKS.json` record the exact evidence and limits.
'''
place += contract+import_contract
boot_text = f"""
Both CPU and GPU jobs follow this order: authenticate and materialize the package; stream only the complete CPython tree from runtime group 0; stage the group 1 environment, a4 entry/overlay and bwrap; run the real worker's import closure through the production interpreter, namespace, environment and cwd; require its boot receipt; then stage all remaining archives and run the workload. Group 0's other members and all of group 2, the checkpoint, base assets, frames and preparation inputs wait for boot success. The streamed mixed archive is authenticated in full but never copied before boot.

Pre-bulk bytes: {build['boot']['interpreter_file_bytes']:,} CPython file bytes; {build['boot']['archive_bytes']:,} environment/overlay archives plus bwrap; {build['boot']['code_archive_bytes']:,} package archive bytes; total **{build['boot']['pre_bulk_bytes']:,} bytes** copied or selectively materialized. Authentication also reads the {build['boot']['interpreter_source_bytes']:,}-byte mixed interpreter archive without staging its other members. The environment and overlay expand to another {build['boot']['environment_expanded_bytes']+build['boot']['overlay_expanded_bytes']:,} file bytes; the package expands to {build['expanded_payload_bytes']:,} bytes plus materialized private sources. These are separate source-transfer and expansion counts, not a measured disk high-water.

Local successful pre-bulk checks took {min(c['boot']['pre_bulk_seconds'] for c in boots['cases'] if not c['missing']):.3f}–{max(c['boot']['pre_bulk_seconds'] for c in boots['cases'] if not c['missing']):.3f} seconds with tiny staging fixtures and read-only local runtime binds. Production pre-bulk seconds remain unmeasured; each return records them in `execution.boot.pre_bulk_seconds`, alongside bytes, mode, interpreter, cwd, closure digest and import duration. Boot uses the existing 600-second staging deadline. The overall forecast retains its existing staging allowance; it does not claim measured Orchard boot time.

The recorded closure contains **{closure['cpu_modules']:,} CPU modules** and **{closure['gpu_modules']:,} GPU modules**, compared with {closure['baseline_modules']:,} importable modules in the prior {closure['baseline_raw_modules']:,}-entry inventory. `tests/trace_worker.py` runs the delivered `runtime.run` on CPU with `sys.addaudithook('import')`, through real restore/meta shape checking, processor construction, model loading with tiny native weights, routed prompt preparation and the first eight-row batch. `tests/record_import_closure.py` unions the successful runtime inventory with `tests/import_baseline.json`; `IMPORT_CLOSURE.json` records every module, digest and exclusion. `src/runtime.py:106` imports every required module before bulk staging. No AST/source scan derives this closure.

CPU replay excludes `fla`, `triton` and `causal_conv1d`; GPU replay requires all three before bulk. Trace harness aliases, local test modules, generated Cython/PyTorch runtime helpers and unsuccessful optional import probes are listed individually with reasons in `IMPORT_CLOSURE.json:exclusions`. Native aliases are imported after their canonical modules. The trace uses tiny tokenizer/RGB/checkpoint boundaries; full-checkpoint GPU execution remains unmeasured.

The four boot tests use the delivered worker, the exact pinned `v/py` and `v/boot.py`, both production supervisors, the production namespace constructor with local runtime fixture binds, and real finalization/fetch. In both modes, omitting the lazy `student_pilot.carrier_c1_canary` module fails with **zero bulk bytes staged**, and its traceback survives authenticated fetch. `out/BOOT_CHECKS.json` pins these checks to this delivery. The test uses local p1cpu libraries; full production-environment execution remains an Orchard check.
"""
place += boot_text
(ROOT/'PLACE.md').write_text(place)
report=f"""The delivery passes **{test_count} local CPU tests**, including staged-interpreter imports and forced early failures in both modes through real authenticated fetch. No placement, submission, network access or GPU execution occurred.

Token: `{token}`. Job: `a15_cot_ap{token}`.
Delivery: **{size:,} bytes**. SHA-256: `{sha}`.
Frozen SHA-256: `{frozen}`. FROZEN.json and the checkpoint pin remain unchanged.

Both streams now reach every return. The controller, namespace supervisor and worker capture output as it arrives; success, partial, failure and overflow cases pass fetch. CPU/GPU memory-stop tests return their failure reason, RSS and stream fields. CUDA telemetry uses a CPU double in tests; production GPU memory remains unmeasured.

CPU and GPU submissions use the same export policy, sanitized environment, chdir, output paths and entry script. Only the `A_M` mode value and GPU `--gres=gpu:1` differ. Both request 200G and 30 minutes. The constructor regression compares complete argument lists, script bytes and environments.

CPU preflight disables CUDA, caps address space at 32 GiB and guarded memory at 110 GiB, validates metadata and two processor batches, and skips resident full-model loading. GPU mode exposes its assigned device, loads the checkpoint and stops at 180 GiB guarded memory. Both use the same staging and namespace path.

The frozen 580 prompts, greedy 64-token limit, first-opening stop and unserved tools remain intact. Native tiny-model batch parity, opaque-source loading, naming scans, staging limits and interrupted-pair retention pass. The actual scorer accepts successful, partial and failed archives produced by real finalization and fetch.

The central timing forecast remains **{total:.1f} seconds ({total/60:.2f} minutes)** with **{100*f['headroom_fraction']:.2f}% headroom**. It assumes an unmeasured 2x batch-forward cost. The all-64-token forecast is {f['all_64_token_total_s']:.1f} seconds. Batch admission uses observed timings; incomplete runs receive no gate verdict.

Evidence: `out/test_probe.log`, `out/test_fixes.log`, `out/FIX_CHECKS.json`, `out/FIX3_CHECKS.json`, `out/CACHE_CHECKS.json`, `NAMING_AUDIT.json`, `FORECAST.json` and `BUILD.json`. `PLACE.md` contains exact operator commands. Full-checkpoint GPU numerical parity remains untested.
"""
report += contract+import_contract
report += boot_text
(ROOT/'REPORT.md').write_text(report)
save('out/BUILD.json',build)
save('out/FINAL_CHECKS.json',dict(passed=True,token=token,delivery=build['delivery'],tests=test_count,frozen=frozen,
    project_budget=build['project_budget'],gpu_memory=build['gpu_memory'],forecast_seconds=total,headroom_fraction=f['headroom_fraction'],artifact=cfg['export']['artifact']['sha256']))
names = [line.split(None, 1)[1] for line in (ROOT/'SHA256SUMS').read_text().splitlines()]
names = sorted(set(names) | {'REPORT.md', 'finish.py', 'tests/test_fixes.py', 'tests/cache_preflight.py', 'tests/write_audit.c', 'out/CACHE_CHECKS.json', 'src/storage.py', 'src/batch.py', 'src/monitor.py', 'DEBUG.md', 'out/fail1_code/control.py', 'out/fail1_code/runtime.py', 'out/FIX_CHECKS.json', 'out/FINAL_CHECKS.json'})
names = sorted(set(names) | {'IMPORT_CLOSURE.json','tests/import_baseline.json','tests/trace_worker.py','tests/record_import_closure.py','out/WORKER_IMPORT_TRACE.json','out/trace_worker.log','IMPORTS.md', 'tests/test_imports.py', 'tests/import_worker.py', 'out/IMPORT_CHECKS.json', 'out/test_imports.log', 'tests/test_boot.py', 'out/BOOT_CHECKS.json', 'out/test_boot.log'})
(ROOT/'SHA256SUMS').write_text(''.join(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in names))
print(json.dumps(read('out/FINAL_CHECKS.json'),sort_keys=True))
