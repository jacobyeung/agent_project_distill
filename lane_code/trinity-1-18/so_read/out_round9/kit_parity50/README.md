The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.

Use the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.

The ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.

## Local preparation

These commands use paths supplied by the operator; they do not depend on the author's `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.

```bash
set -euo pipefail
: "${DELIVERY:?Absolute path to delivered out directory}"
: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"
: "${LOCAL:?Fresh local scratch directory}"
: "${READ_PYTHON:?Approved Python executable}"
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"
mkdir -p "$LOCAL/source" "$LOCAL/a4"
nice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"
nice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |
  nice -n 10 tar -xf - -C "$LOCAL/a4"
nice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"
nice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"
nice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"
nice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"
nice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"
EXT_SOURCE="$LOCAL/source"
```

Keep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.

## Bound export, build and operations

The candidate uses **A4's 636-item schedule, one card, caches only, general/no-requeue**. A4's export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.

The kit binds **step 400 only**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.

`a19 build` checks the reviewed step-400 identity and preparation hashes before reading or copying the base. No other export can authorize adoption. A fresh package token identifies the ON build; it does not reuse the source package's token.

```bash
set -euo pipefail
EXPORT_BINDING="$DELIVERY/operations/binding.default.json"
: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"
PROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \
  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"
nice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .
nice -n 10 sha256sum "$LOCAL/0.tgz"
```

`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner's existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.

```bash
set -euo pipefail
: "${OPS_ARCHIVE:?Received outer archive on Orchard}"
: "${OPS_SHA256:?Printed local SHA256 of that archive}"
: "${D:?Fresh opaque operation directory on Orchard}"
: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"
printf '%s  %s\n' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -
test ! -e "$D"
mkdir -m 700 "$D"
tar -xzf "$OPS_ARCHIVE" -C "$D"
bash "$D/o_place.sh"
bash "$D/o_pull_fill.sh"
# BEGIN FILL_WAIT
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
  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))
  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"
done
test "$(cat "$P/a/1.txt")" = 0
# END FILL_WAIT
bash "$D/o_cpu.sh"
```

`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.

`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It refuses any symlink whose resolved target leaves `logical/d` (including directory links, chains, dangling links and cycles), preserves admitted links with `tar -cf - -C <logical>/d .`, and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. Validation and tar run in the same live namespace. Tar stderr goes to `results/4.err`. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest, export-pin and ENVIRONMENT.json receipts. ON prepare adds the compiled CUDA version to ENVIRONMENT.json and its SHA256 to READY. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.

Archive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:

```bash
set -euo pipefail
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
tar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json ENVIRONMENT.json
sha256sum "$D/2.tgz"
```

After authorized transport, authenticate and extract that archive on local scratch:

```bash
set -euo pipefail
: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"
: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"
printf '%s  %s\n' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -
mkdir "$LOCAL/adopted/proof"
nice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"
```

After the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:

```bash
set -euo pipefail
: "${GATE_ARCHIVE:?Received archive containing ue.json}"
: "${GATE_SHA256:?SHA256 printed on the GPU host}"
printf '%s  %s\n' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -
mkdir "$D/g"
tar -xf "$GATE_ARCHIVE" -C "$D/g"
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
test ! -e "$P/a/g.json"
cp "$D/g/ue.json" "$P/a/g.json"
```

Then run:

```bash
set -euo pipefail
bash "$D/o_sub.sh"
# After the GPU job finishes:
bash "$D/o_fetch.sh"
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
tar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json
sha256sum "$D/3.tgz"
```

`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.

Transfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:

```bash
set -euo pipefail
: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"
: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"
printf '%s  %s\n' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -
mkdir "$LOCAL/adopted/f"
nice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"
(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \
  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \
  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \
  test -s "$LOCAL/adopted/unpack-success.json")
```

A refused unpack leaves its extracted tree behind. Scorers must consume only unpack's **success output after exit status 0**, never a directory merely because it exists; the command's `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4's design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].

**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.

## GPU parity staging and acceptance

The gate must seal **A4 prepare's actual output plus the operator's per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The complete export must equal the supplied step-400 pin. The gate also authenticates ENVIRONMENT.json against CPU READY; submit compares its hash and torch/transformers/CUDA versions with ue.json. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.

The **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job's private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`: **about 33 GB, estimated**, from about 32.6 GB of expanded inputs plus tar headers. Preserving symlinks avoids duplicated shards and heads. Reserve separate space for extraction, sources and runtime outputs. The job records actual bytes; no production archive size was measured here.

Allocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.

