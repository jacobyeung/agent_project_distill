**1. Question and answer**

1. **Can the response predict a wrong gap?** Yes, probabilistically. A logistic check using grounded-frame count, printed gap, and box-size/gap ratio achieves mean held-out-room AUC **0.780 on 142 step-544 gaps** and **0.777 on 85 step-200 gaps**.
2. **Is a better second measurement available today?** No reliable fresh measurement is retained. The records contain candidate scores and frame lists, but no alternative boxes; choosing the better checkpoint with knowledge of truth raises MRA only from **65.29 to 68.00 on 85 shared gaps**.
3. **What would doubt gain?** A rule that flags sparse grounding and chooses a box-based correction on other rooms gains **0.42 type points over 150 step-200 items**, averaged over 20 splits. Replacing every flagged gap with truth would gain **16.13 type points**; detection accounts for little of that recovery.
4. **Could the student learn this from its rows?** The inspected unit rows contain **0 response–answer disagreements among 747 rows**, despite sparse grounding in **199 of 747**. They teach agreement with a measurement, including measurements with sparse support.
5. **Verdict: worth it after the object module improves the head.** The deciding numbers are **0.777 held-out AUC** for detecting risk and only **+0.42 type points** from choosing among currently available box-based alternatives. These returns support a doubt check; they do not support teaching that repeating the measurement will repair it.

**2. Evidence**

All results use dev-S1 and scored `gt`, converted from the question’s unit into metres. Gap scores use the printed response, independently of the final answer. “Wrong” means relative error **>0.25**; the second test uses **>0.50**. MRA is reported on a 0–100 scale.

Sources: [loader](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py), [raw-return scorer](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s/score_r5.py), [unit rows](/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl), and [size-row database](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite). The loader resolves the distance journals to `cont_ops16/work/c15/r1route/out3s/bases/b1/work/ret/metadata/reads/1/metadata/journals/3/0/items.jsonl` at step 544 and `cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` at step 200.

| Population | Step 544 | Step 200 |
|---|---:|---:|
| Calls / all items | 149/150 | 88/150 |
| Numeric gaps / callers | 142/149 | 85/88 |
| Wrong at 0.25 / numeric gaps | 52/142 | 27/85 |
| Wrong at 0.50 / numeric gaps | 31/142 | 15/85 |
| Printed-gap MRA | 61.69, n=142 | 65.29, n=85 |
| Observed answer MRA | 28.27, n=150 | 50.27, n=150 |

**Response signals.** Each AUC cell gives **AUC at 0.25 [95% interval]; AUC at 0.50 [95% interval]**. Intervals use 1,000 room-bootstrap draws, seed 17, excluding draws without both labels. AUC direction follows the named signal; values below 0.5 indicate the opposite association. MRA cells give **below-or-equal / above the signal median**, with group counts in parentheses.

