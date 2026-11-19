**1. Scope**
Step 400 loaded successfully. Object-size performance is nearly unchanged; relative-size accuracy loses 2.7 points against step 200. All results below use the recorded B2048 scores. Triples follow **544 / 200 / 400**.

| Type and set | Items analysed | Scores |
|---|---:|---:|
| Object size, dev-S1 | 150 of 150 | 68.73 / 69.40 / 69.07 |
| Object size, R0-dev | 293 of 293 | 59.08 / 58.29 / 58.09 |
| Relative size, dev-S1 | 150 of 150 | 91.33 / 90.00 / 87.33 |

Files: step-544 dev-S1 came from `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`. Other files were under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/`: `h1read/kit/build/adff67f7ae9` for step-544 R0-dev, `h1read/kit/build/a8102c3207b` for step 200, and `h1read7/kit/build/a59a7bff4c4` for step 400, followed by `/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
The assignment’s centimetre description does not cover dev-S1: its questions ask inches on 47 of 150, feet on 31 of 150, metres on 34 of 150, and centimetres on 38 of 150. R0-dev asks centimetres on 293 of 293, with `unit="cm"` and subtype `longest_dimension`.

**2. Failure modes**
Each cell gives **wrong items; lost type points**. Runaway takes precedence over numerical error. These classifications cover every wrong item.

| Mode and definition | Set/type | Step 544 | Step 200 | Step 400 |
|---|---|---:|---:|---:|
| Overestimate: completed answer exceeds `gt`. | dev-S1 size | 50 of 150; 14.53 | 58 of 150; 19.07 | 51 of 150; 16.40 |
| Underestimate: completed answer falls below `gt`. | dev-S1 size | 57 of 150; 16.73 | 47 of 150; 11.53 | 58 of 150; 14.53 |
| Runaway: B2048 force-closes the trace. | dev-S1 size | 0 of 150; 0.00 | 0 of 150; 0.00 | 0 of 150; 0.00 |
| Overestimate | R0-dev size | 127 of 293; 26.35 | 131 of 293; 27.71 | 134 of 293; 28.53 |
| Underestimate | R0-dev size | 108 of 293; 14.27 | 97 of 293; 13.65 | 101 of 293; 13.04 |
| Runaway | R0-dev size | 1 of 293; 0.31 | 1 of 293; 0.34 | 1 of 293; 0.34 |
| Wrong comparison: the written comparison selects the wrong object, including an irrelevant distance comparison. | dev-S1 relative size | 13 of 150; 8.67 | 13 of 150; 8.67 | 19 of 150; 12.67 |
| No comparison stated: the trace only announces that it will compare. | dev-S1 relative size | 0 of 150; 0.00 | 2 of 150; 1.33 | 0 of 150; 0.00 |

Wrong totals are 107 / 105 / 109 of 150 for dev-S1 size, 236 / 229 / 236 of 293 for R0-dev size, and 13 / 15 / 19 of 150 for relative size. No new primary mode is needed.
For numerical size, the answer matches the trace’s asserted number on 150 of 150 dev-S1 items and 292 of 293 R0-dev items at each step; the remaining R0-dev trace loops without reaching a number. No trace supplies a comparison object that establishes metric scale. At step 400, 58 of 150 dev-S1 traces and 138 of 293 R0-dev traces cite numerical frames; a location alone does not determine a length.
The following ratios use the loader’s `gt`: \(r=\text{answer}/\text{truth}\), so values above one indicate overestimation. Coverage includes equality at each tolerance.

| Set, step | Mean / median ratio | SD; 10th–90th percentile | Within 10% | Within 25% | Within 50% |
|---|---|---|---|---|---|
| dev-S1, 544 | 1.426 / 1.001 | 5.396; 0.647–1.361 | 69 of 150 | 104 of 150 | 139 of 150 |
| dev-S1, 200 | 1.102 / 1.014 | 0.582; 0.757–1.425 | 71 of 150 | 109 of 150 | 135 of 150 |
| dev-S1, 400 | 1.025 / 1.000 | 0.334; 0.700–1.377 | 69 of 150 | 107 of 150 | 139 of 150 |
| R0-dev, 544 | 1.194 / 1.000 | 0.762; 0.680–1.682 | 104 of 293 | 178 of 293 | 242 of 293 |
| R0-dev, 200 | 1.230 / 1.005 | 0.855; 0.714–1.714 | 100 of 293 | 174 of 293 | 243 of 293 |
| R0-dev, 400 | 1.277 / 1.013 | 0.996; 0.714–1.714 | 103 of 293 | 176 of 293 | 239 of 293 |

