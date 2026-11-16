# Step-544 parity-read kit

The kit restores the local step-544 export and runs the end-to-end reader against Orchard job 170056. It uses the sealed trainer, prompt builder, official scorer, and C8r `ThinkingBudget`. It never derives an answer from a tool response.

The default request selects exactly 636 keys from the two task files. Those files contain 1,975 candidate tasks. The pinned dense manifest provides 64 frames for 567 selected items and 32 frames for 69 selected items. The kit preserves those counts and checks every anchor index and hash. Set `require_dense64: true` to refuse the 32-frame captures.

## Inputs

Run commands locally on `trinity-1-18` or `trinity-1-13`, from an existing compute-node session. This kit makes no SSH connections and downloads nothing. Obtain approval before the host's heavy weight hashing or loading. Keep all inputs on local `/scratch`; allow sufficient CPU RAM for the carrier plus its private depth branch.

Set these variables to paths on the current host. `L` must contain this reader, the kit, its metadata, C8r policy, and heads code. `T` must contain the sealed tree. The examples use the requested lane and tree paths; adjust them if the host mounts them elsewhere.

```bash
L=/scratch/jjyeung/orch_n30/b04_e2ehook
T=/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449
M=$L/work/meta/x
PY=/scratch/jjyeung/envs/p1cpu/bin/python
S=/scratch/jjyeung/REPLACE_WITH_STEP544_HF_DIRECTORY
H=/scratch/jjyeung/REPLACE_WITH_STEP544_HEADS_DIRECTORY
G3T=/scratch/jjyeung/REPLACE_WITH_G3T_DIRECTORY
O=$L/parity_kit/host_restore
R=$L/parity_kit/host_results
cd "$L"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR=$L/work/tmp
```

Use a CUDA-capable Python environment for card runs. The provided `p1cpu` environment is for CPU diagnostics and tests. No package installation is part of these commands.

`S` contains the five HF shards, index, config, tokenizer, and processor files. `H` contains `heads.pt`, `artifact.json`, and `full_weights/full_weights.json`. `G3T` contains `model.safetensors` and `config.json`. Frames must already exist beneath `/scratch/jjyeung/devs1_frames`, or a replacement `frames_root` with the same relative paths.

## Restore and manifest on either host

```bash
"$PY" -B -m parity_kit.stage_restore \
  --source "$S" --heads "$H" --meta "$M" --tree "$T" --out "$O"

"$PY" -B -m parity_kit.build_manifest \
  --root /scratch/jjyeung --export-dir "$O" --g3t "$G3T" \
  --selector-head "$L/heads/selector/work/run_iso" \
  --scale-head "$L/heads/scale/work/run1" \
  --code reader="$L/e2e_reader" --code tree="$T" --code heads="$L/heads" \
  --out "$L/parity_kit/E2E_MANIFEST.json"
```

The restore destination must be empty. The restore hashes all shards, the index, and heads; checks their pins; constructs the real private depth branch on the meta device; and checks every depth tensor key and shape in memory-mapped `heads.pt`. It then creates:

- `full_weights/`: the original full-weight manifest, copied index, and shard symlinks.
- `base/` and `model.json`: processor/config copies and symlinks to the step-544 weights.
- `heads.pt`: a symlink to the pinned head file.
- `artifact.json`: only the full-weight and head paths change; both content pins remain intact.
- `receipt.json`: the model pin points to the local manifest and `depth_init` is omitted.
- `RESTORE.json`: original and local hashes, depth coverage, and reasons for each load deviation.

The loader still calls `load_export`, which checks every exported tensor for exact equality after copying it. The stage-1 private-depth initializer is unnecessary because the final strict head load covers its entire state. All parameters are frozen after restoration.

The manifest resolves symlinks and refuses any data file outside `--root`. The root must contain both `O` and all symlink targets. A `/dev/shm/jjyeung` root works only when all data targets are inside it. G3T lookup uses basenames, independent of its relative directory. Code roots may live outside the data root.

