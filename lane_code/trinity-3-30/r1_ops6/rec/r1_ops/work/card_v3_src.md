# R1 registration card, v3 (lane card_fix2, 2026-11-17). Detail and sources: `distill_design/NEXT_LEG_DECISION_20261117.md` sections 2.2 to 2.4, 3.3 and 5
Lane r1_ops completes every `[r1_ops: ...]` field; the orchestrator then registers the card. Official ReVSI and VSI-Bench items select nothing; no control run, no seed replicate. Every probability on this card is a conditional simulation estimate, not a guarantee.

**Launch gates (all five, nothing else).** (1) The production proof with the loader audit, on the final config identity; the audit shows every family named present, the faithful unit rows included. (2) Five bound rows per family, read by the orchestrator and shown to the user. (3) Slot SIZE-V decided (done, section 6). (4) This card registered. (5) Main's release of the slot. The launch waits for no step-544 baseline and not for vehicle N: the leg stays on vehicle P, and N takes over only at a boundary where its continuation proof has passed.

**Before the first export is read.**
- *Baselines.* Step 544 is read under the pinned serving config and each read is registered by sha256 before any R1 export is read: the tower-arm read with the pinned selector (450 camera, 150 distance and 36 room items; it gives H3, the capped and status counts and the exact unit count), the VSTI dev set (`vsti_rel_dev_r0`, b5853845), R0-dev (direct items and its 98 room items), and the count on the 49 ReVSI-worded twins. The dev-S1 direct read exists (`A544.jsonl`, 8347cd84) and is read again only if the reader build changes. A gate whose baseline is missing when it falls due is HOLD.
- *Pooled harm rule.* One test per direct type on dev-S1 and R0-dev items together, with a bootstrap over all rooms, replaces H1's dev-S1 tests only if it is registered before the first export is read, with H2 and H3 recalibrated and its estimated false-stop rate and power recomputed. It is valid only if the baseline is the exact step-544 artifact (1d6eeb28), both arms are read on the same item keys with the same arm, serving pins, decoding and scoring, the physical rooms and the dataset weights are fixed in advance, and R0 exposure is audited. Until then the dev-S1 rule of section 4 binds.

**Identity.** Leg R1, 1,000 steps on four H100, init step 544 (1d6eeb28, every weight; no transplant), GT-valued responses, `max_own_probability 0`, S2 off. Run `[r1_ops: run id]`; vehicle P, tree `[r1_ops: sha]`; config identity `[r1_ops: sha]`; stores `[r1_ops: sha256 per stream]`; mix table `[r1_ops: sha]`; production proof with loader audit `[r1_ops: receipt]`; reader build and selector variant `[r1_ops]`.

**1. Question.** After SFT on GT traces that add unit, recovery and traced room rows and the missing direct families, does one checkpoint place its calls, terminate, and answer from the responses when every call is served inside the checkpoint, without losing direct types?

**2. Difference.** R1's training, against step 544 read by the same reader build, on the same arm and items. The rows are one bundle.

**3. Confounds.** Fresh optimizer and restarted schedule. Five families at once, entering at different boundaries. No size row trains, so a size change is drift or another family's effect; dev-S1 asks 78 of its 150 size items in feet or inches, the official sets and R0-dev in cm only. Step 544's parents saw dev-S1's scenes (both arms share it; only R0-dev is unexposed). Recovery statuses are simulated. The 8,511 away rows use ReVSI's away wording as a question template on non-benchmark scenes, so no ReVSI facing gain is claimed as transfer to an unseen phrasing. G3T and SAM 3 pretraining is unaudited. The depth and gravity heads keep training and set the tower arm's scale and level frame. P and N differ in auxiliary losses (scale token on N). GF-1 may enter at a passing boundary.