| Signal | n, 544/200 | Step 544 AUCs | Step 200 AUCs | Median-split MRA, 544 | Median-split MRA, 200 |
|---|---:|---|---|---|---|
| −Rarer-object frame count | 142/85 | .628 [.529,.709]; .584 [.445,.687] | .593 [.494,.693]; .503 [.344,.623] | 68.2(77) / 54.0(65) | 68.6(44) / 61.7(41) |
| −First-object frame count | 142/85 | .580 [.472,.663]; .585 [.456,.694] | .485 [.374,.592]; .446 [.291,.599] | 68.2(76) / 54.2(66) | 65.9(44) / 64.6(41) |
| −Second-object frame count | 142/85 | .583 [.476,.693]; .529 [.384,.662] | .642 [.518,.758]; .601 [.411,.718] | 68.6(71) / 54.8(71) | 75.1(45) / 54.3(40) |
| No shared frame | 142/85 | .507 [.421,.575]; .488 [.387,.567] | .438 [.340,.544]; .386 [.281,.500] | 61.7(142) / unavailable | 65.3(85) / unavailable |
| Best-frame separation | 142/85 | .428 [.355,.497]; .414 [.307,.509] | .410 [.281,.537]; .410 [.237,.605] | 60.7(73) / 62.8(69) | 62.0(44) / 68.8(41) |
| Largest printed box edge / gap | 142/85 | .652 [.554,.740]; .667 [.551,.771] | .681 [.532,.798]; .698 [.528,.819] | 67.7(71) / 55.6(71) | 72.8(43) / 57.6(42) |
| −Printed gap | 142/85 | .698 [.604,.778]; .727 [.606,.822] | .724 [.578,.841]; .760 [.574,.888] | 70.3(71) / 53.1(71) | 77.9(43) / 52.4(42) |
| Gap <0.3 m | 142/85 | .552 [.511,.596]; .592 [.527,.662] | .547 [.490,.594]; .593 [.492,.682] | 64.3(135) / 11.4(7) | 67.5(81) / 20.0(4) |
| Gap >4 m | 142/85 | .434 [.380,.481]; .431 [.377,.474] | .389 [.317,.453]; .386 [.316,.442] | 58.0(122) / 84.0(20) | 60.9(69) / 84.4(16) |
| Scale | 142/85 | .478 [.358,.577]; .555 [.390,.689] | .507 [.335,.648]; .580 [.338,.747] | 62.5(71) / 60.8(71) | 66.5(43) / 64.0(42) |
| Class-size anomaly¹ | 51/26 | .496 [.274,.691]; .537 [.201,.805] | .556 [.303,.836]; .682 [.444,.926] | 60.4(26) / 52.0(25) | 70.0(13) / 59.2(13) |
| Class-size ratio outside [0.5,2]¹ | 51/26 | .532 [.372,.663]; .529 [.303,.718] | .521 [.342,.711]; .591 [.318,.875] | 59.1(32) / 51.6(19) | 65.3(17) / 63.3(9) |
| Maximum candidate count | 142/85 | .557 [.449,.672]; .554 [.391,.724] | .538 [.401,.686]; .500 [.290,.780] | 64.2(80) / 58.4(62) | 66.0(43) / 64.5(42) |
| −Selector margin² | 142/85 | .636 [.552,.721]; .701 [.596,.809] | .579 [.481,.671]; .604 [.481,.762] | 73.9(71) / 49.4(71) | 72.8(43) / 57.6(42) |
| −Candidate-only margin² | 119/68 | .660 [.555,.757]; .671 [.551,.794] | .587 [.443,.715]; .567 [.412,.750] | 67.0(60) / 50.5(59) | 67.6(34) / 55.6(34) |
| −Selected logit | 142/85 | .600 [.495,.701]; .680 [.565,.787] | .546 [.431,.646]; .567 [.403,.742] | 65.6(71) / 57.7(71) | 66.5(43) / 64.0(42) |
| −Selected candidate peak | 142/85 | .575 [.470,.661]; .621 [.514,.708] | .522 [.392,.641]; .489 [.335,.635] | 65.8(71) / 57.6(71) | 69.8(44) / 60.5(41) |
| Null would beat selected candidate | 142/85 | .550 [.477,.638]; .642 [.548,.736] | .549 [.473,.625]; .617 [.493,.743] | 66.5(91) / 53.1(51) | 70.0(56) / 56.2(29) |
| Maximum total proposal count | 142/85 | .565 [.466,.673]; .582 [.450,.732] | .531 [.396,.684]; .555 [.368,.793] | 65.0(72) / 58.3(70) | 64.4(43) / 66.2(42) |
| Object-class risk³ | 142/85 | .556 [.468,.646]; .399 [.275,.529] | .458 [.328,.590]; .335 [.183,.550] | 64.6(71) / 58.7(71) | 64.0(43) / 66.7(42) |

¹ I sampled 3,000 primary keys from the 9,778 size rows, in batches of at most 200. All 3,000 parsed into 798 class medians. Size means **longest edge**; anomaly is the larger absolute log₂ ratio across the two objects. Both classes matched on 51/142 and 26/85 gaps. Of the matched individual boxes, 75/173 and 46/96 use medians supported by at most two sampled rows.