```bash
set -euo pipefail
GATE_TOKEN=$(/usr/bin/python3 -I -s -B -c 'import secrets;print(secrets.token_hex(6))')
salloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \
  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \
  --exclude=orchard-community-2 --job-name="a15_cot_ap${GATE_TOKEN}" \
  srun --ntasks=1 --pty bash --noprofile --norc
```

On that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.

The shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:

```bash
set -euo pipefail
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
assert Path(asset['path']).resolve()==(p/'a/4.tar').resolve() and archive.stat().st_size==asset['bytes']
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
ln -s binding.json "$GPU_LOGICAL/d/7.json"
test ! -e "$GPU_LOGICAL/d/9.json"
ln -s ENVIRONMENT.json "$GPU_LOGICAL/d/9.json"
```

Create a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. Set `environment_receipt=$GPU_LOGICAL/d/9.json`. The neutral binding and environment aliases must be symlinks, as created above. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. These aliases must be symlinks so `resolve()` reaches the manifest allow-list target; copies are rejected. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:

```bash
set -euo pipefail
: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"
: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"
PRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"
PRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \
  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \
  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \
  --asset-receipts "$LOCAL/adopted/proof" \
  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"
```

```bash
set -euo pipefail
mkdir -p "$LOCAL/public"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \
  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \
  --out "$LOCAL/public/u3"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \
  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \
  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"
```

The package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.

On an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation's actual `CUDA_VISIBLE_DEVICES`.

```bash
set -euo pipefail
# BEGIN GPU_ENVIRONMENT
: "${GPU_LOGICAL:?Exact logical root extracted above}"
GPU_KIT=/scratch/jjyeung/ab0123456789
READ_PYTHON="$GPU_LOGICAL/d/v/py"
export XDG_CACHE_HOME="$GPU_KIT/u6" HF_HOME="$GPU_KIT/u6/u0" TRITON_CACHE_DIR="$GPU_KIT/u6/u1"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
mkdir -p "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR"
nice -n 10 "$READ_PYTHON" -I -s -B - "$GPU_LOGICAL/d/ENVIRONMENT.json" <<'PYENV'
import json,sys,torch,transformers
from pathlib import Path
torch.set_num_threads(8)
environment=json.loads(Path(sys.argv[1]).read_text())
actual=dict(torch=torch.__version__,transformers=transformers.__version__,cuda=torch.version.cuda)
expected=dict(torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])
if actual!=expected or not actual['cuda'] or not torch.cuda.is_available():
    raise ValueError('GPU interpreter/environment preflight failed')
print('Environment preflight passed')
PYENV
# END GPU_ENVIRONMENT
nice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \
  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \
  --enable-gpu --public --repeat-baseline --shards 4
```

The preflight runs the archived production interpreter outside bwrap and fails before the gate if it cannot start, lacks dependencies/CUDA, or differs from ENVIRONMENT.json. No substitute interpreter is accepted. The gate parent, every worker and receipt writer independently compare the recorded versions and SHA256. Cache roots are explicit under the opaque kit root, matching A4's XDG/HF pattern with an explicit Triton root.

Every arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.

Acceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.

Each RUN.json and ue.json record the checked torch/transformers/CUDA versions and ENVIRONMENT.json SHA256. Each RUN.json also records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).

The cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard's coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.

Output directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:

```bash
set -euo pipefail
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \
  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \
  --private-source "$DELIVERY/kit_parity50/sample50.json" \
  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"
```

Restoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.

## Array validation

No multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.

```bash
set -euo pipefail
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \
  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \
  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \
  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json
```

This writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.

No delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.

## Review round 7: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |
| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |
| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |
| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |
| 5. Decision export | Bind only the supplied step-400 export at build and gate. | Other identities refuse before the builder reads the base; wrong artifact refuses at the gate. |

Frozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.

## Review round 8: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Archive breaks loader admission | Preserve in-tree symlinks; refuse escaping targets before tar; estimated archive is about 33 GB. | Extract an absolute heads link and run real Artifact.verify/load_native admission; reject external, chained, directory, dangling and cyclic links. |
| 2. Environment unspecified | Use archived d/v/py; preflight versions/CUDA; pin ENVIRONMENT.json through READY, gate and submit; set opaque cache roots. | Changed versions/hash and CPU build refuse; synthetic matching versions pass; submit rejects each changed field. |
| 3. Other export checked late | Builder admits only reviewed step-400 identity/preparation. | Eleven identity/preparation mutations refuse before reading the base. |
| 4. Unresolved package path | Resolve both archive-path operands. | README validation executes through a symlinked package parent. |
| 5. Handoff details | Aliases are symlinks; retain tar stderr; generate a fresh a15_cot_ap job token. | Error text survives; commands and alias instructions are checked. |
