**1. Question and answer**

1. **Which fields predict a wrong value?** Small printed magnitudes predict numeric errors: step-200 AUC is **0.863 for displacement** and **0.858 for rotation**, each on 150 items. Direction signals remain uncertain because only 8 of 150 answers are wrong.
2. **Is a better second measurement available today?** Sometimes, but no tested rule reliably selects it. The saved student pose head improves 17 of 150 displacement, 8 of 150 rotation, and 5 of 150 direction answers at step 200, while harming 102, 115, and 28, respectively.
3. **What would doubt gain?** For step-200 printed displacement below 0.5 m, averaging checkpoints gains **0.00 type points**; switching to the student pose head loses **13.00 points**. Replacing those flagged values with truth would gain 10.67 points.
4. **Could the student learn the check from its rows?** Ground-truth responses teach neither measurement errors nor successful repairs. The tested warning signs also occur with correct responses; no warning uniquely identifies an error.
5. **Verdict: worth it after the camera head improves and supplies a useful alternate measurement.** The deciding numbers are **0.863 detection AUC** and **−13.00 type points from the available student-head replacement** on the small-displacement flag. Detection works substantially better than repair.

**2. Evidence**

All results use 150 dev-S1 items per type per step. D denotes displacement, R rotation, and M movement direction. Numeric “wrong” means relative error strictly above 0.25 or 0.50; nonzero predictions against zero truth count as wrong at both thresholds. Scores are MRA for D/R and accuracy for M, expressed out of 100.

Sources: [san_kit.py](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py:169), its wrapped `score_r5.load`, and the raw journals. With `P=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route`, journals are `P/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` at step 200 and `P/out3s/bases/b1/work/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` at step 544. Labels and timing come from their corresponding `devs1_routed.json` manifests. I read the requested [analysis record](/data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md:300) and both named first-wave camera reports.

| Type | Rooms | Score, 544 → 200; n=150 each | Wrong >0.25, 544 → 200 | Wrong >0.50, 544 → 200 |
|---|---:|---:|---:|---:|
| D | 36 | 82.33 → 81.87 | 21/150 → 20/150 | 6/150 → 7/150 |
| R | 34 | 75.60 → 76.27 | 33/150 → 33/150 | 21/150 → 20/150 |
| M | 36 | 94.67 → 94.67 | 8/150 → 8/150 | 8/150 → 8/150 |

Raw outputs contain `heads.pose9`, `heads.gravity`, and `scale` on 450 of 450 items at each step. Call records contain the queried indices `i,j`; none of 450 records contains confidence or inlier counts. **The saved pose array belongs to the student head, whereas the printed measurement uses tower geometry.** I reconstructed the student alternative with the existing `OwnGeometry.move_text/turn_text` functions, without running a model.

Elapsed seconds are recoverable on 450 of 450 items per step: `(source_frame_indices[b−1]−source_frame_indices[a−1])/fps`. They are not inferable from the question’s two display indices alone. Runtime `seconds` measures execution time and was excluded.

The following AUCs use rank comparisons with ties worth one-half and percentile intervals from **1,000 room-bootstrap resamples**. Lower gap, elapsed time, magnitude, and student baseline predict greater risk; other signals use higher values. “Ambiguity” is `min(|dx|,|dz|)/max(|dx|,|dz|)`; “vertical” is `|dy|/‖delta‖`. “Disagreement” compares the student alternative with the printed result. Room risk is a **retrospective**, leave-one-item-out, smoothed room error rate; it requires labels and is not a deployable cue.

Each AUC cell gives **>0.25 / >0.50**, with 95% intervals. M has identical labels at both thresholds, so its AUC appears once. Every AUC uses 150 items. Median score cells give **low/high scores (low/high item counts, totaling 150)**; low includes the median.

