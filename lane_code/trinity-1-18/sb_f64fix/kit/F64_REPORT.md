# 64-frame variant of trainer tree N (sb_f64, fixes sb_f64fix): built, not launched

N reads 64 viewpoints as a nested input: the row's 32 anchor frames plus the 32 frames that bisect their largest gaps.
Carriers, `Frame k:` markers, heads, targets and question text stay on the 32 anchors, so N's init artifact, its 32-slot
heads and the "frame i of 32" items remain valid. On synthetic stand-in rows (random-init weights, fixture text, the
native sampler) every rank's first row of every stream encodes at 64 viewpoints, and full-depth CPU forwards with finite
losses covered pose on ranks 0–3 and the other streams on rank 0 only. These rows hold 9,127–10,215 tokens, under the
16,384 ceiling, with nothing truncated; real rows are unknown, because the bound preparation and row plan are MISSING.
GPU memory and step time at 64 viewpoints are unmeasured. `scripts/token_audit.py` must first encode every planned row,
and `scripts/mem_pilot.py` then measures four 80-GB GPUs on the longest of them. 48-GB cards are unsupported for the
non-offloaded config.

## Changes (each with file:line, reason and admission mark A in `kit/CHANGES.md`)
- Config: one 64-specific key, `frame_input: {viewpoints: 64, anchors: 32, rule: nested_bisection_v1}`; `frame_count`
  stays 32. Both configs also pin `min_pixels`/`max_pixels` to DEFAULT_PIXELS. N's null pins make `processor_for_receipt`
  refuse under r1_training, a defect that also blocks the 32-frame launch.
- Tree: `patches/tree_r1_to_f64.patch` (624 lines) applies to a fresh tree_r1 and reproduces tree_f64. It adds
  `frame_input.py`, row admission (`carrier_c1_data.py`, Rows in `carrier_c1_run.py`, `b7_inputs.py`), anchor-only
  markers, carriers and `aux_anchor_groups`, the anchor-only depth view (`decoupled_v.py`), the anchor count in
  `pose_samples.py`, receipt and artifact keys, R1 validation, and the handover key with pixel defaults.
- Stores: `scripts/nest_store.py plan|apply` nests an existing store. `apply` preflights every row and publishes all of
  them, with source index, target, count and anchor order intact, or none: a missing or stale frame pin or
  non-increasing anchors refuse the store. The design record is `kit/DESIGN_F64.md`, with the rejected options.

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

## GPU memory: unmeasured
No GPU ran this kit, so no GPU peak exists for 64 viewpoints. What is known:
- Arithmetic from exact counts (base 9,409,813,744 parameters by meta construction; heads 690,762,761, of which
  234,752,281 trainable, counted in review `forward_review.json`): FP32 masters of the base, LM gradients and Adam state
  sharded over 4 ranks take 33.78 GiB per rank. Replicated heads, gathered BF16 blocks, activations and allocator
  overhead come on top; none of them is measured.
- The CPU runs measure host RSS of one row at 4 or 8 LM layers with BF16 gradients, no FSDP, no FP32 masters and no
  Adam step (8-layer pose RSS above the loaded model: 10.6 → 14.6 GiB). RSS is not a GPU peak.
- The kit holds no H100 calibration logs, so it gives no per-rank GPU estimate.
- 48-GB cards are unsupported for the non-offloaded config: the sharded static state alone takes 33.78 GiB per rank.
- `scripts/mem_pilot.py` (written, not run) settles it on one node with four 80-GB GPUs. It runs the trainer's own
  `prepared`, `load_model`, `wrap_model` (FSDP FULL_SHARD, FP32 masters, BF16 compute), AdamW and `optimize_step` with
  non-reentrant LM checkpointing. Each step is one full accumulation cycle (72 microsteps per rank, global batch 288),
  with every microstep filled by the longest rows of a complete `token_audit` summary. It records allocated and
  reserved peaks per microstep, after the optimizer step and while writing a checkpoint, plus Adam bytes and step
  seconds, into `PILOT.json`. It refuses cards under 79 GiB unless `C1_FSDP_CPU_OFFLOAD=1`, which needs its own pilot.

## Step time per rank, 32 → 64: estimates (world 4; every rank runs 72 microsteps: 16 pose, 32 VQA, 16 routing, 8 pointing)
The H100 column scales a design record's per-microstep times, whose logs are not in this kit, by the FLOP ratio; it is a
planning estimate. `PILOT.json:steady_step_seconds` measures the real step.

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
  and trainability. Peak RSS stayed ≤ 27.4 GiB on 16 cores (24–39). These stand-ins cannot satisfy the planned-run
  gate: each rank's real first batch must pass the full CPU forward once the preparation and row plan are bound.