For ground/gap calls, create a SAM settings JSON under `parity_kit/`:

```json
{
  "source_root": "/scratch/jjyeung/SAM3_SOURCE",
  "checkpoint_path": "/scratch/jjyeung/SAM3_CHECKPOINT.pt",
  "receipt_path": "/scratch/jjyeung/SAM3_RECEIPT.json"
}
```

Check imports without constructing a model:

```bash
"$PY" -B -m parity_kit.sam3_probe \
  --source-root /scratch/jjyeung/SAM3_SOURCE \
  --checkpoint /scratch/jjyeung/SAM3_CHECKPOINT.pt --tree "$T"
```

Add `--sam3 "$L/parity_kit/sam3.json"` to the manifest command. The builder pins the checkpoint, receipt, packaged vocabulary assets, and SAM source code. The tree's SAM tower requires source and checkpoint paths under `/scratch`; its own pin checks still apply. An import probe does not establish checkpoint compatibility or sufficient memory.

## Reader settings

Create `parity_kit/settings.json` with absolute paths. `artifact_manifest` can be the generated binding filename or the binding object itself. `sam3` accepts the object above, not its filename. Use `null` when SAM is unavailable; ground/gap calls then remain unserved. A SAM tower requires a selector head.

```json
{
  "export_dir": "/scratch/jjyeung/orch_n30/b04_e2ehook/parity_kit/host_restore",
  "artifact_manifest": "/scratch/jjyeung/orch_n30/b04_e2ehook/parity_kit/E2E_MANIFEST.binding.json",
  "config": "/scratch/jjyeung/orch_n30/b04_e2ehook/work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json",
  "tree": "/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449",
  "frames_root": "/scratch/jjyeung/devs1_frames",
  "selector_head": "/scratch/jjyeung/orch_n30/b04_e2ehook/heads/selector/work/run_iso",
  "scale_head": "/scratch/jjyeung/orch_n30/b04_e2ehook/heads/scale/work/run1",
  "sam3": null
}
```

Optional settings override `frames_json`, `dense_manifest`, `tasks` (a list of JSONL paths), `request`, `old_items`, and `old_load_receipt`. Defaults point to the supplied metadata and job 170056 under `L`. The CLI supplies `arm`; callers of `make_real` put `arm` in settings.

## CPU first batch

Run the five keys pinned by 170056's `LOAD_RECEIPT.json`, one per question type:

```bash
"$PY" -B -m parity_kit.cpu_first_batch --settings "$L/parity_kit/settings.json" \
  --arm own_depth --device cpu --out "$R/cpu_first"
```

This loads real weights and may take substantial RAM and time. It writes `FIRST_BATCH.json` with load/decode timings, both call-text sequences, and zero-based positions of the first differing call and character. It also writes the same journal and receipts as card runs.

## Card reads on 1-18 and 1-13

On **trinity-1-18**, with that host's local inputs and a CUDA Python environment:

```bash
CUDA_VISIBLE_DEVICES=0 "$PY" -B -m parity_kit.run_parity \
  --settings "$L/parity_kit/settings.json" --arm own_depth --device cuda:0 \
  --out "$R/own_depth"
```

On **trinity-1-13**, with its local inputs and a CUDA Python environment:

```bash
CUDA_VISIBLE_DEVICES=0 "$PY" -B -m parity_kit.run_parity \
  --settings "$L/parity_kit/settings.json" --arm scale_head --device cuda:0 \
  --out "$R/scale_head"
```

Each command runs one process on one visible card. Use `--keys keys.txt` (one full key per line, or a JSON list) for disjoint card partitions. Alternatively, use `--types camera_displacement camera_rotation camera_movement_direction`. Every partition needs its own output directory. The two arms require separate directories and separate comparisons.

The runner writes `LOAD_RECEIPT.json` before loading, `LOAD_TIMING.json` after loading, and one complete JSON line per successful item to `items.jsonl`. It flushes each line. Caches, temporary files, and the process lock stay under `--out`. A second writer to the same output directory is refused.

