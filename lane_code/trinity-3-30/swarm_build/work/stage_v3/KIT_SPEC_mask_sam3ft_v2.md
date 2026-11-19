# KIT SPEC mask_sam3ft v2: fine-tune SAM 3's detector on K1 training rasters with the question vocabulary, priced by room folds (sb_maskdesign, 2026-11-19)

Design record: `distill_design/MASK_QUALITY_DESIGN_20261119.md` (candidate 3). Builder: one Codex Astra job on trinity-1-18 (a hard build), workspace `/scratch/jjyeung/orch_n30/sb_mask_sam3ft` (write there only). This v2 is the only version to build from; it answers review sb_mdrev (findings 8, 11, 12, 13). The data build and CPU dry run may start at once. Training needs the orchestrator's GO (7.0 GPU-h, 1.2 to the fail-fast), which comes only after the phrase kit's result: if written phrases recover most of the 9.9 points that sit on pool recall, this is not the next spend (ruling 09:49Z, item 4). K1 training captures only. A checkpoint that ships this adapter is reported as SAM 3 with a trained detector adapter, not as a frozen tower, and it does not yet ground from the model's own encoder.

## Question the kit answers
Does a small fine-tune of SAM 3's detector (presence, scoring, decoder adapters) on raster instances named in the datasets' vocabulary find the named object on rooms it never saw, and does the unchanged ladder score higher on its pool?

## Inputs (trinity-1-18, read-only; pin by sha256)
- Ladder, rows, labels, published arms, selector head, overlap code, frames and environment: as in `KIT_SPEC_mask_phrase_v2.md`, section Inputs.
- SAM 3, pinned: checkpoint `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` (sha256 9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e); receipts `/scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json` and `/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/SAM3_RECEIPT.json` (upstream revision 5dd401d1c5c1d5c3eedff06d41b77af824517619, six source hashes); source root `/scratch/jjyeung/b01ec87a6f29b/d/s`, first on `sys.path`.
- Model API: `sam3/model_builder.py: build_sam3_image_model(checkpoint_path=..., load_from_HF=False, enable_segmentation=True)` returns `Sam3Image`; forward as the reader calls it (`backbone.forward_text`, `forward_grounding`).
- Loss API: `sam3/train/loss/sam3_loss.py: Sam3LossWrapper` over `sam3/train/loss/loss_fns.py: IABCEMdetr` (classification; its presence term if it has one, else binary cross-entropy on the decoder's presence logit, declared in `MODEL_CARD.json`) and `Boxes`; matcher `sam3/train/matcher.py: BinaryHungarianMatcherV2`; weights from the fine-tune config the source ships under `sam3/train/configs` (the report names the file). `Masks` is not used. These files and class names exist in the source tree on NFS (`/home/jjyeung/agent_project/agent/third_party/sam3`, listed by the design lane), which is never imported. If the staged root lacks them, the kit reports MISSING with the file list and stops until a staged copy exists; it does not write its own loss.
- Training captures: the 239 captures of `sb_kbox4/pinned_train.json` (all `k1_split == train`, all with a raster on disk; ARKitScenes 127, ScanNet++ 71, ScanNet 41). The 209 with priced rows are the pricing set.
- Rasters and class names: `serving_reference.gt_arrays(c)` returns the canvas instances and the raw file; `ids` and `labels` in the raw file give each instance's class.
- Detector call to mirror at inference: `sb_kbox4/reader_src/e2e_reader/stage1.py:sam3_detect` (conditional scores, presence, joint floor 0.05, cap 30, mask logit above 0).
- The phrase kit's `PHRASE_FOLDS.json` and `W_cf` rows, if its bars passed.

## Data build (CPU)
- **Vocabulary, per model.** Every raster class label in that model's training half except `wall`, `floor`, `ceiling`, `object`, `remove`, `split`, `unknown` and labels that contain a digit. Saved as `VOCAB_A.json` and `VOCAB_B.json` with counts and sha256 before training. Counts, sampling weights and negatives of a model come from its own half only; nothing of the other half enters its data.
- **Items.** One item per (capture, anchor). Positive queries: up to 6 vocabulary names visible in the frame, sampled with weight 1/sqrt(count); targets are that name's instances covering at least 0.2% of the frame (box and mask from the raster, nearest-neighbour to the model's size). Smaller instances of the name are ignore regions: a query matched to one carries no loss. Negative queries: 2 names found in the capture but absent from the frame and 2 names of that model's vocabulary absent from the capture; presence target 0.
- **Folds.** Two halves by room (`sha256(room)` parity), so no room, and no capture of one room, sits in both. Model A trains on half A and is read only on half B; model B the reverse.

## Model and training
- Trainable, by module: LoRA rank 16 on the attention projection weights of the fusion encoder (`TransformerEncoderFusion`, built by `_create_transformer_encoder`) and of the decoder (`TransformerDecoder`, built by `_create_transformer_decoder`); the decoder's `presence_token`, `presence_token_head` and `presence_token_out_norm`; the scoring module built by `_create_dot_product_scoring`. Frozen (`requires_grad = False`): the vision backbone and neck, the text encoder, the geometry encoder, the box head, the segmentation head. `MODEL_CARD.json` lists the attribute path, parameter count and trainable flag of every module; a named module that does not exist stops the kit.
- Loss: the pinned loss API above. No mask loss.
- AdamW, learning rate 1e-4, 200 warm-up steps, cosine decay; 4 frames x 10 queries per step; bf16; 1008 px; 6,000 steps per fold; exact resume every 500 steps; seed 20261119.
- Inference: each model on the other half's 32 anchors for every operand name, the reader's contract unchanged, written in the stage-1 cache's format.

