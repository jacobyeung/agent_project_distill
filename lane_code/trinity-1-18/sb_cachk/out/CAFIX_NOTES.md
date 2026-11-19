# sb_cafix: the nine required edits of review sb_carev (NO-GO)

Workspace `/scratch/jjyeung/orch_n30/sb_cafix` holds copies of `sb_mask_carry/kit_v2`, `out/v2` and `in/` (cp -a). Every kit path resolves here. Line numbers refer to `kit_v2/` and tests to `kit_v2/tests/test_kit.py`. Rerun evidence is at the end.

## 1. Empty-mask carry gate and denominator
- `mc_track_io.py:38-40` carries an anchor when the tracker score is above 0, with no other threshold. A positive-score empty mask is carried, RLE-encoded and flagged `positive_empty`.
- `mc_price.py:33` (`added_members`, used at `:87`) passes every carried non-seed anchor, empty ones included, to both the ladder (`Objects.get`/`majority`, where an empty mask yields None and counts as incorrect) and the IoU precision. `carry_precision` stays `summarize_train.precision` over all seeded objects.
- `mc_stubs.py:5,16,42-43` adds a third stub that carries one positive-score empty member per seeded object. `mc_summary.py:286,295` (dry-run step 1b) requires its ladder count to be 760 added and 0 correct, with C_best1 equal to A0.
- `mc_bars.py:43,65` writes `out/v2/BARS_AMENDMENT.json` once and never rewrites it. It replaces the frozen resolution 1 before any GPU-priced number. `BARS_FROZEN.json` (sha256 edff8724…) keeps its bytes, and its bars are unchanged.
- Tests: `test_object_record_positive_empty_carries` (174), `test_zero_score_does_not_carry` (194), `test_bars_amendment_keeps_bars_and_names_population` (351); dry-run step 1b.

## 2. Phrase producer schema, validation and raw-name fallback
- `mc_phrase.py:38` (`row_phrases`) reads each row's `phrases` field and checks it against the policy label: raw gives [name], `q:w` gives [w] (W1), `call:w` gives [name, w] (W2c). The W2 `fb:` policy is refused.
- `mc_phrase.py:58` (`producer`) requires the arm to be the DECISION.json `chosen_arm`, listed in `shippable_passing`, with `phrase_worth` and `phrase_safe` PASS. The DECISION bytes must match their recorded sha256, and the bars sha must agree across PHRASE_FOLDS.json, DECISION.json and the bars file.
- `mc_phrase.py:91` (`parse`) requires integer folds 0..4, no duplicate rows and the same names in every fold. `:113` (`table`) returns the provenance.
- `mc_seeds.py:64` (`phr_choice`, called at `:143`) treats a raw-name call, first or second, as the A0 call and returns the S_A0 record and mask. `:199-203` records the provenance and any names the producer left unlisted.
- Rebuilt seeds: S_PHR is PRESENT with 764 OK, 531 on target and 20 differing from S_A0; the only policy is `radiator`; the S_PHR path parity is 770/770 and check 1 is 770/770 on 209 captures.
- Tests: `test_phrase_parse_producer_w1` (63), `_w2c_pair` (71), `test_phrase_parse_refuses` (80, 16 cases), `test_phrase_table_reads_the_real_phrases_field` (119, 320/320 rows), `test_phrase_table_not_yet` (127), and the four `test_phr_choice_*` tests (148-166).

## 3. Preflight compares the fold-file hash with the seed provenance
- `mc_preflight.py:14` (`phrase_check`) checks the fold file that `mc_common` resolves now (`mc_common.py:17-19`: sb_phfix if present, else sb_mask_phrase). Its path and sha256 must equal the seeds' S_PHR provenance, and the provenance's DECISION.json and BARS.json must still hash to their recorded values. If no fold file exists, the seeds must hold NOT_YET.
- `mc_staging.py:27` (`sources`) stages the fold file and both provenance files.
- Test: `test_preflight_phrase_hash_against_seed_provenance` (381).

