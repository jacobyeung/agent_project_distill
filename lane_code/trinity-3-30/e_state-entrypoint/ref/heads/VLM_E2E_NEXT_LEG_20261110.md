# The next method-carrying leg of the 9B student: tower read layer, MDG grounding, data-carried routing (design lane e2e_leg_scope, 2026-11-10 05:10Z)

Status: DESIGN, read-only lane. Nothing was built or launched. FACT = measured, with the file named; E = estimate with arithmetic shown; HYP = hypothesis.

## Code names used below
- **G3T**: thatbrguy/g3t, a gravity-aligned fine-tune of VGGT-1B (~1.2B), pin c55e91a0, weights sha256 d460957b…; frozen everywhere here.
- **G3T x s**: G3T poses with translation times one per-clip scale s = median(own V-C depth / G3T DPT depth) over grid points above the median G3T confidence (ttower's frozen rule, `ttower/work/geo/scale.py`, hash checked against `scales64.json`).
- **V-C**: the student's private depth substrate: a trainable copy of the Qwen ViT plus a point-depth head.
- **CPDM**: the student's own pose head on the per-frame CAM carrier tokens (pose9 = translation, quaternion xyzw, vertical and horizontal FoV, plus gravity).
- **MDG**: mask-decoder grounding, a 39M decoder (43M in one note) that reads LM taps (layers 16, 24, final), ViT taps (9, 17, 25) and an RGB stem and returns per-frame masks, presence and an interior point. **MDG-A**: stage A, decoder trained on frozen T0 m800 (running on trinity-0-18). **Stage B**: decoder plus a span-gated LoRA (36.2M, active only on the tokens of a grounding call) inside the mixed trainer.
- **T0, CP1, CP1-Rv**: the 9B line. T0 = mixed run from C1-a m800 (pose-only C1 run); CP1 = T0 m800 + paraphrased VQA + camera routing; CP1-Rv = CP1 m200 continued on Orchard (world 4, one pose stream, VQA doubled).
- **v3.11**: SPEC version of the programmatic routed traces (derivgen6). **v3.12**: the `<ground>` extension proposed here.
- **rkit**: mdg_next's routed-read harness (`mdg_next/work/rkit`); **s3i/s3c**: rkit arms where MDG masks (s3i) or T0 marker clicks (s3c) select among SAM 3 instances.
- **E2E-0**: the zero-training end-to-end camera read proposed here. **E2E-1**: the training leg proposed here (two variants, G with object routing, C without).
- **dev 858**: 858 GT-generated VSI-format questions on 84 held-out ScanNet val scenes (VSTI scenes, a disclosure set). **Clean camera pool**: 3,576 GT camera questions on 248 non-benchmark scenes. **E0**: 900-item MP3D navigation cohort (600 camera items).

## 1. The answer in five lines
1. **What:** E2E-1 is the CP1 line with frozen G3T inside `generate()` feeding the read layer the model already has (`<pose>`, `<move>`, `<turn>`, `<depth_at>` plus the printed-point calculator), so G3T x s values print as text. MDG stage B sits inside the forward behind a new `<ground obj="…">` call. Which types route is carried by the training data, with no prompt flag. Object types join the route table only after the MDG routed read wins.
2. **Where:** Orchard 4 x H100 (world 4, advanced QOS; or the world-8 preempt leg). Its reads run on Trinity 48 GB cards, where inference fits. The camera half needs no training: E2E-0 runs it end to end on CP1 m200 on trinity-0-18 or 1-18 under vnice.
3. **Starts from:** CP1-Rv's last leg-1 export if its m200 floor passes, else CP1 m200. MDG starts from MDG-A's best artifact. G3T is frozen.
4. **When:** E2E-0 runs Tue ~11:00-14:00Z (03:00-06:00 PT), after MDG-A frees 0-18 and the G3T weights clear the governor. E2E-1's kit is READY ~Tue 18:00Z. E2E-1 trains at CP1-Rv's first leg boundary, ~22 h after CP1-Rv starts. Orchard estimates put CP1-Rv's start at ≥ ~15:00Z Tue, so E2E-1 starts ~Wed 13:00-16:00Z, earlier only if the preempt leg starts first. Its first decisive read (m200) lands ~18-19 h after its start.
5. **Expected (HYP, from harness evidence):**
   - VSTI camera types: G3T x s programs beat own-pose programs by +21.7 / +26.8 / +36.2 and f17 direct by +33.7 / +48.8 / +64.6 (displacement / movement direction / rotation, clean pool, CIs > 0; `CP1_ROUTING_TABLE_20261109.md`). That is about +4 VSTI overall over own-pose routing (2 of 9 types; `SOTA_BREAKTHROUGH_PLAN_20261109.md` §2.3).
   - VSI-Bench object types: with GT masks + G3T x s, routing beats T0 direct by +24 / +24 / +40 / +27 (direction medium / hard, abs distance, rel distance; dev 858, rkit).
   - At MDG-A's present placement (internal val in-mask 0.674, step 900) the s3i placement curve predicts only abs distance wins (~+17 to +21). That is VSI-Bench macro about +0 to +2 now, and +4 to +7 if placement reaches ≥ 80% (4 of 4 types win at 80% on the curve).
   - ReVSI is unmeasured for every checkpoint.

## 2. Forward pass of E2E-1, module by module
| # | Module | Train / frozen | What it does in E2E-1 | Evidence |
|---|---|---|---|---|
