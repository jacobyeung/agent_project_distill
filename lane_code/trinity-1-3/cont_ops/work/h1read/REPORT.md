# H1-1 read kit

The local fix gate passes: all 94 candidate tests, the separate 53-test ported readk suite, the 53-test original readk reference suite, all four reviewer refute tests, and the four-item runtime fixture. The salted assets rebuild byte-for-byte with the retained key. `FIX2.md` records the binding, asset, item-file and final-manifest hashes; `SHA256SUMS.txt` authenticates the deliverables.

The local kit supports H1-1 run `17c4ffa4` and D0 run `359fcc3c` at m100/m200, plus H1-1's three claimed stop generations. It adds all 2,169 R0-dev items as Orchard family `a7`. All four families total 3,994 items. `readk/` supplies the unchanged D0 reference; the candidate lives in `kit/`.

The new family uses `a7` throughout the bootstrap launcher, batches, configurations and returns. `evidence/FAMILY_ALIASES.json` holds the local `r0dev` alias. Inherited virtual `video_path` values retain dataset names as recorded in the review; those accepted binding bytes remain unchanged. `evidence/NAME_AUDIT.json` separates that inherited boundary from the new asset names.

No network, SSH, Orchard/GCS operation, GPU, Git or deletion was used. No production token or production build was prepared. Fixed `a000000001` preparations under `evidence/test_*` are test fixtures. Every write is inside this workspace. The operator alone uploads and submits.

## Export binding

The public prepare interface and the embedded bootstrap validate the exact namespace `8865619b`. Normal reads allow only m100 and m200 for the two registered runs. All other runs, normal steps, namespaces and unregistered stop generations are refused before cloud staging. The base model and the selected artifact retain the accepted native export checker. Four ordered parts must match the whole-tar byte count and SHA256 before extraction. The unchanged admission function and full export checker then verify the archive and tensor inventory.

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

H1 receipts are `/project/community/jjyeung/okh7/x_3fdda0fb/o/gcs_17c4ffa4_m100.done` and `..._m200.done`. A stop at optimizer step 137 still writes `..._m137.done`; its object can be `17c4ffa4_mstop.tar`. The kit requires `gcs_17c4ffa4_mstop.claim` to contain exactly `m137\n`, then checks the archive's m137 directory and artifact step 137. Stop generations allow actual steps 1–200 only. A registered generation is not evidence that its upload exists. D0 retains `/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m<s>.done`.

D0's `worker.bind`, `worker.validate`, `export_stage.stage_export` and `export_stage.parse_done` function source is byte-identical to the reference. Direct reader, adapters and export checker files are byte-identical. The reference's wider legacy helper API remains in `readk/`; the candidate's public request validator restricts reads to this task's scope.

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

The official-style scorer uses MRA for the four numeric types and parsed option exact match for multiple choice. Explicit refusal text, an unparsed or absent answer, and an output-token/answer-cap hit score zero. Every source item remains in the item denominator. **M5:** the refusal regex and answer-cap zeroing are stricter than main’s scorer. Both R0-dev arms apply this same policy; absolute R0-dev scores therefore use a different policy from main. Forced closure of the thinking prefix at B2048 is the accepted continuation policy; it does not itself discard the subsequent answer. A failed byte, binding, parity or completeness check fails the family and stops the chain.

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

The candidate's `tests/` passes all 94 tests: 53 ported readk tests, 24 builder tests, four reviewer refute tests, six layout/privacy tests, four logical-ID tests and three deployment tests (`evidence/FIX2_TESTS.log`). Separate runs pass all 53 ported tests (`FIX2_READK_PORTED.log`), all 53 original reference tests against `readk/kit/` (`FIX2_READK_REFERENCE.log`), and all four refute tests (`FIX2_REFUTE.log`). The deployment tests verify both milestones and all stop generations, preserve exact D0 binding bytes, check the binding embedded in prepared batches and refuse the old H1 deployment before reading receipts or staging. `FIX2_AUDIT.json` confirms that only `kit/launcher/binding.py` changed among all previously pinned kit files. The port retains assertions for unchanged behavior and adjusts intended differences documented in `DIFF.md`.
`evidence/RUNTIME_FIXTURE.json` records a separate four-item integration through the actual evaluator worker, B2048/B4096 derivation, token audit and mergers, with actual RGB frames. The engine, model staging and GPU parity probe are mocks. It asserts the unchanged main cell, 64 paired frames, doubled indices, duplicate-layout journals, unpatched layout modules and logical IDs in the Trinity inventory. It uses a local event loop without sockets. This proves interface integration, not GPU prompt/pixel parity or vLLM execution.

The runtime fixture imports the candidate reader and supplies the accepted evaluator runtime retained in `readk/evidence/test_fix2_bind_main1000/a0/kit`. The job checks this runtime's complete source digest. The packaged optional `evalpath/kit_inputs.py` filter differs from that runtime, as documented in the reference; the fixture preserves the production digest check and runs the accepted evaluator bytes.

`evidence/FIX1c_DETERMINISM.json` records equal hashes from two asset builds for the tar, item file, registry, identifier map, key, provenance and upload plan. The tar content and modification time and the retained key remain unchanged. Final sealing regenerates `DIFF.md`, `DIFF.patch`, `SHA256SUMS.txt` and `evidence/FINAL_PINS.json` deterministically from fixed source and evidence bytes. `FIX1.md`, `FIX2.md` and post-seal verification logs remain outside the manifest to avoid circular hashes. `evidence/FIX2_FINAL_PIN_TEST.log` checks the final manifest; `evidence/FIX2_SHA256_CHECK.log` checks every checksum entry.

