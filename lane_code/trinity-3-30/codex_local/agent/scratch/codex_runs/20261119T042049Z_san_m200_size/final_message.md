## 1. Scope

Step 200 still asserts unsupported size estimates. Relative-size errors mostly follow an explicitly wrong comparison.

| Type / set | Items analyzed | Step 544 score | Step 200 score | Step 200 wrong |
|---|---:|---:|---:|---:|
| Object size / dev-S1 | 150 of 150 | 68.73 | 69.40 | 105 of 150 |
| Object size / R0-dev | 293 of 293 | 59.08 | 58.29 | 229 of 293 |
| Relative size / dev-S1 | 150 of 150 | 91.33 | 90.00 | 15 of 150 |

I recomputed these scores from the loader’s files. The step-544 dev-S1 file is `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`. Other files sit under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/`: step 200 uses `a8102c3207b/fetched/x/{main,a7}/a0/results/`; step-544 R0-dev uses `adff67f7ae9/fetched/x/a7/a0/results/`. Scores come from `budget_2048/0/items_a0.jsonl`; full traces come from `0/items_a0.jsonl`.

**Unit correction:** dev-S1 asks centimetres on 38 of 150 items, inches on 47 of 150, feet on 31 of 150, and metres on 34 of 150. Its `unit` field is missing on 150 of 150. R0-dev asks centimetres and has `unit=cm`, `subtype=longest_dimension` on 293 of 293.

Here, \(r=\text{answer}/\text{truth}\); signed relative error is \(r-1\). Ratios use the requested units.

| Set / step | Mean r | Median r | SD r | 10th–90th percentile | Within 10% | Within 25% | Within 50% |
|---|---:|---:|---:|---|---|---|---|
| dev-S1 / 544 | 1.426 | 1.000 | 5.396 | 0.649–1.357 | 69 of 150 | 105 of 150 | 138 of 150 |
| dev-S1 / 200 | 1.101 | 1.016 | 0.581 | 0.780–1.431 | 71 of 150 | 109 of 150 | 136 of 150 |
| R0-dev / 544 | 1.194 | 1.000 | 0.762 | 0.683–1.708 | 104 of 293 | 178 of 293 | 242 of 293 |
| R0-dev / 200 | 1.230 | 1.005 | 0.855 | 0.715–1.743 | 100 of 293 | 174 of 293 | 243 of 293 |

At step 200, dev-S1 underestimates on 62 of 150 and overestimates on 82 of 150; R0-dev underestimates on 134 of 293 and overestimates on 147 of 293. Step 544 has corresponding counts of 73 of 150 / 73 of 150 and 135 of 293 / 146 of 293. The large step-544 dev-S1 mean mainly reflects one centimetres-for-metres error.

All classes with at least five items follow. “Distinct” counts unique **(requested unit, numeric answer)** pairs.

| Set / class | Items | Mean r, 544 / 200 | Distinct answers, 544 / 200 |
|---|---|---|---|
| dev-S1 / bathtub | 7 of 150 | 1.016 / 1.023 | 7 of 7 / 5 of 7 |
| dev-S1 / bed | 14 of 150 | 0.955 / 0.965 | 10 of 14 / 9 of 14 |
| dev-S1 / chair | 5 of 150 | 1.065 / 1.130 | 5 of 5 / 5 of 5 |
| dev-S1 / desk | 6 of 150 | 0.870 / 0.980 | 6 of 6 / 4 of 6 |
| dev-S1 / refrigerator | 9 of 150 | 1.011 / 1.020 | 9 of 9 / 8 of 9 |
| dev-S1 / sofa | 7 of 150 | 1.121 / 1.151 | 7 of 7 / 5 of 7 |
| dev-S1 / stool | 5 of 150 | 0.852 / 0.938 | 5 of 5 / 5 of 5 |
| dev-S1 / stove | 7 of 150 | 0.969 / 1.000 | 7 of 7 / 7 of 7 |
| dev-S1 / table | 13 of 150 | 0.913 / 1.204 | 13 of 13 / 10 of 13 |
| dev-S1 / toilet | 6 of 150 | 0.953 / 0.899 | 6 of 6 / 5 of 6 |
| dev-S1 / tv | 14 of 150 | 1.186 / 1.216 | 14 of 14 / 13 of 14 |
| R0-dev / cabinet | 9 of 293 | 1.498 / 1.672 | 7 of 9 / 5 of 9 |
| R0-dev / door | 8 of 293 | 0.943 / 0.943 | 2 of 8 / 1 of 8 |
| R0-dev / keyboard | 6 of 293 | 1.123 / 1.266 | 3 of 6 / 2 of 6 |
| R0-dev / sink | 6 of 293 | 0.930 / 0.983 | 3 of 6 / 4 of 6 |
| R0-dev / telephone | 5 of 293 | 1.466 / 1.221 | 2 of 5 / 3 of 5 |
| R0-dev / toilet | 5 of 293 | 0.876 / 0.868 | 3 of 5 / 4 of 5 |
| R0-dev / window | 5 of 293 | 1.047 / 1.103 | 4 of 5 / 5 of 5 |
| R0-dev / windowsill | 6 of 293 | 1.058 / 1.131 | 5 of 6 / 6 of 6 |

Class repetition is real but not universal: R0-dev doors receive 210 cm in 8 of 8 rooms despite truths spanning 209–309 cm. Keyboards receive 45 cm on 5 of 6 items. Multiples of five in requested units occur on 7 of 150 / 0 of 150 dev-S1 items and 69 of 293 / 76 of 293 R0-dev items at steps 544 / 200.

After converting truths to centimetres, step-200 dev-S1 errors are 5 of 8 below 30 cm, 87 of 118 at 30–200 cm, and 13 of 24 above 200 cm; respective scores are 76.25, 67.20, and 77.92. R0-dev errors are 75 of 88, 125 of 159, and 29 of 46; scores are 47.95, 61.19, and 68.04. Small R0-dev objects fail most; middle-sized objects contribute the greatest total loss in both sets.

## 2. Failure modes

I classified every wrong item. Each cell gives the count and its cost in points on that type and set.

| Mode | Definition | Size: dev-S1 | Size: R0-dev | Relative size: dev-S1 |
|---|---|---|---|---|
| Underestimate | The trace asserts a length below truth; the answer repeats it. | 47 of 150; 11.53 | 97 of 293; 13.65 | 0 of 150; 0 |
| Overestimate | The trace asserts a length above truth; the answer repeats it. | 58 of 150; 19.07 | 131 of 293; 27.71 | 0 of 150; 0 |
| Runaway | Repeated localization text forces closure at the token budget. | 0 of 150; 0 | 1 of 293; 0.34 | 0 of 150; 0 |
| Wrong comparison | The trace states the wrong size relation; the answer follows it. | 0 of 150; 0 | 0 of 293; 0 | 13 of 150; 8.67 |
| Missing comparison | The trace says to compare but supplies neither sizes nor a relation. | 0 of 150; 0 | 0 of 293; 0 | 2 of 150; 1.33 |
| **Total** | **Exclusive primary classifications.** | **105 of 150; 30.60** | **229 of 293; 41.71** | **15 of 150; 10.00** |

Completed numeric traces assert a measurement on 150 of 150 dev-S1 items and 292 of 293 R0-dev items; every stated final measurement matches the answer. Every wrong completed numeric trace lacks a comparison object or scale derivation: 105 of 105 and 228 of 228. Numeric frame references appear on 54 of 150 and 125 of 293, but localization alone does not determine scale.
Relative-size wrong traces state measurements on 0 of 15 items, an incorrect relation on 13 of 15, and no relation on 2 of 15. Shorter questions fail on 8 of 73; longer questions fail on 7 of 77. No demonstrated polarity-selection error occurs on 15 of 15 wrong items: the explicit comparisons already contain the wrong relation. No answer-use mismatch or unparsed answer was found among 349 of 349 wrong items.

## 3. Examples

Excerpts below are verbatim. Questions are shortened where marked. For modes with fewer than three items, every available example is shown.

- **Underestimate:** `vsi590k_054727`, dev-S1. “How many centimeters is the longest side of the desk?” Truth 255; answer 164. “Step 2: the longest edge of the desk is 164 cm.”
- **Underestimate:** `vsi590k_175823`, dev-S1. “What's the measure of the heater's largest side in centimeters?” Truth 222; answer 66. “Step 2: the longest edge of the heater is 66 cm.”
- **Underestimate:** `009f200a5a1f54f3f1e73cf3`, R0-dev. Question: longest dimension of the book, centimetres [shortened]. Truth 27; answer 21. “Step 2: the longest edge of the book is 21 cm.”
- **Overestimate:** `vsi590k_262256`, dev-S1. “How many centimeters is the longest side of the tv?” Truth 65; answer 104. “Step 2: the longest edge of the tv is 104 cm.”
- **Overestimate:** `013961926ac334b14b9bf500`, R0-dev. Question: longest dimension of the basket, centimetres [shortened]. Truth 22; answer 60. “Step 2: the longest edge of the basket is 60 cm.”
- **Overestimate:** `3251cbd6acffd7288ec92ac2`, R0-dev. Question: longest dimension of the mirror, centimetres [shortened]. Truth 18; answer 156. “Step 2: the longest edge of the mirror is 156 cm.”
- **Runaway:** `16884daee5676e0113e6102a`, R0-dev. Question: longest dimension of the keyboard, centimetres [shortened]. Truth 28; answer 44. “Step 1: find the keyboard, first seen in the left view of the left view of the left view”.
- **Wrong comparison:** `vsi590k_061267`, dev-S1. “Which one, the trash bin or the keyboard, has a longest edge that is the longer?” Truth B, keyboard; answer A, trash bin. “Step 3: order them from shortest to longest edge: keyboard, then trash bin.”
- **Wrong comparison:** `vsi590k_186818`, dev-S1. “Between the ceiling light and the bed, whose edge is the shorter in length?” Truth B, ceiling light; answer A, bed. “Step 1: find the ceiling light and the bed, then order them from nearest to farthest from the camera: bed, then ceiling light.”
- **Wrong comparison:** `vsi590k_281078`, dev-S1. “Between the refrigerator and the chair, whose edge is the shorter in length?” Truth B, chair; answer A, refrigerator. “Step 2: the refrigerator is shorter than the chair.”
- **Missing comparison:** `vsi590k_069249`, dev-S1. “Which has the shorter maximum length: the chair's longest edge or the radiator's?” Truth B, chair; answer A, radiator. “Step 1: find the chair and the radiator, then compare their longest edges.”
- **Missing comparison:** `vsi590k_275267`, dev-S1. “Among the longest edges of the tv and the stool, which is the longer?” Truth B, tv; answer A, stool. “Step 1: find the tv and the stool, then compare their longest edges.”

## 4. Step 544 against step 200

“Right” means score 1; partial-credit numeric answers count as wrong.

| Type / set | Right→wrong | Wrong→right | Wrong→wrong |
|---|---|---|---|
| Size / dev-S1 | 10 of 150 | 12 of 150 | 95 of 150 |
| Size / R0-dev | 12 of 293 | 19 of 293 | 217 of 293 |
| Relative size / dev-S1 | 9 of 150 | 7 of 150 | 6 of 150 |

Numeric flips retain a stated length but usually drop “measure its 3D box.” Median think lengths for dev-S1 losses/gains change from 39.5/38 to 35/35.5 tokens; R0-dev changes from 37.5/37 to 34.5/33. Relative-size losses lose explicit measurements on 9 of 9 items; gains retain measurements on 1 of 7. Their median lengths change from 67/68 to 41/40 tokens. Both gains and losses therefore share the shorter trace form.
Step-544 `vsi590k_175250` answers 41 when metres are requested, copying “41 cm”; step 200 correctly converts to 0.41 m but still misses truth 0.61. No explicit requested-unit mismatch occurs at step 200 on 150 of 150 dev-S1 or 292 of 292 completed R0-dev traces. A ratio resembling an inch conversion alone would not establish a unit failure.

## 5. Hypotheses

- **HYPOTHESIS—underestimation and overestimation:** class priors and weak instance-scale evidence drive both modes. Family `object_size_estimation|r1g|rows_rebuild_d0_v1` retains 9,778 of 9,778 rows. The ready-made sample retains 20 of 20; measurement-free targets occur on 20 of 20. Row 39 says: “Step 1: find the webcam, first seen in frame 17. Step 2: the question asks for the longest edge, in centimeters. I estimate it from the frames.” Its answer is 20. This teaches localization and an estimation instruction, without explaining instance scale.
- **HYPOTHESIS—runaway:** the same family’s first-seen phrasing encourages repetitive localization. Row 93435 says “find the decoration, first seen in frame 2.” The failing keyboard repeats a location phrase; this is association, not proof of causation.
- **HYPOTHESIS—wrong comparison:** relative size borrows comparison templates without dedicated supervision. The supplied family inventory contains no `relative_size_object` family. Proxy family `camera_obj_rel_dist_v1|vsti_rel_v4|None`, row 154009, says “ordered nearest to farthest from the camera viewpoint of frame 16”. The ceiling-light failure reproduces this irrelevant relation.
- **HYPOTHESIS—missing comparison:** absent dedicated size-order rows leave “compare” as an unfinished instruction. Proxy family `object_rel_distance|w1g|rows_rebuild_d0_v1`, row 1, explicitly teaches “the candidates ordered nearest to farthest from the bag are: bookshelf, then boxes, then flipchart, then electrical duct.” A dedicated size family could teach the corresponding complete relation.

## 6. Label or scoring defects

No confirmed label or scoring defect was found. The brief’s centimetre-only description conflicts with dev-S1 questions, and its missing `unit` metadata requires question-based normalization.
**Unverified label-review candidates:** R0-dev `bd27924bbd5cdff459ad0fea` labels a cable box 1,139 cm; `f1e39efcfa15c404beecbb56` labels a metal tray 336 cm. These could describe extended structures or merged instances; their unusual sizes do not prove bad labels.

## 7. Three changes

1. **Reword about 2,000 rows** within `object_size_estimation|r1g|rows_rebuild_d0_v1`, using contrasting instances of the same class. Name the visible endpoints, longest axis, and a visible comparison object without inventing measurements. Prioritize small objects: this targets 5 of 150 dev-S1 and 75 of 293 R0-dev wrong items, costing 1.27 and 15.63 points. The row budget is a **guess**; these are affected-item ceilings, not predicted recoveries.
2. **Add about 1,500 rows** in proposed family `relative_size_object|vehicleN_size_pairs|direct_size_order`. Balance shorter/longer questions and require a complete shortest-to-longest relation followed by the selected option. This targets 15 of 150 wrong items, including 13 of 150 wrong relations and 2 of 150 missing relations. The row budget and recovery potential are **guesses**; perception errors may remain.
3. **Reword the localization clause across 9,778 of 9,778 existing size rows** to use one bounded reference to a supplied frame, then proceed. This targets the runaway on 1 of 293 R0-dev items, worth at most 0.34 points. I am **least sure** this training change would stop repetition; that causal claim is a **guess**.

## 8. Not established

Text alone cannot establish whether the model used visual scale, selected the wrong instance, or fabricated localization. Frame numbers outside the supplied range appear on 15 of 150 dev-S1 and 18 of 293 R0-dev traces; original-video indexing could explain them. Matched frames, instance annotations, and frame-index mappings would settle this. Controlled training ablations would establish whether the proposed changes recover any of the priced losses.

## Appendix: CLASSIFIER

```python
import sys, re
from collections import defaultdict
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K

