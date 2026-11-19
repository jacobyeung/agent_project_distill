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

## Step-600 A4 build

Use `a19.py`, which applies cont_ops' `build_r1.py` post-processing pattern to A4's authenticated payload. It preserves A4's `8.py`, export-admission code, vendor code and run keys. It adds the ON overlays and rebuilds the payload, plan, bundle and package pins. The generic `a12.py --operator-source` route is refused because it cannot establish A4's full package contract.

`STEP600_BINDING` must name the reviewed target export JSON, with `run`, `step`, `member_directory`, `lineage`, `object`, `config_sha256`, `base_identity`, `frame_layout`, `preparation_sha256` (config/receipt/data_receipt SHA256s), **`archive_bytes` and `archive_sha256`**. The builder requires step 600 or later; it cannot turn a step-200 receipt into step-600 evidence. It seals the target object/size/hash into A4's existing fill helper, retaining its whole-archive and preparation checks. No real step-600 binding was supplied to this CPU task; its test binding is synthetic.

```bash
: "${STEP600_BINDING:?Reviewed target export binding JSON with whole-archive pins}"
: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

This produces `$LOCAL/step600/package`, a matching `src`, and the exact `tower_sequence.py` that `unpack_return.py` hashes. The profile enables all three caches, uses one card, and disables atomic journals and scene sharding. Add `--processor-only` to select only the processor cache and its 4 GiB allowance; the full cache profile uses 12 GiB. No input receipt, CPU proof or submission ledger is reused. The package's `a/1.json` and `a/export.json` start unresolved.

The operator retains **A4's 636-item schedule**. A different target item set needs a separately reviewed operator and proof. The intended GPU partition is **general**, with `--no-requeue`; A4's preserved submit helper supplies those flags. Do not use preempt or arrays before the separate persistent-storage requeue gate.

After the parity gate, the cont_ops owner fills and checks the package through the existing A4 operations. The following commands are **not executed here**. `P` is the staged package at `/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`; `E` holds four already-staged export parts `0`–`3` and the whole-tar receipt `5`. Set `OBJECT`, `PREP_CONFIG`, `PREP_RECEIPT` and `DATA_RECEIPT` from the reviewed target binding. For an SFT step-600 target:

```bash
/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" \
  --done "$E/5" --object "$OBJECT" --config "$PREP_CONFIG" --receipt "$PREP_RECEIPT" \
  --data-receipt "$DATA_RECEIPT" --lineage SFT --step 600 \
  --out "$P/a/export.json" --prep-tar "$P/a/6" \
  --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
# Run the full CPU proof inside the assigned compute allocation:
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B "$P/a/5.py" \
  --package "$P" --sequence "$P/a/6.py" --results "$P/a/c"
```

The proof must bind payload, plan, inputs and operator SHA256, pass bundle/entry checks, and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes` and `fits=true`. `a/5.py` propagates `read_extensions` into the actual `7.py` rehearsal, which produces `MEMORY.json`. The unchanged `0.py` admission checks proof bindings and `fits`; it does **not independently require the `read_cache_bytes` field**. Inspect that field before adoption. The CPU fixture asserts it and rejects a proof produced by the old helper.

After all gates, the existing explicit submit command is `(cd "$P" && /usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 04:30:00)`. This document grants no new launch authorization. Retain the exact generated local operator directory for fetch/unpack authentication.

Cache-only results use ordinary per-type journals. With `read_extensions=true`, the patched unpacker rejects any existing `WEIGHTS.json` whose `verified` value is not JSON `true`, including partial returns marked FAILED. Processor-only journals need no weight receipt. OFF unpack behavior remains unchanged. The separate generic atomic-journal validation path still merges at `metadata/reads/0/metadata/u0/answer_trace_return.tgz`.

## GPU parity staging and acceptance

Configure separate authenticated `original_source_root` and `source_root` paths in `PRIVATE_NEUTRAL_CONFIG.json`, using `config.example.json` as the schema. Bind identical native inputs, weights, precision, hardware and settings. Cache slots are 0=processor, 1=vision, 2=SAM. Flatten the intended settings and create a private alias JSON before sealing them.

```bash
mkdir -p "$LOCAL/public"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \
  --source-root "$EXT_SOURCE" --input PRIVATE_SETTINGS.json --aliases PRIVATE_ALIASES.json \
  --out "$LOCAL/public/u3"
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \
  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \
  --config PRIVATE_NEUTRAL_CONFIG.json --out "$LOCAL/public/u0"
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

Judge net time from `RUN.json`'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).

The cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard's coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.

Output directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \
  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \
  --private-source "$DELIVERY/kit_parity50/sample50.json" \
  --private-source PRIVATE_NEUTRAL_CONFIG.json --private-source PRIVATE_SETTINGS.json
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
