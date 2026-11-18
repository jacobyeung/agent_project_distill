# H1-1 read kit

The kit supports `--types direct`, isolated production workers and bounded partial journal and diagnostic returns. The FIX5 gate passes 117 candidate tests, the separate 53-test ported suite, the 53-test original-reference suite, four refute tests, and both unfiltered and filtered runtime fixtures. `FIX5.md` records the import audit, plan identity proof, validation and operator commands. `SHA256SUMS.txt` authenticates the deliverables.

The local kit supports H1-1 run `17c4ffa4` and D0 run `359fcc3c` at m100/m200, plus H1-1's three claimed stop generations. Run `469ddece` additionally permits only generation `mstop`, step 544, family `a7`, at deployment `x_07ca49df`. It adds all 2,169 R0-dev items as Orchard family `a7`. Without a filter, all four families total 3,994 items. `readk/` supplies the unchanged D0 reference; the candidate lives in `kit/`.

The new family uses `a7` throughout the bootstrap launcher, batches, configurations and returns. `evidence/FAMILY_ALIASES.json` holds the local `r0dev` alias. Inherited virtual `video_path` values retain dataset names as recorded in the review; those accepted binding bytes remain unchanged. `evidence/NAME_AUDIT.json` separates that inherited boundary from the new asset names.

No network, SSH, Orchard/GCS operation, GPU, Git or deletion was used. No production token or production build was prepared. Fixed `a000000001` preparations under `evidence/test_*` are test fixtures. Every write is inside this workspace. The operator alone uploads and submits.

## Export binding

The public prepare interface and the embedded bootstrap validate the exact namespace `8865619b`. Normal reads allow only m100 and m200 for the two registered runs. Run `469ddece` permits only the claimed mstop/544 identity for `a7`; its receipt is `x_07ca49df/o/gcs_469ddece_m544.done`, its claim is `x_07ca49df/o/gcs_469ddece_mstop.claim` with exact bytes `m544\n`, and its object is `q8/8865619b/469ddece_mstop.tar`. All other runs, normal steps, namespaces and unregistered stop generations are refused before cloud staging. The base model and the selected artifact retain the accepted native export checker. Four ordered parts must match the whole-tar byte count and SHA256 before extraction. The unchanged archive validation and full export checker then verify the archive and tensor inventory.

| Rule | Audit | Current source file:line |
|---|---|---|
| Run `17c4ffa4` | SAME | `../h1/ids.json:1`, `../h1/payload/ids.json:1` (`tokens.run`); `../h1/FIX8.md:7` |
| Namespace `8865619b` | SAME | `../h1/build/fx/b/c.sh:9`; `../h1/runtime/jb.sh:47` |
| Deployment `/project/community/jjyeung/okh7/x_3fdda0fb` | CHANGED | `../h1/FIX8.md:6`; `../h1/payload/z.sh:14`; `../h1/runtime/jb.sh:18`; `../h1orch/L3b_submit.sh:2` |
| m100 object `q8/8865619b/17c4ffa4_m100.tar` and parts 00–03 | SAME | `../h1/EXPORT_OBJECTS.txt:9–12`; `../h1/build/fx/b/c.sh:412,429` |
| m200 object `q8/8865619b/17c4ffa4_m200.tar` and parts 00–03 | SAME | `../h1/EXPORT_OBJECTS.txt:13–16`; `../h1/build/fx/b/c.sh:412,429` |
| mstop, mstopB, mstopC objects and four parts each | SAME | `../h1/EXPORT_OBJECTS.txt:33–44`; `../h1/runtime/jb.sh:46–47` |
| `.done` basename `gcs_<run>_m<actual step>.done`, text `<object> <bytes> <sha256>\n` | SAME; deployment prefix CHANGED | `../h1/build/fx/b/c.sh:411–412,430`; `HM=HX` at :20, `HX=TK_KIT_HOME` at :12 |
| Stop claim binds generation to actual optimizer step, `m<step>\n`; reuse only for the same step | SAME | `../h1/build/fx/b/c.sh:418–423` |
| Stop generations `mstop`, `mstopB`, `mstopC` | SAME | `../h1/build/fx/b/c.sh:418`; `../h1/runtime/jb.sh:46` |
| Part suffix `.part00-of-04` through `.part03-of-04` | SAME | `../h1/build/fx/b/gcsput.py:17–18`; `../h1/build/fx/b/c.sh:429` |
| Training config key/file hash and identity | CHANGED; no executable kit pin | Production `1dd078da` and SHA256 are user-supplied; local pending-review key `d12ae795` and identity appear at `../h1/ids.json:1`, `../h1/FIX8.md:5` |
| `frame_layout=duplicate`: 32 anchors, each repeated, 64 processor frames | SAME | `../h1/build/fx/k/d12ae795.json:1`; identity includes layout at `../h1/payload/d.py:130–135`; expansion at `../h1/source/code/tree/docs/carrier_c1_memory_layout.md:47–52` |