**4. Rule.** One decision per boundary (steps 200, 400, 600, 800), paired against step 544; percentile intervals of a bootstrap over physical rooms, 10,000 draws. The harm rule and the protected outcomes are read on dev-S1; R0-dev is printed and stops nothing alone.
- **Harm rule: STOP** if H1, H2 or H3 holds. H1: one of the seven direct types (150 items each) has its interval wholly below zero, at 99.29% (step 200) or 99.82% (later). Object size is one of the seven: a protected outcome under H1, not an efficacy gate. H2: the interval of the mean of the seven differences (72 rooms, resampled jointly) lies wholly below zero, at 95% (step 200) or 98.75% (later). H3, tower arm: a camera type's interval at H1's level lies wholly below zero, or under 95% of the 450 camera items draw a call.
- **Protected outcomes: HOLD the first time, STOP the second.** Toward-facing accuracy (150 toward twins) or relative size (150 items) has its interval wholly below zero at H1's level. Claimed arm with the pinned selector, at every boundary: more than 5 of the 150 distance reads end at the call cap (the count's interval comes from the room bootstrap). Object size is printed split into its 72 metric and 78 imperial items, with relative size beside it.

| Estimated on D0's m200 read against step 544 (1,050 paired direct items, 150 toward twins, 150 relative-size items; each pseudo-read scored with the tool's interval) | Step 200 | Each later boundary |
|---|---|---|
| Nominal calibrated bound for an unchanged model, H1 + H2 (0.0875 over four looks) | 0.025 + 0.025 | 0.00625 + 0.00625 |
| Estimated: H1 or H2 stops an unchanged model (0.132 summed over four looks; an estimate, not a bound) | 0.063 | 0.023 |
| Estimated power, loss of 9.5 on size: noise as D0's read / with its own item flips | 0.72 / 0.51 | 0.56 / 0.33 |
| Loss of 9.5 on one other type (flips) | 0.40 to 0.64 | 0.24 to 0.47 |
| Uniform loss of 2 on all seven (3 and 4: H2 alone 0.69 and 0.91) | 0.42 | 0.23 |
| Size drift of 3 / 6 with no size row: H1 fires on size | 0.04 / 0.17 to 0.21 | 0.02 / 0.09 to 0.12 |
| HOLD on an unchanged model: toward / relative size (nominal 0.0036 and 0.0009 each) | 0.007 / 0.006 | 0.003 / 0.002 |
| HOLD at D0's losses: toward -4.0 / relative size -12.7 | 0.14 to 0.28 / 0.50 to 0.64 | 0.08 to 0.19 / 0.35 to 0.49 |

  Calibration evidence: `events/next_leg/card_fix_a3_evidence.tgz` (sha256 47b1b97f) and `card_fix2_b5_evidence.tgz` (9278860b). H3's intervals and call floor stay uncalibrated until the tower-arm baseline exists (nominal 0.019 over four looks for the three camera types). The rule guards against large losses; it does not certify the absence of a loss.
- **Efficacy gates.** A family enters at boundary E. Its gate is read once at E + 200 and once more only after a HOLD, paired against step 544, with a 95% room-bootstrap interval. A population under 60 items gives a printed mark, not a gate. MDI is the smallest true improvement that passes the gate with estimated probability 0.80, from the baseline's paired room distribution.

