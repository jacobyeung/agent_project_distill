# KIT SPEC mask_phrase: phrase and retention choices for the SAM 3 pool, priced on K1 training captures (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 1). Builder: one Codex Astra job on trinity-1-18, workspace `/scratch/jjyeung/orch_n30/sb_mask_phrase` (write there only). Part 1 is CPU and may run as soon as its dry run passes. Part 2 needs the orchestrator's GO (0.6 GPU-h). K1 training captures only; no held-out capture, no R0-dev, dev-S1 or official item is opened.

## Question the kit answers
Does widening SAM 3's pool for a name (stored alias prompts; candidates the presence score vetoes; new phrases) raise the distance score of the unchanged ladder, when the choice per name is made on other rooms?

## Inputs (trinity-1-18, read-only; pin every file by sha256 in each output JSON)
- Ladder: `/scratch/jjyeung/orch_n30/sb_kbox4/` (`train_pricing.py`: `setup`, `Objects`, `lifted`; `pricing.session_distance(row, geo, objects, G, 'best1')`; `predicted.py`: `cache_detect`, `member_precision`; `serving_reference.py`: `geometry`, `gt_arrays`, `digest`; `math_v2.folds`; `summarize_train.contrast`; `run.sh`). Archive `out/sb_kbox4.tar` with `out/sb_kbox4.tar.sha256`.
- Rows and labels: `sb_kbox4/pinned_train.json`; `/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt` (sha256 e7646798...8a35a98ac); `/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl` (d781ac7b...).
- Published arms: `sb_kbox4/out/box_ladder/PER_ITEM.jsonl` (3bc7f87f...), arms `A0_deployed`, `A2_gt_masks`.
- Stage-1 cache: `/scratch/jjyeung/k1/run_convert_2/<digest(canonical)[:16]>/candidates.json`; per frame and name: `presence`, `all_instance_scores`, `instances[]` with `score`, `source_prompt`, `source_presence`, RLE `mask`.
- Alias dictionary (read, never edit): `/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py`, `ALIASES`.
- Selector head: `/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work/run_iso/selector_head.{json,safetensors}` (63aa0a69..., 6d97c524...).
- Mask overlap code and rules: `/scratch/jjyeung/orch_n30/sb_maskfail/analyze.py` (`measure`, `metrics`), `RULES.md`; object categories as defined in the design record's Evidence section.
- Part 2 only: frames `pinned_train.json: captures[].dense_frames[anchor_slots].path` (480 x 640 PNG under `/scratch/jjyeung/k1_frames/`); SAM 3 checkpoint with sha256 9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e (candidate folders `/scratch/jjyeung/n13_outage/sam3_ckpt`, `/scratch/jjyeung/qwen_port_1110/sam3_ckpt`; verify the hash, report MISSING otherwise); tower code `vendor_sam/vendor/sam_backend.py` (356802c9...) and `sam3_tower.py` beside it; the reader's detector call `sb_kbox4/reader_src/e2e_reader/stage1.py:sam3_detect`. Interpreter for CPU: `/scratch/jjyeung/envs/p1cpu/bin/python`; for SAM 3: `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` (verify it imports the tower).

## Arms (each is A0 with only the per-name detect function changed; linker, selector `run_iso` with rule `candidates_argmax`, lifting, `best1`, refusal = 0 and the room bootstrap stay byte-identical)
- `P0`: `cache_detect` unchanged. Parity arm.
- `P_all`: for a name with dictionary entries, the pool is every stored instance of the name's record with `score * source_presence >= 0.05`, sorted by score, cap 30; each entry keeps its own `source_presence`. Names without entries keep the raw pool.
- `P_cf` (the arm the bars read): the ladder's five room folds. For fold k and each name, count on the captures of the other four folds the objects whose served track is on target at its priced frame (IoU >= 0.5 with the raster on the track's largest frame, 240 x 320 canvas), under `P0` and under `P_all`. The name takes aliases in fold k when it has at least five fit objects and the `P_all` count is larger. Rows of fold k are priced with fold k's name set. No distance label enters the choice.
- `P_cap100` (diagnostic): raw name, cap 100.
- Part 2, `R_cond`: in a frame where the raw name keeps no candidate, keep the queries with conditional score >= 0.5, at most 5, with the frame's presence as stored. `R_new`: for names without dictionary entries, at most three phrases per name, written by the builder from the list of the 64 operand names alone and saved with sha256 (`NEW_PHRASES.json`) before the GPU pass; pool = raw plus those. Both enter the same per-name, cross-fitted choice as `P_cf`, giving `R_cf` (aliases, vetoed queries and new phrases, each switched per name on fit rooms).

## Bars, written before any score
- `parity`: `P0` equals `A0_deployed` on 1,037 of 1,037 predictions. A miss stops the kit with a BLOCKER.
- `phrase_worth`: `P_cf` minus `A0` at least +1.5 type points, paired 95% lower bound above 0 (10,000 room draws, seed 20261119).
- `phrase_safe`: on the rows whose two operands are both good under `A0` (456 rows by the design record's definition; the kit recomputes the set and reports its size), `P_cf` minus `A0` has a lower bound above -1.0.
- `retention_worth` (part 2): `R_cf` minus `P_cf` at least +1.0, lower bound above 0, and `phrase_safe` holds for `R_cf`.
- Decision: the passing arm with the highest train score is refit on all training rooms by the same rule and frozen as `PHRASE_SET.json` (name, phrases, retention flag). The carry and fine-tune kits take it as their baseline pool. No bar passed: the pool stays raw.

## Report for every arm
MRA with interval, paired contrast against `A0`, refusals; served-mask IoU per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`); operand categories (good, wrong object, weak, poor priced frame, refused); pool recall at IoU 0.5 by operand; masks served on raster-absent frames; tables by dataset and by name; member precision of `sb_kbox4`'s merge at its three thresholds on the arm's pool, against the 90% bar; first-seen pair rate against 90%.

## CPU dry run (before any priced number)
1. `P0` parity on 5 captures, then on all.
2. Pool recall check: the raw pool holds an IoU 0.5 mask for 1,804 of 2,074 operands and `P_all` for 1,883 (the design lane's count); a different count is reported, not forced.
3. The selector and `F.cache_for` accept entries with differing presence in one frame; if they refuse, stop and report the exact assertion (do not edit reader code).
4. Fold disjointness by room; every capture has `k1_split == train`.
5. Part 2: SAM 3 loads on CPU or stub; on one capture the rerun reproduces the stored raw instances (scores within bf16 tolerance, masks IoU >= 0.99) before any new retention is trusted.

## GPU budget and stops (part 2)
One 48 GB card, two fresh empty `nvidia-smi` readings 5 minutes apart recorded in the launch event, under `vnice.sh` off trinity-0-13. 209 captures x 32 anchors, about 770 names plus new phrases: estimate 0.4 GPU-h, hard stop 0.6. Time the first 10 captures; stop if the projection exceeds the cap. A kill is reported, not rerun.

## Outputs (`out/`)
`PHRASE_REPORT.md` (first table: arms with contrasts and bars), `DECISION.json`, `PHRASE_SET.json`, `PER_ITEM.jsonl`, `OBJECTS.json`, `NEW_PHRASES.json`, part 2 candidates in the cache's format under `out/pool_part2/<key>/candidates.json`, `sb_mask_phrase.tar` with sha256. STATUS.md after each stage.

## R0-dev
None here. The frozen stack's single absolute-distance look is defined in the design record (Answer 6).