² Selector margin is selected logit minus the strongest alternative, including null; the item takes the weaker object’s margin. Candidate-only margin excludes null and requires alternatives for both objects. Candidate count and proposal count take the larger object value; logit and peak take the weaker value.

³ Class risk comes from class-indicator logistic models trained on other rooms, separately for each error threshold. Bootstrap intervals hold those predictions fixed. Class associations do not generalize reliably. “No shared frame” has median 1, leaving no above-median group; its shared/not-shared MRA is 60.6/62.0 on 34/108 items at step 544 and 54.4/68.2 on 18/67 at step 200.

The three-feature logistic model uses **−rarer-object frame count, −gap, and largest box edge/gap**. It standardizes features using training rooms and fits an L2-regularized logistic model. Across 20 half-room splits, mean AUC is **.780/.752** at thresholds .25/.50 for step 544 and **.777/.737** for step 200. Test folds contain 56–89 and 33–48 items, respectively. Adding class and raw metadata lowers mean AUC at .25 to .675 and .663.

A trace can truthfully state those three inputs. For `vsi590k_161799` at step 200: “The toilet was grounded in one frame. The printed gap is 0.27 m. The largest printed box edge is 0.73 m, about 2.7 times the gap.” The scored truth is 3.04 m. These observations justify uncertainty, not certainty that the gap is wrong.

**Available second measurements.**

| Comparison | Step 544 | Step 200 |
|---|---:|---:|
| Other checkpoint closer / shared gaps | 29/85 | 49/85 |
| Own / other / oracle / mean MRA, same 85 gaps | 67.18 / 65.29 / 68.00 / 66.00 | 65.29 / 67.18 / 68.00 / 66.00 |
| Centre distance: closer / available; MRA | 38/142; 36.48 | 20/85; 41.53 |
| Recomputed box distance: closer / available; MRA | 63/142; 61.97 | 46/85; 65.29 |
| Class-median-resized boxes: closer / available; MRA | 20/51; 46.27 | 12/26; 59.23 |
| Same-item original gap MRA for resized-box comparison | 56.27, n=51 | 64.62, n=26 |
| Sparse-grounding subset: resized / original MRA | 44.84 / 45.81, n=31 | 61.67 / 56.11, n=18 |

Recomputed box distance uses the printed yaw, centres and dimensions. It differs from the printed gap by at most 0.05 m on **227/227 gaps**; its small gains reflect rounding/grid differences. Median resizing preserves each box’s aspect ratio and replaces its longest edge with the training class median. The size rows do not establish a median three-dimensional shape.

Raw output keys include `calls`, `heads`, `frames`, and `scale`. Ground-call records include `stage1`; its candidates contain `id`, `frames`, `peak`, `logit`, and feature `inputs`. Multiple candidates exist in **268/291** successful grounds at step 544 and **156/173** at step 200. None of the **2,357 + 1,314 candidate records** provides an explicit alternative 3D box. The returns retain no per-frame object boxes, so an unselected-candidate oracle cannot be scored.

Direct answers are available on **62/150 step-200 items**, scoring **44.68**. Pairing them with step-544 numeric gaps gives **57 items**, with direct/head MRA **44.91/53.51**. Excluding two zero direct answers reproduces **46.55/55.45 on 55 items**. On sparse-grounding items, direct/head MRA is **43.75/40.31 on 32 items**, but switching harms **9/16** initially right gaps. On size-anomaly items it is **52.50/31.25 on 8 items**, harming **1/3** initially right gaps. No independent numerical estimate precedes the call in **149/149** step-544 or **88/88** step-200 calling traces.

**Priced flags.** To isolate measurement repair, the following baseline answers every existing numeric gap with its correct unit conversion and retains observed answers elsewhere: **59.60/56.13 MRA over 150 items**, and **60.70/56.98 over 43 metre items**, at steps 544/200. These are counterfactual measurement scores, not new generations.