Every class with at least five items appears below. Cells give **mean ratio; distinct answers**, after converting answers to centimetres and rounding to 0.1 cm.

| Set/class | Step 544 | Step 200 | Step 400 |
|---|---|---|---|
| dev-S1 bathtub | 1.015; 7 of 7 | 1.022; 5 of 7 | 1.015; 6 of 7 |
| dev-S1 bed | 0.954; 10 of 14 | 0.965; 8 of 14 | 0.966; 11 of 14 |
| dev-S1 chair | 1.065; 5 of 5 | 1.130; 5 of 5 | 1.115; 5 of 5 |
| dev-S1 desk | 0.858; 6 of 6 | 0.972; 4 of 6 | 0.956; 6 of 6 |
| dev-S1 refrigerator | 1.012; 8 of 9 | 1.021; 8 of 9 | 1.055; 9 of 9 |
| dev-S1 sofa | 1.121; 7 of 7 | 1.152; 5 of 7 | 1.018; 6 of 7 |
| dev-S1 stool | 0.851; 4 of 5 | 0.938; 5 of 5 | 0.827; 3 of 5 |
| dev-S1 stove | 0.968; 6 of 7 | 0.999; 6 of 7 | 0.954; 7 of 7 |
| dev-S1 table | 0.914; 12 of 13 | 1.206; 10 of 13 | 0.877; 12 of 13 |
| dev-S1 toilet | 0.952; 6 of 6 | 0.899; 5 of 6 | 0.899; 5 of 6 |
| dev-S1 tv | 1.187; 14 of 14 | 1.217; 12 of 14 | 1.213; 11 of 14 |
| R0-dev cabinet | 1.498; 7 of 9 | 1.672; 5 of 9 | 1.972; 7 of 9 |
| R0-dev door | 0.943; 2 of 8 | 0.943; 1 of 8 | 0.943; 1 of 8 |
| R0-dev keyboard | 1.123; 3 of 6 | 1.266; 2 of 6 | 1.272; 1 of 6 |
| R0-dev sink | 0.930; 3 of 6 | 0.983; 4 of 6 | 0.976; 4 of 6 |
| R0-dev telephone | 1.466; 2 of 5 | 1.221; 3 of 5 | 1.473; 3 of 5 |
| R0-dev toilet | 0.876; 3 of 5 | 0.868; 4 of 5 | 0.868; 4 of 5 |
| R0-dev window | 1.047; 4 of 5 | 1.103; 5 of 5 | 1.056; 4 of 5 |
| R0-dev windowsill | 1.058; 5 of 6 | 1.131; 6 of 6 | 1.033; 6 of 6 |

The strongest constant-answer evidence is R0-dev: doors receive 210 cm on 8 of 8 items from different rooms, although truths span 209–309 cm; keyboards receive 45 cm on 6 of 6 items from different rooms, although truths span 27–51 cm. Answers divisible by five occur on 69 / 76 / 61 of 293 items, so increased rounding does not explain the deterioration.
After converting truths to centimetres, dev-S1 scores for small (<30), middle (30–200), and large (>200) objects are respectively 63.8 / 76.3 / 72.5, 68.0 / 66.9 / 66.6, and 74.0 / 78.8 / 79.6. Their step-400 wrong counts are 7 of 8, 88 of 117, and 14 of 25.
R0-dev scores for those ranges are 46.5 / 48.0 / 46.3, 63.3 / 61.2 / 61.9, and 68.7 / 68.0 / 67.6. Step-400 wrong counts are 74 of 88, 132 of 159, and 30 of 46. Small objects alone cost 16.14 type points; 25 of 88 receive answers at least 30 cm. Their mean ratio is 1.681, versus 0.875 for large objects.
No confirmed metre/inch substitution was found on centimetre questions. **Unit-error candidates, not established failures:** step-400 `vsi590k_056006`, `vsi590k_175119`, and `vsi590k_264364` give metre-like numbers labelled feet; `vsi590k_058075` gives 120 inches for truth 37.9 inches. At step 544, `vsi590k_175250` explicitly states “41 cm” and answers 41 when metres are requested, producing the extreme ratio 67.213.

