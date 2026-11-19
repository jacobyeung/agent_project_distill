# Review verdict: next-leg trainer tree a1f559e2 and kits A0 5c2ca33ca02a / A2 473395544605

Reviewer: lane review_tree (Devin, trinity-1-3), 2026-11-15. Package `tree_rebuild_b3_a1f559e2.tar`, sha256 39b2b5db82d0a5ae4b3208febf4aa49ab98fa8057a02733d464c2919c6d1c9df (verified). Base tar 845b1789 (verified). Row slices: rows_rebuild `slices/` on trinity-1-13 (30 files, the 15:45 local-time set, which predates validator a41ba191). Every check below ran on CPU in `/scratch/jjyeung/orch_n30/review_tree/work`. Evidence files sit beside this verdict in `out/`, mirrored in the events folder.

## Verdict: NOT READY

Neither kit can reach its intended refusal on Orchard as delivered. The data path refuses every real row family that A0 needs for its recovery and totals cells. Two gates trust labels that the caller supplies. Items 1 to 6 block the leg; items 7 to 15 are fixes.

## Blocking findings

1. **The kit has no runtime environment.** `job.sh` runs bare `python3 -B b/e.py . t ...`, and `b/f.sh` runs `env -i PATH=/usr/bin:/bin python3 ...`. `launch_r2/entry.py` then imports `student_pilot.carrier_c1_run`, which needs numpy and torch, in that same interpreter. The parent never ran the trainer under system python. Its `job.sh` and `r.sh` use `/usr/bin/python3 -I` only for stdlib scripts. Its `c.sh` stages the pinned `venv` into node-local `/tmp/jjyeung/okit_*` and runs the trainer inside bwrap. The new kit's staging record `k/5c0c0f1f…json` still pins `venv` (ffc81db4…), but no code in `launch_r2` reads it (grep shows that `staging` appears only where build.py writes it).
   - Failing input: staging either kit from empty with a python3 that lacks numpy.
   - Result: `ModuleNotFoundError: No module named 'numpy'` before any gate (`work/stage2/*/o/ee000007.json`). Under this node's `/usr/bin/python3` (3.6), `b/a.py:18` fails on `Path.is_relative_to` instead.
   - With a numpy-capable interpreter (`work/stage3`), both kits stop where intended: mode t at `Missing component evidence: init_m544` (`student_pilot/r2_policy.py:31`) and mode h (f.sh) at `Missing pose source: require both sealed pose sources` (`launch_r2/host.py:86`). Those are the intended missing-evidence refusals, but they occur only in an environment that the kit never creates.

2. **Nothing stages the kit's 57 relative `u/<sha256(path)>` pins.** The A0 config (`k/879c0084…json`) references 57 distinct `u/…` files: depth_init, the exclusion lists, admission, readout bank, scene-coverage reference, s1_routing catalog, remove_files and others. None of them is in the kit or its `SHA256SUMS.txt`. The parent's `c.sh` assembled them from `k/0.json` `extra`/`tars`; the new kit never runs that code. The frame-host packet (`launch_r2/host.py:native_config`) replaces only `streams`, `init_artifact` and `r2_membership`, so `run.prepare(cfg)` would read missing paths.