| Family | E `[r1_ops]` | Items | Step 544 | Gate | MDI |
|---|---|---|---|---|---|
| VSTI relative, six types | 1 | 900 dev items, 68 R0-dev rooms | its dev read (above) | pooled accuracy rises, interval above zero, and no single type's interval lies wholly below zero | from the dev read. Planning, at VSTI-450's per-type levels: +0.8 points if no right answer flips back, +8.3 if 5% do (the type clause then binds) |
| Facing away | 1 | 150 away twins, 33 rooms; the 49 in ReVSI's wording are a printed mark | 32 of 150 | accuracy over the 150 rises, interval above zero; printed by forward band, because "away means back" answers 84.5% of away-hard rows | +3.9 points; +8.9 if right answers flip back at D0's rate (5 of 32). D0 m200 gained 59.3 |
| Units (rows required from launch) | 1 | all 107 non-metre distance items, unperturbed, claimed arm | exact count from the tower-arm read; own arm 22 of 107 | correct conversions over all 107 rise, interval above zero | from the tower-arm read. Own arm: +5.8 points (6 items); +12.8 with 15.6% back-flips (assumed). P trains feet rows almost alone, and the gate still counts cm 28, ft 46, in 33 |
| Recovery | the boundary at which N takes over | the distance items whose baseline read drew a status, if at least 60; otherwise the mark "no read with a status caps" | tower-arm read; about 7 of 150 expected, so the mark; own arm 33 of 63 capped, MRA 0.138 | capped reads among them fall, interval below zero; MRA not lower | from the tower-arm read. Own arm: 6 fewer capped reads of 33; 16 fewer if 15.6% of terminating reads cap (assumed) |
| Room, traced rows | 1 if store v7 binds at launch | 36 dev-S1 + 98 R0-dev items, 107 rooms | dev-S1: 36 of 36 call, 27 capped, MRA 0.139; R0-dev: its read | MRA rises, interval above zero, and the one-sided 95% upper bound of the call rate, bootstrap over the 107 rooms, is below 25% (24 calls spread over rooms pass, 24 in whole dev-S1 rooms fail). Mark at E + 400: that bound below 5% | from the R0-dev room read |

- **Verdict.** STOP: the harm rule fires, or a protected outcome or a gate fails a second time. HOLD: a protected outcome fails once, or a due gate fails or lacks its baseline; the leg trains one more boundary and the gate is read once more. PASS: every due gate has passed and no HOLD is open. A passing boundary is a PASS with the unit gate among those passed.
- **Spending rule.** A family not in the leg by step 400 leaves R1's claim. The leg passes step 400 only if the VSTI and facing gates have passed and no protected outcome is on its second failure; otherwise it stops at step 400, at about 83 H100-hours. A restart after any STOP needs a new card.

**5. Decision.** PASS: continue; A2 may enter at a passing boundary as a new pin; at step 1,000 the export the init rule selects gets one official read, report-only. STOP: the leg ends at that export, and the new card starts from the cause. On object size: the metric and imperial split, because no size row trains. On another type or H2: the family that feeds it, rebuilt. On H3: an audit of the serving pins and the camera rows. On a gate, toward-facing or relative size: that family, rebuilt. On capped reads: recovery rows on vehicle N.

