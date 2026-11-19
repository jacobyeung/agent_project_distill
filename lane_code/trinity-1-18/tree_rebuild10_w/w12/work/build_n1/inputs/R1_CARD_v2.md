# R1 registration card, v2 (lane card_fix, 2026-11-17). Detail and sources: `distill_design/NEXT_LEG_DECISION_20261117.md` sections 2.2 to 2.4, 3.3 and 5
Lane r1_ops completes every `[r1_ops: ...]` field before registration. One confirmation review is owed. Official ReVSI and VSI-Bench items select nothing; no control run, no seed replicate.

**Identity.** Leg R1, 1,000 steps on four H100, init step 544 (1d6eeb28, every weight; no transplant), GT-valued responses, `max_own_probability 0`, S2 off. Run `[r1_ops: run id]`; vehicle `[r1_ops: P or N]`, tree `[r1_ops: sha]`; config identity `[r1_ops: sha]`; stores `[r1_ops: sha256 per stream]`; mix table `[r1_ops: sha]`; production proof with loader audit `[r1_ops: receipt]`; reader build and selector variant `[r1_ops]`.

**1. Question.** After SFT on GT traces that add recovery, unit and traced room rows and the missing direct families, does one checkpoint place its calls, terminate, and answer from the responses when every call is served inside the checkpoint, without losing direct types?

**2. Difference.** R1's training, against step 544 read by the same reader build, on the same arm and items. The rows are one bundle.

**3. Confounds.** Fresh optimizer and restarted schedule. Six families at once, entering at different boundaries. D0's size loss has no verified cause (slot SIZE-V). Step 544's parents saw dev-S1's scenes (both arms share it; only R0-dev is unexposed). Recovery statuses are simulated. G3T and SAM 3 pretraining is unaudited. The depth and gravity heads keep training and set the tower arm's scale and level frame. P and N differ in auxiliary losses (scale token on N). GF-1 may enter at a passing boundary.

**4. Rule.** One decision per boundary (steps 200, 400, 600, 800) on dev-S1, paired against step 544; percentile intervals of a room bootstrap, 10,000 draws; R0-dev is printed and stops nothing alone.
- **Harm rule: STOP** if H1, H2 or H3 holds. H1: one of the seven direct types (150 items each) has its interval wholly below zero, at 99.29% (step 200) or 99.82% (later). H2: the interval of the mean of the seven differences (72 rooms, resampled jointly) lies wholly below zero, at 95% (step 200) or 98.75% (later). H3, tower arm, only once step 544's tower-arm read on the same reader build exists: a camera type's interval at H1's level lies wholly below zero, or under 95% of the 450 camera items draw a call.

| Computed on D0's m200 read (1,050 paired items; 8,000 pseudo-reads scored with the tool's interval) | Step 200 | Each later boundary |
|---|---|---|
| H1 or H2 stops an unchanged model | 0.063 (nominal 0.050; uncorrected 95% intervals: 0.179) | 0.023 |
| Loss of 9.5 on size: noise as D0's read / with its own item flips | 0.72 / 0.51 | 0.56 / 0.33 |
| Loss of 9.5 on one other type (flips) | 0.40 to 0.64 | 0.24 to 0.47 |
| Uniform loss of 2 on all seven (3 and 4: H2 alone 0.69 and 0.91) | 0.42 | 0.23 |

  Over the leg H1 or H2 stops an unchanged model with probability at most 0.132 (union bound, four looks); with H3's uncalibrated camera intervals at most 0.186 (guess). The rule guards against large losses; it does not certify the absence of a loss.
- **Efficacy gates.** A family enters at boundary E and its gate is read at E + 200, paired against step 544, 95% room-bootstrap interval.

