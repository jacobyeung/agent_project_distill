# 64-frame variant of trainer tree N (sb_f64): built, not launched

N reads 64 viewpoints as a nested input: the row's 32 anchor frames plus the 32 frames that bisect their largest gaps.
Carriers, `Frame k:` markers, heads, targets and question text stay on the 32 anchors, so N's init artifact, its 32-slot
heads and the "frame i of 32" items remain valid. Every rank's first batch of every stream encodes and runs the full
forward on CPU at 64 viewpoints with finite losses. Those rows hold 9,127–10,215 tokens, under the 16,384 ceiling, with
nothing truncated. On the measured H100 line they need 69.5–72.4 GiB per rank at world 4, under the 76 GiB tripwire.
A 64-frame step should take about 1.91× a 32-frame step. The micro-batch (one row per microstep) and the ceiling stay
as they are. The open risk is real long rows. A routing row with a suffix above about 2.4k tokens (4:3) or 1.4k (16:9)
passes the tripwire at world 4, and `kit/scripts/token_audit.py` lists such rows before launch.

## Changes (each with file:line, reason and admission mark A in `kit/CHANGES.md`)
- Config: one 64-specific key, `frame_input: {viewpoints: 64, anchors: 32, rule: nested_bisection_v1}`; `frame_count`
  stays 32. Both configs also pin `min_pixels`/`max_pixels` to DEFAULT_PIXELS. N's null pins make `processor_for_receipt`
  refuse under r1_training, a defect that also blocks the 32-frame launch.
- Tree: `patches/tree_r1_to_f64.patch` (624 lines) applies to a fresh tree_r1 and reproduces tree_f64. It adds
  `frame_input.py`, row admission (`carrier_c1_data.py`, Rows in `carrier_c1_run.py`, `b7_inputs.py`), anchor-only
  markers, carriers and `aux_anchor_groups`, the anchor-only depth view (`decoupled_v.py`), the anchor count in
  `pose_samples.py`, receipt and artifact keys, R1 validation, and the handover key with pixel defaults.
- Stores: `scripts/nest_store.py plan|apply` nests an existing store and records rows it cannot nest as deferred.
  Those rows stay in the denominator. The design record is `kit/DESIGN_F64.md`, with the rejected options.

## Tokens per sample (real tokenizer and processor; every rank × stream encoded; all 4 ranks agree)
| Stream | 4:3 (640×480 → 320×416), 32 → 64 | 16:9 (1280×720 → 288×512), 32 → 64 |
|---|---|---|
| pose | 4,703 → 9,127 | 5,159 → 10,039 |
| VQA | 4,839 → 9,271 | 5,295 → 10,183 |
| routing | 4,879 → 9,303 | 5,335 → 10,215 |
| pointing (video rows) | 4,719 → 9,151 | 5,175 → 10,063 |

A 64-viewpoint video row adds 4,424 tokens at 4:3 (4,160 visual + 264 timestamp text) or 4,880 at 16:9, and the visual
cap rises from 4,608 to 9,216 tokens. Single-image rows do not change. `check_row` raises above `max_row_tokens` (16,384),
nothing truncates, and R1 aborts the run on a failed row rather than substituting it. A 64-viewpoint row therefore fits
the ceiling only if its 32-frame length is at most 11,960 (4:3) or 11,504 (16:9) tokens. The routing build admits
suffixes up to 9,600 tokens, so that bound no longer holds by construction.

## Memory per rank, H100 80 GB, world 4 (GiB)
| Rank | Microstep, stream | 4:3, 32 → 64 | 16:9, 32 → 64 |
|---|---|---|---|
| 0, 1, 2, 3 | 0, pose (first batch) | 57.5 → 69.5 | 58.8 → 72.0 |
| 0, 1, 2, 3 | 8, VQA | 57.9 → 69.9 | 59.1 → 72.3 |
| 0, 1, 2, 3 | 24, routing (123-token suffix) | 58.0 → 70.0 | 59.3 → 72.4 |
| 0, 1, 2, 3 | 56, pointing | 57.6 → 69.6 | 58.8 → 72.0 |
| any | routing, suffix S tokens | 70.0 + 2.7·(S − 123)/1000 | 72.4 + 2.7·(S − 123)/1000 |

