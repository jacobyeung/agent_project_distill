The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.

Use the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.

The ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.

## Local preparation

These commands use paths supplied by the operator; they do not depend on the author's `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.

```bash
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

## Step-600 binding, build and operations

The candidate uses **A4's 636-item schedule, one card, caches only, general/no-requeue**. A4's export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the three patched operator hashes from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.

The owner supplies a **reviewed step-600 target template** in cont_ops' `bind400_partial.json` schema: target run, step, member_directory, lineage, object, preparation_sha256, `done` and `prep_paths`. `done` and `prep_paths` are paths on Orchard; preparation_sha256 holds hashes, not paths. Use authenticated local copies of that target's artifact.json, whole-tar `.done` receipt and three preparation files. The helper fills configuration/archive fields from those files and checks target run/member/step and preparation hashes. Do not edit a step-200/400 receipt to manufacture step-600 evidence. No real target receipt was supplied to this CPU task.

```bash
: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"
: "${TARGET_ARTIFACT:?Authenticated local artifact.json from target export}"
: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"
: "${TARGET_CONFIG:?Authenticated local preparation config.json}"
: "${TARGET_RECEIPT:?Authenticated local preparation s1_receipt.json}"
: "${TARGET_DATA_RECEIPT:?Authenticated local data_receipt.json}"
STEP600_BINDING="$LOCAL/binding600.json"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \
  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \
  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \
  --out "$STEP600_BINDING"
: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"
PROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600" "${PROFILE_ARGS[@]}"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \
  --operator "$LOCAL/step600" --binding "$STEP600_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"
nice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .
nice -n 10 sha256sum "$LOCAL/0.tgz"
```

`step600` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner's existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.

```bash
: "${OPS_ARCHIVE:?Received outer archive on Orchard}"
: "${OPS_SHA256:?Printed local SHA256 of that archive}"
: "${D:?Fresh opaque operation directory on Orchard}"
printf '%s  %s\n' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -
test ! -e "$D"
mkdir -m 700 "$D"
tar -xzf "$OPS_ARCHIVE" -C "$D"
bash "$D/o_place.sh"
bash "$D/o_pull_fill.sh"
bash "$D/o_cpu.sh"
```

`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins, fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.

`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/step600/proof/` before the parity preparation below. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.

Archive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:

```bash
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
tar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json
sha256sum "$D/2.tgz"
```

After authorized transport, authenticate and extract that archive on local scratch:

```bash
: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"
: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"
printf '%s  %s\n' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -
mkdir "$LOCAL/step600/proof"
nice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/step600/proof"
```

After the zero-difference GPU parity gate for this exact plan/profile passes, the authorized owner runs:

```bash
bash "$D/o_sub.sh"
# After the GPU job finishes:
bash "$D/o_fetch.sh"
P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}
tar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json
sha256sum "$D/3.tgz"
```

`o_sub.sh` runs the exact CPU receipt/binding/cache-memory checks, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. It does not replace the GPU parity gate with a CPU receipt. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.

Transfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:

```bash
: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"
: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"
printf '%s  %s\n' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -
mkdir "$LOCAL/step600/f"
nice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/step600/f"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$LOCAL/step600/unpack_return.py" \
  --archive "$LOCAL/step600/f/0.tgz" --exit "$LOCAL/step600/f/EXIT.json" \
  --out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json" && \
  test -s "$LOCAL/step600/unpack-success.json"
```

A refused unpack leaves its extracted tree behind. Scorers must consume only unpack's **success output after exit status 0**, never a directory merely because it exists; the command's `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4's design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].

**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast is a step-600 measurement.

## GPU parity staging and acceptance

The gate must seal **A4 prepare's actual output plus the operator's per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes against CPU.json's READY pin and checks its payload, plan and operator bindings. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.

Create a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots and the intended staged asset paths. Use `PRIVATE_ALIASES.json` to map every private prepared asset path to its staged opaque path. Keep all private files and reverse maps on Trinity. The following commands use files under `$LOCAL`:

```bash
: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"
: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"
PRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"
PRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \
  --operator "$LOCAL/step600" --prepared "$LOCAL/step600/proof/SETTINGS.json" \
  --proof "$LOCAL/step600/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \
  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"
```

```bash
mkdir -p "$LOCAL/public"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \
  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \
  --out "$LOCAL/public/u3"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \
  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \
  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"
```

The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.

On an assigned GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation's actual `CUDA_VISIBLE_DEVICES`.

```bash
nice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \
  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \
  --enable-gpu --public --repeat-baseline --shards 4
```

Every arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.

Acceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.

Each RUN.json records the adopted package plan, read profile, cache slots and budget. Judge net time from `RUN.json`'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).

The cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard's coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.

Output directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \
  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \
  --private-source "$DELIVERY/kit_parity50/sample50.json" \
  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"
```

Restoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.

## Array validation

No multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \
  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \
  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \
  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json
```

This writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.

No delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.

## Review round 4: finding -> fix -> test

| Finding | Fix | Test |
|---|---|---|
| 1. Incomplete step-600 build | A4 post-processing preserves run keys, 8.py and admission; requires reviewed export/whole-archive binding and seals the fill helper. | Package pins and target binding match; wrong run/step/object/preparation/archive fails. The documented old build fails the same regression. |
| 2. Test bypasses real configuration/profile | Real `a/5.py` generates proof memory through 7.py; real 0.py/job.main writes actions 0/1 from untouched package configuration. | Cache-only stub read completes 636 items with five verified ordinary journals. The old CPU-proof helper fails the cache-allowance assertion. |
| 3. Unverified cache-only return | ON unpack rejects any non-true weight receipt, including partial returns. | False/null/0/1/string receipts fail before/pass after; real authenticated unpack accepts a verified partial return and refuses an unverified one. |
| 9. README path/base/proof nits | Explicit portable roots; A4-only kit pin; exact distinction between generated proof and bootstrap admission. | All shown Python tools ship in the patched tree; CPU integration verifies generated cache allowance. |

Prior cache, parity-schema, OFF-byte, frozen-weight, lock/recovery, public-boundary and array-policy regressions remain in the suites. REPORT.md contains commands, exact outputs, resource measurements and limitations.

## Review round 5: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Dropped batch wrapper | Exact cont_ops wrapper retains exclusion, EXIT log and USR1 forwarding. | Built script equals wrap_batch output and passes the real a/5.py bundle guard. |
| 2. Unpinned build inputs | Reviewed A4 payload, operator MANIFEST pins, extension inventory and alias bases must match before copying. | Changed self-consistent payload, each operator, extensions and alias pins are refused before output. |
| 3. Incomplete operations | Binding derivation, delivery archive/SHA, place/fetch/fill/dry/allocated-proof/guarded-submit/fetch scripts and gated unpack command. | Generated shell syntax, delivery members and command order pass; actual submit checker refuses missing cache proof and an oversized pool. |
| 4. Unbound GPU profile | Prepare bytes plus operator overrides bind settings, selectors, budget and package plan. | Both cache profiles pass; changed settings, selectors, cap and plan fail. |
| 5. Forecast scope | Package D and a19's A4 schedule have separate labelled estimates. | Documentation regression requires both scopes and A4's 7,351.824 s estimate. |
| 7. Refused unpack tree | Scorers require success output after exit 0; the shell handoff uses &&. | Documentation regression checks the warning and executable success chain. |