| Type/signal | AUC, step 544 | AUC, step 200 | Median, 544 → 200 | Scores below/above median, 544 | Scores below/above median, 200 |
|---|---|---|---|---|---|
| D gap | .703 [.561,.837] / .658 [.288,.939] | .696 [.552,.839] / .687 [.364,.919] | 8 → 8 | 77.82/87.22 (78/72) | 77.44/86.67 (78/72) |
| D seconds | .632 [.483,.779] / .537 [.113,.879] | .632 [.473,.789] / .564 [.204,.856] | 26.44 → 26.44 | 82.40/82.27 (75/75) | 82.40/81.33 (75/75) |
| D magnitude | .850 [.783,.911] / .771 [.702,.848] | .863 [.801,.915] / .775 [.702,.856] | .955 → .965 m | 71.73/92.93 (75/75) | 71.87/91.87 (75/75) |
| D scale | .464 [.348,.573] / .572 [.315,.786] | .433 [.309,.551] / .628 [.411,.841] | 2.496 → 2.534 | 82.47/82.19 (77/73) | 81.69/82.05 (77/73) |
| D student baseline | .736 [.623,.837] / .594 [.328,.856] | .771 [.678,.861] / .664 [.473,.854] | 1.165 → 1.460 m | 75.07/89.60 (75/75) | 74.67/89.07 (75/75) |
| D first frame | .473 [.453,.491] / .476 [.458,.492] | .473 [.451,.492] / .476 [.455,.492] | 0 → 0 | 81.82/92.86 (143/7) | 81.19/95.71 (143/7) |
| D last frame | .461 [.438,.484] / .465 [.444,.485] | .462 [.438,.484] / .465 [.443,.485] | 0 → 0 | 81.50/94.00 (140/10) | 81.07/93.00 (140/10) |
| D ambiguity | .522 [.384,.661] / .466 [.212,.679] | .520 [.372,.671] / .514 [.298,.701] | .455 → .458 | 82.76/81.89 (76/74) | 83.07/80.67 (75/75) |
| D vertical | .694 [.574,.805] / .726 [.618,.885] | .672 [.559,.785] / .671 [.474,.830] | .0793 → .0799 | 88.93/75.73 (75/75) | 86.53/77.20 (75/75) |
| D disagreement | .721 [.575,.860] / .784 [.622,1.000] | .757 [.616,.860] / .768 [.479,.950] | .236 → .239 | 87.33/77.33 (75/75) | 87.60/76.13 (75/75) |
| D room risk | .478 [.282,.631] / .723 [.487,.908] | .484 [.284,.649] / .649 [.353,.854] | .167 → .167 | 84.35/79.69 (85/65) | 84.24/78.10 (92/58) |
| R gap | .493 [.376,.592] / .532 [.405,.661] | .493 [.383,.606] / .488 [.363,.612] | 8 → 8 | 74.42/76.85 (77/73) | 75.19/77.40 (77/73) |
| R seconds | .433 [.322,.564] / .509 [.374,.666] | .433 [.314,.566] / .451 [.325,.598] | 28.125 → 28.125 | 76.67/74.53 (75/75) | 77.33/75.20 (75/75) |
| R magnitude | .856 [.769,.944] / .849 [.725,.955] | .858 [.772,.940] / .843 [.716,.950] | 37 → 37.5° | 59.20/92.00 (75/75) | 60.13/92.40 (75/75) |
| R scale | .580 [.424,.697] / .526 [.354,.673] | .578 [.432,.696] / .565 [.398,.733] | 2.540 → 2.560 | 80.66/70.41 (76/74) | 81.45/70.95 (76/74) |
| R student baseline | .386 [.272,.518] / .436 [.312,.565] | .403 [.289,.535] / .401 [.272,.540] | 1.400 → 1.478 m | 77.87/73.33 (75/75) | 80.13/72.40 (75/75) |
| R first frame | .522 [.468,.597] / .505 [.443,.599] | .522 [.469,.591] / .508 [.443,.605] | 0 → 0 | 76.06/70.77 (137/13) | 76.64/72.31 (137/13) |
| R last frame | .474 [.458,.491] / .477 [.462,.492] | .474 [.458,.491] / .477 [.463,.492] | 0 → 0 | 74.58/100.00 (144/6) | 75.28/100.00 (144/6) |
| R disagreement | .839 [.763,.921] / .852 [.763,.935] | .806 [.697,.905] / .823 [.673,.938] | .358 → .353 | 94.00/57.20 (75/75) | 92.00/60.53 (75/75) |
| R room risk | .488 [.306,.608] / .498 [.334,.623] | .488 [.305,.618] / .513 [.349,.650] | .25 → .25 | 72.56/80.17 (90/60) | 73.00/81.17 (90/60) |
| M gap | .591 [.424,.837] | .591 [.425,.835] | 12 → 12 | 92.77/97.01 (83/67) | 92.77/97.01 (83/67) |
| M seconds | .340 [.120,.696] | .340 [.123,.710] | 45.813 → 45.813 | 94.67/94.67 (75/75) | 94.67/94.67 (75/75) |
| M magnitude | .410 [.155,.846] | .412 [.150,.815] | 1.995 → 2.020 m | 96.00/93.33 (75/75) | 96.00/93.33 (75/75) |
| M scale | .769 [.487,.926] | .769 [.484,.931] | 2.660 → 2.671 | 98.72/90.28 (78/72) | 98.72/90.28 (78/72) |
| M student baseline | .496 [.220,.800] | .419 [.177,.805] | 1.790 → 2.039 m | 96.00/93.33 (75/75) | 94.67/94.67 (75/75) |
| M first frame | .461 [.436,.480] | .461 [.438,.482] | 0 → 0 | 94.24/100.00 (139/11) | 94.24/100.00 (139/11) |
| M last frame | .520 [.440,.630] | .520 [.439,.632] | 0 → 0 | 94.89/92.31 (137/13) | 94.89/92.31 (137/13) |
| M ambiguity | .719 [.467,.935] | .716 [.464,.937] | .374 → .381 | 97.33/92.00 (75/75) | 97.33/92.00 (75/75) |
| M vertical | .660 [.476,.891] | .676 [.510,.887] | .0475 → .0456 | 98.67/90.67 (75/75) | 98.67/90.67 (75/75) |
| M disagreement | .641 [.386,.900] | .776 [.539,.924] | 0 → 0 | 96.52/88.57 (115/35) | 98.28/82.35 (116/34) |
| M room risk | .770 [.426,.963] | .770 [.432,.953] | .125 → .125 | 96.43/92.42 (84/66) | 96.43/92.42 (84/66) |