missing = {'vsi590k_069249', 'vsi590k_275267'}
wrong_order = {
 'vsi590k_061267','vsi590k_067566','vsi590k_183977',
 'vsi590k_186818','vsi590k_190123','vsi590k_190252',
 'vsi590k_272533','vsi590k_272841','vsi590k_274378',
 'vsi590k_276450','vsi590k_277228','vsi590k_278439',
 'vsi590k_281078'}
modes = ['Underestimate', 'Overestimate', 'Runaway',
         'Wrong comparison', 'Missing comparison']

for se, typ in [('dev-S1','object_size_estimation'),
                ('R0-dev','object_size_estimation'),
                ('dev-S1','relative_size_object')]:
 rows = K.direct('R1',200,se,types=[typ])
 counts, costs = defaultdict(int), defaultdict(float)
 for r in rows:
  if r['score'] == 1:
   continue
  if r['forced_close']:
   mode = 'Runaway'
  elif typ == 'relative_size_object':
   assert r['id'] in missing | wrong_order, r['id']
   mode = ('Missing comparison' if r['id'] in missing
           else 'Wrong comparison')
  else:
   t = r['text'].split('</think>')[0]
   nums = re.findall(
       r'(\d+(?:\.\d+)?)\s*(?:cm|inches|in|feet|ft|m)\b', t)
   assert nums and float(nums[-1]) == float(r['pred']), r['id']
   mode = ('Underestimate' if float(r['pred']) < float(r['gt'])
           else 'Overestimate')
  counts[mode] += 1
  costs[mode] += 100 * (1-r['score']) / len(rows)
 assert sum(counts.values()) == sum(r['score'] < 1 for r in rows)
 print(se, typ)
 for mode in modes:
  print('%s: %d of %d; %.4f points' %
        (mode, counts[mode], len(rows), costs[mode]))
 print('Wrong total: %d of %d' % (sum(counts.values()), len(rows)))
```