## 4. KILLED is refused unconditionally, the budget survives exceptional exits, resumes are bound
- `mc_track_pass.py:59` (`refusal`) refuses a KILLED stop with no override and treats a ledger left active as KILLED. Only `--resume-after-stop` continues a HARD_STOP or PROJECTION stop (`:28`). `launch_gpu.sh:60-71` applies the same rule before any reading.
- `mc_track_pass.py:209` (`on_term`) saves the elapsed budget on SIGTERM, SIGHUP and SIGINT. `:231-235` records any exception and saves the budget in `finally`. `launch_gpu.sh:127` records KILLED on exits 124, 137 and 143.
- `mc_track_pass.py:221-225` refuses a resume under another population id or code contract (exit 5). `:294-296` binds every unit file to its frames, seed masks, seed metadata and population id, and `done` (`:299`) stops on any mismatch.
- Tests: `test_refusal_rules` (202), `test_main_refuses_killed_even_with_resume` (227), `test_main_refuses_other_binding` (236), `test_main_saves_budget_on_exception` (243), `test_launch_ledger_rules` (473, 7 cases).

## 5. Global arm order with repeated embeddings counted
- `mc_track_pass.py:105` (`units`) runs units arm-major in `C.ORDER`: S_A0/D64 on all 209 captures (the 204 decision captures first), then S_GT/D64, S_A0/A32, S_GT/A32, S_PHR/D64 and S_PHR/A32.
- Each unit embeds the frames its arm reads (`:369`, `:402`). `unit_cost` (`:83`) and `predicted` (`:310-312`) count that embedding, and an S_PHR seed equal to its S_A0 seed reuses the S_A0 record without embedding.
- The 10-unit receipt, the projection drops (`plan_drop`, `:95`) and the 2-hour cumulative stop (`:356`, `:413-419`) are kept.
- Tests: `test_units_are_arm_major` (265), `test_unit_cost_counts_its_own_embedding` (269), `test_projection_and_drop` (275), `test_plan_unit_reuses_phr_twin_and_reads_its_frames` (285).

## 6. Caches and the timing receipt stay under out/v2/track
- `gpu_inner.sh:9` points every cache and TMPDIR at `$MC_OUT/cache`. `:14` keeps `timeout -k 30` at the remaining budget.
- `mc_track_pass.py:136` (`timing_receipt`) writes only `<track>/TIMING_RECEIPT.json`. `mc_summary.py:339` publishes it to out/v2 after the pass.
- The launcher keeps its two readings 300 s apart, the 1,024 MiB rejection and vnice.
- Tests: `test_timing_receipt_writes_only_the_track_dir` (295), `test_gpu_inner_keeps_caches_under_track` (302), `test_launch_refuses_busy_second_reading` (458), `test_launch_refuses_cards` (452).

## 7. Self-contained staging with a pinned local vnice
- `kit_v2/vendor/vnice.sh` (sha256 3ab2b542…) and `terminator.sh` (sha256 19727987…) were copied once from `/data3/shared/scripts/vnice/`. vnice runs the terminator from its own directory, and the terminator writes only `/tmp/terminator/$USER-<pid>`.
- `launch_gpu.sh:14,50-51` runs the local copy after checking both pins. `mc_common.py:23-24` holds the pins, and `manifest.sh` covers `vendor/*.sh`.
- `mc_staging.py:27-38` lists every input of the pass, the launcher and the preflight. The list includes STAGING.json (its own size is a fixed point, `:71`), STAGING_FRAMES.txt, POPULATION.json, the ruling, BARS_AMENDMENT.json and the phrase files, and the script refuses any path outside /scratch (`:57`).
- Tests: `test_staging_is_self_contained` (396), `test_vendor_vnice_is_pinned_and_local` (412), `test_nothing_reads_data_paths` (310).

