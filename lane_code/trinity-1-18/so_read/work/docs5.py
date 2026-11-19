from pathlib import Path
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
p=O/'kit_parity50/README.md';old=p.read_text()
start=old.index('## Step-600 A4 build');end=old.index('```bash\nmkdir -p "$LOCAL/public"',start)
replacement=r'''## Step-600 binding, build and operations

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

After the zero-difference GPU parity gate for this exact plan/profile passes, the authorized owner runs:

```bash
bash "$D/o_sub.sh"
# After the GPU job finishes:
bash "$D/o_fetch.sh"
```

`o_sub.sh` runs the exact CPU receipt/binding/cache-memory checks, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. It does not replace the GPU parity gate with a CPU receipt. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.

Transfer that fetched return as one archive through the authorized transport into `$LOCAL/step600/f/`, preserving the local operator directory. Run locally:

```bash
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

'''
p.write_text(old[:start]+replacement+old[end:])
s=p.read_text().replace('--input PRIVATE_SETTINGS.json --aliases PRIVATE_ALIASES.json','--input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES"').replace('--config PRIVATE_NEUTRAL_CONFIG.json','--config "$PRIVATE_CONFIG"').replace('--private-source PRIVATE_NEUTRAL_CONFIG.json --private-source PRIVATE_SETTINGS.json','--private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"')
s+='''\n## Review round 5: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| 1. Dropped batch wrapper | Exact cont_ops wrapper retains exclusion, EXIT log and USR1 forwarding. | Built script equals wrap_batch output and passes the real a/5.py bundle guard. |
| 2. Unpinned build inputs | Reviewed A4 payload, operator MANIFEST pins, extension inventory and alias bases must match before copying. | Changed self-consistent payload, each operator, extensions and alias pins are refused before output. |
| 3. Incomplete operations | Binding derivation, delivery archive/SHA, place/fetch/fill/dry/allocated-proof/guarded-submit/fetch scripts and gated unpack command. | Generated shell syntax, delivery members and command order pass; actual submit checker refuses missing cache proof and an oversized pool. |
| 4. Unbound GPU profile | Prepare bytes plus operator overrides bind settings, selectors, budget and package plan. | Both cache profiles pass; changed settings, selectors, cap and plan fail. |
| 5. Forecast scope | Package D and a19's A4 schedule have separate labelled estimates. | Documentation regression requires both scopes and A4's 7,351.824 s estimate. |
| 7. Refused unpack tree | Scorers require success output after exit 0; the shell handoff uses &&. | Documentation regression checks the warning and executable success chain. |
'''
p.write_text(s)
note=r'''VERDICT: PARTIAL Round-5 fixes are implemented; full CPU rerun and final packaging are in progress.

**Adopt only after the exact package/profile passes the zero-difference GPU gate.** Step 600 uses A4's 636-item schedule, one card, caches only, general/no-requeue. The all-cache allowance is 12 GiB; processor-only uses 4 GiB and must pass its own gate. No GPU or production launch ran here.

The builder authenticates the reviewed A4 payload, MANIFEST operator hashes, exact extension inventory and alias bases before copying. Its batch preserves cont_ops' excluded node, EXIT failure log and USR1 forwarding. The required build is:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

Add `--processor-only` when adopting that profile. [README](kit_parity50/README.md) contains the full executable sequence: derive the target binding from authenticated receipts; build; generate the delivery and operation scripts; place; fetch/fill; dry checks; allocated CPU proof; prepare and run the GPU gate; guarded submit; fetch; authenticated unpack. `prep_paths` supplies paths; preparation_sha256 supplies their pins. The synthetic test binding is not production evidence.

The generated submit script requires CPU payload/plan/inputs/operator bindings, entry/bundle success, the exact cache allowance and fits=true, both dry checks, an empty general queue, and a return pool at most 75,000,000 bytes. The GPU gate uses A4 prepare output with the operator's overrides and pins the adopted cache slots/budget. Require zero answer/trace byte differences, useful hits, lower complete worker wall time, and measured host/GPU headroom. No cache saving is credited yet.

**Forecast scope:** Package D is the 580-item distance read, a B5 fork with 03:30 walltime; it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), based on measured 23.600 s/item. For the **636-item** A4 read that a19 builds, the **estimate** is **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, carrying forward A4's supplied total with zero assumed saving. Neither is a measured step-600 result; queue/staging time and target-specific cache costs are excluded.

A refused unpack leaves its tree behind. Scorers must use only unpack's **success output after exit status 0**; an existing directory proves nothing. The README's command chains that handoff with `&&`. Successful partial returns still require partial-result handling. Hard kills may leave unverified weight journals and require fresh output. Whole-archive pins remain enforced at fill time under A4's reviewed design.

## Review round 5: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1 MEDIUM | Exact wrap_batch output includes exclusion, EXIT log and USR1 forwarding; the built package passes a/5.py's bundle guard. |
| 2 LOW | Pre-copy payload/operator/extension/alias pins; tampered inputs are refused before output. |
| 3 LOW | Executable binding/delivery/place/fill/dry/CPU/submit/fetch/unpack steps; actual submit preflight refuses incomplete memory evidence and an oversized pool. |
| 4 LOW | Gate derives and validates the built package's prepared per-read profile; both cache profiles pass, mismatches fail. |
| 5 INFO | Package D and A4 forecasts are separately scoped estimates; documentation tests require both. |
| 7 INFO | Refused trees remain unscoreable; documentation tests require the success-output handoff. |

All six findings have fail-before/pass-after regressions. OFF reader files/output bytes and ON answer/trace byte equality remain the bar. The GPU gate, real restore/storage/transport/requeue and a multi-card operator remain unrun or undelivered. The review sections are retained because the dispatch requires them.

Exact commands, outputs and limitations: [REPORT](REPORT.md). Pins: [MANIFEST](patches/MANIFEST.json).
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
with (L/'work/STATUS.md').open('a') as f:f.write(subprocess.check_output(['date','-u'],text=True)+'Round-5 code and adoption instructions drafted. Wrapper/bundle guard, pre-copy pins, binding/operation scripts and both profile gates pass development checks. Pool-stat fixture corrected; final suites pending.\n')
print('Updated README and NOTE with executable operations, bound GPU profile, scoped estimates and refused-return handoff.')
