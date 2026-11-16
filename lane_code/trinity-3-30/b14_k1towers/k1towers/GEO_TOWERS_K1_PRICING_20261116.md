# Candidate geometry towers priced on K1 (MoGe-2, DA3, Pi3X; MapAnything pending), 2026-11-16, lane b14_k1towers

Status: DECIDED on K1 for {MoGe-2, DA3, Pi3X} (one held-out look at 15:51Z under ORCH 1453Z GO). MapAnything is not run: it changes no decision (raw scale off 25% on the CPU first pass; ORCH 1553Z).

## Answer
- Room: DA3 (`da3_native`) wins under the C-rule and passes the other-type guard, so DA3 replaces G3T for room programs: held-out R0 72.92 vs S4+G1 56.25, +16.67 [+7.39,+26.92] (+2.08 VSI points); train +20.64 [+13.36,+28.21]. It misses the room bar (73.4) by 0.5, so no GT-free arm reaches the bar and the room head path is not worth training on this evidence.
- Distance: decide.py returns G3T. MoGe-2 (`moge2_scale`) is the top distance qualifier (train +6.17 [+3.92,+8.73]; held-out 68.56, +5.65 [+1.42,+10.09], clears the +5 bar) but fails the guard: its room train lower bound is -2.06 (< -2). Pi3X qualifies on distance (held-out +3.89) and room (+11.25) but is not the top qualifier on either type. DA3 distance on held-out: -0.56.
- Reading of the winner rule (stated by the pre-registration, coded before the look): the top train-mean qualifier per type wins and replaces G3T only if it passes the guard; the rule does not fall through to the next qualifier. Unregistered observation, not a decision input: had the rule fallen through to the next qualifier, Pi3X would win distance. Pre-registration `GEO_TOWERS_K1_PREREG_20261116.md` (sha256 dd40e6d2...5c88). Brief `orch_n30/briefs/qs/14_geo_towers_k1.md`.

## Frozen before the held-out look (2026-11-16T15:50Z)
- Arm set for the decision: {MoGe-2 (`moge2_scale`), DA3 (`da3_native`), Pi3X (`pi3x_native`)}. MapAnything is out of this decision (ORCH 1453Z); it will be priced on train later as a separately labelled arm.
- Decision code: `decide.py` sha256 9c1586b12db8558d9c6e3579957d8a3a2784c7c4ac5e800cd24544a7bc5c0615 (merge_caps.py 6b97e80f..., k1_infer.py b1d731b6..., k1_convert.py e2748156..., k1_price.py 9e7e205e...). Copies: trinity-1-18 `/scratch/jjyeung/orch_n30/geo_k1/k1towers`, trinity-3-30 `/scratch/jjyeung/orch_n30/b14_k1towers/k1towers`.
- Input: trinity-1-18 `geo_k1/harness/out_merged_mdp` (296 captures: E3 reference rows + the three candidates).

## Question
Does a frozen tower that is metric by construction, or has better pose, beat the deployable G3T setting (S4+G1) on K1 under the C-rule, on metre distance (GT masks) and room size (R0, mask-free)?

## Evidence (K1 train, 192 rooms distance / 102 rooms room; MRA x100; paired diff vs S4+G1 with 95% room-bootstrap CI)
| arm | distance | vs S4+G1 | room R0 | vs S4+G1+R0 |
|---|---|---|---|---|
| S4+G1 (reference) | 67.36 | | 56.27 | |
| moge2_scale (primary) | 73.53 | +6.17 [+3.92,+8.73] | 61.18 | +4.91 [-2.06,+11.88] |
| da3_native (primary) | 71.79 | +4.44 [+1.18,+8.13] | 76.91 | +20.64 [+13.36,+28.21] |
| pi3x_native (primary) | 73.49 | +6.13 [+2.46,+10.31] | 70.18 | +13.91 [+7.38,+20.62] |
| moge2_depth | 72.32 | +4.97 | 70.64 | +14.36 |
| da3_scale / pi3x_scale | 66.96 / 66.66 | -0.40 / -0.69 | 74.00 / 71.55 | +17.73 / +15.27 |
| SO+G1 (oracle scale) / GT | 70.62 / 82.30 | +3.26 / +14.94 | 76.91 / 100 | |
- Train median anchor AbsRel vs GT (raw / median-aligned): da3_native 0.057/0.039, pi3x_native 0.061/0.039, moge2_scale 0.075/0.052, moge2_depth 0.102/0.093. `_scale` arms put the G3T scale within 20% of the oracle on 99-100% of captures.
- Refusals: 18 captures refuse every G3T-pose arm (`reference_camera_up_opposes_gravity`, the same captures E3 refuses); da3_native refuses 11, pi3x_native 10. Refused rows score 0.
- Reproduction: this harness copy reproduces E3's 4,563 per-item reference rows exactly (296 captures). 64 frames on every tower (Pi3X 35.7 GB on an A6000; GPU s/capture MoGe-2 7, DA3 9, Pi3X 11.7).
- Reviews: Codex gpt-6-astra high, three passes (codex_runs/20261116T131340Z_b14_k1t_review, ...132557Z_review2, ...134518Z_review3): drivers and E3 edits without blocking items; decide.py fixed to PASS_WITH_FIXES, fixes applied with 7 tests.

## Options rejected and why
- MapAnything in this decision: no card fitting its stage before the freeze (ORCH 1453Z). Its CPU first pass showed raw scale 25% off (AbsRel 0.34 raw, 0.04 aligned).
- 32-frame or CPU substitutes: not priced; every arm uses the 64 dense frames.

## What might not work and how we notice
- Room labels follow the floor-area rule on GT geometry (E3 caveat); held-out room has 24 rows / 23 rooms, so intervals are about +-13.
- Joint towers inherit the G1 gravity rule on their own poses; per-capture gravity error is in each capture's diagnostics.

## Held-out (one look, 15:51Z; distance 216 rows / 48 rooms, room 24 / 23)
| arm | distance | vs S4+G1 | room R0 | vs S4+G1+R0 |
|---|---|---|---|---|
| S4+G1 | 62.92 | | 56.25 | |
| moge2_scale | 68.56 | +5.65 [+1.42,+10.09] | 63.33 | +7.08 [-6.09,+20.36] |
| da3_native | 62.36 | -0.56 [-8.13,+7.12] | 72.92 | +16.67 [+7.39,+26.92] |
| pi3x_native | 66.81 | +3.89 [-0.24,+8.44] | 67.50 | +11.25 [+3.91,+19.13] |
| moge2_depth (secondary) | 70.14 | +7.22 [+2.55,+11.85] | 70.42 | +14.17 |
| SO+G1 / GT | 65.60 / 77.92 | +2.69 / +15.00 | 73.75 / 100 | +17.50 |
Output: trinity-1-18 `geo_k1/out/decide_heldout_once.json` (sha256 5d83da67...f1c0); train-only tables `geo_k1/out/decide_train_mdp.json`. Mirror: trinity-3-30 `/scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar` (sha256 7b75239c...ededf, equal on both ends).

## Tests that would settle it
- DA3 for room at the next seal: price it under the deployed own-scale column (GD) once K1's own phase lands; a held-out room bar test needs more than 24 rows.