“R” selects among recomputed box distance, centre distance and median-resized distance using flagged items in the other half of rooms; unavailable median corrections retain the gap. Every item is evaluated once through complementary room halves, seed 17. “C” replaces flagged gaps with truth. Threshold medians use the relevant step’s available values. Entries under “flags” are **flagged/eligible; wrong-at-.25/flagged, wrong-at-.50/flagged**. Harm means a gap initially within .25 loses MRA; the parenthesis gives lost points over all 150 items.

| Flag | Step 544 flags | Step 200 flags | R/C, all 150: 544; 200 | R/C, 43 metres: 544; 200 | Right gaps harmed: 544; 200 |
|---|---|---|---|---|---|
| Rarer object <3 frames | 93/142; 41/93,23/93 | 61/85; 22/61,12/61 | 59.80/87.33; 56.80/72.27 | 60.93/88.37; 59.53/80.00 | 1/52 (.07); 5/39 (.47) |
| First object <3 frames | 66/142; 28/66,18/66 | 41/85; 12/41,7/41 | 59.80/79.73; 55.80/65.80 | 60.93/77.21; 56.74/69.77 | 1/38 (.07); 2/29 (.27) |
| Second object <3 frames | 56/142; 25/56,13/56 | 40/85; 17/40,10/40 | 59.40/76.33; 56.53/68.33 | 61.16/77.21; 57.67/70.70 | 2/31 (.60); 3/23 (.20) |
| No shared frame | 108/142; 40/108,23/108 | 67/85; 19/67,9/67 | 59.93/86.93; 55.73/70.33 | 60.93/85.35; 56.98/74.42 | 0/68 (0); 4/48 (.67) |
| Best-frame separation >median | 69/142; 23/69,15/69 | 41/85; 10/41,6/41 | 59.60/76.73; 56.13/64.67 | 60.70/80.23; 56.98/68.84 | 2/46 (.13); 0/31 (0) |
| Box/gap ratio >median | 71/142; 31/71,19/71 | 42/85; 17/42,11/42 | 59.73/80.60; 56.20/68.00 | 61.40/84.42; 57.21/81.40 | 2/40 (.13); 0/25 (0) |
| Gap <median | 71/142; 33/71,21/71 | 42/85; 20/42,13/42 | 59.80/81.80; 56.13/69.47 | 61.40/88.14; 57.21/80.00 | 2/38 (.13); 0/22 (0) |
| Gap <0.3 m | 7/142; 6/7,6/7 | 4/85; 3/4,3/4 | 59.73/63.73; 56.27/58.27 | 61.16/65.81; 57.44/62.09 | 0/1 (0); 0/1 (0) |
| Gap >4 m | 20/142; 3/20,1/20 | 16/85; 1/16,0/16 | 59.60/61.73; 55.93/57.80 | 60.70/62.56; 56.98/58.60 | 0/17 (0); 2/15 (.20) |
| Scale >median | 71/142; 25/71,18/71 | 42/85; 12/42,9/42 | 59.67/78.13; 52.73/66.20 | 60.93/73.95; 53.49/67.21 | 1/46 (.07); 14/30 (3.33) |
| Class-size anomaly >median | 25/51; 12/25,6/25 | 13/26; 5/13,3/13 | 59.53/67.60; 56.00/59.67 | 60.70/71.86; 57.44/66.05 | 1/13 (.07); 4/8 (.67) |
| Class-size ratio outside [0.5,2] | 19/51; 9/19,5/19 | 9/26; 3/9,2/9 | 59.60/65.73; 56.13/58.33 | 60.70/67.91; 56.98/62.33 | 0/10 (0); 0/6 (0) |
| Candidate count >median | 62/142; 25/62,16/62 | 42/85; 15/42,7/42 | 59.73/76.80; 56.67/66.07 | 60.93/77.21; 58.60/68.84 | 0/37 (0); 4/27 (.33) |
| Selector margin <median | 71/142; 35/71,25/71 | 42/85; 16/42,10/42 | 59.73/83.53; 55.20/68.00 | 60.70/87.44; 56.74/76.74 | 1/36 (.07); 5/26 (.80) |
| Margin <0 / null wins | 51/142; 22/51,18/51 | 29/85; 11/29,8/29 | 59.67/75.53; 56.13/64.60 | 60.70/77.21; 56.98/70.93 | 1/29 (.07); 0/18 (0) |
| Candidate-only margin <median | 59/119; 29/59,18/59 | 34/68; 14/34,8/34 | 59.73/79.07; 55.73/66.20 | 60.93/83.02; 56.74/73.95 | 0/30 (0); 2/20 (.20) |
| Selected logit <median | 71/142; 28/71,21/71 | 42/85; 13/42,8/42 | 59.67/79.60; 55.33/66.20 | 60.70/81.86; 57.44/73.49 | 2/43 (.13); 5/29 (.80) |
| Candidate peak <median | 71/142; 29/71,19/71 | 41/85; 15/41,8/41 | 59.80/79.67; 56.13/66.93 | 60.93/84.19; 56.98/77.67 | 2/42 (.13); 3/26 (.33) |
| Proposal count >median | 70/142; 28/70,18/70 | 42/85; 13/42,8/42 | 57.20/79.07; 56.27/65.60 | 58.14/83.72; 57.44/73.49 | 10/42 (2.93); 0/29 (0) |
| Class includes “table”⁴ | 14/142; 10/14,6/14 | 5/85; 3/5,1/5 | 58.33/65.60; 55.93/57.67 | 58.14/65.58; 56.28/59.30 | 4/4 (1.60); 1/2 (.20) |

