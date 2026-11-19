# Object size: the answer partly follows the instance, and no trace form the ruling allows carries the missing evidence (lane san_dd_size, 2026-11-19)

Scope: `object_size_estimation` on dev-S1 (150 items) and R0-dev (293 items) at step 544 (base), R1 step 100 and R1 step 200, read through `san_kit`; all 9,778 store-v7 size rows fetched by primary key (`object_size_estimation|r1g|rows_rebuild_d0_v1`); 747 feet/inch unit rows; the trace ruling's Answer section and size parts. Scores are the B2048 arm. Lengths are converted to centimetres (inch 2.54, foot 30.48, metre 100). Prices follow the brief: type points (tp) = 100 x summed (1 - score) / items of the type in the set; VSI-Bench points = dev-S1 tp / 8; ReVSI points = R0-dev tp / 7 (object size has one leaf, `longest_dimension`). "v7 rows" below means the 4,892 base rows of the size family; the other 4,886 rows are paraphrases that repeat a base row's scene, object and answer. Every count comes from the files; guesses carry the word "guess".

## 1. Answers

1. **Does the answer follow the instance? Partly.** Within the ten largest classes of each set, a doubling of the true length raises the answer by a factor of about 2^0.6: the pooled within-class slope of log answer on log truth is 0.64 on dev-S1 (93 items) and 0.56 on R0-dev (58 items) at step 200, with correlations 0.56 and 0.50 (step 544: 0.69 and 0.54). Per class, 4 of 21 classes track the instance (tv, table, windowsill, trash can), 4 track it partly (sofa, stove, cabinet, window) and 13 show no instance signal (Table A). The no-signal classes are mostly narrow ones that the prior already scores well (bed 94, door 92, sink 90, bathtub 86). Some classes get one fixed number: R0-dev doors get "210" on 8 of 8 items, keyboards "45" on 5 of 6, and dev-S1 tables asked in inches get 106.3 in (270 cm) on 4 of 5. When dev-S1 asks about the same object twice, the answers agree within 5% on 9 of 13 same-unit pairs but on only 5 of 13 pairs asked in two different units. The asked unit therefore shifts the estimate itself: beds asked in feet get 7.11 ft (217 cm) on 3 of 4 items, and beds asked in inches get 71.1 to 75.2 in (181 to 191 cm) on 3 of 3.
2. **What kind of object fails?** The 100 lowest-scoring items (73 R0-dev, 27 dev-S1; all score 0.3 or less) hold 16.53 of the 30.60 dev-S1 tp and 23.45 of the 41.71 R0-dev tp. By primary cause (Table C), R0-dev's share sits in small objects answered too large (24 items, 7.95 tp), unusual or ambiguous names (13, 4.16 tp), other over- and underestimates (13, 4.13 tp), classes with fewer than five v7 rows (7, 2.15 tp), implausible truths (6, 2.01 tp), broad classes answered near the class middle (6, 1.98 tp) and large objects answered too small (4, 1.06 tp). dev-S1's share sits in classes with fewer than five v7 rows (11 items, 6.67 tp), inch questions answered with a round centimetre value (7, 4.40 tp), other overestimates (7, 4.20 tp) and large objects answered too small (2, 1.27 tp). A wrong unit or wrong conversion causes none of the 100.
3. **Truth convention.** No. The median ratio of dev truth to the v7 class median is 0.997 on dev-S1 (119 items whose class has a v7 row) and 0.938 on R0-dev (213 items); on classes with five or more rows it is 0.962 (50) and 0.911 (135). Well-defined classes sit at 1 on R0-dev (sink 0.97, stove 0.94, bathtub 0.97, dishwasher 1.03, windowsill 1.03). The low R0-dev median comes from broad classes whose R0-dev instances are small (cabinet 0.45 on 9 items, picture 0.36 on 4, umbrella 0.60, shelf 0.79). The numbers therefore rule out a different box or longest-dimension definition, which would shift every class. In broad classes, R0-dev's named instances are smaller; these files cannot tell whether that is a different choice of instance or a part named like its whole, such as one cabinet unit named "cabinet" (Table D). The v7 rows come from ScanNet++ alone (dataset `d2` on 9,778 of 9,778 rows, 611 scenes); dev-S1 mixes ARKitScenes (76), ScanNet++ (42) and ScanNet (32), and its ratio is about 1 in each (0.98 to 1.02).
4. **Small objects (R0-dev truth under 30 cm; 88 items, MRA 48.0, 15.63 tp, 2.23 ReVSI).** They span 66 classes; the commonest are telephone (4), smoke detector, faucet and bucket (3 each). Of the 88, 59 have a v7 class row and 36 have five or more. The error is mostly scatter with an upward bias, not a floor: 36 items overshoot with no large class prior behind them (MRA 31.9, 8.36 tp), 10 follow a class prior that is too large (MRA 7.0, 3.17 tp), 15 undershoot (2.15 tp), 22 score 0.9 or more, and only 5 sit under the observed 10 cm answer floor (MRA 4.0, 1.64 tp). Across R0-dev the answer shrinks toward the middle sizes (log slope 0.82): the median answer/truth ratio is 1.19 under 30 cm, 0.97 to 1.18 from 30 to 250 cm, and 0.70 at 250 cm and above. The v7 rows hold 762 of 4,892 answers under 30 cm and 41 under 10 cm; R0-dev holds 88 of 293 items under 30 cm.
5. **Units on dev-S1 (47 inch, 31 feet, 34 metre items).** The trace states the asked unit on 112 of 112 items, and its number equals the answer on 112 of 112. The conversion is right: all 11 explicit conversion statements are arithmetically correct, and 19 of 21 two-decimal inch answers equal an integer centimetre value divided by 2.54 (about 2.5% by chance). No step-200 item loses points to a wrong factor (0 of 112). Step 544 had five: four feet questions answered with the metre value, which score 0.7 to 1.0 at step 200, and the metre question `vsi590k_175250` answered with the centimetre value (found by the first wave). The unit costs points through the estimate instead: 16 of 47 inch answers are a round centimetre value converted (30, 80 and 270 cm three or four times each), and they score 46.9 against 69.0 for the other inch answers, which costs 5.67 dev-S1 tp (0.71 VSI). MRA by unit at step 200 is cm 73.2, inch 61.5, feet 71.3, metre 74.4.
6. **An evidence-bearing trace.** The ruling allows one evidence-bearing form in a direct row, a Relate line in words that compares the object with a co-visible object, and one in a head row, a box call whose response prints three edges. It forbids the frame-extent-plus-distance form in a direct row, because no response prints those numbers. No real training row carries the comparison form: 0 of 9,778 size targets and 0 of 760 sampled rows across 38 families state a size relation. Store v7 size rows carry the target's instance id and cited frame (8,201 of 9,778 rows) but no reference object and no box edges. The comparison form could reach at most 44 items (41 R0-dev, 12.42 tp; 3 dev-S1, 1.73 tp), and its effect is untested. The extent form could move nothing until a head prints both numbers, and the box form could move at most the 14 of 58 joined items where the box beats the direct answer (Table G). The box form exists in real unit rows, but the deployed head scores 50.7 against 73.1 for the direct answer on 58 joined dev-S1 items. **So the reading shows that, beyond the labels and the dev-S1 inch issue, only a better size head or a better prior can move this type.** The remaining loss is scatter (answers within 0.75 to 1.33 of the truth cost 11.27 dev-S1 tp and 10.99 R0 tp) and the R0-dev small-object bias.
7. **Label defects.** Two R0-dev truths are implausible on reading: `bd27924bbd5cdff459ad0fea` (cable box, 1,139 cm, answer 40) and `f1e39efcfa15c404beecbb56` (metal tray, 336 cm, answer 34). They cost 0.68 R0 tp (0.10 ReVSI). Four more truths are suspect: `caf221b9b1dd4aea59c3ce5d` (toilet paper, 59 cm; v7 range 10 to 55 cm, median 14), `ce209e8115bd37e2fd7f0bfd` (toilet paper, 7 cm, below a roll's width), `6752ad32d669179c5cad3302` (mouse, 5 cm) and `a3ad240810f07801c1b07852` (outlet, 28 cm; one v7 outlet row at 9 cm). They cost 1.33 R0 tp (0.19 ReVSI). dev-S1 has no implausible truth. Its scored `answer` and released `ground_truth` differ on 78 of 150 items by at most 6.1%, which moves the MRA by 0.26. The v7 labels are clean: 5 of 2,909 base rows in classes with ten or more rows lie beyond five times, or below a fifth of, their class median.

## 2. Evidence

**Table A. The ten largest classes per set (ties included), read at all three steps.** rho = Spearman correlation of answer with truth (cm) at 544 / 100 / 200; distinct = distinct answers in whole cm at step 200; modal = share of items on the commonest answer at step 200. Verdict rule: instance if rho >= 0.6 at all three steps; partly if rho >= 0.45 at step 200 and >= 0.2 at the other two, or >= 0.6 on two of three; prior only if one answer covers >= 60% of items, or rho < 0.45 at step 200 and < 0.5 at another step.

| Set / class | n | truth cm | v7 rows | rho 544 / 100 / 200 | distinct | modal | MRA 544 -> 200 | verdict |
|---|---:|---|---:|---|---:|---:|---|---|
| dev-S1 bed | 14 | 203-232 | 3 | -0.02 / -0.04 / -0.17 | 8 | 0.21 | 92 -> 94 | prior only |
| dev-S1 tv | 14 | 61-116 | 0 | 0.73 / 0.71 / 0.63 | 12 | 0.14 | 64 -> 60 | instance |
| dev-S1 table | 13 | 85-425 | 3 | 0.64 / 0.67 / 0.60 | 10 | 0.31 | 63 -> 55 | instance |
| dev-S1 refrigerator | 9 | 147-271 | 1 | 0.11 / 0.23 / 0.34 | 7 | 0.22 | 72 -> 71 | prior only |
| dev-S1 sofa | 7 | 80-204 | 6 | 0.43 / 0.61 / 0.59 | 5 | 0.43 | 71 -> 76 | partly |
| dev-S1 stove | 7 | 56-85 | 30 | 0.79 / -0.68 / 0.95 | 6 | 0.29 | 84 -> 93 | partly |
| dev-S1 bathtub | 7 | 162-192 | 15 | -0.07 / 0.25 / 0.25 | 4 | 0.43 | 86 -> 86 | prior only |
| dev-S1 desk | 6 | 139-254 | 71 | 0.49 / -0.06 / -0.09 | 4 | 0.33 | 43 -> 47 | prior only |
| dev-S1 toilet | 6 | 51-93 | 0 | 0.37 / 0.54 / -0.06 | 4 | 0.50 | 82 -> 78 | prior only |
| dev-S1 chair | 5 | 73-108 | 1 | 0.00 / -0.05 / 0.40 | 5 | 0.20 | 74 -> 80 | prior only |
| dev-S1 stool | 5 | 50-64 | 12 | 0.46 / -0.50 / 0.40 | 5 | 0.20 | 78 -> 72 | prior only |
| R0 cabinet | 9 | 42-126 | 64 | 0.36 / 0.23 / 0.48 | 5 | 0.22 | 46 -> 22 | partly |
| R0 door | 8 | 209-309 | 2 | 0.25 / one answer / one answer | 1 | 1.00 | 92 -> 92 | prior only |
| R0 windowsill | 6 | 96-707 | 137 | 0.70 / 0.60 / 0.66 | 6 | 0.17 | 38 -> 48 | instance |
| R0 keyboard | 6 | 27-51 | 0 | 0.34 / one answer / 0.39 | 2 | 0.83 | 57 -> 48 | prior only |
| R0 sink | 6 | 55-65 | 95 | 0.03 / 0.00 / 0.28 | 4 | 0.50 | 82 -> 90 | prior only |
| R0 telephone | 5 | 22-39 | 1 | -0.40 / -0.29 / 0.35 | 3 | 0.40 | 26 -> 58 | prior only |
| R0 window | 5 | 107-310 | 103 | 0.62 / 0.62 / 0.20 | 5 | 0.20 | 60 -> 50 | partly |
| R0 toilet | 5 | 47-89 | 0 | 0.16 / -0.05 / 0.36 | 4 | 0.40 | 68 -> 70 | prior only |
| R0 trash can | 4 | 36-79 | 0 | 1.00 / 1.00 / 1.00 | 4 | 0.25 | 95 -> 92 | instance |
| R0 picture | 4 | 15-59 | 36 | -0.32 / 0.60 / -0.40 | 4 | 0.25 | 18 -> 18 | prior only |

In a class whose truths span only about 7% either way (bed, sink, door), rho cannot detect instance use under the answer noise, so "prior only" there means that the answer carries no detectable instance signal. The verdicts rest on 4 to 14 items per class; treat a single class's verdict as weak and the pooled slope as the finding.

Excerpts for the fixed class number (verbatim step-200 traces):
- `b2324fbb7ee075fb75d3b00b`, "...the longest dimension (length, width, or height) of the door, measured in centimeters?" Truth 309; answer 210 (score 0.4). "Step 1: find the door, first seen in frame 1. / Step 2: the longest edge of the door is 210 cm." The seven other R0 doors (truth 209 to 221) get the same 210.
- `d8584f855ccfcfcfa4fac318`, keyboard. Truth 27; answer 45 (0.0; step 544 answered 20). "Step 1: find the keyboard, first seen in frame 28. / Step 2: the longest edge of the keyboard is 45 cm."
- `vsi590k_176034`, "What's the length in inches of the table's longest side?" Truth 64.8; answer 106.3 (0.0; step 544 answered 63.0 for 1.0). "Step 2: the longest edge is 106.3 inches." `vsi590k_266808` (truth 45.5) and `vsi590k_054222` (truth 167.3) get the same 106.3, and `vsi590k_266805` (truth 45.4) gets 106.30.

Excerpts for the unit-specific value (beds, step 200): `vsi590k_264363`, "What's the maximum length of the bed measured in feet?" Truth 6.8; answer 7.11. "Step 2: measure its 3D box; the longest edge is 7.11 feet." `vsi590k_261149` (truth 6.9) also gets 7.11. Against these, `vsi590k_053924`, "Provide the longest side's length for the bed in inches." Truth 83.8; answer 75.2. "Step 2: the longest edge of the bed is 75.2 inches." `vsi590k_177235` (truth 80.8) also gets 75.2.

**Table B. The same object asked twice in dev-S1** (pairs from one room and class whose truths agree within 10%).

| Step | Same-unit pairs: within 5% / within 10% of each other | Cross-unit pairs: within 5% / within 10% | Median answer ratio, same / cross |
|---|---|---|---|
| 544 | 9 / 11 of 13 | 7 / 7 of 13 | 1.034 / 1.047 |
| 100 | 9 / 11 of 13 | 7 / 9 of 13 | 1.009 / 1.030 |
| 200 | 9 / 11 of 13 | 5 / 9 of 13 | 1.016 / 1.062 |

**Table C. The 100 lowest-scoring step-200 items by primary cause.** Ties at score 0 (64 items) are broken by the largest |log(answer/truth)|. Each item takes the first cause it meets, in this order. Label: an implausible truth on reading (Q7). Unusual name (my judgment): a rare or ambiguous name whose answer fits another referent (tub answered 176 like a bathtub; panel, screen, piping, slide bar, subway tunnel, clothe, award, announcement speaker, smartboard, manual forklift, power extender, decoration). Inch round: an inch question whose implied centimetre value is a multiple of 10. Small too large: truth under 30 cm and answer above it. Large too small: truth 150 cm or more and answer below it. Wide middle: a class with five or more v7 rows and a quartile ratio of at least 1.8, an answer nearer the class median than the truth is, and a truth outside the class quartiles. Few rows: fewer than five v7 rows. Wrong unit: an answer that a unit factor rescues on reading; none qualifies at step 200.

| Cause | dev-S1 items; tp; VSI | R0-dev items; tp; ReVSI | Of these, few v7 rows |
|---|---|---|---:|
| Label (implausible truth) | 0 | 6; 2.01; 0.29 | 4 |
| Unusual or ambiguous name | 0 | 13; 4.16; 0.59 | 12 |
| Inch question, round cm value | 7; 4.40; 0.55 | 0 | 5 |
| Small object answered too large | 0 | 24; 7.95; 1.14 | 12 |
| Large object answered too small | 2; 1.27; 0.16 | 4; 1.06; 0.15 | 4 |
| Broad class answered near the middle | 0 | 6; 1.98; 0.28 | 0 |
| Few v7 rows, no other cause | 11; 6.67; 0.83 | 7; 2.15; 0.31 | 18 |
| Other overestimate | 7; 4.20; 0.53 | 10; 3.31; 0.47 | 0 |
| Other underestimate | 0 | 3; 0.82; 0.12 | 0 |
| Wrong unit or conversion | 0 | 0 | 0 |
| **Total** | **27; 16.53; 2.07** | **73; 23.45; 3.35** | 55 |

Excerpts (step 200, verbatim):
- Small too large: `3251cbd6acffd7288ec92ac2`, mirror. Truth 18; answer 156, the v7 mirror median exactly (30 rows). "Step 1: find the mirror, first seen in the bathroom. / Step 2: the longest edge of the mirror is 156 cm." `aeda2b45b6f2711f8457d09e`, picture: truth 15, answer 100, "the longest edge of the picture is 100 cm." `41833b9f52acf20d51fe13c2`, speaker: truth 26, answer 104.
- Unusual name: `b285772b5cf626a054618d27`, tub. Truth 33; answer 176. "Step 1: find the tub, first seen in the bathroom. / Step 2: the longest edge of the tub is 176 cm." `4f5eefa87789b64c07320809`, panel: truth 21, answer 122. `57df5c3c1927604424570d3a`, announcement speaker: truth 12, answer 64.
- Broad class at the middle: `bc35174838a9a5eb0af59d24`, cabinet. Truth 61; answer 176 (v7 cabinet median 152, quartiles 101 to 220). "Step 2: the longest edge of the cabinet is 176 cm." `a97acb82e56ff16172daf79d` (cabinet, truth 69) gets 176, and `398206ec6118667f01819166` (picture, truth 33) gets 74 (v7 picture median 73).
- Large too small: `vsi590k_175823`, "What's the measure of the heater's largest side in centimeters?" Truth 222.1; answer 66. `vsi590k_058303`, refrigerator: truth 167.9, answer 86; the one v7 "refrigerator" row says 90. `bd9a1d221d61c6bedaf4a0e2`, bedsheet: truth 200, answer 102.
- Few rows: `58bd7727a930c23baf999cd0`, toilet (0 v7 rows). Truth 89; answer 40. "Step 1: find the toilet, first seen in the bathroom. / Step 2: the longest edge of the toilet is 40 cm." `vsi590k_262256`, tv (0 rows): truth 65, answer 104. `vsi590k_175246`, paper bag in inches: truth 14.3, answer 28.34.

The v7 rows lack most of the commonest benchmark classes: tv 0 (television 8), toilet 0, keyboard 0, trash can 0 (trash bin 14), door 2, refrigerator 1 (fridge 8), chair 1, bed 3, table 3. Coverage does not predict the score, though. Classes with no v7 row score 65.5 on dev-S1 (31 items) and 57.6 on R0-dev (80), against 67.6 (50) and 55.9 (135) for classes with five or more rows. On rare classes the answer lands within 5% of one of the class's 1 to 3 v7 rows on 24 of 68 dev-S1 items and 31 of 70 R0-dev items, against 10.3 and 15.3 for a random class with a similar median. That pattern suggests memorized row values, but the truth lands as close on 22 and 21 of those items.

**Table D. Truth convention: dev truth / v7 class median (classes with five or more v7 rows; median over items).**

| Class (v7 rows, median cm) | dev-S1 items: truth / median; answer / median | R0-dev items: truth / median; answer / median |
|---|---|---|
| cabinet (64, 152) | - | 9: 0.45; 0.66 |
| sofa (6, 232) | 7: 0.71; 0.91 | 2: 1.13; 0.81 |
| window (103, 170) | 3: 0.81; 0.81 | 5: 0.83; 0.94 |
| desk (71, 139) | 6: 1.19; 1.30 | 1: 0.87; 0.92 |
| bathtub (15, 169) | 7: 0.97; 1.04 | - |
| stove (30, 64) | 7: 0.94; 0.96 | - |
| windowsill (137, 205) | - | 6: 1.03; 1.25 |
| sink (95, 62) | - | 6: 0.97; 0.97 |
| stool (12, 59) | 5: 0.88; 0.78 | - |
| dishwasher (14, 82) | 4: 1.09; 1.10 | 1: 1.03; 1.01 |
| picture (36, 73) | - | 4: 0.36; 0.99 |
| mirror (30, 156) | 2: 0.94; 0.74 | 1: 0.12; 1.00 |
| toilet paper (14, 14) | - | 3: 0.86; 0.93 |
| ceiling light (13, 70) | 3: 0.67; 0.94 | - |
| umbrella (12, 57) | - | 3: 0.60; 0.44 |
| shelf (64, 160) | - | 3: 0.79; 1.26 |
| towel (35, 79) | 2: 0.54; 0.83 | 1: 0.24; 0.39 |
| smoke detector (11, 10) | - | 3: 1.20; 1.00 |
| trash bin (14, 42) | 1: 1.57; 1.91 | 2: 0.79; 0.81 |
| soap dispenser (11, 30) | - | 3: 1.13; 1.03 |
| **All items with >= 1 v7 row** | 119: 0.997; 0.995 | 213: 0.938; 0.976 |
| **All items with >= 5 v7 rows** | 50: 0.962; 0.964 | 135: 0.911; 0.952 |

The answers do not sit on the class median either. Within 10% of the v7 median fall 20 of 50 dev-S1 and 51 of 135 R0-dev answers at step 200, against 21 and 57 at step 544. Classes with five or more v7 rows lost 5.4 MRA points on R0-dev from step 544 to step 200 (61.3 to 55.9), while classes with fewer rows gained (57.2 to 60.3). The answers did not move toward the v7 medians (median |log(answer/median)| went from 0.132 to 0.191), so the v7 prior does not explain the loss.

**Table E. R0-dev small objects (truth under 30 cm), step 200.** Rules are applied in order: score 0.9 or more is "fine"; then "prior too large" (class median 30 cm or more on three or more v7 rows, and the answer nearer that median than the truth); then "floor" (truth under 10 cm, answer 10 cm or more); then the direction of the error.

| Group | Items | MRA | tp; ReVSI | Median answer / median truth (cm) |
|---|---:|---:|---|---|
| Fine (score >= 0.9) | 22 | 95.9 | 0.31; 0.04 | 21 / 22 |
| Prior too large | 10 | 7.0 | 3.17; 0.45 | 68 / 21 |
| Floor | 5 | 4.0 | 1.64; 0.23 | 14 / 7 |
| Overestimate, no large prior | 36 | 31.9 | 8.36; 1.19 | 28 / 19 |
| Underestimate | 15 | 58.0 | 2.15; 0.31 | 19 / 24 |

Excerpts: for the floor, `6752ad32d669179c5cad3302`, mouse: truth 5, answer 17, "Step 2: the longest edge of the mouse is 17 cm."; `ce209e8115bd37e2fd7f0bfd`, toilet paper: truth 7, answer 13; `da0458c0efb8a3a5f1e0ea76`, phone charger: truth 7, answer 10. For overestimates without a large prior: `3303755d505788155595b198`, telephone: truth 22, answer 37, "Step 2: the longest edge is 37 cm." (the one v7 telephone row says 38); `d8584f855ccfcfcfa4fac318`, keyboard: truth 27, answer 45 (no v7 row); `e38c965e0fd3aefb064b88ce`, hairdryer: truth 18, answer 28, "Step 1: find the hairdryer, first seen in the left luggage."

**Table F. Units on dev-S1.**

| Unit | Items | MRA 544 / 100 / 200 | Stated unit = asked (200) | Median answer/truth (200) | Implied cm a multiple of 10 (200) |
|---|---:|---|---|---:|---:|
| cm | 38 | 72.6 / 70.0 / 73.2 | 38 of 38 | 0.986 | 0 of 38 |
| inch | 47 | 68.5 / 67.0 / 61.5 | 47 of 47 | 1.041 | 16 of 47 |
| feet | 31 | 60.3 / 66.8 / 71.3 | 31 of 31 | 1.030 | 2 of 31 |
| metre | 34 | 72.4 / 72.6 / 74.4 | 34 of 34 | 1.005 | 5 of 34 |

Excerpts:
- Correct conversion: `vsi590k_055098`, "What's the measure of the door's largest side in feet?" Truth 6.8; answer 6.89 (1.0). "Step 2: the longest edge is 2.10 m, which is 6.89 ft." `vsi590k_055211`: "the longest edge is 78 inches, which is 6.50 feet." (the arithmetic is right; truth 4.6, so the estimate is wrong). `vsi590k_056006`: "the longest edge of the window is 1.22 m, which is 4.00 ft." (truth 4.5, 0.8).
- Step 544's metre-for-feet errors: `vsi590k_055098` "the longest edge is 2.07 ft." (truth 6.8; 2.07 m = 6.79 ft); `vsi590k_056006` "1.22 feet" (truth 4.5); `vsi590k_057218` "1.29 ft" (truth 4.2). All three score 0 at step 544, and `vsi590k_176744` (0.11 ft for 0.4) is the fourth.
- Round centimetre values under inch questions: `vsi590k_177710`, heater: truth 52.2 in; answer 362.20 in (920 cm). "Step 2: the longest edge of the heater is 362.20 inches." The four 106.3 in tables above are the same pattern (270 cm), and `vsi590k_055440`, mirror, gets 31.50 in (80 cm) for a truth of 64.5.

**Table G. The three evidence-bearing forms against the ruling and the rows.**

| Form | What the ruling allows | Real training row, verbatim | The row source must supply | Store v7 size rows carry | Dev items it could move |
|---|---|---|---|---|---|
| Comparison with a co-visible object | A Relate line in words in a direct row (section 2.1). Section 2.2 prescribes "two Locate lines and a Relate line for relative size". The reference's size as a number is forbidden: "A length, area, angle or coordinate that no response printed never appears in a trace." | None: 0 of 9,778 size targets and 0 of 760 sampled rows. The nearest real Relate line is `object_rel_distance` row i=40 (`q0b9247b4d1f832b93b4f029d`): "Step 2: the nearest-to-farthest order from the backpack is: ceiling beam, then box, then jacket, then bag." | A reference instance visible in the cited frame, and the ground-truth boxes of both objects, so that the relation is true. | The target's instance id and cited frame (`retrace_a2.cited`, 8,201 of 9,778 rows) and a raster name (`scannetppv2__*.npz`); no reference and no box. | At most 44: 41 R0-dev (12.42 tp, 1.77 ReVSI) and 3 dev-S1 (1.73 tp, 0.22 VSI). These are answers stuck at the class prior, small objects answered more than 1.5 times too large, and broad classes answered near the middle. Effect untested. |
| Extent in the frame with the distance | Not in a direct row, because neither number is printed by a response. Allowed only as a Call, and no head in the files I read prints an image extent. | None. | A camera pose per frame, the 3D box and the mask extent. | 32 frame indices, timestamps and a raster name; no pose and no box. | None until a head prints both numbers. |
| Box call printing three edges | A Call line in head rows (Answer 6: about 2,000 rows, kept where the printed response is right). Converting a printed value is an allowed Step. | Unit rows, `packed.jsonl` line 62: `<ground obj="desk" mode="box">` ... "size 1.45 x 0.97 x 0.95 m". | The head's response on the training scene, and the ground truth to keep only right responses. | The ground truth (the answer) only; no response. | At most 14 of 58 joined dev-S1 items, where the box beats the direct answer. The expected net effect with the deployed head is a loss (50.7 against 73.1). |

Trace form: the v7 targets never state the length (0 of 9,778 think blocks; four Step 2 wordings such as "the question asks for the longest edge, in centimeters. I estimate it from the frames."). Step 200 nevertheless states it on 442 of 443 traces. It took the v7 Locate line ("first seen in ...") but kept the base form's stated length, and 20 of 150 dev-S1 traces still say "measure its 3D box".

## 3. For vehicle N (ranked)

1. **Add unit-varied size rows, conditional on VSI-Bench asking non-centimetre units (open point 2 in section 5).** Add about 2,000 rows (guess) to `object_size_estimation|r1g|rows_rebuild_d0_v1`: copies of base rows whose question asks inches, feet or metres in proportion to dev-S1's mix (31%, 21%, 23%), and whose answer is the ground-truth centimetre value converted and rounded to the dev precision. The trace keeps the v7 form with the unit word changed, for example: "<think>\nStep 1: find the bed, first seen in frame 4.\nStep 2: the question asks for the longest edge, in inches. I estimate it from the frames.\n</think>\n\n83.8". The change addresses the 112 non-centimetre dev-S1 items, and above all the 16 inch answers that collapse onto round centimetre values (5.67 tp). Expected effect: inch MRA rises toward the centimetre level, up to +3.7 tp (0.46 VSI) if it reached 73.2 (guess). The basis is that store v7 holds no non-centimetre size row (0 of 9,778) and that cross-unit answers for the same object disagree more than same-unit answers (Table B). The next read shows failure if inch MRA stays under 65, 12 or more of 47 inch answers remain round centimetre values, or cross-unit pairs still agree within 5% on 5 or fewer of 13.
2. **Add small-object rows (size rebalancing).** Paraphrase the 762 base rows whose answer is under 30 cm once more (about 760 rows), and add any rows under 10 cm the ScanNet++ source holds beyond the current 41. The change addresses the 88 R0-dev small items (15.63 tp), above all the 46 overshoots (11.53 tp). Expected effect: partial; the size of the gain is a guess. The basis is the 1.19 overshoot under 30 cm against 0.97 to 1.18 for 30 to 250 cm, and the share of small rows (16% of v7 against 30% of R0-dev items). The next read shows failure if the median ratio under 30 cm stays at 1.15 or more, or if the 30 to 60 cm band falls under 0.92 (overcorrection).
3. **Fix the dev labels; this is a scoring change, not a row change.** Review `bd27924bbd5cdff459ad0fea` and `f1e39efcfa15c404beecbb56` (0.68 R0 tp) and the four suspects (1.33 tp) against their scans, then correct or exclude them. The next read shows failure if the scan shows the label is right; the cable box might then be a long cable duct whose name is wrong.
4. **A gated experiment, not seal content: the comparison Relate line.** Rewrite about 2,000 size rows (guess) whose cited frame also shows a reference object, and compute the relation from the ground-truth boxes of both. Proposed trace (no real row carries this form): "<think>\nStep 1: find the mirror, first seen in frame 9.\nStep 2: the sink below it is also seen in frame 9; the mirror's longest edge is shorter than the sink's.\nStep 3: the question asks for the longest edge, in centimeters. I estimate it from the frames.\n</think>\n\n18". The change addresses the 44-item cohort (answer stuck at the class prior, a small object answered more than 1.5 times too large, or a broad class answered near its middle: 12.42 R0 tp, 1.73 dev-S1 tp). Expected effect: unknown. The relative-size dev type scores 90.0 at step 200, so such comparisons are usually right, but nothing shows that a comparison changes the stated number. The next read shows failure if the Relate lines are right on 85% or more of the cohort while the cohort's MRA moves by less than 3 points. The builder first has to confirm that the `scannetppv2__*.npz` rasters named in the rows hold every instance with its box.
5. **Box-head rows (ruling Answer 6; about 2,000 rows, head row only where the printed box is right): keep them for RL exploration only.** A real row form: `<ground obj="desk" mode="box">` / `<tool_response>` / "desk: frames 5,6,7,8,9,10,12,13,14,16,17 (best 12)" / "B1: f1 centre (-1.46, -0.82, -1.04) m" / "size 1.45 x 0.97 x 0.95 m" (unit rows, `packed.jsonl` line 62), which a size row would follow with "Step 2: the longest of its three edges is 1.45 m, which is 145 cm." The printed boxes in training rows agree with v7 class medians (357 boxes: median ratio 0.96, quartiles 0.76 to 1.12). The deployed head on dev does not: it scores 50.7 against 73.1 direct on 58 joined items and is better on 14 of 58 (deep_size audit). Expected effect: negative wherever the policy calls the head. The next read shows failure if the policy calls on more than 10% of size items and those items score below their direct answers.
6. **Drop the idea of class-coverage rows on this evidence.** Classes absent from v7 score no worse (Table C note), and classes covered by v7 lost points on R0-dev from step 544 to step 200. Coverage rows from ScanNet or ARKitScenes training scenes would need a source, and they have no demonstrated effect.

## 4. Refuted or corrected

- Record 10.9 says the class median "carries most of the answer". The level comes from the class, but the answer is not the class median: only 20 of 50 dev-S1 and 51 of 135 R0-dev answers lie within 10% of it, and within a class the answer moves by about 0.6 of the truth's log deviation (Q1).
- deep_size's "classes absent from the sample score no worse (70.6 against 68.6)" used a 3,000-row sample. With all 9,778 rows, dev-S1 classes with no v7 row score 65.5 (31 items), below the 1-to-4-row classes (72.5, 69 items) and close to the five-or-more-row classes (67.6, 50). The conclusion that coverage does not predict the score stands.
- First-wave `size` (section 4) names one step-544 unit error (centimetres for metres, `vsi590k_175250`). Step 544 also answered four feet questions with the metre value. Those four items gain 3.4 in summed score by step 200, which is the whole net feet gain from 60.3 to 71.3 (3.4 over 31 items).
- The brief and the record describe every trace as two lines ending "the longest edge of the X is N cm". At step 200, 12 of 150 dev-S1 traces add a conversion clause and 20 keep "measure its 3D box". The v7 rows never state the length, so the step-200 form is a hybrid of the v7 Locate line and the base form's stated length.
- Confirmed as stated: doors get 210 on 8 of 8 (7 of 8 at step 544), keyboards 45 on 5 of 6, small-object MRA is 48.0 on 88 items, v7 size rows ask centimetres only (9,778 of 9,778), and the cable box and metal tray truths are implausible.

## 5. Not established, and what would settle it

1. Whether the instance signal comes from the object's pixels or from scene context such as room type or scan. A video swap would settle it: ask the same dev-S1 question over another room's frames (dev items only).
2. Whether VSI-Bench asks units other than centimetres. dev-S1's unit mix comes from VSI-590K phrasing, and R0-dev asks centimetres only. The public task description would settle it without reading items. If the benchmark asks centimetres only, change 1 fixes a proxy artifact worth nothing on the benchmark.
3. Why inch answers collapse onto round centimetre values: R1's feet/inch distance rows, the base, or the question wording. The round-value share (15 of 47 at step 544, 17 at step 100, 16 at step 200) says the habit predates R1, but the fixed 106.3 for tables is new at step 200. Inch answers at legs D0 and H1-1 would settle it.
4. Whether the rasters named in the v7 rows hold every instance, which change 4 needs. Opening one raster would settle it.
5. Why the v7-covered classes lost 5.4 MRA on R0-dev from step 544 to step 200. Per-class reads at later steps would settle it.
6. R0-dev's source dataset: its room ids are hashed, so the convention test cannot be split by dataset there.
7. The box-head join pairs items by object name within a room, so its 50.7 may mix instances. An instance-id join would settle it.
