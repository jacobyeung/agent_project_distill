# Full fine-tuning, the CPD / PDG / FT-A tracks and the GXS variant: design

The head-call arms HC, HX and HA on this trainer: `DESIGN_HEADCALL_FULLFT.md`.

Branch `fullft-gxs` (base: pd-build2-heads df6cf8c, plus GX's geometry input ported from f5cad82). Every choice below
cites its source; the last section lists each place where the build differs from that source, with the reason.

Sources: Cambrian-P = arXiv 2605.22819 and its released configs, as transcribed in
`L/pd_heads_20261030/CAMBRIANP_RECIPE_REPORT.md` (L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`).
Spatial-MLLM = arXiv 2505.23747 and github.com/THU-SI/Spatial-MLLM (`src/qwenvl/model/connector/mlp_add_connector.py`,
`scripts/training/spatial_mllm_train_demo.sh`). VG-LLM = arXiv 2505.24625 and github.com/LaVi-Lab/VG-LLM
(`src/qwen_vl/model/feature_fusion.py`, `scripts/train/train_sr.sh`). VLM-3R = arXiv 2505.20279. MERV = arXiv 2501.01426.
Video-LLaVA = arXiv 2311.10122. PLAN64 = `L/frames64_20261030/PLAN.md`.

## 1. The three tracks

All three train on the same RG2P2 v2 question rows (RG2P2_A_W32_S17: 396,649 trace rows, segment loss), 32 frames,
seed 17, global batch 256, world 32, one epoch, from plain Qwen3.5-9B.

| Track | Stages | Trained | Extra rows | Steps |
|---|---|---|---|---|
| CPD | one: head-only warmup, then joint full FT | LLM + merger 1e-5, vision 2e-6, pose + depth heads 1e-4 | 34,888 pose-only samples (beta 1) | 1,686 |
| PDG | S1: frozen VLM; S2: full FT | S1: G3T connector 1e-3, heads 1e-4. S2: LLM + merger 1e-5, vision 2e-6, heads 1e-4, connector 1e-5 | S1: 200,000 stage-1 geometry rows | 782 + 1,550 |
| FT-A | one | LLM + merger 1e-5, vision 2e-6 | none | 1,550 |

- PDG - FT-A isolates G3T + heads + alignment; CPD - FT-A isolates the Cambrian-P heads and pose-only data;
  PDG - CPD (both with heads) bounds the G3T contribution, though CPD also carries the pose-only rows.
- FT-A has no stage 1: a frozen VLM without attached modules has nothing to train, so "stage 1 without adapter or heads"
  is the identity. Running FT-A's LLM on the geometry questions instead would add geometry data to the control and break
  the isolation.
- CPD's steps exceed the others' by the interleaved pose-only rows (Cambrian-P's beta = 1 adds samples; it does not
  replace QA rows). Every QA row is seen exactly once in all three tracks, and CPD sees its QA rows in exactly FT-A's
  order (section 6), so CPD - FT-A changes no data order.
- Arm configs and the smoke spec: `tools/fullft_arm_configs.py` (it rebuilds RG2P2_A's config from RG2P2_X's pinned
  bytes and checks the SHA-256 cdee3d05). GXS (G3T only) remains a variant: `GXS_S1`, `GXS_S2`, `GXS_X_S2`.

## 2. Full fine-tuning in the trainer (`student_pilot/full_ft.py`)

- A `full_ft` block turns LoRA off and names the trained groups: `llm` (decoder layers, embed_tokens, final norm,
  lm_head), `vision_blocks`, `merger`. The patch and position embeddings never train. A block with no group is the
  frozen-VLM stage: the base stays BF16 and only attached modules train.
- Master weights: every base parameter is stored FP32 when anything trains; FSDP FULL_SHARD shards all of them
  (decoder layers, vision blocks, embed_tokens and lm_head are their own units), with MixedPrecision param BF16 and
  reduce FP32. BF16 -> FP32 -> BF16 is exact, so step 0 computes the BF16 base forward (test: bitwise equal to the LoRA
  recipe at LR 0, B = 0). Attached modules (G3T connector, heads) stay replicated FP32 outside FSDP, as in the LoRA path.
  Cambrian-P trains with DeepSpeed ZeRO-2, BF16, FP32 masters; FSDP with FP32 masters and BF16 compute is the same
  arithmetic.
- Optimizer: AdamW, one group per family (llm, vision_blocks, merger, geometry, heads), each with its base LR on the
  shared warmup-cosine schedule; weight decay 0 (Cambrian-P).
- Clipping at 1.0 (the reference config), per family: the base groups over their global (all-rank) norm, the connector
  alone (as GX clips its projector apart from LoRA), the heads alone. Each norm is logged every step.
- Checkpoints (format `rank_sharded_v2`): each rank writes its local base shards and their optimizer state straight
  into the durable root (ORCHARD_CHECKPOINT_ROOT on code-aws), hashed while written. The replicated attached modules
  (connector, heads) and their optimizer state are identical on every rank, so rank 0 alone writes them, once
  (`replicated.pt`); resume loads them on rank 0 and broadcasts them. Rank 0 seals the directory. Resume needs the same
  world size and sharding layout and is bit-exact (tests, including a resume with the connector attached).
- Retention: a full state serves only to resume, so the rolling pool holds every rolling, epoch, milestone and final
  full state and keeps the newest 2; signal and gate stops (and a resumed run's parent) pin theirs. Each milestone
  (every 200 steps, the reference config) also pins a milestone export in `MILESTONES.jsonl`: the BF16 cast of the
  masters (`full_weights/`, the evaluator's format) plus the FP32 connector and heads, ~21 GB. Arms launch with
  R1_ROLLING_MINUTES=60.
- Graceful stop (SIGUSR1/SIGTERM/stop file): every rank polls the stop file each optimizer step and any rank's request
  stops all; the trainer saves and pins a signal checkpoint, writes the stop marker and exits. Slurm jobs launch with
  `--signal=B:USR1@900`, and the batch shell turns USR1 into the stop file, so the step in flight and the full write
  finish inside the 900 s lead (the default KillWait after SIGTERM is 30 s). The next save removes the `.step_N_*.tmp`
  of a killed save. A CPU test sends SIGUSR1 to one rank and checks the pinned state resumes bit-exactly.
- Size (Qwen3.5-9B: 9,409,813,744 parameters; 9,405,388,912 trained when all three groups train): params + Adam's two
  moments in FP32 = 12 bytes x 9.405e9 = 112.9 GB per full state, plus the heads (235.5M parameters, 2.8 GB) and the
  connector (335.6M, 4.0 GB) once: FT-A 112.9, CPD 115.7, PDG S2 119.7 GB at any world size. Milestone exports: 18.8,
  19.8, 21.1 GB. Per arm: 2 full states + 7-8 milestone exports = ~0.36-0.39 TB on the durable root.
- Export: publication writes `adapter-<label>/full_weights/` = the BF16 cast of every base tensor (18.8 GB) in the
  Hugging Face sharded layout with a manifest pinning every file; the evaluator loads it over the pinned base snapshot
  with exact tensor equality. The frozen-VLM stage publishes only its attached modules (`geometry/`, `auxiliary_heads.pt`).
- Stage 2 loads the stage-1 connector and heads through `full_ft.init_modules` (path + sha256, exact names, shapes,
  dtypes and values).

### Memory estimate per H100 80 GB (world 32, 8 rows per GPU)

| Item | GB per GPU |
|---|---|
| Activations etc. (measured LoRA+GX peak 38.4 GiB at 8 rows/GPU, minus LoRA states) | ~37 |
| Sharded FP32 params + grads + Adam, 9.405e9 trained / 32 | 4.7 (18.8 at world 8) |
| Unsharded BF16 unit + its gradient (lm_head / embed_tokens, 1.02e9 each) | ~4 |
| Pose + depth heads at Cambrian-P width, replicated FP32 + Adam | ~3.5 |
| G3T connector (335.6M), replicated FP32 + Adam | ~5.4 |

FT-A ~46, CPD ~49, PDG S2 ~55, PDG S1 ~47 GB at world 32; add ~14 GB at world 8. Step time (E): the reference LoRA run
takes 22.3 s/step; PLAN64 puts full FT at 1.26x LoRA FLOPs at 32 frames, so ~28 s/step plus ~2-4 s of FSDP gathers and
FP32 reductions. The smoke (section 7) measures both.

## 3. Init: plain base (recommended, default) or base + r1835 merged

Recommendation: start every new full-FT arm from plain Qwen3.5-9B.
- The scaled plan trains on all of VSI-590K, and r1835 was itself trained partly on VSI-590K: a merged start would
  count that data twice and make "student - base" include r1835's training, which the 10-30 audit already flagged for
  every current AWS arm.
- r1835's start did not survive further training: A1 and X fell from r1835's ~59.5 to ~51 on new rows.
- Full FT at 1e-5 over 1,550 steps moves the weights far more than an r32 LoRA delta, so the warm start buys little and
  costs a clean lineage. Cambrian-P, Spatial-MLLM and VG-LLM all fine-tune from their released base checkpoints.
- `init.kind = base_merged_init_adapter` is implemented: it attaches the pinned parent LoRA, loads it, merges it in FP32
  (no BF16 rounding of the delta) and drops PEFT; the protocol must pin the parent at prepare time. Use it only as an
  ablation if plain base trails.

## 4. The G3T adapter: Spatial-MLLM's connector

GX (the current arm) feeds G3T layer-23 features pooled to the merged grid into a frame-strict cross-attention block
(1024 wide, 8 heads, zero-init output) added to the merged video tokens. No published VGGT-into-Qwen system uses that
block. The published designs:

| System | Encoder -> VLM | Fusion | Alignment | Recipe |
|---|---|---|---|---|
| Spatial-MLLM | VGGT -> Qwen2.5-VL, video | RMSNorm(merged) -> Linear(merged, merged) -> GELU -> Linear(merged, LLM width), added to Qwen's merged video tokens (`connector_type mlp_add`) | 2x2 spatial cells x the 2 frames of Qwen's temporal patch concatenated per merged token; last VGGT layer, frame + global features (2 x 1024) | one SFT stage; vision and VGGT frozen; connector + LLM trained (paper: peak 1e-5, 1 epoch) |
| VG-LLM | VGGT-1B -> Qwen2.5-VL | 2x2 concat -> RMSNorm -> 2-layer GELU MLP, added | per image | one stage; LLM full FT 1e-5; vision and merger frozen (`tune_mm_vision False`, `tune_mm_mlp False`) |
| VLM-3R | CUT3R -> LLaVA-Video (SigLIP), not Qwen-VL | one cross-attention layer (18 heads) before the projector | per frame, no 2-frame grouping | LoRA r128 |
| MERV | several 2D video encoders | learned-query softmax over encoders, additive mix | resample to common frames, 2D pool to a common grid | Video-LLaVA two stages |

Spatial-MLLM is the closest to our setting: a VGGT-family encoder (G3T is a VGGT-1B fine-tune) into a Qwen-VL video
model whose temporal patch fuses two frames, exactly as Qwen3.5 does. VG-LLM's ablation also favours addition over
cross-attention (ScanRefer 36.4 vs 33.7 and 34.4 for 1 and 3 cross-attention layers). The build therefore replicates
Spatial-MLLM's connector (`geometry_input.SPATIAL_INJECTION`, `SpatialMLLMConnector`): G3T layer 23 (the last aggregator
layer, Spatial-MLLM's `spatial_embeds_layer_idx -1`), 2,048 features per cell (frame + global attention, Spatial-MLLM's
2 x vggt_dim), the 2x2 cells of both frames concatenated in Spatial-MLLM's permute order (merged width 16,384),
RMSNorm (eps 1e-6), Linear(16,384, 16,384), GELU, Linear(16,384, 4,096), added to the merged video tokens (335.6M
parameters). The init is the source's effective one: Spatial-MLLM builds the connector inside its Qwen2.5-VL model, and
`from_pretrained` (transformers 4.51.3, its pin) fills the missing connector keys with
`Qwen2_5_VLPreTrainedModel._init_weights`, so both Linear weights start N(0, 0.02) (the checkpoint's initializer_range),
biases 0, RMSNorm 1 (read from THU-SI/Spatial-MLLM 9fc4738: `spatial_mllm.py`, `connector/mlp_add_connector.py`,
`train_qwen.py`). MERV's two findings carry over as alignment, not as a mixer: G3T tokens are aligned
to the student's own temporal patches and pooled onto its patch grid; MERV's mixer weighs several 2D encoders against
each other and has no counterpart with one 3D encoder whose output is added.

The G3T store therefore changes: cells on the unmerged Qwen patch grid `[32, 2h, 2w, 2048]` (encoder pooling
`roi_align_valid_region_aligned_sr2_patch_grid`), not the merged grid of fs/9cdefbc2. `tools/g3t_patch_grid_store.py`
is the GX extractor (geo_build x.py 480e25b6) with the pooling grid changed: `lists` collects the selections, `extract`
writes the rows, `seal` verifies them and writes the pinned manifest. Two stores, extracted before stage 1: training
(every RG2P2_A/X and stage-1 v2 video, ~1,600, ~110 GB at 68 MB per 320x416 video, 4 x 1 GPU for ~12 min) and eval
(the VSI-500 and VSTI-450 selections, ~444, ~30 GB, 1 GPU for ~15 min); `SPEC.json` `extraction` holds the job spec.
Training nodes read the store from local disk (each rank reads ~0.55 GB per step).

Stage recipe (two stages: USER 10-30; MERV and Video-LLaVA show two beat one):
- Stage 1: VLM frozen (vision + LLM), connector (and PDG's heads) trained; Video-LLaVA stage 1: LR 1e-3, batch 256,
  1 epoch, warmup 0.03, cosine, the encoders and LLM frozen. Heads at Cambrian-P's head LR 1e-4.
- Stage 2 (PDG): Cambrian-P's full fine-tuning (LLM + projector 1e-5, vision 2e-6, heads 1e-4); the connector is a vision
  projector and trains at 1e-5. GXS stage 2: VG-LLM / Spatial-MLLM freeze the vision tower (VG-LLM also the merger) and
  train LLM + connector at 1e-5.

## 5. Stage-1 geometry questions (v2, `/scratch/jjyeung/fullft/geo_stage1_v2/`, builder commit cd44a555)

Block 0 holds 200,000 materialized train rows over 1,232 ScanNet/ScanNet++ scenes and 2,040 dev rows over 55 held-out
scenes (v1's held-out physical groups); every answer comes from GT poses, first-hit depth or 3D boxes; 35% scale-free.

| category | train | dev |
|---|---:|---:|
| depth_at_pixel (m) | 28,000 | 220 |
| nearer_pixel | 24,000 | 220 |
| pixel_3d_distance (m) | 20,000 | 200 |
| object_at_pixel_3d_centre | 22,000 | 200 |
| object_camera_distance (m) | 20,000 | 200 |
| camera_motion_translation (m) | 16,000 | 180 |
| camera_motion_rotation (deg) | 14,000 | 160 |
| camera_motion_direction | 14,000 | 180 |
| camera_position_vs_frame1 (m, x y z) | 18,000 | 180 |
| camera_heading_vs_frame1 (deg) | 18,000 | 180 |
| camera_trajectory_extent (m, scene-scale readout) | 6,000 | 120 |

- Metric scale: G3T's pooled features predict per-video log scale to ~6% (`L/g3t_scale_20261029/PROBE_RESULT.md`), and
  scale follows trajectory extent (`RESULT.md`), so the mix keeps 65% metric rows and adds the explicit trajectory-extent
  readout, object-camera distance and camera position.
- Rows carry the rung-1 scene token, so 197,084 train and 2,016 dev rows join the label bank and receive head losses in
  PDG stage 1. 48,000 ARKitScenes/ADT rows wait in `pending_aws_fetch/` until their frames and G3T cells exist.
- Growth (USER 10-30): `--block N` builds the N-th disjoint 200k block with the same generator. Rule
  (`tools/stage1_dev_metrics.py`): at the end of each epoch, score the dev set at the epoch end and one quarter-epoch
  earlier (MC accuracy, VSI-Bench MRA for numbers, MRA of 3D error for points, wrapped angular MRA for heading); grow by
  one block only if the aggregate error still falls by more than max(0.005, 2 x the paired bootstrap SE).

## 6. CPD: Cambrian-P with the PD heads

- Head (Cambrian-P-7B config): one carrier per temporal group with c_first / c_rest tokens, final-layer carrier states,
  linear projector to 2,048, VGGT camera head (trunk 4 x 16 heads, 4 refinements), loss weight 0.2 x 5.0 = 1.0,
  w_T 1, w_R 1, w_f 0.5, gamma 0.6, trajectory balance off, metric translations. Gravity (0.5) and metric scale (0.2)
  branches and the point-depth head (PD design, DESIGN.md section 4) are the user's additions.
- One stage (Cambrian-P): heads random-init, trained jointly with the whole model. The user asked for a short
  head-only warmup first: head losses send no gradient into the student for 51 steps (= the 3% LR warmup of 1,686
  steps), then ramp over 51.
- Pose-only samples (Cambrian-P Sec. 3.3, PLAN64 section 3): 28 per label-bank training scene, 34,888 rows over 1,246
  scenes (`tools/build_pose_rows.py`, rows in `/scratch/jjyeung/fullft/pose_rows_v1/`), shuffled together with the QA
  rows (beta 1). Each shows N in {8, 16, 24, 32} of the scene's 32 frames: 50% temporal mode (contiguous at stride
  1..floor(32/N), reversed with p 0.5), 50% collection mode (random subset in random order); photometric augmentation
  (colour jitter 0.3/0.3/0.3/0.05, blur p 0.1, grayscale p 0.05), per frame, seeded per row. Targets are relative to the
  sample's first frame, computed from the scene's 32 metric GT poses; on the natural order they equal the bank's anchors
  to 1.1e-5 m.
- Loss routing follows Cambrian-P (camera config `row_routing: cambrian_p_question_rows_lm_only_pose_rows_heads_v1`):
  QA rows train the next-token loss only, carry no camera tokens and no head loss; pose-only rows train the camera
  head (pose, plus the user's gravity and scale branches) and no text. A pose-only row's LM weight is 0, and the LM
  term divides by the step's QA rows (`lm_row_scale` = batch / QA rows), so QA rows keep their gradient scale. The camera
  head and the depth head accept G = N / 2 groups (padded slots masked); 32-frame rows are unchanged (test).
- Depth supervision (the user's addition; Cambrian-P has no depth head) sits on the geometry rows only, the pose-only
  rows: each sample group describes its second frame, and where that frame is one of the bank's first-hit depth frames
  (0-based 1, 3, ..., 31) the group carries that frame's 64 bank depth queries. Over POSE32_V1 that is 174,597 of
  349,144 groups (50%) in 26,008 of 34,888 rows, 11.2M points. CPD is scored with `--carriers none` (section 8).
- Order: the QA rows follow `random.Random(seed + epoch)` over the QA rows alone, exactly FT-A's permutation, and the
  pose-only rows take uniformly drawn seeded slots between them (`ddp_core.epoch_order`). `batch_plan.json` records
  `question_order_sha256`, equal for CPD and FT-A when CPD's manifest keeps RG2P2_A's rows in FT-A's order. Only the
  epoch-end padding (the first rows of the epoch repeated to fill the last batch) differs, because the row counts
  differ.
- Frame knob: `frames: {count, pixels_per_frame: [min, max]}` in the training config; the processor budget is the
  per-frame budget times the frame count, so no frame is resized silently. 64 frames at 224x288 is
  `{"count": 64, "pixels_per_frame": [16384, 73728]}` (test: grid [32, ...] and 224x288). The 32-frame default encodes
  bit-identically to today.

## 7. AWS 8-GPU smoke (`SPEC.json` from `tools/fullft_arm_configs.py`)

One exclusive 8 x H100 node, world 8, global batch 64 (8 rows per GPU, the arms' per-rank load), 30 steps, a milestone
at step 20 (export pinned, full state to the pool) and 10-minute rolling saves, `--signal=B:USR1@900`, no gates; four
jobs in one allocation (~2 h, ~20 GPU-h):
SMOKE_FT_A (full FT alone), SMOKE_CPD (+ heads and pose-only rows), SMOKE_PDG_S1 (frozen VLM + connector + heads on
stage-1 rows), SMOKE_PDG_S2 (full FT + connector + heads). Rows: the 20 smoke-bank scenes' RG2P2_A rows, their 560
pose-only rows, and their stage-1 rows, pre-staged on CPU. It records the probe's microbatch (must be 8), peak memory per
rank, s/step over steps 11-30, checkpoint bytes and write time, export bytes and time, per-group gradient flow and clip
norms, and the label audit; it passes with no OOM at 8 rows, finite losses, nonzero gradient flow in every trained
group, a stop-file stop after step 25 that pins step 25 and whose resume reproduces steps 26-30, an exactly loading
step-20 milestone export, and an unchanged base in PDG_S1. G3T's cost is SMOKE_PDG_S2 - SMOKE_CPD. Prerequisites: the patch-grid G3T store, the shipped label bank, and admitted smoke rows.

## 8. Evaluator variant

- `orchard_eval` admits full-FT publications by their export manifest, index and every shard (sha256 and size checked
  against the publication census and `full_ft.read_export`), the adapter provenance, `PUBLISHED.json`, the result's
  `full_ft` record and the `full_ft.py` bytes; it loads the BF16 base snapshot and replaces every tensor with
  `full_ft.load_export` (exact equality; no PEFT). A frozen-VLM publication is the base snapshot plus its modules.
- G3T: `--geometry-store-manifest` with `--geometry-store-sha256` pin the eval feature store; the projector, its
  settings, the store and `geometry_input.py` enter the model identity; one vision forward consumes each item's features.
- Carriers: `--carriers none|insert`. `insert` inserts the 16 carriers in `pack_input` (the audit covers the extended
  prompt) and replaces their prefill embeddings with the published c_first / c_rest through the trainer's own
  `embedding_hook`; decode steps are untouched (test: prefill embeddings and logits equal the training forward). A
  camera-head publication must name the option; `insert` refuses without a head. Each head arm is scored the way its
  QA rows trained: CPD with `none` (Cambrian-P: QA rows carry no camera tokens), PDG_S2 with `insert` (its QA rows in
  bank scenes train with carriers); the other mode is the ablation. A carrier run pairs with the cold base through its
  carrier-free audits.
- `scripts/orchard/eval_job.py` passes `EVAL_CARRIERS` and `EVAL_GEOMETRY_STORE` / `EVAL_GEOMETRY_STORE_SHA256` to both
  cpu-check and generate and records them in the cell identity; unset, every command is byte-identical to df6cf8c's
  (test). `generate --allow-unpaired-adapter`, which the AWS eval closure passes, has evaluator 4259ec3's meaning: no
  cold-base pair, and the run core records `comparison_mode: external_parent`.
- Scoring without these options is byte-identical to df6cf8c: for the base and a LoRA publication the input audits,
  protocol identity, work id, preflight, run core, receipts and scores (per-question scores, results table, metrics)
  match the df6cf8c tree run on the same fixtures; a head arm scores with its carriers re-validated.

## 9. Deviations from the cited sources

| Choice | Source value | Ours | Reason |
|---|---|---|---|
| G3T cells per merged token | Spatial-MLLM: VGGT patch 14 = Qwen2.5-VL patch 14, no resampling | G3T's 518-px tokens ROI-aligned onto Qwen3.5's 16-px patch grid | G3T's square-padded 518 input and Qwen3.5's 16-px patches do not tile each other |
| Stage structure of the G3T arms | Spatial-MLLM, VG-LLM: one SFT stage | two stages (frozen-VLM alignment, then VQA) | USER 10-30 ruling (MERV, Video-LLaVA) |
| Stage-1 data | Video-LLaVA: 558K image + 702K video captions | 200k GT geometry questions | USER 10-30 ruling |
| Heads in stage 1 | none trained on a frozen VLM in any source | PD heads train with the connector | USER 10-30 (PDG); head LR is Cambrian-P's |
| Camera carriers | Cambrian-P: one per frame | one per temporal group (16), describing the group's second frame | Qwen3.5 fuses frame pairs into one temporal patch |
| Gravity and metric-scale branches | not in Cambrian-P | weights 0.5 / 0.2 (PD) | USER: "with gravity/metric scale"; no published weight exists |
| Point-depth head | Cambrian-P Table 7: depth supervision lowers VSI | PD's DepthVLM-recipe head, weight 0.5; in CPD on the pose-only rows alone, at the groups whose frame has bank depth (50%) | USER: "+ depth"; Cambrian-P trains QA rows on NTP only, so depth goes on the geometry rows; the bank holds depth at odd frames only |
| Head losses in PDG S2 | Cambrian-P: QA rows NTP only, pose-only rows the heads | the PD heads train on every labelled QA row (bank scenes), whose prompts carry the carriers; scored with `--carriers insert` | PDG keeps the PD design (DESIGN.md) it extends; CPD carries Cambrian-P's routing |
| Head-only warmup | Cambrian-P: none | 51 steps, then a 51-step ramp | USER: "a short head-only warmup"; length = Cambrian-P's 3% LR warmup |
| Pose-only frames | Cambrian-P: N up to the clip length (pools up to 128 frames) | N in {8, 16, 24, 32} from the row's 32 frames | only 32 sampled frames exist per scene now (PLAN64 stages 64/128-frame pools separately) |
| Pose-only augmentation | Cambrian-P: colour, blur, grayscale, rescale, rotation | photometric only | rescale and rotation change the pose targets (PLAN64) |
| Base model | Cambrian-P: Cambrian-S-7B stage 3; Spatial-MLLM / VG-LLM: Qwen2.5-VL | Qwen3.5-9B | our student |
| Visual tokens per frame | Cambrian-P-32f: 196 | 65 (320x416) | the 32-frame RGB contract; the frame knob can raise it |
| GXS weight decay | VG-LLM 0.01, Spatial-MLLM 0.1 | 0 | GXS stays matched to PDG / FT-A (Cambrian-P: 0) |