A trace can truthfully state frame gap, endpoint inclusion, printed magnitude, horizontal ambiguity, and vertical fraction. Seconds, scale, student baseline, student disagreement, and labeled room history require additional inputs or response fields.

I fitted L2-regularized logistic rules on half the rooms and evaluated the other half over 20 splits. Features were log-transformed and standardized using training rooms only; room identities and room-label statistics were excluded. “Text” uses only question/response-visible signals; “all” adds seconds, scale, student baseline, and disagreement. Intervals below are the **range across splits**, not confidence intervals.

| Type/step | Text AUC >.25, mean [range] | All AUC >.25, mean [range] | Text / all AUC >.50, mean | Gain from switching predicted-wrong items to student head, text / all |
|---|---|---|---|---|
| D/544 | .809 [.642,.916] | .819 [.628,.908] | .569 / .609 | −1.72 / −4.06 points |
| D/200 | .812 [.665,.908] | .813 [.641,.919] | .630 / .672 | −1.16 / −3.34 points |
| R/544 | .856 [.785,.941] | .869 [.765,.918] | .858 / .830 | −1.91 / −3.17 points |
| R/200 | .859 [.787,.942] | .868 [.773,.911] | .860 / .846 | −2.47 / −4.48 points |
| M/544 | .694 [.377,.933] | .736 [.480,.892] | Same classification target | 0.00 / −0.54 points |
| M/200 | .719 [.395,1.000] | .845 [.423,.987] | Same classification target | 0.00 / +0.01 points |