3. **No real row family that A0 needs passes intake** (`out/INTAKE_REAL_*.json`; harness `out/mk.py`, `out/run_intake.py`).
   - As published, intake refuses all 30 slices. Direct rows refuse with `KeyError 'question'`: `student_pilot/r2_adapters.py:31` needs a top-level `question`, but these rows carry it only inside `student_input`. A0 units and recovery rows refuse with `Program-type row offered as direct` (`student_pilot/r2_contract.py:115`), because derivgen-row-v2 rows from rows_rebuild carry `ground_record.events` but no packed `events`. No row carries `trace_contract`, so every direct row would also hit `Old-format direct row` (`r2_contract.py:117-118`).
   - With a reviewer adapter that lifts `question`/`options`, packs events and adds `trace_contract='next-leg-r2-v1'` and `response_source='ground_truth'`, the D0 direct families pass (85–99%; the rest are `excluded:eval_rooms`). Units admit 1,915/2,000. Three families still fail:
     - recovery admits 0/1,532 at `r2_contract.py:196` (`'Locate:' not in target`). The rows (v1 slices and the a0_v4 samples alike) write prose such as "I see the whiteboard in frame 29", which is the dialect the shared grammar accepts.
     - totals admits 0/1,240 (`Shared grammar: number_not_allowed,unit_quantity`). The tree pins grammar 49e814eb (`r2_grammar.py:SHARED_SHA256`), but rows_rebuild's final validator is a41ba191 (event `20261115T2151Z_RESULT_d0_fix_round_review_request.md`). The current validator passes all 1,240 rows directly, and 49e814eb inside the tree wrapper refuses all of them.
     - units without the two added fields fail `Absolute label mismatch` (1,784/2,000; `ground_rows.py:91`, a metres check on feet and centimetre answers) or `Grounding membership flags differ` for not-seen rows (`ground_rows.py:81`).
   - Why it matters: the recovery and totals cells would be empty. `r2_mix.preflight` then refuses (`Empty or invalid mix cell`), and the full host materializer raises on any non-exclusion refusal (`r2_materialize.py:72-75`), so one bad row stops the frame-host job.

4. **Nothing persists exports or state to GCS first.** The parent uploaded every milestone export with `c.sh:tk_persist_exports` → `b/gcsput.py`. The new path, job.sh → e.py → entry → torchrun → w.py → `carrier_c1_run.train`, never calls it. The kit's `b/` holds no gcsput.py, the card does not mention GCS, and `job.sh` drops the parent's `#SBATCH --signal=B:USR1@3600`. The output `runs/<hex>` is relative to the kit, which lives on the project filesystem whose ENOSPC risk `LEGS1_STATE_COPY_TO_GCS_20261113.md` records. With `checkpoint_disk_guard` planning 14 full states and 9 exports, a full filesystem would cost the leg's state.

5. **The bank gateway trusts a catalog that the caller supplies** (`student_pilot/r2_policy.py:94-131`; probe `out/PROBE_BANK.json`). `read_bank` takes `catalog_pin` from the caller and checks only its schema and reader hash. Three probes ran:
   - MindCube items labelled `dev-S1` in the caller's catalog → **admitted**, labelled "paired-comparison only". Review-3 F4 requires that such items refuse.
   - A VSI-Bench item relabelled as VSTI `camera_displacement` with `camera_routing=True` → **admitted without the dated freeze**.
   - The deployed-selector refusal (`:118`) keys on the caller-declared `choices`. A caller who uses the selector but omits it from `choices` is not refused by that check.
   - Fix: bind the catalog to a sealed membership record pinned in the kit (benchmark item digests → bank), and derive program choices from the run configuration, not from arguments.

6. **The old-selector refusal trusts a self-declared label** (`out/ROW_MUTATIONS.json`). `r2_contract.event_row:183-186` and `r2_grammar.validate_program:380` check only `row['response_source']`. Two units rows whose `ground_record.mask_source` is `deployed_selector_v3` or `sam3_fitted_selector` (`gt_authority='selector'`) were **admitted**. Fix: require `ground_record.mask_source == 'gt'` and `geometry_source == 'gt'`; those are the values on all 2,000 real units rows.

## Fixes (each with file, input and consequence)

7. **The four-stream parity claim is tautological.** `launch_r2/parent.py:reproduce` copies five files and compares each copy with its source. A fake parent made of garbage files also returns `identical: true` for all five (`work/h/repro`). The test therefore proves no reproduction through `configure()`. I could not rerun it on the real parent records: `work/kit07ca49df_meta` is not in the package.