- Static state, analytic from exact parameter counts (base 9,409,813,744; heads 690.8M, 234.8M trainable): 43.57 GiB.
  FP32 masters of every base parameter take 8.76, LM grads 8.34 and Adam 16.68, sharded over 4 ranks. Replicated
  heads with grads and Adam take 5.20, and the all-gathered BF16 root plus two blocks take 4.59.
- Activations follow the measured H100 line of design record VLM_E2E_NEXT_LEG_20261110 §4. It passes 57 GiB at ~4.5k
  tokens (C1 pose) and 70.3 GiB at 9–10k tokens (an earlier 64-frame run), a slope of 2.7 GiB per 1k tokens. The
  tripwire therefore falls at 11,537 tokens: a 64-viewpoint routing row fits only with a suffix of at most ~2.4k (4:3)
  or ~1.4k (16:9) tokens. v3.12 allowed 5k at 32 frames. At world 8 (same record: 39.75 GiB at 4.5k, 66.2 GiB at
  13.5k), these rows need 53.3–56.5 GiB, and a row at the 16,384 ceiling needs 74.7 GiB.
- CPU forward + backward (first row of each process): peak RSS above the loaded model rose 7.9 → 12.3 GiB at 4 LM
  layers and 10.6 → 14.6 GiB at 8. RSS mixes allocator retention and the frozen ViT's transient with LM activations, so
  I do not scale H100 memory by it.

## Step time per rank, 32 → 64 (world 4; every rank runs 72 microsteps: 16 pose, 32 VQA, 16 routing, 8 pointing)
| Rank, stream | CPU forward s, 32 layers | CPU fwd+bwd s, extrapolated to 32 layers | train TFLOP/row | H100 s/microstep (record × FLOP ratio) |
|---|---|---|---|---|
| 0, 1, 2, 3, pose | 74.6, 70.6, 62.1, 56.4 → 132.7, 130.2, 120.2, 123.0 | rank 0: 288.7 → 766.9 | 299.6 → 577.7 | 4.0 → 7.7 |
| 0, VQA | 45.1 → 117.6 | 311.1 → 912.4 | 307.5 → 586.4 | 4.5 → 8.6 |
| 0, routing | 55.0 → 122.2 | 297.0 → 725.7 | 309.8 → 588.3 | 6.0 → 11.4 |
| 0, pointing | 50.1 → 118.5 | 289.8 → 629.4 | 300.5 → 579.1 | 3.0 → 5.8 |

- The mix-weighted 64/32 ratio is 1.91 by FLOPs, 1.92 by tokens, 2.30 by CPU forward and 2.68 by CPU forward +
  backward. I expect H100 near the FLOP ratio: CPU attention (SDPA math path) and the torch fallback of gated delta
  grow faster than fused kernels, and fixed FSDP costs pull H100 lower.
- The 32-frame step basis is unsettled. C′'s estimate implies 137.7 s per step (0.153 GPU-hours on 4 GPUs); the
  record's per-microstep times imply 328 s. At 64 viewpoints a step takes 263 s or 627 s, so 1,000 steps take 73.1 h
  or 174.2 h (32 frames: 38.2 h or 91.1 h). A 24-hour allocation (82,800 s of trainer budget) fits 314 or 132 steps,
  against 601 or 252 at 32 frames, so plan four or eight allocations.

## Dry-run evidence (`kit/evidence/`; logs in `work/logs/`)
- Stand-ins: the real Qwen3.5-9B architecture at random init, since no 9B weights exist on /scratch; the real tokenizer
  and processor with synthetic RGB at 640×480 and 1280×720; synthetic SQLite stores with fixture text, one row per rank
  per stream; the native sampler, since the r2_sampling table is absent; camera and depth from P's preparation receipt.
- Full depth (32 LM layers, 27 ViT blocks) ran the no-grad forward of every rank's first batch (pose, microstep 0) and of
  rank 0's first row of each other stream. Reduced depth (4 and 8 layers) ran forward + backward with N's checkpointing
  and trainability. Peak RSS stayed ≤ 27.4 GiB on 16 cores (24–39).