**6. Mix per step.** Rule: every cell is at most 4 x eligible / 1,000 exactly (eligible = the loader audit's post-filter count); freed VQA slots go to direction, freed routing slots to the four program cells pro rata.

| Cell | Launch cell | Eligible today | Admitted and final cell `[r1_ops]` |
|---|---|---|---|
| VQA: direction + facing pairs | 31.166 + 18.17 (direction holds size's 10.81 and room's remainder; 32.89 + 18.17 while room is 0) | 84,859, + 8,511 ReVSI-worded away rows in v7 | |
| relative distance / counting + totals | 22.74 / 10.87 + 3.39 | 20,665 / 20,669 | |
| object size | 0 (slot SIZE-V) | 9,778 rows stay in the store; none is drawn | |
| appearance / first-seen / 3D box / route | 14.42 / 2.00 / 1.82 / 9.70 | 27,791 / 7,076 / 3,813 / 8,894 | |
| VSTI relative, six types | 2.00 each | 1,951 / 1,983 / 1,998 / 1,998 / 2,000 / 1,996 | |
| room, traced only | min(2.00, 4 x eligible / 1,000): 1.724 at v7's 431 rows (1.876 at 469); 0 if v7 is not bound | 431 in v7 | |
| VSTI camera-object absolute distance | excluded, 0 | 0 rows exist | |
| Routing on P: displacement / direction / rotation / absolute distance | 17.71 / 15.40 / 12.16 / 15.86 (17.42 / 15.15 / 11.96 / 15.60 once recovery holds 1.00) | 14,020 / 12,260 / 9,143 / 11,728 (plan metadata) | |
| recovery | 0 on P; 1.00 from the boundary at which N takes over (5.1% of distance rows; 2.00 after a HOLD of its gate) | N 1,458; P 0 | |
| units, required from launch in faithful form | min(2.87, 4 x eligible / 1,000): 2.87 at 1,224 rows | **slot UNIT-P, filled:** `units_p_slice_v2` (40437c8a), the 1,224 of all 10,945 rows whose answer already equals the label: ft 1,130, in 94, cm 0. Inch and cm are named missing on P (under 100 rows each). If the open box-extent audit removes the 710 ScanNet++ rows, the cell is 2.056 | |
| Pose 64, pointing 32 | unchanged | | |

  Families missing or partial at launch: `[r1_ops: name each, with its entry boundary]`. Known today: recovery (enters with N), inch and cm unit rows (missing on P), object size (out of the leg).
  **Slot SIZE-V: decided, verdict (b)** of lane size_diag (`events/size_diag/20261117T1520Z_RESULT_d0_size_loss_verdict_b.md`). The size rows' trace form caused D0's loss, their labels are right, and stores v6 and v7 keep that form. No size row is drawn, and none enters R1 unless a new form is built and carded. Without size rows lane size_diag expects a drift of 0 to -6 points on dev-S1 size (guess). H1 treats that drift as a loss: at -3 it stops the leg with estimated probability 0.04 at step 200 and about 0.10 over four looks; at -6, 0.17 to 0.21 at step 200 and at most 0.44 to 0.56 over four looks (sum of the per-look estimates).

**7. Cost per boundary** (H100-hours, cumulative, one allocation; 0.153 per step, 11 staging, about 5.2 of reads per boundary).

| Step | 200 | 400 | 600 | 800 | 1,000 |
|---|---|---|---|---|---|
| Training + staging / with reads | 41.6 / 47.6 | 72.2 / 83.4 | 102.8 / 119.2 | 133.4 / 155.0 | 164.0 / 190.8 |
| Export at | T+10.5 h | T+18 h | T+26 h | T+33.5 h | T+41 h |

  The direct read runs first: a STOP arrives about 1 h after the export (4 more H100-hours); gate reads end about 5.5 h after it. A stop at step 200 costs about 52; a held gate costs about 36; the spending rule ends a leg whose VSTI or facing gate has not passed at step 400, at about 83. Step 544's baseline reads run in the job place before the first export is read.

**8. Scenarios** (upside if a repair works in full; no predictive interval; each allows a loss). VSTI primary 73.89: +0 to +8.9. ReVSI through the claimed reader, about 51.2 (guess): facing +0 to +5.1, room +0 to +5.6. VSI-Bench about 67.1: +0 to +1.5. Object size has no repair in this leg.

**9. Pins and exposure.** One row per boundary: `[r1_ops: launch | 200 | 400 | 600 | 800: vehicle, tree, config identity, stores, family entries and cells, mix sha, auxiliary losses, S2, reader build, selector, scale rule, tower weights, arm]`. A pin changes only at a boundary; both arms of a comparison share the serving pins, and a serving pin that changes forces a new registered read of step 544. N replaces P only with its continuation proof: init from P's export, with the absolute step, the schedule position and the row plans kept. Selector: best candidate once lane reader_r1's check passes, null slot kept until then. Every report prints, per arm and item set, the rooms and the exact items the arm's lineage trained on, and the tower arm's scale statistic. No report prints a student number on K1 held-out rooms without a contamination flag (store v6 trains 6,159 rows on 92 of them); no number registered here uses those rooms.

**10. Open before registration.** The loader audit's counts; the box-extent audit of the unit slice's ScanNet++ rows; the orchestrator's ruling on the conditions of store v7's review (210b2534, ADMIT WITH CONDITIONS: C1 and C2 are stated in sections 3 and 9; C3, room traces that locate but do not derive, is the orchestrator's to accept); in the read tools (cont_ops), the interval level, the joint mean of seven and the metric and imperial split.