## 8. Population: RULING 1056Z
- `in/RULING_1056Z.md` holds the ruling's text verbatim. `mc_population.py` writes `out/v2/POPULATION.json`: the decision population of 204 captures / 1,012 rows, the beside population of 209 / 1,037, and a track order that puts the decision captures first. Its id (f0ecd8ee…) is a content digest that `mc_common.py:113-120` verifies.
- The id binds the tracker contract (`mc_track_pass.py:112`), every stub and track file (`mc_price.py:63` refuses another id) and the bars amendment. Priced files of captures outside the population are listed as ignored (`mc_price.py:138`, `mc_summary.py:32`).
- `mc_summary.py:58,121` computes the bars and completeness on the decision population and reports the 209/1,037 numbers beside them. The A32 per-fold choice fits on decision rooms (`:166`).
- `launch_gpu.sh:42` refuses arguments, because the old `--exclude-withheld` flag is gone.
- Tests: `test_population_counts_and_digest` (361), `test_completeness_reads_each_population` (342), `test_launch_refuses_arguments` (481).

## 9. Per-dataset measurements and frame spacing in mc_summary
- `mc_summary.py:121` (`evaluate`) runs `measure` (`:85`) for every arm by dataset (ARKitScenes, ScanNet, ScanNet++). `:133` (`deployed_reference`) gives the deployed track's mask numbers by scope and dataset, and `:214` (`report`) prints them in parentheses.
- `:148` (`frame_spacing`) reports the native gaps between anchors and between dense frames, from FRAME_SETS.json, beside the spec's 272/35/25.
- Test: `test_frame_spacing_by_dataset` (332); the dry-run stub report `out/v2/dry/CARRY_REPORT_STUB.md`.

## Beyond the nine edits
- 24 GB Ampere: `launch_gpu.sh:19-20,94` accepts a card with at least 24e9 bytes, compute capability 8.0 or higher, and every field numeric. `mc_track_pass.py:268` refuses a card without native bf16 (exit 6). Test: `test_launch_accepts_24e9_bytes_with_bf16` (444).
- `mc_bars.py:96` compares the frozen bars without their spec path, because the frozen file names the builder workspace and the spec bytes are identical.
- `review/` holds the reviewer's `reproduce.sh`, `review_run.*`, `tests_run.py` and `contract_audit.py`, repointed to sb_cafix (originals' sha256 in `review/SOURCE_SHA256SUMS`). It adds the population step and the empty stub, and `contract_audit_4col.py` adds a 4-column nvidia-smi mock.

## Rerun evidence (2026-11-19, CPU only, nice 10, 8 threads, at most 8 workers)
- `bash kit_v2/dryrun.sh` (12:11-12:17Z; the full-capture run had finished at 12:10Z): steps 0-3, 1b and the seeds pass, and the 74 tests pass. `out/v2/DRYRUN.json`, `dry/STUB_PARITY.json`.
- Step 4 (11:32-12:10Z) is PARTIAL with timing: 2,291 s for S_A0/D64, S_GT/D64 and S_A0/A32 on all 64 frames of arkitscenes/41048124. The projection for all four arms (2,739 s) exceeded 2,700 s, so S_GT/A32 and the trailing S_PHR arms were dropped.
- `review/reproduce.sh`, `tests_run.py`, `contract_audit.py`, `contract_audit_4col.py` and the preflight all exit 0 (`work/v2/logs/after_cpu.log`). The results are in `review/logs/`, `review/CONTRACT_AUDIT.json` and `review/CONTRACT_AUDIT_4COL.json`.
- Phrase folds used: `/scratch/jjyeung/orch_n30/sb_mask_phrase/out/PHRASE_FOLDS.json`, sha256 5af09f4b670382bcbb0253690ba109e4002f849b53b7bd3e2e8cd599375f2285 (sb_phfix absent).
- vnice.sh sha256 3ab2b542726f32dbecdbe30104f903aa2bef3526a9257013fd5f8bcc99461c6b; terminator.sh sha256 19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d.
- Not edited: `mc_tracker.py`. The pass drops whole suffixes of `C.ORDER`, so a zero-cost S_PHR arm (all seeds reused) goes with any arm before it, as the spec's order requires.