- Commands, from `/scratch/jjyeung/orch_n30/sb_f64` (kit `scripts/` = `work/scripts/`; `run_cpu.sh` sets a 40 GiB
  address cap, 16 threads and offline caches):
  - `work/scripts/run_cpu.sh work/scripts/f64_dryrun.py encode --config out/kit/configs/r1_config_{n32_pinned,f64}.json --out out/evidence/encode_{n32,f64}.json`
  - `work/scripts/run_stage2.sh mem_f64_4 fwd_f64_a43 fwd_n32_a43 fwd_f64_b169 fwd_n32_b169`, then
    `work/scripts/run_stage2b.sh fwd_f64_a43_local mem_n32_4 mem_f64_8 mem_n32_8 mem_f64_b169_8` and `work/scripts/run_stage2c.sh`.
    Each case runs `f64_dryrun.py {forward|trainmem} --config CFG --clips {a43|b169} [--layers 4|8] [--limit 1]`, and
    `work/scripts/analyze.py` writes `out/evidence/ANALYSIS.json`. Every timing comparison pairs p1cpu runs (torch
    2.11.0+cpu); encode, forward_smoke, fwd_f64_a43 and mem_f64_4 ran on torch 2.11.0+cu130.

## Read configs (`kit/read/`)
The student reads the nested 64 viewpoints it trained on: `f64_read.student_row` calls the training function `nest_row`
on strictly increasing anchors equal to the capture's. `training_layout` needs matching `frame_input` declarations in
the export artifact and the config (absent, null or different refuses), and `check_layout` refuses unless that spec
matches the read layout, count, anchors and rule. Install `read/f64_read.py` as `src/b/f64_read.py`, a top-level module
beside the `src/b/e2e_reader` package: the patched `parity.py` imports it absolutely with `src/b` on sys.path.
`reader_f64.patch` changes `parity.py`, `parity_adapter.py` and `orchard_h10/prepare.py` so the settings carry `frames`
and `student_manifest` and record counts follow the declared count. `READ_PLAN_F64_DIFF.md` diffs the 64-frame read
against the 32-frame plan. `STUDENT_FRAMES_PLAN.json` lists 152 captures and 4,864 bisection frames (3,733 still to
decode), because the tower's devs1_tower_v2 dense manifest follows another rule.

## Tests (env `F64_TREE`, `F64_WORK`, `F64_META`, `F64_CONFIG`, `F64_READER_ROOT`; sb_f64fix `work/scripts/run_fix.sh` sets them)
- `tests/test_f64_layout.py`: 12 of 12 pass. The train/read agreement tests check that training rows equal read rows,
  that the layout check binds the export, and that `data.encode` of a training row equals the reader's `prompt_batch`.
- `tests/test_nest_store.py` 6, `tests/test_token_audit.py` 16 (real encode of the 16 planned dry-run rows) and
  `tests/test_f64_fix.py` 11: all pass, including the review's counterexamples.
- The review's focused regression suite gives 109 tests and one error on both tree_r1 and tree_f64. The error
  (`test_revision_3_11_rows_rerender_closest_as_one_min_line`) needs the MISSING
  `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`; that test stays unexecuted until the authentic pool returns.

## Missing inputs (none fabricated; `token_audit run` and `mem_pilot` refuse until they exist)
| Input | State | Owner |
|---|---|---|
| preparation receipt `…/ap/8865619b/f/469ddece/receipt.json`; config `preparation` pin | MISSING; must be a new preparation over `nest_store`-published 64-viewpoint stores | lane tree_rebuild (W), whose native prepare is NO-GO |
| `r2_sampling`, `r1_training.row_plan_sha256`, `host_receipt`, `review`; `store_hashes` for pose, routing, pointing (vqa only) | MISSING or null | W's production population binding, then the host audit and the independent review |
| code pin `…/8865619b/k/7.json`, admission pin `…/k/review.json` | MISSING; tree_f64 needs its own | orchestrator (sealed contract from an epoch checkout), independent reviewer |
| depth-init `heads.json` (sha fd60ac2f…) | absent at its in-job path; a matching copy sits in W's `ext/preceipts` | P's kit x_ee227714, staged by W |
| reader `student_manifest`; 3,733 bisection PNGs | placeholder; not decoded | reader lane |

## Open risks
1. Real row lengths and GPU memory decide the launch: run `token_audit.py run` (full horizon) over the bound preparation,
   one shard per core, then `summarize` and `mem_pilot.py`. Rows over `--tripwire` (default 11,500 tokens, unmeasured)
   block `launch_ready` but still feed the pilot; rerun the audit with the bound the pilot measures. If the pilot exceeds its budget, the first fallback is
   `C1_FSDP_CPU_OFFLOAD=1` with its own pilot; deferring rows changes admission; world 8 needs a new pinned row plan.
2. The admission changes marked A need one independent review, and tree_f64 needs its own sealed contract and epoch checkout.
3. The 32-frame step basis differs 2.4× between the C′ estimate and the record; the pilot's steady step settles it.

## Kit
`out/sb_f64fix.tar` (sb_f64fix workspace) holds configs, patches, read, scripts, tests, evidence (JSON only), `CHANGES.md`,
`DESIGN_F64.md`, this report and `SHA256SUMS`, with no data, weights, PNGs or SQLite; its sha256 is in `out/sb_f64fix.tar.sha256`.