These gains average held-out scores over 20 splits, with a 0.5 probability threshold. A separate rule trained directly to predict **student-head improvement** produced step-200 gains of −0.93 D, 0.00 R, and −0.33 M points using all signals. Thus, detecting a bad tower value does not establish that the student value is better.

The next table prices every median flag and the requested explicit thresholds. Median flags select the lower half for gap/seconds/magnitude/baseline and the upper half otherwise. Each paired cell is **544 → 200**. F counts flagged items out of 150; W25/W50 count truly wrong items among F. All replacement scores use the complete 150-item type. O uses the saved student head; A averages checkpoints; T substitutes truth; P uses the other items’ room median. L gives gross points lost on flagged **right-at-.25** items under O, then A. P is inapplicable to direction.

| Type/flag | F, of 150 | W25 | W50 | Score O | Score A | Score T | Score P | Loss L: O; A |
|---|---|---|---|---|---|---|---|---|
| D gap median | 78→78 | 16→15 | 4→5 | 62.13→63.20 | 82.40→82.13 | 93.87→93.60 | 52.07→51.67 | 19.00→18.27; .20→.20 |
| D seconds median | 75→75 | 12→11 | 3→4 | 62.00→62.93 | 82.40→81.93 | 91.13→90.67 | 51.87→51.13 | 19.93→19.07; .20→.20 |
| D magnitude median | 75→75 | 21→20 | 6→7 | 61.07→60.53 | 82.33→81.80 | 96.47→95.93 | 53.80→53.07 | 19.47→21.87; .27→.27 |
| D scale median | 73→73 | 9→8 | 4→5 | 65.40→66.73 | 82.40→82.00 | 91.00→90.60 | 51.67→51.07 | 16.47→15.73; .07→.07 |
| D baseline median | 75→75 | 18→17 | 4→6 | 61.67→63.60 | 82.27→81.93 | 94.80→94.53 | 53.73→53.53 | 19.07→19.33; .33→.27 |
| D first frame | 7→7 | 0→0 | 0→0 | 80.53→80.33 | 82.40→81.80 | 82.67→82.07 | 79.33→78.67 | 1.87→1.67; .00→.07 |
| D last frame | 10→10 | 0→0 | 0→0 | 78.93→78.93 | 82.27→81.87 | 82.73→82.33 | 77.93→77.47 | 3.47→3.00; .07→.00 |
| D ambiguity median | 74→75 | 11→11 | 2→4 | 66.60→67.27 | 82.33→81.93 | 91.27→91.53 | 52.80→52.20 | 15.20→15.73; .07→.13 |
| D vertical median | 75→75 | 17→15 | 5→5 | 61.93→61.33 | 82.40→81.67 | 94.47→93.27 | 52.20→51.00 | 19.27→21.33; .20→.27 |
| D disagreement median | 75→75 | 14→14 | 5→6 | 50.87→52.60 | 82.33→81.93 | 93.67→93.80 | 53.60→52.47 | 29.60→28.80; .13→.27 |
| D room-risk median | 65→58 | 9→9 | 4→4 | 68.20→71.33 | 82.33→81.87 | 91.13→90.33 | 56.13→60.00 | 13.93→11.07; .13→.20 |
| D gap 1 | 12→12 | 5→5 | 2→2 | 79.47→79.40 | 82.40→81.80 | 85.67→85.07 | 77.73→77.07 | 2.87→2.67; .00→.07 |
| D gap 2–4 | 29→29 | 6→5 | 1→2 | 75.00→75.67 | 82.33→81.93 | 86.53→86.13 | 70.40→69.87 | 6.67→6.27; .13→.13 |
| D gap ≥5 | 109→109 | 10→10 | 3→3 | 57.27→58.00 | 82.13→82.20 | 92.47→92.53 | 38.20→38.07 | 24.67→24.93; .27→.07 |
| D printed <0.5 m | 47→46 | 16→16 | 5→6 | 67.33→68.87 | 82.40→81.87 | 93.13→92.53 | 63.47→63.33 | 13.33→13.40; .13→.20 |
| R gap median | 77→77 | 17→17 | 12→10 | 55.93→56.73 | 76.40→76.67 | 88.73→89.00 | 41.80→42.20 | 18.93→19.47; .13→.27 |
| R seconds median | 75→75 | 14→14 | 10→8 | 58.93→57.13 | 76.33→76.67 | 87.27→87.60 | 42.07→42.47 | 16.67→19.33; .13→.27 |
| R magnitude median | 75→75 | 28→28 | 18→17 | 55.27→56.13 | 76.47→76.67 | 96.00→96.20 | 50.53→50.67 | 20.40→19.67; .07→.33 |
| R scale median | 74→74 | 20→20 | 11→12 | 57.13→55.27 | 75.60→76.00 | 90.20→90.60 | 45.40→45.87 | 17.67→20.93; .07→.33 |
| R baseline median | 75→75 | 14→13 | 10→8 | 59.80→56.00 | 76.40→76.73 | 86.67→86.20 | 40.53→39.80 | 16.33→20.00; .13→.20 |
| R first frame | 13→13 | 4→4 | 2→2 | 74.40→74.67 | 76.33→76.87 | 78.13→78.67 | 70.53→71.07 | .93→1.60; .00→.07 |
| R last frame | 6→6 | 0→0 | 0→0 | 74.07→73.40 | 75.60→76.27 | 75.60→76.27 | 71.60→72.27 | 1.53→2.87; .00→.00 |
| R disagreement median | 75→75 | 29→28 | 20→18 | 50.47→48.07 | 76.53→76.67 | 97.00→96.00 | 50.20→49.13 | 25.20→27.27; .07→.33 |
| R room-risk median | 60→60 | 10→10 | 6→6 | 60.93→59.33 | 75.87→76.13 | 83.53→83.80 | 46.87→47.13 | 14.13→16.53; .00→.20 |
| R gap 1 | 22→22 | 6→6 | 4→3 | 69.40→71.07 | 76.33→76.67 | 80.33→80.67 | 66.60→67.00 | 6.20→5.67; .07→.07 |
| R gap 2–4 | 28→28 | 4→4 | 3→2 | 67.80→68.00 | 75.60→76.40 | 79.07→79.87 | 62.73→63.53 | 7.53→7.93; .07→.07 |
| R gap ≥5 | 100→100 | 23→23 | 14→15 | 56.87→50.73 | 75.73→75.93 | 91.80→92.00 | 29.87→30.07 | 19.00→25.00; .00→.40 |
| R printed magnitude <20° | 60→59 | 27→27 | 18→17 | 59.33→61.13 | 76.47→76.80 | 95.13→95.40 | 58.47→59.27 | 16.67→14.93; .07→.20 |
| M gap median | 83→83 | 6→6 | 6→6 | 87.33→87.33 | 94.67→94.67 | 98.67→98.67 | — | 8.67→9.33; 0→0 |
| M seconds median | 75→75 | 4→4 | 4→4 | 88.00→88.00 | 94.67→94.67 | 97.33→97.33 | — | 7.33→7.33; 0→0 |
| M magnitude median | 75→75 | 3→3 | 3→3 | 84.67→83.33 | 94.67→94.67 | 96.67→96.67 | — | 10.67→11.33; 0→0 |
| M scale median | 72→72 | 7→7 | 7→7 | 84.00→90.67 | 94.67→94.67 | 99.33→99.33 | — | 11.33→7.33; 0→0 |
| M baseline median | 75→75 | 3→4 | 3→4 | 84.00→86.00 | 94.67→94.67 | 96.67→97.33 | — | 11.33→9.33; 0→0 |
| M first frame | 11→11 | 0→0 | 0→0 | 94.00→94.00 | 94.67→94.67 | 94.67→94.67 | — | .67→.67; 0→0 |
| M last frame | 13→13 | 1→1 | 1→1 | 92.67→93.33 | 94.67→94.67 | 95.33→95.33 | — | 2.00→2.00; 0→0 |
| M ambiguity median | 75→75 | 6→6 | 6→6 | 83.33→85.33 | 94.67→94.67 | 98.67→98.67 | — | 12.00→12.00; 0→0 |
| M vertical median | 75→75 | 7→7 | 7→7 | 86.67→85.33 | 94.67→94.67 | 99.33→99.33 | — | 9.33→12.00; 0→0 |
| M disagreement | 35→34 | 4→6 | 4→6 | 75.33→79.33 | 94.67→94.67 | 97.33→98.67 | — | 20.67→18.67; 0→0 |
| M room-risk median | 66→66 | 5→5 | 5→5 | 85.33→87.33 | 94.67→94.67 | 98.00→98.00 | — | 10.00→10.00; 0→0 |
| M gap 1 | 1→1 | 0→0 | 0→0 | 94.67→94.67 | 94.67→94.67 | 94.67→94.67 | — | 0→0; 0→0 |
| M gap 2–4 | 23→23 | 1→1 | 1→1 | 92.00→90.00 | 94.67→94.67 | 95.33→95.33 | — | 2.67→4.67; 0→0 |
| M gap ≥5 | 126→126 | 7→7 | 7→7 | 78.00→84.00 | 94.67→94.67 | 99.33→99.33 | — | 18.00→14.00; 0→0 |
| M ambiguity ≥2/3 | 27→27 | 5→5 | 5→5 | 90.67→92.67 | 94.67→94.67 | 98.00→98.00 | — | 4.67→4.00; 0→0 |