A normal resume skips completed keys only when settings, selection, code pins, metadata pins, restore record, and artifact binding match. A partial JSON line or changed receipt causes a refusal. The runner does not catch and relaunch failed jobs. If the cluster kills a run, stop and obtain the user's answer before rerunning it.

## Compare one arm with 170056

Once a journal is locally available:

```bash
"$PY" -B -m parity_kit.compare --new "$R/own_depth/items.jsonl" \
  --out "$R/own_depth_comparison"
```

For disjoint partitions, pass all their journals after `--new`. The command runs `tests/price_agg.py` unchanged: 10,000 room-paired bootstrap draws, seed 20261116, 95% percentile intervals, with item-weighted mean differences. It uses released labels for the primary stratum and answer labels otherwise.

Outputs are `TABLE.txt`, `paired.json`, `paired_new_paired.json`, `CALL_AGREEMENT.json`, and `COVERAGE.json`. Coverage lists omitted baseline keys; a partial run is never described as full coverage. Camera call agreement compares exact strings and reports the common prefix before divergence. It does not assert that later calls should match after an earlier response differs.

## Python interface

```python
from e2e_reader.parity import load_native, bind_item, score, make_real

gen = make_real(export_dir, manifest_binding, task_dicts,
                settings=settings, device="cuda:0",
                perception_factory=my_factory)
result = gen(task_dicts[0])
```

`my_factory(artifact=..., model=..., processor=..., device=..., item=...)` returns the reader's perception object for that task. The model loads once. `load_native` returns `(model, processor, info)`; `bind_item` returns `{id, row, frames}`; `score(task, output_or_decode)` returns both label scores. `bind_item(..., verify=False)` validates metadata and returns frame paths without opening images; generation always verifies and loads RGB frames.

`ParityGenerator` subclasses `E2EGenerator` to pass the explicit 16,384-token cap to `generate_real`; the parent's dispatch does not expose that argument. It uses the same hook, audited prefill, and cache continuation. Its budget factory instantiates the actual C8r `reader_policy.ThinkingBudget` used by `nomdg.py`; `evalpath.runtime` does not expose that policy. Forced responses do not count as sampled callbacks.

## Verification and remaining host checks

CPU validation passed 17 kit tests and all 26 existing tests. The scoring adapter reproduced all 636 recorded unflagged scores (634 decodes and two refusals). All 636 frame bindings passed metadata checks. `test_results/VALIDATION.json` records the scope and results.

Run tests with a fresh, nonexistent basetemp directory to avoid pytest removing a prior directory:

```bash
mkdir -p parity_kit/test_runs
TMPDIR=$PWD/work/tmp "$PY" -B -m pytest -q -p no:cacheprovider \
  --basetemp="$PWD/parity_kit/test_runs/NEW_KIT_RUN" parity_kit/tests/
TMPDIR=$PWD/work/tmp "$PY" -B -m pytest -q -p no:cacheprovider \
  -p parity_kit.pytest_scope \
  --basetemp="$PWD/parity_kit/test_runs/NEW_REGRESSION_RUN" tests/
```

The output-only pytest plugin redirects the existing suite's `TINY_E2E.json` proof into `parity_kit/test_results/`. It changes no assertions or reader behavior. The tiny parity fixture uses real random Qwen3 forwards and the existing sampled-token script helper; it substitutes the carrier-specific preparation/continuation boundary because no Qwen3.5 weights are available locally.

Real shard restoration, GPU logits, real tower execution, SAM compatibility, peak memory, and cross-host parity remain unverified until the host runs. Full score equality is not promised: the reader uses a 1,024-token call window instead of 96, has no 200-call limit, omits the own-depth range gate and fallback suffix, leaves room calls unserved, and uses the configured grounding socket. These differences are distinct from the unchanged budget logits processor and official scoring path.