| Family | E `[r1_ops]` | Items | Step 544 | Gate |
|---|---|---|---|---|
| VSTI relative, six types | 1 | 900 dev items on R0-dev rooms (`vsti_rel_dev_r0`, in build) | unread; read in the same job | pooled accuracy rises, interval above zero |
| Facing away with ReVSI's wording | 1 if v7 binds | 150 away twins; 49 in ReVSI's wording | 32 of 150; the 49: `[r1_ops: from b13 dev544]` | both rise, intervals above zero; toward printed |
| Object size (first-seen repair) | 1, or as SIZE-V | 150 items, 59 rooms | 68.7 | interval not wholly below zero (unchanged model fails 0.029; D0's loss fails 0.71 to 0.87) |
| Recovery | `[r1_ops]` | own arm: the 63 of 150 distance items whose step-544 read drew a status | 33 of 63 capped; MRA 0.138 | capped reads fall, interval below zero; MRA not lower. Claimed arm: capped rate over 150 printed, must not rise |
| Units | `[r1_ops]` | 107 non-metre distance items, unperturbed | 13 to 30 of 107 converted `[r1_ops: exact, out/unit_none.py]` | converted count rises, interval above zero; at least 80% of gap-valued answers convert |
| Room, traced rows | `[r1_ops; none at launch today]` | 36 dev-S1 + 98 R0-dev items | 36 of 36 call, 27 capped, MRA 0.139; R0-dev unread | MRA rises, interval above zero; at most 24 of 134 reads call (2 of 134 at E + 400) |

- **Verdict.** STOP as above. HOLD: a due gate fails or cannot be evaluated; the leg trains one more boundary and the gate is read again; a second failure stops the leg. PASS: every due gate has passed. A passing boundary also needs the recovery and unit gates. Recovery and unit rows are hard requirements from step 200 on.

**5. Decision.** PASS: continue; A2 may enter at a passing boundary as a new pin; at step 1,000 the export the init rule selects gets one official read, report-only. STOP on size alone: size moves to a head route and its rows leave the store. STOP on another type or H2: rebuild the family that feeds it and restart from the last passing export (step 544 if none). STOP on H3: audit serving pins and camera rows. A gate that fails twice: stop, rebuild, restart from the last passing export.

**6. Mix per step.** Rule: every cell is at most 4 x eligible / 1,000 (eligible = the loader audit's post-filter count); freed VQA slots go to direction, freed routing slots to the four program cells pro rata.

| Cell | Plan | Eligible today | Admitted and final cell `[r1_ops]` |
|---|---|---|---|
| VQA: direction + facing pairs | 20.08 + 18.17 | 84,859 (+ 8,740 ReVSI-worded away rows in v7) | |
| relative distance / size (SIZE-V) / counting + totals | 22.74 / 10.81 / 10.87 + 3.39 | 20,665 / 9,778 / 20,669 | |
| appearance / first-seen / 3D box / route | 14.42 / 2.00 / 1.82 / 9.70 | 27,791 / 7,076 / 3,813 / 8,894 | |
| VSTI relative, six types | 2.00 each | 1,951 / 1,983 / 1,998 / 1,998 / 2,000 / 1,996 | |
| room, traced only | min(2.00, ceiling), 0 while none | 0 (469 traceable before exclusions) | |
| VSTI camera-object absolute distance | excluded, 0 | 0 rows exist | |
| Routing: displacement / direction / rotation / absolute distance | 17.42 / 15.15 / 11.96 / 15.60 | 14,020 / 12,260 / 9,143 / 11,728 (plan metadata) | |
| recovery | 1.00 (5.1% of distance rows; 2.00 if its gate holds) | N 1,458; P 0 | |
| units | 2.87 | N 1,915 of a 2,000-row slice; P 216 | |
| Pose 64, pointing 32 | unchanged | | |

  P as its tree admits rows today: recovery 0, units 0.86, program cells 18.29 / 15.90 / 12.56 / 16.39. Families missing or partial at launch: `[r1_ops: name each, with its entry boundary]`.
  **Slot SIZE-V** `[size_diag verdict]`: row form at fault and v6 shares it, or answers wrong by the factor of two: size cell 0, slots to direction, rebuilt rows enter at a boundary. Form at fault but v6 removes it, or rows not at fault: 10.81 with v6 rows. No verdict by the vehicle gate: the orchestrator decides (recommended: 0 at launch, entry at step 200).

**7. Cost per boundary** (H100-hours, cumulative, one allocation; 0.153 per step, 11 staging, about 5.2 of reads per boundary).

| Step | 200 | 400 | 600 | 800 | 1,000 |
|---|---|---|---|---|---|
| Training + staging / with reads | 41.6 / 47.6 | 72.2 / 83.4 | 102.8 / 119.2 | 133.4 / 155.0 | 164.0 / 190.8 |
| Export at | T+10.5 h | T+18 h | T+26 h | T+33.5 h | T+41 h |

  The direct read runs first: a STOP arrives about 1 h after the export (4 more H100-hours); gate reads end about 5.5 h after it. A stop at step 200 costs about 52; a held gate costs about 36.

**8. Scenarios** (upside if a repair works in full; no predictive interval; each allows a loss). VSTI primary 73.89: +0 to +8.9. ReVSI through the claimed reader, about 51.2 (guess): facing +0 to +5.1, room +0 to +5.6. VSI-Bench about 67.1: +0 to +1.5. A loss on size is possible.

**9. Pins and exposure.** One row per boundary: `[r1_ops: launch | 200 | 400 | 600 | 800: vehicle, tree, config identity, stores, family entries and cells, mix sha, auxiliary losses, S2, reader build, selector, scale rule, tower weights, arm]`. A pin changes only at a boundary; both arms of a comparison share the serving pins. Every report prints, per arm and item set, the rooms and the exact items the arm's lineage trained on, and the tower arm's scale statistic.

**10. Open before registration.** The loader audit's counts; slot SIZE-V; the exact unit baseline; the interval level and the joint mean of seven in the read tools (cont_ops); the VSTI dev set and its step-544 read; the tower-arm read of step 544 (H3 and the claimed-arm marks wait for it).
