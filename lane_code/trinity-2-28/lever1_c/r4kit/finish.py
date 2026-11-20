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
assert checks['passed'] and tests['passed']
files=members((ROOT/'out/delivery.tgz').read_bytes());payload=members(files['0.tgz'])
cfg=B.storage.loads(files['2.json']);sources=B.storage.loads(files['8.bin'])
f=read('FORECAST.json');mapping=read('PAIR_MAP.json');ids={m['source_id'] for m in mapping};positions={}
for line in (ROOT/'in/D400/ret/metadata/reads/0/metadata/journals/3/0/items.jsonl').open():
    r=json.loads(line)
    if r['id'] in ids:
        toks=r['output']['tokens'];positions[r['id']]=next(i+2 for i in range(len(toks)-1) if toks[i:i+2]==[27,1884])
steps=[max(positions[m['source_id']] for m in mapping[i:i+4]) for i in range(0,len(mapping),4)]
fixed_worker=f['model_load_s']+580*(f['per_item_other_mean_s']+f['prefill_mean_s'])
decode=sum(steps)*2*f['tool_free_decode_s_per_token'];worker=fixed_worker+decode;total=f['base_other_s']+worker
f.update(token=build['token'], delivery=build['delivery'],
    batch_timing_return='3.jsonl: packed per-batch preparation, prefill, slowest synchronized token-step, total seconds, completed pairs, admission estimate and remaining time',
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
    caveat='Full-checkpoint GPU numerical parity, batch memory use and speed are unmeasured. Slow openings/staging can still yield a partial return with no gate verdict.',
    cpu_parity_evidence='out/FIX_CHECKS.json:evidence.native_cpu_parity',
    code_pins={str(p.relative_to(ROOT)):B.pin(p.read_bytes()) for p in (ROOT/'src/batch.py',ROOT/'src/runtime.py')})
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
         reason='These are the previously placed pinned inputs, authenticated before extraction. They retain original binary contents; retained job metadata is encoded during extraction and excluded roots are never extracted.')]
audit=dict(passed=True,deny_list=B.DENY,case_sensitive=False,match='literal substring',delivery=build['delivery'],token=build['token'],
    checks=inventory,source_files=len(source_paths),renamed_source_paths=sum(a!=b for a,b in source_paths.items()),source_paths=source_paths,
    source_storage='Every authored source/resource is stored in an a0 hex envelope at a path whose components pass the deny-list. Import names and decoded program text exist only in memory; __file__ uses the opaque path.',
    json_storage='Job metadata and returned JSON/JSONL use a0 hex envelopes. Scans check raw text and JSON-decoded keys/strings (including escaped Unicode). Intentional hex payload decoding occurs only in memory or in the local scorer.',
    archive_scanning='Archive names and decompressed members are scanned recursively; compressed binary byte coincidences are not textual identifiers.',
    cpu_rehearsal=checks['evidence']['cpu_rehearsal'],remaining_external_interfaces=exceptions,
    logs='The numeric worker/controller redirect native stdout/stderr before imports. Controller and worker tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes, inside a0 hex envelopes. The saved transport stream is also hex-packed.',
    limitations='The CPU rehearsal uses tiny pinned export inputs, a head-shape proof double, and processor/RGB doubles. GPU library-generated cache contents and production external assets were not executed or rescanned here.')
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
        assert total <= 32*1024**2
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

The resource arguments fix general, one GPU, 16 CPUs, 200G, 30 minutes, `--exclude=orchard-community-4` and `--no-requeue`. The CPU job omits the GPU request. Submission-attempt markers prevent duplicate submissions. A killed job must not be retried without the user's answer.

Fetch the GPU success or failure return:

```bash
P={package}
R={ret}
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" g
```

The authenticated archive is `$R/0.tgz`; its receipt is `$R/1.json`. JSON receipts and result lines use `{{"a0":"<hex bytes>"}}`. Return members are paired results `0.jsonl`, summary `1.json`, optional controller traceback `2.json`, per-batch timings `3.jsonl`, and optional worker traceback `4.json`. Tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes before packing. Controller and worker errors have separate files so both survive. The saved `0.stream` is hex-packed; the original framed protocol still authenticates the archive in memory. Both expanded and compressed returns stay below 50 MB. Every completed arm pair is flushed and synced immediately; an interrupted final pair is omitted during finalization. The scorer decodes envelopes locally. Decode diagnostics only after bringing the archive back locally:

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

All **{tests['tests']+checks['tests']} CPU tests pass**. They include eleven injected failures in each of CPU and GPU modes followed by real fetch, real delivered-worker subprocess failures with locally decoded tracebacks, bounded diagnostic and output scans, slow/fast batch admission with fetched timing records, interrupted-pair retention, the real staging allowance, native batch parity, and the actual CPU runtime/restore with tiny pinned inputs and processor doubles. `out/FIX_CHECKS.json` records every file scanned during that rehearsal. Expanded delivery: {build['expanded_delivery_bytes']:,} bytes; inner payload: {build['expanded_payload_bytes']:,} bytes, both below 32 MiB.