**3. Examples**
Questions are shortened; quoted excerpts are verbatim. Examples use step 400 unless marked otherwise.

| Mode | Three examples, or every available example |
|---|---|
| Overestimate | R0-dev `004a4084e194e2fdf9ba5dc9`, stationery length in cm, truth 18, answer 29: “the longest edge of the stationery is 29 cm.” Dev-S1 `vsi590k_053930`, refrigerator length in metres, truth 1.48, answer 1.74: “the longest edge of the refrigerator is 1.74 m.” R0-dev `013961926ac334b14b9bf500`, basket length in cm, truth 22, answer 41: “the longest edge of the basket is 41 cm.” |
| Underestimate | Dev-S1 `vsi590k_053924`, bed length in inches, truth 83.8, answer 75.2: “the longest edge of the bed is 75.2 inches.” Dev-S1 `vsi590k_053935`, microwave length in metres, truth 0.52, answer 0.43: “the longest edge of the microwave is 0.43 m.” R0-dev `009f200a5a1f54f3f1e73cf3`, book length in cm, truth 27, answer 20: “the longest edge of the book is 20 cm.” |
| Runaway | R0-dev step 544 `296abef79d35976277095e10`, windowsill cm, truth 217, answer 113: “first seen in the first seen in the first seen”. Step 200 `16884daee5676e0113e6102a`, keyboard cm, truth 28, answer 44: “the left view of the left view of the left view”. Step 400 `82879df19d54448be7244a9d`, screen cm, truth 64, answer 194: “the right half of the right half of the right half”. |
| Wrong comparison | Dev-S1 `vsi590k_183977`, coat hanger/heater longer, truth heater, answer coat hanger: “the coat hanger is longer than the heater.” `vsi590k_272841`, sofa/table shorter, truth table, answer sofa: “the longest edge of the sofa is 101 cm; the longest edge of the table is 120 cm.” `vsi590k_277228`, table/tv longer, truth tv, answer table: “the table is longer than the tv.” |
| No comparison stated | Both examples are step 200, dev-S1: `vsi590k_069249`, chair/radiator shorter, truth chair, answer radiator: “Step 1: find the chair and the radiator, then compare their longest edges.” `vsi590k_275267`, tv/stool longer, truth tv, answer stool: “Step 1: find the tv and the stool, then compare their longest edges.” These are all 2 of 150; no third example exists. |

**4. Step 200 against step 400**
Right→wrong, wrong→right, and wrong→wrong counts are respectively **9 of 150, 5 of 150, 100 of 150** for dev-S1 size; **14 of 293, 7 of 293, 222 of 293** for R0-dev size; and **8 of 150, 4 of 150, 11 of 150** for relative size.
All 14 of 14 dev-S1 numerical flips and 21 of 21 R0-dev numerical flips retain an asserted-length trace. Their mean think lengths change from 40.6 to 37.6 and 34.5 to 35.1 tokens, respectively. The number changes; no new scale evidence appears.
Relative-size traces state measurements on 150 / 27 / 61 of 150 items. Among step-400 errors, 6 of 19 state numerical sizes, 12 of 19 state qualitative size comparisons, and 1 of 19 substitutes camera distance. All answers follow those conclusions. Mean think length is 66.8 / 44.4 / 52.1 tokens.
Against step 544, the corresponding transition counts are **10 of 150, 8 of 150, 99 of 150** for dev-S1 size; **15 of 293, 15 of 293, 221 of 293** for R0-dev size; and **14 of 150, 8 of 150, 5 of 150** for relative size.
Every relative-size answer flip across the three checkpoints appears below: **25 of 150**. Questions are shortened; answers and quoted trace excerpts follow 544 / 200 / 400.

