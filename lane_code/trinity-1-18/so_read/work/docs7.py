from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/kit_parity50/README.md';s=p.read_text()
s=s.replace('## Step-600 binding, build and operations','## Bound export, build and operations')
start=s.index('The owner supplies a **reviewed step-600 target template**')
end=s.index(': "${PACKAGE_TOKEN:',start)
s=s[:start]+'''The gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.

`BOUND_EXPORT` selects the gate's exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package's token.

```bash
BOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}
EXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}
'''+s[end:]
s=s.replace('$STEP600_BINDING','$EXPORT_BINDING').replace('$LOCAL/step600','$LOCAL/adopted').replace('`step600`','`adopted`')
s=s.replace('neither forecast is a step-600 measurement','neither forecast measures the selected export')
# A separate derivation route remains available for explicitly selected other exports.
pos=s.index('`adopted` retains')
s=s[:pos]+'''For a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target's reviewed export.json:

```bash
: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"
: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"
: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"
: "${TARGET_CONFIG:?Authenticated preparation config.json}"
: "${TARGET_RECEIPT:?Authenticated preparation receipt}"
: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"
: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\
  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\
  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\
  --out "$EXPORT_BINDING"
```

'''+s[pos:]
old='''P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
# Detached worker: inspect completion no more than once per minute.
while test ! -f "$P/a/1.txt"; do sleep 60; done
test "$(cat "$P/a/1.txt")" = 0'''
new='''# BEGIN FILL_WAIT
: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
FILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}
[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1
FILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))
while test ! -f "$P/a/1.txt"; do
  FILL_PID=$(cat "$P/a/0.txt") || exit 1
  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1
  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then
    echo 'Fill worker is gone without an exit receipt' >&2; exit 1
  fi
  if (( SECONDS >= FILL_DEADLINE )); then
    echo 'Fill wait exceeded its maximum' >&2; exit 1
  fi
  sleep 60
done
test "$(cat "$P/a/1.txt")" = 0
# END FILL_WAIT'''
assert old in s;s=s.replace(old,new)
# Guard before any launch as well as in the executable wait block.
s=s.replace(': "${D:?Fresh opaque operation directory on Orchard}"',': "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"')
s=s.replace('A duplicate launch refuses;', 'The wait checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours), plus one polling interval. A duplicate launch refuses;')
s=s.replace('The proof emits exact restore, artifact-binding, manifest and export-pin receipts.', 'Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts.')
s=s.replace('CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json','CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json')
s=s.replace(' -s -B ./unpack_return.py',' -s -E -B ./unpack_return.py')
s=s.replace('and checks payload, plan and operator bindings.', 'checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it.')
start=s.index('Stage the exact retained CPU data')
end=s.index('Create a private neutral configuration',start)
s=s[:start]+'''The **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job's private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.

Allocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.

```bash
salloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\
  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\
  --exclude=orchard-community-2 --job-name=ab0123456789
srun --ntasks=1 --pty bash --noprofile --norc
```

On that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.

The shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:

```bash
: "${PACKAGE_TOKEN:?Fresh package token from the build}"
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
ASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}
GPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<'PYASSET'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/'a/c/CPU.json').read_text())
assert proof['passed'] is True
with tarfile.open(p/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
asset=proof['gate_assets'];assert asset['logical']==cfg['logical']
assert asset['path']==str(p/'a/4.tar') and archive.stat().st_size==asset['bytes']
h=hashlib.sha256()
with archive.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
assert h.hexdigest()==asset['sha256']
print(cfg['logical'])
PYASSET
)
test -d /scratch/jjyeung && test -w /scratch/jjyeung
test ! -e "$GPU_LOGICAL"
mkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"
tar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"
tar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"
test ! -e "$GPU_LOGICAL/d/7.json"
cp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"
```

'''+s[end:]
s=s.replace('  --asset-receipts "$LOCAL/adopted/proof" \\', '  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\')
s=s.replace('The staged `u3.json` pins every extension;', 'The package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension;')
s=s.replace('refuses a different GPU family, compute capability or memory class', 'refuses a different exact name, SM count, compute capability or memory class')
s=s.replace('Archive it with `tar -cf "$LOCAL/5.tar" -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum "$LOCAL/5.tar"` for the authenticated return transport.', 'On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport.')
start=s.index('## Review round 6:')
s=s[:start]+'''## Review round 7: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |
| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |
| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |
| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |
| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |

Frozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.
'''
p.write_text(s)
print('README: default bound export, live-job archive, bounded fill, exact H100 allocation, receipt and host paths documented.')