## Arms (the ladder unchanged downstream)
- `FT_sel`: the fine-tuned pool, deployed selector `run_iso`. The arm the bars read.
- `FT_top` (diagnostic): the linked candidate with the highest mean detector score, selector bypassed.
- Baselines: `A0_deployed`, and the phrase kit's `W_cf` (or its part 2 successor) if one passed.
- Stack arm `FT_sel+PHR`, only if the phrase bars passed: each row's calls use the phrase policy of the phrase fold that held its room out, on the model that never saw its room. The all-room phrase set and an all-room detector are reserved for the final frozen arm.

## Bars, written before any score
- `ft_failfast` (model A at step 1,500, on 200 half-B operand objects drawn with seed 20261119): the top-scoring detection for the name on the object's largest visible anchor is on target (IoU >= 0.5) at least 5 points more often than frozen SAM 3 on the same objects, and pool recall is not lower. A miss stops the kit.
- `ft_worth`: `FT_sel` minus the best baseline at least +3.0 type points, paired 95% lower bound above 0, on all 1,037 rows (each priced by the model that never saw its room; 10,000 room draws, seed 20261119).
- `ft_object`: wrong-object plus refused operands at most 10% (17.1% under `A0`), pool recall at IoU 0.5 at least 93% (87.0%).
- `ft_safe`: on the rows whose operands are both good under `A0`, `FT_sel` minus `A0` has a lower bound above -1.5; the frozen mask head's mean IoU on matched instances is within 0.02 of frozen SAM 3's.
- Printed against their own bars, deciding nothing here: served-mask IoU per visible operand-frame and at the priced frame (`sb_maskfail/analyze.py: stats`); member precision of `sb_kbox4`'s merge at its three thresholds (90%), first-seen pair rate (90%), and for raster classes with two or more instances the share of (capture, class) pairs whose number of linked objects with score above 0.5 equals the raster count.
- Decision: `ft_worth`, `ft_object` and `ft_safe` pass: the fine-tuned detector joins the stack. The final fit on all 239 training captures is a separate run with its own GO and budget (3.0 GPU-h), after the K1 verdict and before the R0-dev look. Otherwise the pool stays frozen SAM 3.

## CPU dry run
1. Loader on 3 captures: positives, ignores and negatives per item printed; boxes drawn from rasters match the instance extents.
2. Writer parity: the stored raw pool pushed through the kit's cache writer reproduces `A0_deployed` on 1,037 of 1,037 predictions.
3. Fold check: 0 shared rooms and 0 shared captures between the halves; no capture outside the 239; a manifest holding any other capture is refused; each `VOCAB` file is recomputed from its half and compared.
4. One optimizer step on CPU with LoRA attached (loss finite, only the listed parameters change), then exact resume from its checkpoint.
5. Trainable parameter count and the list of frozen modules written to `MODEL_CARD.json`.

## GPU budget and stops
One or two 48 GB cards, placed by swarm_build3, two fresh empty readings 5 minutes apart per card in the launch event, `vnice.sh` off trinity-0-13. Per fold: training about 2.6 GPU-h, inference 0.4. Fail-fast evaluation 0.2. Hard cap 7.0. No throughput has been measured: the kit writes `out/TIMING_RECEIPT.json` after the first 100 steps and reports the projection; if 6,000 steps would exceed 2.6 GPU-h, cut the step count to fit and record it (the bars stay). Stop on `ft_failfast`, on a non-finite loss, or at the cap. Model B starts only after model A passes `ft_failfast`. A kill is reported, not rerun. Read frames from `/scratch`, write to `/scratch`.

## Outputs (`out/`)
`FT_REPORT.md` (first table: arms, contrasts, bars), `BARS_FROZEN.json`, `TIMING_RECEIPT.json`, `DECISION.json`, `VOCAB_A.json`, `VOCAB_B.json`, `MODEL_CARD.json`, per-fold adapter weights (`ft_A.safetensors`, `ft_B.safetensors`, sha256), pools under `out/pool/<key>/candidates.json`, `PER_ITEM.jsonl`, `OBJECTS.json`, training logs, `sb_mask_sam3ft.tar` with sha256 (weights listed, not packed, above 5 GB). STATUS.md after each stage.

## Registration and leakage guard
- Before any priced number the builder writes `out/BARS_FROZEN.json`: sha256 of this spec, UTC time, and the list of bars. A later change to a bar voids the result.
- No arm, phrase, threshold or stop is chosen from R0-dev, dev-S1, K1 held-out or official items; none of them is opened.
- R0-dev capture-exclusion manifest: MISSING (owner: orchestrator). The data build and the CPU dry run may proceed, but no training starts and no training-data legality is certified until the manifest is named and 0 of the 239 captures and 0 of their rooms are in it.

## R0-dev
None here. A passing detector enters the frozen stack's single absolute-distance look (design record, Answer 6).