| ID; question | Truth; answers | Trace excerpts at the three steps |
|---|---|---|
| `vsi590k_061155`; table/bookshelf shorter? | Bookshelf; table / bookshelf / bookshelf | “The table is shorter.” / “the bookshelf is shorter than the table.” / “the bookshelf is shorter than the table.” |
| `vsi590k_061267`; trash bin/keyboard longer? | Keyboard; trash bin / trash bin / keyboard | “The trash bin is longer.” / “the trash bin is longer than the keyboard.” / “the keyboard is longer than the trash bin.” |
| `vsi590k_061681`; nightstand/pillow shorter? | Pillow; pillow / pillow / nightstand | “The shorter edge is the pillow's.” / “The question asks for the shorter: the pillow.” / “the nightstand is shorter than the pillow.” |
| `vsi590k_066181`; window/sofa longer? | Sofa; window / sofa / window | “The window is longer.” / “The question asks for the largest: the sofa.” / “the window is longer than the sofa.” |
| `vsi590k_067566`; window/table longer? | Table; table / window / window | “the table is longer.” / “the window is longer than the table.” / “the window is longer than the table.” |
| `vsi590k_069249`; chair/radiator shorter? | Chair; radiator / radiator / chair | “The radiator has the shorter edge.” / “then compare their longest edges.” / “the chair's longest edge is shorter than the radiator's.” |
| `vsi590k_069295`; trash bin/window longer? | Trash bin; trash bin / trash bin / window | “The trash bin is longer.” / “the trash bin is longer than the window.” / “the window is longer than the trash bin.” |
| `vsi590k_183787`; slippers/shoes longer? | Shoes; shoes / shoes / slippers | “The shoes is longer.” / “The question asks for the longest: the shoes.” / “the slippers is longer than the shoes.” |
| `vsi590k_185213`; headphones/pillow shorter? | Headphones; pillow / headphones / headphones | “The pillow has the shorter edge.” / “the headphones is shorter than the pillow.” / “the headphones is shorter than the pillow.” |
| `vsi590k_186818`; ceiling light/bed shorter? | Ceiling light; ceiling light / bed / bed | “The shorter edge is the ceiling light.” / “the bed is shorter than the ceiling light.” / “The question asks for the closest: the bed.” |
| `vsi590k_188138`; shoes/slippers longer? | Shoes; shoes / shoes / slippers | “The shoes is longer.” / “then compare their longest edges.” / “the slippers is longer than the shoes.” |
| `vsi590k_189335`; plant/shoes longer? | Plant; shoes / plant / plant | “The shoes has the longer edge.” / “the plant is taller than the shoes, so its edge is longer.” / “the plant is taller than the shoes.” |
| `vsi590k_190123`; paper bag/laptop longer? | Laptop; laptop / paper bag / paper bag | “The laptop is longer.” / “the paper bag is longer than the laptop.” / “the paper bag is longer than the laptop.” |
| `vsi590k_190252`; bed/door shorter? | Door; door / bed / door | “The shorter edge is the door.” / “the bed is shorter than the door.” / “The question asks for the closest: the door.” |
| `vsi590k_191570`; trash can/bucket longer? | Trash can; trash can / trash can / bucket | “The trash can is longer.” / “the trash can is longer than the bucket.” / “the bucket is longer than the trash can.” |
| `vsi590k_272533`; refrigerator/table shorter? | Table; table / refrigerator / refrigerator | “The shorter edge is the table's.” / “the refrigerator is shorter than the table.” / “the refrigerator is shorter than the table.” |
| `vsi590k_274378`; toilet/table longer? | Table; table / toilet / toilet | “The table is longer.” / “the toilet is longer than the table.” / “the toilet is longer than the table.” |
| `vsi590k_274542`; sofa/table shorter? | Table; table / table / sofa | “The table is shorter.” / “the table is shorter than the sofa.” / “the sofa is shorter than the table.” |
| `vsi590k_275267`; tv/stool longer? | Tv; tv / stool / stool | “The tv is longer.” / “then compare their longest edges.” / “the stool is longer than the tv.” |
| `vsi590k_276759`; chair/stove shorter? | Stove; chair / stove / stove | “The chair is shorter.” / “then compare their longest edges.” / “the stove is shorter than the chair.” |
| `vsi590k_277330`; sofa/chair shorter? | Chair; chair / chair / sofa | “The chair is shorter.” / “the chair is shorter than the sofa.” / “the longer edge of the sofa is 101 cm; the longer edge of the chair is 104 cm.” |
| `vsi590k_278439`; toilet/chair shorter? | Chair; chair / toilet / chair | “The chair is shorter.” / “The question asks for the shorter: the toilet.” / “The question asks for the shorter: the chair.” |
| `vsi590k_278866`; stove/chair shorter? | Stove; chair / stove / stove | “The shorter edge is the chair's.” / “the stove is shorter than the chair.” / “the stove is shorter than the chair.” |
| `vsi590k_280289`; tv/chair longer? | Chair; tv / chair / chair | “The tv is longer.” / “the chair is longer than the tv.” / “the chair is longer than the tv.” |
| `vsi590k_281078`; refrigerator/chair shorter? | Chair; chair / refrigerator / refrigerator | “The shorter edge is the chair's.” / “the refrigerator is shorter than the chair.” / “the refrigerator is shorter than the chair.” |

