# Pre-registration: candidate geometry towers priced on K1 (2026-11-16, lane b14_k1towers)

Written at 2026-11-16T11:54Z, before any candidate tower has run on a K1 capture and before any candidate K1 number exists. A change to anything below needs a new dated note written before the data it would use is read. Brief: `orch_n30/briefs/qs/14_geo_towers_k1.md`. Parents: `E3_BACKEND_GEOMETRY_PRICING_20261116.md` (harness, fits, reference arms), `REFREEZE_PREREGISTRATION_20261115.md` (C-rule), `GEOMETRY_BACKEND_BAKEOFF_20261111.md` (kit, backends).

## Question
Does a candidate frozen tower that is metric by construction, or has better pose, beat the deployable G3T setting on K1 under the C-rule, on metre distance and on room size?

## Data
- K1 manifest `trinity-1-18:/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json` (the file E3 used), 296 captures with GT rasters; `k1_split` train / heldout by physical room. Rows and labels are E3's: distance on GT instance masks (train 1,037 rows / 192 rooms, held-out 216 / 48 with geometry); room mask-free (train 110 / 102, held-out 24 / 23).
- No ScanNet validation, benchmark or BENCH v2 scene is read. K1 decides program-side choices only; no model answer enters.

## Candidates and inference protocol
Four towers from the sealed bake-off kit (seal 0ef8fe08, backends unchanged): MoGe-2 ViT-L, MapAnything, DA3 Nested Giant-Large, Pi3X. MoGe-3 is not run (CUDA-only reserve, not in the kit's CPU-verified set).
- Input: the capture's 64 dense frames listed in the manifest (sha256 checked), in the order of the G3T tower's `frame_indices`; output kept for the tower's exact 32 `anchor_slots`. No 32-frame substitute.
- Official settings as in the kit: MoGe-2 3,600 tokens per frame; DA3 504 px, ref view `saddle_balanced`; Pi3X 255,000-pixel rule; MapAnything 518 px, memory-efficient minibatch 1; bf16 autocast on CUDA; seed 0. No GT enters inference.
- Each tower runs at its own native scale. No scalar is fitted to GT or to train rows for any primary arm.
- A capture whose inference or conversion fails keeps its rows; they score 0 for that arm and are counted.

## Arms
Every arm is written as one `geometry.npz` per capture in the deployed `scaled_g3t_depth` format (51 x 51 canvas grid, K, canvas_to_source, camera_to_world, one scale) and priced by E3's programs unchanged (distance: two box grounds + `box_grid_5cm` gap, predicted mode; room: `room_v314` predicted mode).
- **Primary, joint towers (MapAnything, DA3, Pi3X): `X_native`.** The tower's own depth, intrinsics (full, off-centre allowed), poses and scale, scale = 1. Gravity: the G1 rule applied to the tower's own 32 anchor poses (mean camera up), expressed through the deployed `to_gravity_reference_frame` convention.
- **Primary, MoGe-2 (no trajectory): `moge2_scale`.** G3T depth and pose with G1 gravity, exactly as E3 builds them, with the scale given by the deployed rule `tower_scale_rule.estimate(G3T depth, G3T confidence, MoGe-2 depth on the same grid)`: the own-depth input replaced by MoGe-2's metric depth.
- Secondary (diagnostic, never decide): `X_scale` for the joint towers (G3T geometry, scale from the deployed rule fed the tower's depth; separates scale from shape and pose); `moge2_depth` (MoGe-2 depth and intrinsics on G3T rotations and G3T translations times `moge2_scale`'s s); every arm with room rule R2 (train-fitted multiplier, E3's fit procedure per arm).
- Reference and ceilings, recomputed in the same driver and required to reproduce E3's per-item rows exactly before any candidate is priced: `S4+G1` with E3's frozen `FITS.json`, `SO+G1`, `GT`.

## Reference
The decision reference is the deployed own-scale column (`GD`: step-544 own depth and gravity, K1 convert output) if it exists before any candidate held-out number is read; otherwise `S4+G1`. As of 11:54Z K1's own phase has not landed, so the reference is `S4+G1`, and the report says so. GD, when it lands, is reported beside.

## Metric, statistics, decision rule
- VSI-Bench MRA (0.50:0.05:0.95), x100; refusals and errors score 0. Item-weighted means; 95% percentile bootstrap over physical rooms, 10,000 draws, seed 20261116, paired on shared items (E3's `agg.py`).
- Primary comparisons: 4 candidates x {distance (GT masks), room (R0, mask-free)} = 8.
- **C-rule** (per type): a candidate qualifies if its paired (candidate − reference) 95% lower bound is above 0 on K1 train and its point estimate is above 0 on K1 held-out. Among qualifiers, the largest K1-train mean wins; ties go to G3T.
- **Bars** (held-out): distance clears at reference + 5 task points; room clears at 73.4 MRA (f17 direct 63.40 + 10; sensitivity bar 79.0).
- **Tower decision:** a candidate replaces G3T for programs and GF-1 only if it qualifies on at least one type and its paired train lower bound on the other type is at least −2 task points. **Room head path:** worth training only if a GT-free arm reaches the room bar on held-out.
- VSI-Bench eight-task value: Δ task points / 8 per type.
- Held-out tables are not read until an independent reviewer has read E3's two harness edits, this lane's driver edits and the analysis code (brief 14 review clause). Train tables may be read first.

## Diagnostics reported (not decision inputs)
Per capture and split: candidate scale s / SO (fraction within [0.8, 1.2]); gravity angle of the candidate's G1 against GT gravity; depth AbsRel at the anchors' grid points against GT before and after per-capture median alignment; pose rotation and translation error after similarity alignment; inference seconds and peak GPU memory.

## What might be wrong
- Off-centre principal points (MapAnything) are kept in K; the deployed `ProfileGeometry` uses K rays, so no centring is applied. DA3 and Pi3X intrinsics are restored by the kit's pure-resize rule; a crop inside a preprocessor would bias them. The CPU first pass checks the anchor depth against GT on one capture before the GPU pass.
- 216 / 24 held-out rows; room intervals are wide (E3: about ±13).
- Room labels are the floor-area rule on GT geometry (E3 caveat), so room measures agreement with that rule.