⁴ This is an illustrative class flag selected from the observed class breakdown, not a validated class policy. The numeric medians at steps 544/200 are: separation 9/10 frames; box/gap .496/.386; gap 2.035/2.520 m; scale 2.691/2.644; size anomaly .814/.805; candidate count 10/8; selector margin .441/.540; candidate-only margin 1.114/1.323; selected logit .338/.670; peak .807/.839; proposals 121/102.

**Benchmark-point conversions.** Each cell gives **VSI gain R/C; ReVSI-proxy gain R/C**, relative to the measurement baseline. These divide the metre-type gains by 8 and 7, respectively; they are not official-benchmark measurements.

| Flag | Step 544 | Step 200 |
|---|---|---|
| Rarer object <3 frames | .03/3.46; .03/3.95 | .32/2.88; .36/3.29 |
| First object <3 frames | .03/2.06; .03/2.36 | −.03/1.60; −.03/1.83 |
| Second object <3 frames | .06/2.06; .07/2.36 | .09/1.72; .10/1.96 |
| No shared frame | .03/3.08; .03/3.52 | .00/2.18; .00/2.49 |
| Best-frame separation >median | .00/2.44; .00/2.79 | .00/1.48; .00/1.69 |
| Box/gap ratio >median | .09/2.97; .10/3.39 | .03/3.05; .03/3.49 |
| Gap <median | .09/3.43; .10/3.92 | .03/2.88; .03/3.29 |
| Gap <0.3 m | .06/.64; .07/.73 | .06/.64; .07/.73 |
| Gap >4 m | .00/.23; .00/.27 | .00/.20; .00/.23 |
| Scale >median | .03/1.66; .03/1.89 | −.44/1.28; −.50/1.46 |
| Class-size anomaly >median | .00/1.40; .00/1.59 | .06/1.13; .07/1.30 |
| Class-size ratio outside [0.5,2] | .00/.90; .00/1.03 | .00/.67; .00/.76 |
| Candidate count >median | .03/2.06; .03/2.36 | .20/1.48; .23/1.69 |
| Selector margin <median | .00/3.34; .00/3.82 | −.03/2.47; −.03/2.82 |
| Margin <0 / null wins | .00/2.06; .00/2.36 | .00/1.74; .00/1.99 |
| Candidate-only margin <median | .03/2.79; .03/3.19 | −.03/2.12; −.03/2.42 |
| Selected logit <median | .00/2.65; .00/3.02 | .06/2.06; .07/2.36 |
| Candidate peak <median | .03/2.94; .03/3.36 | .00/2.59; .00/2.96 |
| Proposal count >median | −.32/2.88; −.37/3.29 | .06/2.06; .07/2.36 |
| Class includes “table” | −.32/.61; −.37/.70 | −.09/.29; −.10/.33 |