`evidence/EXPORT_SOURCES.json` retains current numbered excerpts and complete source hashes. `evidence/FIX2_AUDIT.json` records the checks. The current `build/fx` exporter function and uploader match `build/fx_r7` byte-for-byte; `payload/jb.sh` matches `runtime/jb.sh`. `FIX8b.md:7` and `FIX8c.md:10` preserve the deployment/config/export bindings while changing proof tooling. The source table describes configured paths; the running job 170710 is a user-supplied fact, not a remote observation by this kit.

The supplied production config is `k/1dd078da.json`, SHA256 `9385cc71bad6424f04f50d536462e59e9fefc84b6a06767fdbef3912728a5130`, identity `eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8`. No file named `1dd078da.json` was found in the accessible local H1 tree; `evidence/FIX2_SEARCH_ERRORS.log` records one unreadable fixture directory. The local retained config `build/fx/k/d12ae795.json` has file SHA256 `f74f2f60097856bd6c10a7fb199dcc8e6ca140e8d28abf9be52524d78c948a83` and computes to exactly the supplied production identity using the packet's identity function. Because that function includes `frame_layout`, this establishes the same `duplicate` layout for that identity without claiming to authenticate unavailable production file bytes. The kit pins its evaluation contract, runtime and assets; it contains no H1 training-config key/hash/identity pin. The config references in source evidence are provenance only and have been refreshed. No layout or asset change is required.

H1 receipts are `/project/community/jjyeung/okh7/x_3fdda0fb/o/gcs_17c4ffa4_m100.done` and `..._m200.done`. A stop at optimizer step 137 still writes `..._m137.done`; its object can be `17c4ffa4_mstop.tar`. The kit requires `gcs_17c4ffa4_mstop.claim` to contain exactly `m137\n`, then checks the archive's m137 directory and artifact step 137. H1-1 stop generations allow actual steps 1–200 only; the separately registered init read allows only mstop/544. A registered generation is not evidence that its upload exists. D0 retains `/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m<s>.done`.

D0's `worker.bind`, `worker.validate` and `export_stage.parse_done` function source is byte-identical to the reference. `stage_export` differs only in its entry gate, which admits run `469ddece` at step 544; its archive and checker logic remains byte-identical. The pinned direct wrapper, adapters, evaluator source and export checker files are byte-identical. The outer reader selects kept tasks only after full source validation when `--types direct` is present. The reference's wider legacy helper API remains in `readk/`; the candidate's public request validator restricts reads to this task's scope.

## R0-dev protocol and assets

The item file preserves all source rows, questions, options, answers, units and ordered f32 indices. The source contains 2,167 distinct qids across 2,169 rows: two appearance questions repeat a qid with different options. Opaque item, room and frame IDs use domain-separated HMAC-SHA256 with a random 256-bit key held only in `evidence/ID_KEY.json`. Each logical item ID is its source qid, except that the second occurrence of each registered duplicate receives the suffix `#2`. The opaque item ID salts that logical ID. The local map stores `id` (logical ID), `source_qid` and one-based `source_line` for each opaque ID. The same key makes rebuilds deterministic. No row is deduplicated. `evidence/ID_MAP.json` stays on Trinity and is never packaged for Orchard.

The tar holds exactly 3,136 used PNGs from 98 physical rooms, with sorted opaque names, UID/GID 0, empty owner names, mtime 0 and mode 0644. Both appearances of a room use the same opaque physical-room ID. Every item uses its own 32 `frame_indices` in order, with source FPS and total frame count. Each anchor is duplicated consecutively, giving 64 input frames and doubled `frames_indices`, exactly as `media.frame_list` defines the trained `duplicate` layout.

The job first requires directory mode 0700 and file modes 0600, then hashes both uploaded files before use, checks sizes, validates item/type/room counts and frame references, verifies every extracted PNG's bytes/SHA256, and checks RGB mode, dimensions and pixel hashes when loading frames. Model staging retains the 200 GiB free-space floor. `UPLOAD_PLAN.md` gives the exact upload targets and pins.

| Asset | Bytes | SHA256 |
|---|---:|---|
| `assets/d81f4a26.tar` | 797,685,760 | `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` |
| `assets/e52a690b.jsonl` | 5,728,183 | `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b` |

The two uploads total 803,413,943 bytes. `evidence/FIX1_RESERVE.json` verifies all 3,136 selected frames against the approved node-local reserve archive, whose full SHA256 is `2bbae12a984fde1228bdb571f5aee390c1e6a82dc554310aa04c6fd0fe80a116`. The rebuild uses authenticated frame bytes retained in `evidence/FIX1_ASSET_SOURCE/`; that directory and the identifier key remain necessary local build inputs.