For the requested gap bins, original scores at steps 544→200 are: D, **58.33→60.00 (12 items), 78.28→77.93 (29), 86.06→85.32 (109)**; R, **67.73→70.00 (22), 81.43→80.71 (28), 75.70→76.40 (100)**; M, **100→100 (1), 95.65→95.65 (23), 94.44→94.44 (126)**.

For every D/M replacement score above, the VSTI-equivalent gain is `(replacement−original)/5`; divide loss L by five too. At step 200, the D <0.5 m flag gives **−2.60 VSTI points with O, 0.00 with A, and +2.13 with truth**. The M ambiguity flag gives **−0.40, 0.00, and +0.67**, respectively. These are arithmetic equivalents, not measured VSTI improvements. Rotation has no VSTI category.

| Second measurement comparison; 150 items per type | D | R | M |
|---|---:|---:|---:|
| Other checkpoint closer: from 200 / from 544 | 70/150 / 42/150 | 24/150 / 34/150 | 0/150 / 0/150 |
| Equal error between checkpoints | 38/150 | 92/150 | 150/150 |
| Better-checkpoint oracle score | 82.87 | 76.80 | 94.67 |
| Mean of checkpoints score | 82.20 | 76.47 | 94.67 |
| Student-head score, 544 → 200 | 47.07→49.33 | 42.87→37.27 | 75.33→79.33 |
| Student beats printed score, 544 → 200 | 12/150→17/150 | 6/150→8/150 | 2/150→5/150 |
| Student harms printed score, 544 → 200 | 108/150→102/150 | 101/150→115/150 | 31/150→28/150 |
| Oracle over printed, other checkpoint, and student, 544 → 200 | 84.13→85.80 | 78.60→78.33 | 96.00→98.00 |