The seed-17 sparse-grounding gain is optimistic relative to split variation. Across 20 room partitions, the correction selector averages **−0.55/+0.42 type points over 150 items** at steps 544/200, and **−0.24/+1.94 metre-type points over 43 items**. At step 200, always applying the available median-size correction to sparse items gains .67 type points, with room-bootstrap interval **[−.40,2.00]**; its metre gain is 2.56 **[.26,5.11]**. Substituting the archived step-544 gap instead gains **1.13 type points and .47 metre-type points**, but requires the other checkpoint’s measurement.

**Training support.** All **747/747** unit rows identify both masks and geometry as `gt`. Their provenance records a source metric value, conversion factor and decimal rounding; **747/747** printed gaps match that metric value, and **747/747** converted answers agree after rounding. The file contains **683/747 feet rows**, **64/747 inch rows**, and **0/747 missing-ground responses**. It represents **747 source questions, 459 captures and 434 physical rooms**. All **747/747** rows have `training_admitted:false`; this file alone does not establish consumption by training.

Sparse grounding occurs in **199/747** unit rows. None of the dev numeric gaps has a rarer-object frame count outside the training file’s observed range of 1–16 frames. Across the three logistic inputs, **5/142 step-544** and **4/85 step-200** gaps fall outside the unit rows’ observed univariate ranges. These are empirical support gaps, not proof that those values are impossible under ground truth, and not a justified percentage of rows that must be replaced. Real erroneous responses are needed within the familiar range too.

**3. What this changes for vehicle N**

1. **Prioritize a diagnostic replacement set of 747 real-response rows, before admitting doubt/recovery targets.** The inspected family is `object_abs_distance|None|None`, with `provenance.family="units"`; literal pool/retrace fields are absent, and the v7 index has no absolute-distance family. Run the deployed proposal/selector, G3T geometry, checkpoint scale/gravity, box fitting and gap calculation on the same **459 training captures**, with the same sampled frames and operands. Retain candidate boxes and frame-specific alternatives. This would supply evidence for the **22/61 sparse, wrong step-200 gaps**; how many it fixes remains unmeasured.
2. **Reword the 747 unit targets to describe the evidence actually printed.** Example: “The tool returned one box for each object. Their printed gap is 2.55 m. Converting to feet gives 8.37.” Remove “taken over every pair of instances” unless the response supplies that evidence. This improves trace fidelity; **no score gain is established**.
3. **Add zero unconditional retry rows now.** After a distinct alternative measurement has demonstrated recovery, add rows that expose the real first response, state its observable weakness, request the supported alternative, and reconcile both measurements. Example wording, conditional on that capability: “The toilet was grounded in one frame. I will check it in another visible frame before using this gap.” Failure at the next read means repeated identical measurements, worse scores on initially right gaps, or detection AUC without positive held-out recovery gain. The needed row count cannot be inferred from these returns.

**4. Refuted**

The claim that no numeric response cue separates good and bad gaps is contradicted by gap AUC **.698/.724** and the three-field held-out AUC **.780/.777**. The example assumption that ground-truth-derived rows never show fewer than three grounded frames is contradicted by **199/747 rows**. The stated direct score **46.5** applies to **55 positive paired answers**, not all **62 no-call items**, which score **44.68**. The current loader’s `gt` exposes the scored answer; the first-wave report’s loader-label caveat does not apply to this analysis.

**5. Not established**