**5. Hypotheses**
**HYPOTHESIS—overestimate and underestimate:** inherited class priors dominate instance scale. The constant door and keyboard answers support this; they do not prove the mechanism. The relevant proposed family is `object_size_estimation|r1g|rows_rebuild_d0_v1`. Its sampled webcam target says, “the question asks for the longest edge, in centimeters. I estimate it from the frames.” It then answers 20. All 20 of 20 sampled targets omit a measurement inside the think block.
The store catalog contains 9,778 of 9,778 kept size rows, but the coordinator explicitly states that R1 trains no size rows. Catalog presence therefore does not establish exposure. The observed numerical assertions cannot be attributed to newly trained size rows.
**HYPOTHESIS—wrong comparison and missing comparison:** transfer from other direct tasks changes an untrained relative-size task. `object_rel_distance|w1g|rows_rebuild_d0_v1` supplies the relevant ordering form on 20 of 20 sampled rows: “the candidates ordered nearest to farthest from the bag are: bookshelf, then boxes, then flipchart, then electrical duct.” Relative-size distance-order traces increase from 3 of 150 to 7 of 150; only 1 of 150 is wrong at either step. This supports template transfer, but does not explain the other reversed size relations.
**HYPOTHESIS—runaway:** the decoder repeats a Locate phrase. The removed `object_counting|r1g|rows_rebuild_d0_v1` sample says, “list each distinct box once, by the frame where it first appears: frame 7; frame 7; frame 8; frame 10; frame 15; frame 25.” However, the size loops repeat location words, not that list.
The removal file contains 17,879 of 17,879 records labelled `count_diag_first_seen_list_form`. Removal offers no direct explanation for changed length values, reversed comparisons, restored numerical traces, added distance wording, or increased out-of-range citations. A changed training mixture could indirectly cause these changes; that is a hypothesis. Runaways remain 1 of 293, so this read shows no reduction for size.

**6. Label or scoring defects**
Dev-S1’s `gt` and `gt_released` differ on 82 of 150 size items. For `vsi590k_055098`, step 400 answers 7.11 against `gt=6.8`, which is within 5%, yet receives 0.9; the released label 6.7 explains that score. Similarly, `vsi590k_053935` answers 0.43, with `gt=0.52`, released truth 0.54, and score 0.6. This is a loader/scoring-label inconsistency, not established physical-label error. All prices retain recorded scores; all ratios explicitly use `gt`.
No physical ground-truth or option defect was established. R0-dev `bd27924bbd5cdff459ad0fea` has cable-box truth 1,139 cm versus answer 40 cm; this deserves a geometry/instance audit, not automatic relabelling.

