# KIT SPEC mask_sam3ft: fine-tune SAM 3's detector on K1 training rasters with the question vocabulary, priced by room folds (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 3). Builder: one Codex Astra job on trinity-1-18 (a hard build), workspace `/scratch/jjyeung/orch_n30/sb_mask_sam3ft` (write there only). The data build and CPU dry run may start at once; training needs the orchestrator's GO (7.0 GPU-h, 1.2 to the fail-fast). K1 training captures only.

## Question the kit answers
Does a small fine-tune of SAM 3's detector (presence, scoring, decoder adapters) on raster instances named in the datasets' vocabulary find the named object on rooms it never saw, and does the unchanged ladder score higher on its pool?

## Inputs (trinity-1-18, read-only; pin by sha256)
- Ladder, rows, labels, published arms, selector head, overlap code, frames, SAM 3 checkpoint and environment: as in `KIT_SPEC_mask_phrase.md`, section Inputs.
- Training captures: the 239 captures of `sb_kbox4/pinned_train.json` (all `k1_split == train`, all with a raster on disk; ARKitScenes 127, ScanNet++ 71, ScanNet 41). The 209 with priced rows are the pricing set.
- Rasters and class names: `serving_reference.gt_arrays(c)` returns the canvas instances and the raw file; `ids` and `labels` in the raw file give each instance's class.
- Detector call to mirror at inference: `sb_kbox4/reader_src/e2e_reader/stage1.py:sam3_detect` (conditional scores, presence, joint floor 0.05, cap 30, mask logit above 0).
- `PHRASE_SET.json` and the phrase kit's `P_cf` rows, if they exist.

## Data build (CPU)
- **Vocabulary.** Every raster class label in the 239 captures except `wall`, `floor`, `ceiling`, `object`, `remove`, `split`, `unknown` and labels that contain a digit. Saved as `VOCAB.json` with counts and sha256 before training.
- **Items.** One item per (capture, anchor). Positive queries: up to 6 vocabulary names visible in the frame, sampled with weight 1/sqrt(count); targets are that name's instances covering at least 0.2% of the frame (box and mask from the raster, nearest-neighbour to the model's size). Smaller instances of the name are ignore regions: a query matched to one carries no loss. Negative queries: 2 names found in the capture but absent from the frame and 2 vocabulary names absent from the capture; presence target 0.
- **Folds.** Two halves by room (`sha256(room)` parity), so no room, and no capture of one room, sits in both. Model A trains on half A and is read only on half B; model B the reverse.

## Model and training
- SAM 3 image model from the pinned checkpoint. Frozen: vision encoder and neck, text encoder, mask head. Trainable: LoRA rank 16 on the attention projections of the fusion encoder and the decoder, the presence head, the scoring head.
- Loss: the package's own detection loss if the installed SAM 3 ships its training code; otherwise Hungarian matching with focal classification (alpha 0.25, gamma 2), L1 and GIoU on boxes, and binary cross-entropy on presence. No mask loss.
- AdamW, learning rate 1e-4, 200 warm-up steps, cosine decay; 4 frames x 10 queries per step; bf16; 1008 px; 6,000 steps per fold; exact resume every 500 steps; seed 20261119.
- Inference: each model on the other half's 32 anchors for every operand name, the reader's contract unchanged, written in the stage-1 cache's format.

## Arms (the ladder unchanged downstream)
- `FT_sel`: the fine-tuned pool, deployed selector `run_iso`. The arm the bars read.
- `FT_top` (diagnostic): the linked candidate with the highest mean detector score, selector bypassed.
- Baselines: `A0_deployed`, and `P_cf` or `R_cf` if the phrase kit froze one.

## Bars, written before any score
- `ft_failfast` (model A at step 1,500, on 200 half-B operand objects drawn with seed 20261119): the top-scoring detection for the name on the object's largest visible anchor is on target (IoU >= 0.5) at least 5 points more often than frozen SAM 3 on the same objects, and pool recall is not lower. A miss stops the kit.
- `ft_worth`: `FT_sel` minus the best baseline at least +3.0 type points, paired 95% lower bound above 0, on all 1,037 rows (each priced by the model that never saw its room; 10,000 room draws, seed 20261119).
- `ft_object`: wrong-object plus refused operands at most 10% (17.1% under `A0`), pool recall at IoU 0.5 at least 93% (87.0%).
- `ft_safe`: on the rows whose operands are both good under `A0`, `FT_sel` minus `A0` has a lower bound above -1.5; the frozen mask head's mean IoU on matched instances is within 0.02 of frozen SAM 3's.
- Printed against their own bars, deciding nothing here: served-mask IoU per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`); member precision of `sb_kbox4`'s merge at its three thresholds (90%), first-seen pair rate (90%), and for raster classes with two or more instances the share of (capture, class) pairs whose number of linked objects with score above 0.5 equals the raster count.
- Decision: `ft_worth`, `ft_object` and `ft_safe` pass: the fine-tuned detector joins the stack, and the record asks for one training run on all eligible rasters before the R0-dev look. Otherwise the pool stays frozen SAM 3.

## CPU dry run
1. Loader on 3 captures: positives, ignores and negatives per item printed; boxes drawn from rasters match the instance extents.
2. Writer parity: the stored raw pool pushed through the kit's cache writer reproduces `A0_deployed` on 1,037 of 1,037 predictions.
3. Fold check: 0 shared rooms; no capture outside the 239; a manifest holding any other capture is refused.
4. One optimizer step on CPU with LoRA attached (loss finite, only the listed parameters change), then exact resume from its checkpoint.
5. Trainable parameter count and the list of frozen modules written to `MODEL_CARD.json`.

## GPU budget and stops
One or two 48 GB cards, two fresh empty readings 5 minutes apart per card in the launch event, `vnice.sh` off trinity-0-13. Per fold: training about 2.6 GPU-h, inference 0.4. Fail-fast evaluation 0.2. Hard cap 7.0. Time the first 100 steps; if 6,000 steps would exceed 2.6 GPU-h, cut the step count to fit and record it (the bars stay). Stop on `ft_failfast`, on a non-finite loss, or at the cap. Model B starts only after model A passes `ft_failfast`. A kill is reported, not rerun. Read frames from `/scratch`, write to `/scratch`.

## Outputs (`out/`)
`FT_REPORT.md` (first table: arms, contrasts, bars), `DECISION.json`, `VOCAB.json`, `MODEL_CARD.json`, per-fold adapter weights (`ft_A.safetensors`, `ft_B.safetensors`, sha256), pools under `out/pool/<key>/candidates.json`, `PER_ITEM.jsonl`, `OBJECTS.json`, training logs, `sb_mask_sam3ft.tar` with sha256 (weights listed, not packed, above 5 GB). STATUS.md after each stage.

## R0-dev
None here. A passing detector enters the frozen stack's single absolute-distance look (design record, Answer 6).