These returns do not establish whether an alternate frame or unselected instance would repair the gap, whether the student can execute a calibrated doubt check after training, or whether the class-median gain survives new rooms and a fixed policy. Retained alternative geometry, real-response training examples, and a fresh dev read with a predeclared recovery rule would settle those questions. No official benchmark items, model calls, file changes, or GPU work were used.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the held-out AUCs, paired-checkpoint ceiling, and sparse-grounding training count.

```python
import sys, re, json
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import numpy as np
S = K._scorer().scorers
def auc(y, x):
    p = np.asarray(x)[np.asarray(y, bool)]
    n = np.asarray(x)[~np.asarray(y, bool)]
    return np.mean((p[:, None] > n) + .5 * (p[:, None] == n))
def mra(g, t):
    return np.mean(abs(g-t)/abs(t) < 1-np.arange(.50, 1., .05))
data = {}
for step in (544, 200):
    rows = []
    for r in K.routed(step, types=["object_abs_distance"]):
        gaps = [S.printed(c) for c in r["calls"] if c["family"] == "gap"]
        gaps = [v["distance"] for v in gaps if v]
        grounds = [c["response"] for c in r["calls"] if c["family"] == "ground"]
        fs = [re.search(r"frames ([\d,]+) \(best", t) for t in grounds]
        sizes = [re.search(r"size ([\d.]+) x ([\d.]+) x ([\d.]+)", t)
                 for t in grounds]
        if not gaps or len(fs) != 2 or not all(fs) or not all(sizes):
            continue
        g = gaps[-1]
        truth = float(r["gt"]) / S.unit_factor(r["question"])
        rare = min(len(m[1].split(",")) for m in fs)
        edge = max(float(v) for m in sizes for v in m.groups())
        rows.append(dict(id=r["id"], room=r["room"], g=g, truth=truth,
                         err=abs(g-truth)/truth, score=mra(g, truth),
                         X=[-rare, -g, edge/max(g, .01)]))
    data[step] = rows
    rooms = sorted({r["room"] for r in rows})
    rng = np.random.default_rng(17)
    splits = [set(rng.permutation(rooms)[:len(rooms)//2]) for _ in range(20)]
    for threshold in (.25, .5):
        scores = []
        for trainrooms in splits:
            train = [r for r in rows if r["room"] in trainrooms]
            test = [r for r in rows if r["room"] not in trainrooms]
            A, B = [np.array([r["X"] for r in group]) for group in (train, test)]
            mu, sd = A.mean(0), A.std(0)
            sd[sd < 1e-6] = 1
            A, B = np.c_[np.ones(len(A)), (A-mu)/sd], np.c_[np.ones(len(B)), (B-mu)/sd]
            y = np.array([r["err"] > threshold for r in train], float)
            w = np.zeros(4)
            pen = np.array([0., 1., 1., 1.])
            for _ in range(50):
                p = 1/(1+np.exp(-np.clip(A@w, -30, 30)))
                H = (A.T*(p*(1-p)))@A + np.diag(pen+1e-6)
                dw = np.linalg.solve(H, A.T@(p-y)+pen*w)
                w -= dw
                if np.linalg.norm(dw) < 1e-6:
                    break
            scores.append(auc([r["err"] > threshold for r in test], B@w))
        print("held-out room AUC", step, threshold, len(rows), round(np.mean(scores), 3))
old = {r["id"]: r for r in data[544]}
pairs = [(old[r["id"]], r) for r in data[200] if r["id"] in old]
print("shared", len(pairs), "544/200/oracle/mean MRA",
      [round(100*np.mean(v), 3) for v in (
          [a["score"] for a,b in pairs], [b["score"] for a,b in pairs],
          [max(a["score"], b["score"]) for a,b in pairs],
          [mra((a["g"]+b["g"])/2, a["truth"]) for a,b in pairs])])
n = sparse = 0
path = "/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl"
for line in open(path):
    r = json.loads(line)
    counts = [len(f.split(",")) for f in re.findall(r"frames ([\d,]+) \(best", r["target"])]
    n += 1
    sparse += min(counts) < 3
print("GT-derived unit rows with fewer than three frames", sparse, "of", n)
```