8. **Withheld rooms: OPEN, pending build 3b.** In a1f559e2, intake and the native membership reader refuse the 80 rooms on the r2 path. I tried 6 mutations (alias token, native name, canonical-only, a routing units row) and all were refused; `Rows.row` checks `Admission` for rows that carry r2 membership (`carrier_c1_run.py:1043`). The three sealed bindings named by ORCH 2018Z (`s1_exclusions.py:232-241`, `:281-284`; `s1_routing.py:419-421`) are unchanged and bind only the sealed dev list 969cdb56. As the builder confirms (event 2146Z) and ORCH 2149Z states, camera, pose, pointing and pool rows of the 80 rooms therefore still reach training through the sealed s1 path. I did not exercise that path. `out/PRELAUNCH_CARD.md` never mentions the 80 rooms. Build 3b, which binds the merged list a1869ae2 at all three places, is meant to close this item; I judge it when its package appears.

9. **Opener keep switch.** The A0 config binds `routing_opener_init='keep'` but no `routing_vocabulary` witness, and neither the packet nor preparation checks for one. The first refusal therefore happens at GPU model load (`r2_openers.py:24-25`). When `lm != 'full'` or lineage differs, keep silently degrades to reset (`:20-21,33-35`). The mutation that removes the witness check survives the runnable tests; its test sits in `test_r2_build3.py`, which cannot run from the package.

10. **The production entry skips two checks.** `b/e.py:46` (from `launch_r2/bootstrap.py`) always calls `a.main(root, build_only=True)`, so the `ANON_OK` status/hits check and the commit check (`b/a.py:10,24`) never run at production entry.

11. **Job-visible strings.** The kit's external names are clean: job name `a15_cot_apa2b4a29a30a9`, paths `b/ k/ o/ee0000xx runs/<hex> u/<hex>`, env `TK_JOB_START`, `K1`, cache dirs. I do not accept the builder's exception as built, because the new kit goes further than the parent in four ways:
   - (a) It extracts the native-named source (`student_pilot/benchmark_eval`, `trace_grammar.py`, `g3t_vendor`, `gf1*.py`) into `o/ee000001` inside the persistent kit folder on Orchard. The parent extracted into node-local `/tmp`.
   - (b) Plaintext benchmark and dataset words sit in kit records: claim scope "VSI-Bench/ReVSI/VSTI" in `k/112fa977…json` and in the config's `r2_identity`, and `ARKIT_*` source names in `scene_coverage`.
   - (c) `host.py` sets `STUDENT_R2_FRAME_HOST` and `C1_INIT_LOCAL` in the process environment, and "student" is on the builder's own forbidden list (`build.py:WORDS`).
   - (d) `o/ee000007.json` writes refusal reasons in plaintext, which can include module paths such as `student_pilot/benchmark_eval/...`.

   The scanner skips `o/ee000001/` and `o/ee000002/` (`build.py:56`) and inspects only "operational" JSON fields. Fix: carry the disclosure as a base64 capsule, extract to node-local tmp, and hash refusal reasons.

12. **`k/4.json` is the parent's authorization, relocated.** It carries config_sha256 a7ad7051, account mt01 and the parent's 1113Z conditions. It refuses correctly (go false, hash mismatch), but it misstates what was authorized.

13. **The packet configuration is never compared with the kit's bound config.** `host.execute_packet` loads `packet['configuration']`, and `entry.host_receipt` reuses `prepared['config']` without comparing it to `launch['config']`. Only the GO record's config hash ties the trained config to anything reviewed.

14. **`eval_rooms` exclusion now applies to every VQA family.** It removes 5–15% of real D0 rows (box_3d 301/2000, appearance order 291/2000; `excluded:eval_rooms`). The sealed VQA store was not filtered by it: sealed appearance-order rows also hit it. This is conservative, but it changes populations and repeats; say so in the card.

15. **Minor wording.** A duplicate qid across two VQA families refuses with the message "Unfiltered route-planning ID collision" even for box_3d (`r2_materialize.py:44`).

## Step results

