The delivery preserves the frozen 580 prompts, greedy decoding, 64-token cap and first-call-opening stop. No tool response is served. The checkpoint is step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`.

Token: `d93a17be024f5`. Job: `a15_cot_apd93a17be024f5`.
Delivery: **4,235,885 bytes**, SHA-256 `9d023abcd0335d57ce99f02e54961b20838c3114c9cd3b537056d4532ca2ef36`.
Frozen SHA-256: `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`.

The lane places and submits; this builder ran only local CPU checks. Use the existing approved transport to place `out/delivery.tgz` at `/project/community/jjyeung/okh7/add93a17be024f5/0.tgz`. The checkpoint, environment and frame archives already on Orchard remain pinned and are reused.

Place and authenticate once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apd93a17be024f5
D=/project/community/jjyeung/okh7/add93a17be024f5/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 4235885
assert hashlib.sha256(src.read_bytes()).hexdigest() == '9d023abcd0335d57ce99f02e54961b20838c3114c9cd3b537056d4532ca2ef36'
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
P=/project/community/jjyeung/okh7/a15_cot_apd93a17be024f5
/usr/bin/python3 -I -s -B "$P/3.py" cpu
```

After the CPU job finishes, fetch its success or failure return explicitly:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apd93a17be024f5
R=/project/community/jjyeung/okh7/afd93a17be024f5c
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" c
```

After a successful CPU preflight, submit the GPU job once. The controller itself requires the successful CPU receipt and matching package, payload and frozen hashes before submission:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apd93a17be024f5
/usr/bin/python3 -I -s -B "$P/3.py" submit
```

The resource arguments fix general, one GPU, 16 CPUs, 200G, 30 minutes, `--exclude=orchard-community-4` and `--no-requeue`. The CPU job omits the GPU request. Submission-attempt markers prevent duplicate submissions. A killed job must not be retried without the user's answer.

Fetch the GPU success or failure return:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apd93a17be024f5
R=/project/community/jjyeung/okh7/afd93a17be024f5
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R" g
```

The authenticated archive is `$R/0.tgz`; its receipt is `$R/1.json`. JSON receipts and result lines use `{"a0":"<hex bytes>"}`. Return members are paired results `0.jsonl`, summary `1.json`, optional controller traceback `2.json`, per-batch timings `3.jsonl`, and optional worker traceback `4.json`. Tracebacks retain the last 200 lines, capped at 120 characters per line and 24,000 ASCII bytes before packing. Controller and worker errors have separate files so both survive. The saved `0.stream` is hex-packed; the original framed protocol still authenticates the archive in memory. Both expanded and compressed returns stay below 50 MB. Every completed arm pair is flushed and synced immediately; an interrupted final pair is omitted during finalization. The scorer decodes envelopes locally. Decode diagnostics only after bringing the archive back locally:

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

All **24 CPU tests pass**. They include eleven injected failures in each of CPU and GPU modes followed by real fetch, real delivered-worker subprocess failures with locally decoded tracebacks, bounded diagnostic and output scans, slow/fast batch admission with fetched timing records, interrupted-pair retention, the real staging allowance, native batch parity, and the actual CPU runtime/restore with tiny pinned inputs and processor doubles. `out/FIX_CHECKS.json` records every file scanned during that rehearsal. Expanded delivery: 15,210,568 bytes; inner payload: 13,065,735 bytes, both below 32 MiB.

`NAMING_AUDIT.json` records opaque physical source names and raw/JSON-decoded output scans. Logical names and generated text are decoded only in memory. Its remaining exceptions are limited to fixed kernel/CUDA interfaces and immutable external runtime/model assets required by native libraries; each has a stated reason. Production GPU cache contents were not exercised here.

Reproduce locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B finish.py
```