`evidence/BIND_100_main.log` and `BIND_200_main.log` prove exact main-family prompt bytes against the real D0 m200 return and the accepted evaluator digest `d27804f7…`. The local reference lacks away/forward payload directories, so fresh binds for those two families are not claimed; the unchanged functions and existing suite cover their preserved code. `evidence/D0_SELF_PAIR.json` pairs all 1,825 real D0 m200 items with themselves: every type has delta 0 and interval [0,0].

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/audit_fix2.py > evidence/FIX2_AUDIT.log
"$PY" -B tests/runtime_fixture.py > evidence/FIX2_RUNTIME.log 2>&1
"$PY" -B tools/seal.py --pre-test > evidence/FIX2_PRESEAL.log
"$PY" -B -m unittest discover -s tests -p 'test_*.py' -v > evidence/FIX2_TESTS.log 2>&1
PYTHONPATH=tests "$PY" -B -m unittest test_kit test_chain test_verdict -v > evidence/FIX2_READK_PORTED.log 2>&1
(cd readk && "$PY" -B -m unittest discover -s tests -p 'test_*.py' -v) > evidence/FIX2_READK_REFERENCE.log 2>&1
"$PY" -B -m unittest discover -s tests -p 'test_refute.py' -v > evidence/FIX2_REFUTE.log 2>&1
"$PY" -B tools/seal.py > evidence/FIX2_SEAL.log
PYTHONPATH=tests "$PY" -B -m unittest test_kit.KitTests.test_final_pins_match -v > evidence/FIX2_FINAL_PIN_TEST.log 2>&1
sha256sum -c SHA256SUMS.txt > evidence/FIX2_SHA256_CHECK.log
```

Pre-test sealing excludes the four pending suite logs; final sealing includes their completed results. Tests install the offline process/socket guard before kit imports. Fixtures remain on disk; `REMOVAL_CANDIDATES.md` lists their paths. No cleanup command ran.

## Estimated time and local space

These are **estimates**, not measured H1 reads. `readk/REPORT.md` reports 52m51s for 1,825 items, including 47m11s generation, and 497.6s staging. Scaling by 2,169/1,825 estimates about 62m49s for the additional family's bind/generate/merge work. Scaling all 3,994 items gives about 115m40s plus staging. Allow **125–145 minutes for all four families** and **75–90 minutes for r0dev only**; full hashes, answer lengths and model staging remain uncertainties.

Budget approximately **275 GB additional `/tmp` space** for all four families: the reference's 220 GB estimate plus a fourth base/export model copy, the 0.80 GB extracted asset and working margin. Start with at least **500 GB free**, retaining the 200 GiB floor. For r0dev-only, allow approximately **150 GB additional**, starting with **375 GB free**. The actual per-family admission checks remain authoritative. The inherited 512 MiB expanded/sub-90 MB compressed return limits remain enforced; oversize returns fail rather than silently omit journals.

## Choices

- Run the original reference suite from `readk/`, because it resolves accepted evidence relative to its working directory. Keep the candidate port as a separate run.
- Bind H1 only to `x_3fdda0fb`; retain the D0 mapping exactly. Keep the existing normal-step and stop-step admission limits. The packet has additional milestone sessions, but this kit remains scoped to m100/m200 and stop steps 1–200.
- Use the retained config with the matching production identity to verify `duplicate`; record the supplied production key/file hash as provenance, without adding a new training-config dependency. FIX1 receipts retain their recorded evidence; REPORT.md and EXPORT_SOURCES.json state the current packet.
- Use the accepted main cell unchanged for R0-dev: 32 anchors, each duplicated, for 64 input frames. Preserve the evaluator's layout guards and receipt literals.
- Apply `20261116T2218Z_ORCH_RULING_r0dev_dup_qids.md` ("ORCH RULING: R0-dev duplicate qids, one rule for every kit"): retain all 2,169 rows in source line order. Logical IDs equal the source qid; only the second occurrence of `r0_5f3b5ae38f23ff697994` and `r0_c07cd9b246d953847b90` gets `#2`, matching b04’s `BUILD_R0DEV.json`. Keep `source_qid` and `source_line` in the Trinity map and decoded inventories. Derive Orchard IDs from logical IDs with the retained salted key; keep the key and map on Trinity.
- Use the explicitly approved node-local reserve archive for the full source digest and frame checks. Rebuild from the authenticated retained frame asset with the same random key; keep all outputs inside this workspace.
- Run the candidate reader with the exact accepted evaluator runtime required by its source digest. Keep the packaged optional filter and all evaluator layout code unchanged.
- Preserve the registered 100-room coverage denominator, while retaining the source's exact 2,169-item scoring denominator; do not fabricate questions for deferred rooms.
- Use the reference's ON16k/B2048/B4096 answer policy, with explicit zero scoring for new-family refusals, nonanswers and answer-cap hits. Use chance for appearance and relative distance.
- Preserve D0's binder and raw journal content. Keep the local alias map and identifier key out of every packaged surface; use `a7` in operator preparation commands.
- Keep the reference kit, input copies, test fixtures and failed fixture directories. No files were deleted. Reference source and pins under `readk/` remain unchanged; the original suite creates retained fixtures there, while the ported suite runs on the candidate.
- Use the supplied measured D0 timings for planning, without claiming that a live export, upload, credential, runtime archive or GPU read has been verified.