Checkpoint averaging for M averages displacement vectors and then applies the option rule. Oracle scores require truth and are ceilings, not usable selectors. The saved student alternative is computationally available, but the current call does not expose a choice of head. Moreover, [the reader](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s/A/src/b/e2e_reader/generate.py:31) builds its geometry once and reuses it: repeating the identical call is not a new measurement.

**Consistency:** Neither numeric type contains a complete, capture-matched three-edge chain at either step. Combining D and M produces two apparent room/display-index triangles, but both mix captures; neither is valid. Of three apparent cross-type sibling pairs, only one D–M pair shares the capture and source frames; it has identical move responses and a correct direction answer at both steps. **None of 8 wrong direction items has a valid sibling measurement.** Displacement lengths also cannot generally be added; valid checks require triangle inequalities or vectors transformed into a common frame.

**Prior:** On the small-displacement flag, the leave-one-out room median is available for 46/47 flagged items at 544 and 45/46 at 200, and is closer on only 2/47 and 1/46. For small rotation it is available on 58/60 and 57/59, and closer on 5/60 and 5/59. Store v7’s [family index](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json) contains no routed camera-motion family. Primary-key samples from its three camera-named families confirm `camera_obj_rel_dist_v{1,2,3}|vsti_rel_v4|None`; these cannot supply a camera-motion-by-gap prior.