`NAMING_AUDIT.json` records opaque physical source names and raw/JSON-decoded output scans. Logical names and generated text are decoded only in memory. Its remaining exceptions are limited to fixed kernel/CUDA interfaces and immutable external runtime/model assets required by native libraries; each has a stated reason. Production GPU cache contents were not exercised here.

Reproduce locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B finish.py
```
'''
(ROOT/'PLACE.md').write_text(place)
report=f'''The delivery contains the three fixes and passes {tests['tests']+checks['tests']} CPU tests. No placement, submission, network access or GPU execution occurred.

Token: `{token}`. Job: `a15_cot_ap{token}`.
Delivery: **{size:,} bytes**. SHA-256: `{sha}`.
Frozen SHA-256: `{frozen}`. The frozen design and artifact pin are unchanged.

Fetch selects `a/c` or `a/g` explicitly and verifies the receipt mode. All eleven injected failure paths pass real fetch in both modes (22 cases). Delivered-worker subprocess failures in both modes return tracebacks that decode locally. Diagnostics retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes, packed as hex. Controller and worker files remain separate so a later controller failure preserves the worker traceback. Saved transport text is hex-packed and passes the deny scan. Staging, submission, launch and finalization have explicit deadlines.

Each batch writes packed preparation, prefill, slowest synchronized token-step and total timing, completed-pair count, remaining time and admission estimate to returned `3.jsonl`. The worker admits only whole pair batches when its conservative 64-token estimate plus a 10-second reserve fits. The first estimate is 60 seconds; later estimates use 1.25 times the slowest observed cost. The slow-batch regression returns four complete pairs and rejects the next batch; the fast-batch regression finishes both batches. Both timing journals pass real fetch and decode locally. Unexpected slowdowns may still interrupt an admitted batch; unfinished pairs never enter the return.

Every authored source/resource has an opaque physical path and encoded bytes. The import hook resolves real module names in memory. The real CPU runtime and restore execute against tiny pinned inputs, with doubles for head-shape proof and processor/RGB work. All {len(checks['evidence']['cpu_rehearsal']['files'])} files in that rehearsal pass raw-text and JSON-decoded scans; the deliberate escaped-string leak is rejected. The audit lists only fixed external interfaces and immutable library/model input exceptions with reasons. Full production GPU cache outputs remain untested.

Eight-row decoding uses the package's left-padded hybrid-cache merge and row compaction. The native tiny CPU model returns identical tokens for eight unequal-length prompts against serial decoding; its rows exercise EOS, compaction and the 64-token cap. Generation never enters a response-serving path. Prompt order alternates the two arms, and each finished pair is flushed and synced immediately.

The central forecast is **{total:.1f} seconds ({total/60:.2f} minutes)**, including {f['base_other_s']:.1f} seconds overhead, with **{100*f['headroom_fraction']:.2f}% headroom** before the 1,720-second effective cutoff. This assumes an eight-row token forward costs twice a serial forward; GPU throughput and checkpoint parity are unmeasured. The worker estimate is {worker:.1f} seconds, below its 1,500-second cap. The all-64-token forecast is {f['all_64_token_total_s']:.1f} seconds under the same unmeasured assumption. Timing-based admission may stop earlier; slow staging or longer openings produce an authenticated partial return without a gate verdict.

Evidence: `out/test_probe.log`, `out/test_fixes.log`, `out/FIX_CHECKS.json`, `NAMING_AUDIT.json`, `FORECAST.json`, and `BUILD.json`. `PLACE.md` contains the exact placement, CPU, submit, fetch and local scoring commands. Both package levels pass the base extractor's 32 MiB allowance.
'''
(ROOT/'REPORT.md').write_text(report)
save('out/BUILD.json',build)
save('out/FINAL_CHECKS.json',dict(passed=True,token=token,delivery=build['delivery'],tests=tests['tests']+checks['tests'],frozen=frozen,
    forecast_seconds=total,headroom_fraction=f['headroom_fraction'],artifact=cfg['export']['artifact']['sha256']))
names = [line.split(None, 1)[1] for line in (ROOT/'SHA256SUMS').read_text().splitlines()]
names = sorted(set(names) | {'REPORT.md', 'finish.py', 'tests/test_fixes.py', 'src/storage.py', 'src/batch.py', 'out/FIX_CHECKS.json', 'out/FINAL_CHECKS.json'})
(ROOT/'SHA256SUMS').write_text(''.join(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in names))
print(json.dumps(read('out/FINAL_CHECKS.json'),sort_keys=True))