**7. Three changes**
1. **Proposed allocation: about 2,000 size rows** in `object_size_estimation|r1g|rows_rebuild_d0_v1`, actually included in training. Pair differently sized instances of the same class, especially small objects, and retain a bounded Locate line plus the longest-dimension instruction. The observable target is 344 of 443 completed numerical errors; this is an addressable set, not a predicted recovery. R0-dev small objects account for 74 of 88 errors and 16.14 points.
2. **Proposed allocation: about 1,500 new relative-size rows**, `relative_size_object|new_size_pairs|direct_longest_edge`. Use two Locate lines, an explicit size relation, and shorter/longer twins with shuffled options. The observable target is 19 of 150 wrong comparisons; direct task coverage also counters the distance-template substitution. Expected recovery is unknown.
3. **Proposed allocation: about 500 unit-twin size rows** in the size family, using the same instance in centimetres, metres, feet, and inches. Keep units attached through conversion and place the requested-unit scalar in the answer. This targets 4 of 150 step-400 unit-error candidates. **I am least sure of this change:** those errors could instead reflect wrong instance sizes.

**8. Not established**
RGB traces alone cannot distinguish perception error, instance selection, class-prior substitution, and incorrect geometry labels. Resolving them requires the dev videos with instance identities and verified dimensions. Attributing drift to counting-row removal requires matched continuation runs with and without removal; the active sampler manifest would also resolve catalog presence versus actual size-row exposure.

**Gates**
Force-closed items are 0 / 0 / 0 of 150 for dev-S1 size, 1 / 1 / 1 of 293 for R0-dev size, and 0 / 0 / 0 of 150 for relative size. The three R0-dev runaways are different items, listed above.
Traces explicitly citing a frame above 32 occur on 1 / 15 / 15 of 150 dev-S1 size items, 6 / 18 / 27 of 293 R0-dev size items, and 4 / 2 / 2 of 150 relative-size items. Explicit seconds-labelled images are excluded from this frame-index count.
Confirmed answer departures from a stated conclusion are 0 of 150 dev-S1 size items, 0 of 293 R0-dev size items, and 0 of 150 relative-size items at each step. Missing conclusions are not counted as agreement: numerical size has 1 of 293 at each step; relative size has 0 / 12 / 1 of 150.
Relative size has shorter/smaller questions on 73 of 150 items. Step 400 gets 8 of 73 wrong, but selects the trace’s shorter object on each: confirmed polarity reversals are 0 of 73. Calls occur on 0 of 593 analysed items at each step; away-turn and counting gates do not apply.

**Appendix — CLASSIFIER**
```python
import sys
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

types = ["object_size_estimation", "relative_size_object"]
no_comparison = {
    544: set(),
    200: {"vsi590k_069249", "vsi590k_275267"},
    400: set(),
}
for dataset in ["dev-S1", "R0-dev"]:
    for run, step in [("S1", 544), ("R1", 200), ("R1", 400)]:
        rows = K.direct(run, step, dataset, types=types)
        for typ in types:
            group = [r for r in rows if r["type"] == typ]
            if not group:
                continue
            counts, losses = Counter(), defaultdict(float)
            for r in group:
                if r["score"] == 1:
                    continue
                if r["forced_close"]:
                    mode = "Runaway"
                elif typ == "object_size_estimation":
                    mode = ("Overestimate"
                            if float(r["pred"]) > float(r["gt"])
                            else "Underestimate")
                elif r["id"] in no_comparison[step]:
                    mode = "No comparison stated"
                else:
                    mode = "Wrong comparison"
                counts[mode] += 1
                losses[mode] += 1 - r["score"]
            modes = (["Overestimate", "Underestimate", "Runaway"]
                     if typ == "object_size_estimation"
                     else ["Wrong comparison", "No comparison stated"])
            assert sum(counts.values()) == sum(
                r["score"] < 1 for r in group
            )
            for mode in modes:
                print(dataset, typ, step, mode,
                      f"{counts[mode]} of {len(group)}",
                      f"{100 * losses[mode] / len(group):.2f} points")
```