**Training support:** Small values are legitimate: the truth itself falls below 0.5 m on 47/150 displacement items and below 20° on 59/150 rotation items. Gap and endpoint signals are unchanged when a response is replaced by truth. No tested question/response warning is logically forbidden in a ground-truth-valued row. What those rows omit is the response–answer mismatch: it occurs above the requested error threshold on **62/450 items at 544 and 61/450 at 200**, including wrong direction options. Detecting that mismatch during training requires actual head responses paired with the target; the student cannot access the target at inference.

**3. What this changes for vehicle N**

1. **Add zero production “doubt, repeat the same call” rows now.** Keep the existing camera call and option-mapping behavior. Identical retries reuse geometry, and the existing traces already place and use their call correctly on 450/450 items per step. No dev repair from that wording is established.
2. **After an alternate measurement improves, test 600 diagnostic rows—200 per camera type—before admitting a production family.** This count is a proposed pilot budget, not a measured sample-size requirement. Proposed family names are `camera_displacement|routing|doubt_real_v1`, `camera_rotation|routing|doubt_real_v1`, and `camera_movement_direction|routing|doubt_real_v1`; they are new identifiers, not verified existing tuples. Use actual tower and student responses on **600/600 pilot rows**, retaining correct first measurements as well as errors. Current student alternatives provide improvement ceilings on 17/150 D, 8/150 R, and 5/150 M items at step 200; those counts do not establish a learnable selector.
3. **Make the warning truthful and require evidence before replacing the answer.** A diagnostic example is: “The tool reports 0.35 m. Small reported displacements are less reliable, but that does not show this value is wrong. Repeating this call uses the same poses. I use the reported distance, 0.35 m.” This wording alone fixes 0 demonstrated items and should not be added merely to lengthen traces. A repair version needs an exposed alternate response and a held-out gain after false-positive losses.

Producing the pilot requires the deployed G3T pose path, its scale/depth path and student gravity, plus the student pose/gravity outputs on the **same training captures and sampled frames**. Save capture identity, source indices, fps, both formatted responses, and ground truth. The necessary fraction of the complete training pool is **not established**; 100% real responses applies to the proposed diagnostic subset, not to an inferred global quota. Failure at the next read means repeated identical calls, answers changed without an independent measurement, or nonpositive held-out score gain despite higher error-detection AUC.

**4. Refuted**

- “18 adjacent-frame displacement items score about 64” conflates gaps one and two. Strict adjacency covers **12/150 items**, scoring **58.33→60.00**. Gaps at most two cover **18/150**, scoring **63.89→65.00**.
- Room plus display-frame numbers do not identify a common camera trajectory: **2/2 apparent mixed-type triangles** and **2/3 apparent sibling pairs** fail capture matching.
- The routed loader returns the **G3T/tower arm**, as the first-wave reports state. These scores are not independently verified B2048 results. I found no contradiction of their call-placement or response-following findings.

