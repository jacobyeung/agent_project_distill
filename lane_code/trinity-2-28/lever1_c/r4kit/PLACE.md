The delivery contains 580 label-free prompts: 290 ORIG/REVSI pairs from 98 rooms. It stops at the first recognized call opening, EOS or token 64 and never serves a tool. Arm codes are 0 = ORIG and 1 = REVSI. The local scorer maps them back to their names.

`out/delivery.tgz`: **3,513,016 bytes**; SHA-256 `8f9778a47da1afd9158b1ed10fb62a8a4fe0448b7775d41e6476cd3a93cf1e1d`.

`FROZEN.json`: SHA-256 `3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d`.

Step-400 artifact: `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The package reuses D400's pinned Orchard archives and frame inputs directly. It omits the dedicated geometry archive and instantiates neither external tool component. Its shared environment archive remains unchanged.

The builder ran only local CPU tests. The lane runs every command below on Orchard. Use the lane's existing approved transport to put the delivery at `/project/community/jjyeung/okh7/ad3743891f7781/0.tgz`. No weights or frames need placement.

Place and authenticate the delivery once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apb3743891f7781
D=/project/community/jjyeung/okh7/ad3743891f7781/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 3513016
assert hashlib.sha256(src.read_bytes()).hexdigest() == '8f9778a47da1afd9158b1ed10fb62a8a4fe0448b7775d41e6476cd3a93cf1e1d'
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

Submit the CPU preflight once. It uses general, 16 CPUs, 200G and 30 minutes, with no GPU. It authenticates and restores the existing export, checks all 3,136 RGB pins, imports the native APIs and builds both prompt batches for one pair. It confirms their image/carrier inputs match. It allocates no full model.

```bash
P=/project/community/jjyeung/okh7/a15_cot_apb3743891f7781
/usr/bin/python3 -I -s -B "$P/3.py" cpu
```

After the CPU job finishes, require its receipt and submit the GPU job once:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apb3743891f7781
/usr/bin/python3 -I -s -B - "$P" <<'PYCPU'
import hashlib, json, sys
from pathlib import Path
p = Path(sys.argv[1]); r = json.loads((p/'a/4.json').read_text())
assert r['passed'] is True
assert r['package'] == hashlib.sha256((p/'0.json').read_bytes()).hexdigest()
assert r['payload'] == hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()
assert r['frozen'] == '3743891f778115529710461333ad09a9588b8075e2173a74fac0065dc5d0382d'
print('OK')
PYCPU
/usr/bin/python3 -I -s -B "$P/3.py" submit
```

The GPU argv fixes `--partition=general --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:30:00 --exclude=orchard-community-4 --no-requeue`. The job name is `a15_cot_apb3743891f7781`. The worker limits itself to 1,500 seconds and respects the earlier allocation deadline. Submission-attempt files prevent accidental resubmission, including after an ambiguous failure. Do not retry a killed job.

After the GPU job finishes, fetch the authenticated return using the base kit's framed-stream protocol:

```bash
P=/project/community/jjyeung/okh7/a15_cot_apb3743891f7781
R=/project/community/jjyeung/okh7/af3743891f7781
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R"
```

The return is `$R/0.tgz`, with its byte count and SHA-256 in `$R/1.json`. Both expanded and compressed returns are capped at 50,000,000 bytes. Return members are `0.jsonl` (generated text, IDs, flags and timings), `1.json` (completion and pins) and, on failure, `2.json` (opaque error fingerprint). `g` means the literal `<ground` prefix occurred; `o` lists other opener indices in `src/probe.py`. Each record retains all generated token IDs, including an EOS token if emitted. No log contains generated text.

Bring the small return back through the lane's existing transport, save it as `out/return.tgz` in this kit, and run locally:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B score.py out/return.tgz --out out/call_rates.json
```

The scorer reports per-arm call rates, their paired difference and 95% paired room-bootstrap intervals from 10,000 draws with seed 20261120. It refuses duplicates, invalid counts and mismatched flags. It issues no gate verdict unless all 290 pairs complete. REVSI >=95% means no change; below 95% means the lane reports to the orchestrator. Arm D stays closed. It computes no item-answer score.

The forecast is **29.1 GPU-minutes**, including D400's measured staging/other overhead; plan for the full 30-minute allocation. Its central worker estimate is 22.6 minutes. The estimate assumes REVSI opens as early as ORIG. If all prompts consume 64 tokens, the extrapolated worker time is 44.3 minutes, so the fixed caps will produce a partial return. `FORECAST.json` records every timing and assumption. The CPU receipt records whether the token pair used to infer D400 opening positions decodes to `<ground`.

All 14 local CPU tests passed, including Python 3.6 operator syntax/API compatibility and namespace negative cases: label allow-list and exact paired inputs; all opener families and fragmented prefixes; token 64 versus token 65; EOS; the base `extract_stream` function on both delivery and inner payload at the actual 32 MiB allowance; built-source CPU imports; package pins; submission resources and duplicate-attempt guard; complete/incomplete scoring and reproducible bootstrap. Expanded delivery: 3,995,537 bytes. Expanded inner payload: 2,220,191 bytes.

`NAMING_AUDIT.json` records the literal scan of both archive inventories and public scripts. Required private module names remain inside the encoded runtime, as in the base kit. The argument/environment guard permits the OS interfaces `--dev-bind`, `/dev`, and the key `CUDA_VISIBLE_DEVICES`; it scans CUDA device values. This implements the public-surface interpretation of the naming rule, not a ban on native module identifiers or OS vocabulary.

Reproduce the build and CPU tests from this directory:

```bash
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
```