- **Step 1** (requirements, written before the reports): `out/STEP1_EXPECTED.md`.
- **Step 3** (bound A0 config compared with the card):
  - The config binds four streams {vqa 128, routing 64, pose 64, pointing 32}, recipe mix per rank 32/16/16/8 (×4 = 288), steps 1000, warmup 0.05, wall 86400, and init artifact 1d6eeb28 with `lm: full` and heads pose, depth and frame_embeddings.
  - Route table: route = `absolute_distance_object`, `object_abs_distance`, `camera_displacement`, `camera_movement_direction`, `camera_rotation`; everything else, including room size and route planning, is direct. `s1_route_policy` pins the same table.
  - The type quotas (mix ce1ffad1, fallback 019eb6f2) match `r2_mix.table()` and the card to 4 decimals. The builder moved route planning from routing to VQA, against plan §4, which lists it under routing; this is stated in the card. Routing types are scaled ×1.196 as a result: camera displacement 17.35 against the plan's 14.5.
  - The kit has no `r2_sampling`; the host requires it (`host.py:221`), but the training path silently falls back to the natural draw when it is absent (`carrier_c1_data.py:450`).
- **Step 4:** see item 7.
- **Step 5** (17 row mutations; `out/ROW_MUTATIONS.json`):
  - Answer-only targets (5 variants), stated measurements (8, including "half a meter", "two meters", 120cm, angle and coordinate), withheld rooms (3), benchmark scenes (3), program rows of a direct-only type or in the VQA stream (5), a direct row with `<tool_response>`, `response_source` deployed or missing, and duplicate qids within or across families all **refused**.
  - **Admitted:** the 2 old-selector rows (item 6).
- **Step 6:** opener switch (item 9); withheld rooms (item 8); bank gateway and scope (item 5). Legacy entrypoints refuse: `benchmark_eval`, `orchard_eval` and `scripts.orchard.eval_job` refuse at `--help`, and `evalpath/run.py` refuses at item load. Selector refusal (items 5 and 6); GCS (item 4).
- **Step 7:** see item 11.
- **Step 8** (18 statement mutations against the 32 tests runnable from the package; `out/COVERAGE_MUTATIONS.json`): baseline 32/32 OK; 11 killed, 7 survived.
  - Survivors with no test anywhere: the route-planning VQA-only check (`r2_contract.py:106-107`), the wrong-scene check (`r2_exclusions.py:65`) and the distinct-pose check (`host.py:103-104`).
  - Survivors whose only tests cannot run from the package: answer-restatement (redundant with the shared grammar), deployed `response_source` (`test_r2_edges`), repeats > 4 (`test_r2_build`, `test_r2_portable`) and the opener witness (`test_r2_build3`).

## Builder claims I could not confirm

- "136/136 CPU tests." Only 32 tests in 9 modules run from the package, and all pass. The other 12 modules need builder-lane files absent from the package: `work/kit07ca49df_meta`, `out/B3_*.json`, `work/build3/*.py`. Some tests read or write builder proof files.
- "Coverage 4358/4370" (`B3_COVERAGE_CLASSIFIED.json` is not in the package).
- B3_PARENT_REPRO, B3_LOADER_PROOF, B3_BANK_AUDIT/ENTRYPOINTS, B3_NATIVE_JOB_PROOF, B3_FRESH_ENTRY_PROOF and B3_ALL_TEST_RESULTS are not in the package.
- "The entry stages from empty and stops at the missing init_m544 evidence." This holds only with a numpy-capable python3 (item 1).

## Not checked

- The contract patches and the 14 evidence records (known absent).
- Real frames, dense manifests, the export bytes and vocabulary, pretrained parity, GPU fit and time, and distributed behaviour.
- The A2 stage-2 kit (not delivered).
- Whether Orchard's system python3 has torch. The parent's design implies it does not; I made no Orchard call.
- The current a41ba191 rows and `slices_final/`; I used the earlier slices.
- `evalpath` scripts beyond the four entrypoints named in step 6.
- `scripts/gpu_routed_batch.py`, which imports an absent external module.