**5. Not established**

No return demonstrates a successful fresh measurement after doubt. A supported decision requires capture-matched alternate measurements, a response-visible selector tested on unseen rooms, and positive score gain after damage to correct answers. The eight direction errors and absence of valid chains also prevent a strong conclusion about consistency-based recovery. All recommendations above concern the supplied dev data; no official benchmark item was used.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the displacement detection AUC, flagged replacement scores, and checkpoint oracle.

```python
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import sys, ast, itertools, math
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
types = ["camera_displacement", "camera_rotation", "camera_movement_direction"]
data = {s: K.routed(s, types=types) for s in (544, 200)}
S = K._scorer()
path = S.O.parent / "out3/A4/src/tree/student_pilot/carrier_c1_routing.py"
with open(path) as f:
    tree = ast.parse("".join(itertools.islice(f, 81, 303)))
names = {"RenderError", "r2", "f2", "s2", "wrap", "r8", "level_basis", "OwnGeometry"}
rotation_from_xyzw = S.scorers.rotation_from_xyzw
FLIP = np.diag([1., -1., 1.])
nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
         and n.name in names]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"))
def auc(x, y, w):
    order = np.argsort(x)
    x, y, w = x[order], y[order], w[order]
    _, starts = np.unique(x, return_index=True)
    p, n = np.add.reduceat(w*y, starts), np.add.reduceat(w*(~y), starts)
    if not p.sum() or not n.sum():
        return np.nan
    return (p*(np.cumsum(n)-n+.5*n)).sum()/(p.sum()*n.sum())
rng = np.random.default_rng(17)
for step in (544, 200):
    args = (S.BASE/"b1/work/ret", S.BASE/"b1", 0, 544, "null_argmax")
    if step == 200:
        args = (S.O.parent/"out3/A4/ret", S.O/"A", 0, 200, "candidates_argmax")
    raw, items, _, _ = S.load(*args)
    ds = [d for d in data[step] if d["type"] == types[0]]
    old = {d["id"]: d for d in data[744-step]}
    p = np.array([float(d["answer"]) for d in ds])
    g = np.array([float(d["gt"]) for d in ds])
    y, flag = abs(p-g)/abs(g) > .25, p < .5
    scores = np.array([d["score"] for d in ds])
    own, mean = [], []
    for d in ds:
        o = raw[d["id"]]["output"]
        geo = OwnGeometry(o["heads"]["pose9"], o["heads"]["gravity"], None)
        c = S.scorers.records(o)[0]
        text = geo.move_text(c["i"], c["j"])
        v = S.scorers.printed({"call": c["call"], "response": text})["distance"]
        task = dict(items[d["id"]], ground_truth=d["gt"])
        def score(v):
            return S.scorers.benchmark({"text": "</think>\n"+str(v),
                                       "finish": "eos"}, task)["score"]
        own.append(score(v))
        mean.append(score((float(d["answer"])+float(old[d["id"]]["answer"]))/2))
    rooms, ri = np.unique([d["room"] for d in ds], return_inverse=True)
    w = rng.multinomial(len(rooms), np.ones(len(rooms))/len(rooms), 1000)[:, ri]
    ci = np.nanquantile([auc(-p, y, z) for z in w], [.025, .975])
    oracle = np.maximum(scores, [old[d["id"]]["score"] for d in ds])
    print(step, "n", len(ds), "small/wrong", flag.sum(), (flag & y).sum(),
          "AUC", round(auc(-p, y, np.ones(len(ds))), 3), "CI", ci.round(3),
          "base/own_on_small/mean_on_small/checkpoint_oracle",
          np.round([100*scores.mean(), 100*np.where(flag, own, scores).mean(),
                    100*np.where(flag, mean, scores).mean(), 100*oracle.mean()], 3))
```