- Commands, from `/scratch/jjyeung/orch_n30/sb_f64` (kit `scripts/` = `work/scripts/`; `run_cpu.sh` sets a 40 GiB
  address cap, 16 threads and offline caches):
  - `work/scripts/run_cpu.sh work/scripts/f64_dryrun.py encode --config out/kit/configs/r1_config_{n32_pinned,f64}.json --out out/evidence/encode_{n32,f64}.json`
  - `work/scripts/run_stage2.sh mem_f64_4 fwd_f64_a43 fwd_n32_a43 fwd_f64_b169 fwd_n32_b169`, then
    `work/scripts/run_stage2b.sh fwd_f64_a43_local mem_n32_4 mem_f64_8 mem_n32_8 mem_f64_b169_8` and `work/scripts/run_stage2c.sh`.
    Each case runs `f64_dryrun.py {forward|trainmem} --config CFG --clips {a43|b169} [--layers 4|8] [--limit 1]`, and
    `work/scripts/analyze.py` writes `out/evidence/ANALYSIS.json`. Every timing comparison pairs p1cpu runs (torch
    2.11.0+cpu); encode, forward_smoke, fwd_f64_a43 and mem_f64_4 ran on torch 2.11.0+cu130.

## Read configs (`kit/read/`)
The student reads the nested 64 viewpoints it trained on: `f64_read.student_row` calls the training function `nest_row`,
and `check_layout` refuses unless the export's `frame_input` matches the read layout, count, anchors and rule.
`reader_f64.patch` changes `parity.py`, `parity_adapter.py` and `orchard_h10/prepare.py` so the settings carry `frames`
and `student_manifest` and record counts follow the declared count. `READ_PLAN_F64_DIFF.md` diffs the 64-frame read
against the 32-frame plan. `STUDENT_FRAMES_PLAN.json` lists 152 captures and 4,864 bisection frames (3,733 still to
decode), because the tower's devs1_tower_v2 dense manifest follows another rule.

## Tests
- `tests/test_f64_layout.py`: 12 of 12 pass (env `F64_META=in/qwen35_9b_meta F64_CONFIG=out/kit/configs/r1_config_f64.json
  F64_READER_ROOT=work/read_a/root`). The train/read agreement tests check that training rows equal read rows, that the
  layout check binds the export, and that `data.encode` of a training row equals the reader's `prompt_batch` (ids,
  grid, pixels, carriers, anchor groups). `tests/test_token_audit.py`: 4 of 4 pass on the synthetic nested store.
- The focused build-18 suite on tree_f64 (121 tests) gives one error and one skip. The error (`test_carrier_c1_cp2`
  `test_revision_3_11_rows_rerender_closest_as_one_min_line`) needs the absent `orch_cd/derivgen/review_pool/POOL.jsonl` and
  fails the same way on the unpatched tree; the skip is the encoded-agreement test, run there without its env.

## Open risks
1. Real row lengths decide the launch. Run `token_audit.py run --steps 1000` over the bound preparation, one shard per
   core, then `summarize`; its `run` path is untested against a real receipt, because none exists here. If it lists rows
   over 11,537 tokens, the first fallback is `C1_FSDP_CPU_OFFLOAD=1`, the tree's own path: it frees ~33.8 GiB per rank
   and changes no row, at an unmeasured speed cost. Deferring the listed rows changes admission. World 8 fits every row,
   but R1 pins world 4 (`r1_training.py:69`, `r1_mix.py:70`, `r1_handover.py:300`), so it needs a new pinned row plan.
2. The admission changes marked A need one independent review, and tree_f64 needs its own sealed contract and epoch checkout.
3. Each training store needs `nest_store.py plan`, a frame decode and `apply`, and the reader needs 3,733 PNGs decoded.
4. The 32-frame step basis differs 2.4× between the C′ estimate and the record. The first H100 steps settle it.
5. The early runs' vllm env imported its stdlib from `/data2/jjyeung/envs/vllm` (NFS); nothing was killed, and later runs use p1cpu.

## Kit
`out/sb_f64_kit.tar` holds configs, patches, read, scripts, tests, evidence (JSON only), `CHANGES.md`, `DESIGN_F64.md` and
`SHA256SUMS`. It contains no data, weights, PNGs or SQLite. Its sha256 is in `out/sb_f64_kit.tar.sha256` and STATUS.md.
