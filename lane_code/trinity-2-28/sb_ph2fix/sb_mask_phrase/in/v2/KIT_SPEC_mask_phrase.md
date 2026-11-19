# KIT SPEC mask_phrase: the phrase the model writes in its ground call, and retention on frozen SAM 3, priced on K1 training captures (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 1). Builder: one Codex Astra job on trinity-1-18, workspace `/scratch/jjyeung/orch_n30/sb_mask_phrase` (write there only). Part 1 is CPU and has the orchestrator's GO (ruling 09:49Z). Part 2 needs a placement GO (0.6 GPU-h). K1 training captures only; no held-out capture, no R0-dev, dev-S1 or official item is opened.

## Question the kit answers
If the model writes another phrase for an object name in its `<ground obj=...>` call (one call, or a second call when the first returns nothing), does the unchanged ladder score higher, when each name's phrase is chosen on other rooms? Which phrases carry the gain, and how many routed rows would teach it? An alias table inside the tool does not ship (ruling 09:49Z, item 3), so the bars read only arms the model's own call can produce.

## Inputs (trinity-1-18, read-only; pin every file by sha256 in each output JSON)
- Ladder: `/scratch/jjyeung/orch_n30/sb_kbox4/` (`train_pricing.py`: `setup`, `Objects`, `lifted`; `pricing.session_distance(row, geo, objects, G, 'best1')`; `predicted.py`: `cache_detect`, `member_precision`; `serving_reference.py`: `geometry`, `gt_arrays`, `digest`; `math_v2.folds`; `summarize_train.contrast`; `run.sh`). Archive `out/sb_kbox4.tar` with `out/sb_kbox4.tar.sha256`.
- Rows and labels: `sb_kbox4/pinned_train.json`; `/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt` (sha256 e7646798...8a35a98ac); `/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl` (d781ac7b...).
- Published arms: `sb_kbox4/out/box_ladder/PER_ITEM.jsonl` (3bc7f87f...), arms `A0_deployed`, `A2_gt_masks`.
- Stage-1 cache: `/scratch/jjyeung/k1/run_convert_2/<digest(canonical)[:16]>/candidates.json`. Per frame and name: `presence`, `all_instance_scores`, `instances[]` with `score`, `source_prompt`, `source_presence`, RLE `mask`. The cache merged an alias instance into a raw-name instance when their IoU exceeded 0.95, so an alias's stored pool lacks the instances the raw name also found.
- Alias dictionary (read, never edit): `/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py`, `ALIASES` (written from language alone).
- Selector head: `/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso/selector_head.{json,safetensors}` (63aa0a69..., 6d97c524...). Tree: `/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449` (`student_pilot/routed_features.py: cache_for` takes one presence per frame, that of the frame's first entry).
- Mask overlap code and rules: `/scratch/jjyeung/orch_n30/sb_maskfail/analyze.py` (`measure`, `metrics`, `stats`), `RULES.md`; object categories as defined in the design record's Evidence section.
- Routed rows of leg R1 (for the rewrite count): swarm_build3 names the store; `trinity-1-18:/scratch/jjyeung/n30_mirror/rows_r1` mirrors store v7 (`ROWS_V7_R1_20261117.md`). If no named file holds rows with `<ground obj=`, the count says MISSING with the expected path.
- Part 2 only: frames `pinned_train.json: captures[].dense_frames[anchor_slots].path` (480 x 640 PNG under `/scratch/jjyeung/k1_frames/`; all 64 files of all 239 captures are present). SAM 3 checkpoint `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` (sha256 9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e, checked by this lane; `SAM3_RECEIPT.json` beside it); staged source root `/scratch/jjyeung/b01ec87a6f29b/d/s` (verify the six source hashes of the receipt in `vendor_sam/vendor/SAM3_RECEIPT.json`); tower wrapper `vendor_sam/vendor/sam3_tower.py`, which refuses a checkpoint or source outside `/scratch`; the reader's detector call `sb_kbox4/reader_src/e2e_reader/stage1.py: sam3_detect`. Interpreters: CPU `/scratch/jjyeung/envs/p1cpu/bin/python`; SAM 3 `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` (its editable `sam3` points at NFS; put the staged source root first on `sys.path`).

## Arms (each is A0 with only the phrase behind a name's call changed; retention floor 0.05 and cap 30, linker, selector `run_iso` with rule `candidates_argmax`, lifting, `best1`, refusal = 0 and the room bootstrap stay byte-identical)
- `P0`: `cache_detect` unchanged. Parity arm.
- **Policies the model can write.** For object name n, the candidate phrases are n and its dictionary aliases. A phrase w's pool is the stored instances of n's record with `source_prompt == w`, each with its `source_presence`, kept at `score * source_presence >= 0.05`, sorted by score, cap 30. The reader runs with w as the call's name (the selector featurises w alone). A policy is one phrase (one call), or an ordered pair (w1, w2): the object takes w1's result unless that call returns `not seen` (no accepted candidate), and then w2's.
- `W_cf` (the arm the bars read): the ladder's five room folds. For fold k and name n, score every policy on the captures of the other four folds by the number of n's objects whose served track is on target at its priced frame (IoU >= 0.5 with the raster on the track's largest frame, 240 x 320 canvas). The name takes the best policy; ties go to fewer calls, then to the raw name; a name with fewer than five fit objects keeps the raw name. Rows of fold k are priced with fold k's policies. No distance label enters the choice.
- `P_cf` (ceiling, not shippable, reads no bar): the pooled raw-plus-alias pool per name (every stored instance at the same floor and cap; presence per frame as `cache_for` takes it), switched per name by the same cross-fit. It shows what a detector that answered the raw name with the alias's objects would reach, the target of the fine-tune kit.
- `P_cap100` (diagnostic): raw name, cap 100.
- Part 2 (GPU): `W_exact`: each policy of `W_cf` rerun through SAM 3 with the written phrase alone, replacing the stored approximation. `W_new`: for names without dictionary entries, at most three phrases per name, written by the builder from the list of the 64 operand names alone and saved with sha256 (`NEW_PHRASES.json`) before the pass; they join the candidate phrases and the same cross-fit. `R_cond` (a reader constant, not a phrase): in a frame where the written phrase keeps no candidate, keep the queries with conditional score >= 0.5, at most 5; priced on top of the best W arm and adopted only through a seal review.

## Bars, written before any score
- `parity`: `P0` equals `A0_deployed` on 1,037 of 1,037 predictions. A miss stops the kit with a BLOCKER.
- `phrase_worth`: `W_cf` minus `A0` at least +1.5 type points, paired 95% lower bound above 0 (10,000 room draws, seed 20261119).
- `phrase_safe`: on the rows whose two operands are both good under `A0` (456 rows by the design record's definition; the kit recomputes the set and reports its size), `W_cf` minus `A0` has a lower bound above -1.0.
- Part 2: `exact_holds`: `W_exact` minus `W_cf` has a lower bound above -1.0. `new_worth`: the cross-fitted arm with new phrases minus `W_exact` at least +1.0, lower bound above 0, and `phrase_safe` holds. `retention_worth`: `R_cond` minus the best W arm at least +1.0, lower bound above 0, and `phrase_safe` holds.
- Decision: if `phrase_worth` and `phrase_safe` pass, the policies are refit on all training rooms by the same rule and frozen as `PHRASE_SET.json` (name, policy). The carry and fine-tune kits take it as their baseline. Otherwise the model keeps writing the raw name.

## Report
- For every arm: MRA with interval, paired contrast against `A0`, refusals; pool recall at IoU 0.5 by operand; served-mask IoU per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`); operand categories (good, wrong object, weak, poor priced frame, refused); masks served on raster-absent frames; tables by dataset and by name; member precision of `sb_kbox4`'s merge at its three thresholds against the 90% bar; first-seen pair rate against 90%.
- Which phrases carry it: per name, the frozen policy, its fit and held-out on-target counts, and the paired gain of the rows that name it.
- Rows to rewrite: the names whose policy differs from the raw name; the K1 train rows that name them (91 of 1,037 name heater or coat hanger by this lane's count); names whose best policy differs but that have fewer than five fit objects, listed with their counts and left on the raw name; the count in leg R1's routed rows, by name, and how many of those need a second call.

## CPU dry run (before any priced number)
1. `P0` parity on 5 captures, then on all.
2. Pool recall check against this lane's counts (IoU 0.5 in some visible anchor, row-weighted operands of 2,074): at the retention floor alone, raw 1,804 and pooled raw-plus-alias 1,883; with the lifting floor of 0.3 on the conditional score as well, raw 1,757, the best single phrase per name 1,828 (heater to radiator 84 of 84, coat hanger to coat rack 8 of 8, in-sample) and pooled 1,856. A different count is reported, not forced.
3. The reader accepts a call whose name is the written phrase (selector features build, no exception); if it refuses, stop and report the exact assertion (do not edit reader code).
4. Fold disjointness by room; every capture has `k1_split == train`.
5. Part 2: SAM 3 loads from the staged source; on one capture the rerun of the raw name reproduces the stored raw instances (scores within bf16 tolerance, masks IoU >= 0.99) before any new pool is trusted.

## GPU budget and stops (part 2)
One 48 GB card, placed by swarm_build3, two fresh empty `nvidia-smi` readings 5 minutes apart recorded in the launch event, under `vnice.sh` off trinity-0-13. 209 captures x 32 anchors, the chosen and new phrases of their operand names: estimate 0.4 GPU-h, hard stop 0.6. Time the first 10 captures; stop if the projection exceeds the cap. A kill is reported, not rerun.

## Outputs (`out/`)
`PHRASE_REPORT.md` (first table: arms with contrasts and bars; second: phrases by name; third: rows to rewrite), `DECISION.json`, `PHRASE_SET.json`, `PER_ITEM.jsonl`, `OBJECTS.json`, `NEW_PHRASES.json`, part 2 pools in the cache's format under `out/pool_part2/<key>/candidates.json`, `sb_mask_phrase.tar` with sha256. STATUS.md after each stage.

## R0-dev
None here. The frozen stack takes the one absolute-distance look (design record, Answer 6); its arm and bar go into `B/events/swarm_build/R0DEV_LOOKS.md` before the read.