The new family uses the accepted prompt builder and ON16k → B2048/B4096 continuation policy, with B2048 primary, greedy decoding, the same 64-token continuation answer cap, vLLM 0.32.0, max-model length 49152, max sequences 32 and inflight 16. The adapter reuses the main cell unchanged (`devrows`, 32 anchors, `duplicate`). Evaluator source and layout guards/receipt literals run byte-identical to main, without in-memory source patches.

The official-style scorer uses MRA for the four numeric types and parsed option exact match for multiple choice. Explicit refusal text, an unparsed or absent answer, and an output-token/answer-cap hit score zero. Every source item in a kept type remains in that type’s item denominator. **M5:** the refusal regex and answer-cap zeroing are stricter than main’s scorer. Both R0-dev arms apply this same policy; absolute R0-dev scores therefore use a different policy from main. Forced closure of the thinking prefix at B2048 is the accepted continuation policy; it does not itself discard the subsequent answer. A failed byte, binding, parity or completeness check fails the family and stops the chain.

| Type | Items | No-information score (%) | Chance (%) |
|---|---:|---:|---:|
| object_counting | 385 | 62.2 | — |
| object_abs_distance | 290 | 29.5 | — |
| object_size_estimation | 293 | 18.3 | — |
| room_size_estimation | 98 | 33.1 | — |
| object_rel_direction_easy | 192 | 51.6 | 50 |
| object_rel_direction_medium | 194 | 35.6 | 33.33 |
| object_rel_direction_hard | 192 | 30.7 | 25 |
| obj_appearance_order | 246 | 25.0 | 25 |
| object_rel_distance | 279 | 25.0 | 25 |

`SUMMARY.json` places `no_information_pct` beside each new-family type score. The registered room denominator remains **100**, including the two deferred rooms, and the summary reports 98 rooms with items and two deferred opaque room IDs. The source gives those deferred rooms no questions. Their unknown per-type item counts are not invented: item accuracy uses exactly the 2,169 supplied items, while room coverage uses 98/100.

## Operator commands

These operator commands were not executed. Upload the two pinned assets with the permissions in UPLOAD_PLAN.md before submission. No official benchmark family is available.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh

prepare_read() {
  local label=$1 run=$2 step=$3
  shift 3
  local token=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
  local dest=$PWD/kit/build/$token
  "$PY" -B "$L" prepare --run "$run" --namespace 8865619b --step "$step" \
    --families "$@" --token "$token" --destination "$dest" || return
  printf -v "$label" '%s' "$dest"
}

prepare_read D0_200 359fcc3c 200 a7
prepare_read D0_100 359fcc3c 100 main away forward a7
prepare_read H1_100 17c4ffa4 100 main away forward a7
prepare_read H1_200 17c4ffa4 200 main away forward a7

submit_read() {
  local dest=$1 cmd
  cmd=$("$PY" -B "$L" submit-command --destination "$dest") || return
  timeout 300 bash "$A_TRANSPORT" "$cmd" < "$dest/BATCH.sh" \
    > "$dest/SUBMIT.out" 2> "$dest/SUBMIT.err" || return
  "$PY" -B "$L" record-submission --destination "$dest"
}
```

Submit each only when its exact `.done` receipt exists and the allocation is authorized. Execute these calls separately as reads become eligible; they are not a request for concurrent jobs:

```bash
submit_read "$D0_200"
submit_read "$D0_100"
submit_read "$H1_100"
submit_read "$H1_200"
```

Each call performs test-only admission and submits one H100 on `general`, 16 CPUs, 200G, six hours, no requeue. Family execution is sequential in fresh processes. Runtime, base, export and GPU admission remain inherited.

After each corresponding job finishes:

```bash
"$PY" -B "$L" fetch --destination "$D0_200"
"$PY" -B "$L" fetch --destination "$D0_100"
"$PY" -B "$L" fetch --destination "$H1_100"
"$PY" -B "$L" fetch --destination "$H1_200"
```

For a return ≥20 MB, `fetch` retains the verified exit receipt and prints the exact transfer command for the operator to register with the IO governor. Execute that governed command; do not loop or bypass the governor. Then authenticate and extract each downloaded archive. On Trinity, `unpack_return.py` decodes the root and per-family `ITEMS.jsonl` IDs through `evidence/ID_MAP.json` and exposes `source_qid` and `source_line`. The authenticated archive and raw `items_a0.jsonl` journals retain their opaque IDs:

```bash
"$PY" -B tools/unpack_return.py --destination "$D0_200"
"$PY" -B tools/unpack_return.py --destination "$D0_100"
"$PY" -B tools/unpack_return.py --destination "$H1_100"
"$PY" -B tools/unpack_return.py --destination "$H1_200"

"$PY" -B h1pair.py --step 100 \
  --d0 "$D0_100/fetched/x/ITEMS.jsonl" \
  --h1 "$H1_100/fetched/x/ITEMS.jsonl" --output evidence/PAIR_100.json
"$PY" -B h1pair.py --step 200 \
  --d0 readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl "$D0_200/fetched/x/ITEMS.jsonl" \
  --h1 "$H1_200/fetched/x/ITEMS.jsonl" --output evidence/PAIR_200.json
```

`h1pair.py` accepts multiple files per side so D0's existing three-family m200 return can accompany the new r0dev-only return. It decodes mapped opaque item IDs to logical IDs and normalizes `a7` to `r0dev` locally, requires equal `(family,id)` sets across every family on either side, exits nonzero with missing-item counts on a mismatch, and refuses duplicate keys, mismatched task/room metadata, invalid scores, wrong budgets or wrong steps. It computes H1-1 minus D0 for each family/type using the reference bootstrap: item-weighted means, complete physical-room resampling with replacement, 10,000 draws, seed 20261115, linearly interpolated percentile 95% intervals. An interval whose upper endpoint is strictly below zero flags harm only for one of D0's seven registered F1 types in **main or r0dev**. Away and forward intervals are information only. Absolute distance, room size and appearance are reported without becoming F1 stopping types.

For an unscheduled H1 stop, prepare with `--run 17c4ffa4 --step <actual optimizer step> --generation mstop` (or `mstopB`/`mstopC`) and the same family arguments. The `.claim` binds that generation to the actual step. `h1pair.py` intentionally compares registered m100/m200 pairs only.

## Validation

The offline gate passes 117 candidate tests, 53 ported readk tests, 53 original-reference tests and four reviewer refute tests. The ten FIX4 tests and seven step-544 admission tests also pass separately. Six FIX5 tests cover cold imports of all 20 packaged Python modules under `-I`, a negative control with the broken import order, identical filtered and unfiltered FIX4 plans, diagnostic tail contents, journal priority under a small cap, oversized lines and symlinks.

Both runtime fixtures execute the packaged outer worker and accepted evaluator, B2048/B4096 derivation, token audit and mergers with actual RGB frames. They use the generated `exec <python> -I "$@"` wrapper form with the local CPU interpreter. The unfiltered fixture completes four items; the direct-filter fixture completes three. The chain tests use real isolated children with synthetic family computation. Engine, model staging and GPU parity probes remain mocks; these tests do not establish live GPU parity or cancellation delivery.

Partial returns retain at most 256 KiB from the end of each `launcher_chain.log`, `launcher_staging.log` and selected family `.hex` file. Identity, journals and metadata take priority. Cut first lines and unfinished last lines are omitted; `PARTIAL.json` records original and retained bytes, offsets, retained lines, truncation and omissions. The existing production and proof archive caps remain enforced.

`tools/test_fix3.py` confines fixtures and ledgers to `evidence/test_*`. Its process guard admits only exact validated local isolation commands; each child installs network, process and write guards before loading the tested entry point. The reference source and production preparations stay unchanged. The FIX2 provenance audit is not rerun because it reads outside this kit. The pinned direct wrapper, evaluator, adapters and export checker remain unchanged; `evidence/FIX5_AUDIT.json` records the source audit and changed outer files.

The existing salted asset rebuild and identifier evidence remains in FIX1c_DETERMINISM.json. The frame tar, item file, registry and key were not changed. The sealer regenerates DIFF.md, DIFF.patch, SHA256SUMS.txt and FINAL_PINS.json. FIX1.md through FIX5.md and post-seal verification logs remain outside the manifest to avoid circular hashes.

```bash
set -e
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/test_fix3.py fix5 > evidence/FIX5_NEW_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py fix4 > evidence/FIX5_FIX4_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py targeted > evidence/FIX5_TARGETED.log 2>&1
"$PY" -B tools/test_fix3.py runtime > evidence/FIX5_RUNTIME.log 2>&1
"$PY" -B tools/test_fix3.py runtime_direct > evidence/FIX5_RUNTIME_DIRECT.log 2>&1
"$PY" -B tools/seal.py --pre-test > evidence/FIX5_PRESEAL.log
"$PY" -B tools/test_fix3.py candidate > evidence/FIX5_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py ported > evidence/FIX5_READK_PORTED.log 2>&1
"$PY" -B tools/test_fix3.py reference > evidence/FIX5_READK_REFERENCE.log 2>&1
"$PY" -B tools/test_fix3.py refute > evidence/FIX5_REFUTE.log 2>&1
"$PY" -B tools/seal.py > evidence/FIX5_SEAL.log
"$PY" -B tools/test_fix3.py pins > evidence/FIX5_FINAL_PIN_TEST.log 2>&1
sha256sum -c SHA256SUMS.txt > evidence/FIX5_SHA256_CHECK.log
```
