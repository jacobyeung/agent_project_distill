**1. Scope**

All 117 of 300 step-200 errors occur in the stated spatial relation. The answers follow those relations correctly.

I analyzed only the assigned VSTI relative dev items. Below, **v3** means `camera_obj_rel_dist_v3`; **nf** means `obj_obj_relative_pos_nf`.

| Type | Step 544 correct | Step 200 correct | Change |
|---|---:|---:|---:|
| v3 | 83 of 150; 55.33% | 89 of 150; 59.33% | +4.00 points |
| nf | 77 of 150; 51.33% | 94 of 150; 62.67% | +11.33 points |

I recomputed scores from `items_a0.jsonl` under the following paths. Each directory supplies `a0/results/budget_2048/0/` for scores and `a0/results/0/` for full traces:
- Step 200: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/build/a35f73e87f0/fetched/x/r6/`.
- Step 544: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/build/acb2faedd41/fetched/x/r6/`.

The exact v3 form is “Measuring from the closest point of each object, which of these objects (A, B) is the closest to the camera in frame k of 32?” All 150 of 150 have two object options and ask **closest**.
The exact nf form is “In frame k of 32, relative to the camera, is A [Near/Far] compared to B?” All 150 of 150 have Near/Far options, with their letter assignment shuffled.

Uniform random choice has 50% expected accuracy, or 75 of 150, for each type. Each type’s truth letters are A on 75 of 150 and B on 75 of 150.
The best constant letter scores 75 of 150: step 200 exceeds it by 9.33 points for v3 and 12.67 points for nf.
For nf, the best constant **word**, “Far,” scores 86 of 150, or 57.33%. Step 200 exceeds that baseline by only 5.33 points. For v3, object words vary; the most frequent truth word, “bed,” occurs on 6 of 150.

**2. Failure modes**

I classified every wrong item. Costs are percentage points of the corresponding type, using `100 × error count / 150`.

| Primary mode | Definition | v3 count; cost | nf count; cost |
|---|---|---:|---:|
| Wrong distance order | The stated nearest-to-farthest order contradicts the truth; the answer follows it. | 61 of 150; 40.67 | 0 of 150; 0 |
| Wrong near/far relation | The stated nearer-object relation contradicts the truth; the answer follows it. | 0 of 150; 0 | 56 of 150; 37.33 |
| Answer contradicts trace | The answer does not follow the stated relation. | 0 of 150; 0 | 0 of 150; 0 |
| Runaway | The think block is force-closed. | 0 of 150; 0 | 0 of 150; 0 |
| Missing or unparsed answer | The scored answer is absent or invalid. | 0 of 150; 0 | 0 of 150; 0 |
| **Total errors** | Each error appears once. | **61 of 150; 40.67** | **56 of 150; 37.33** |

The relation, concluding sentence, and answer agree on 150 of 150 items per type. B2048 and ON16k answers also agree on 150 of 150 per type.

**Frame use.** Every trace names the correct requested viewpoint: 150 of 150 per type. However, both Locate lines cite frames other than k on 142 of 150 v3 items and 144 of 150 nf items. Those groups contain 59 of 61 v3 errors and 54 of 56 nf errors.

| Trace’s first-seen claims | v3 errors within group | nf errors within group |
|---|---:|---:|
| At least one first-seen frame exceeds k | 42 of 94; 44.68% | 37 of 102; 36.27% |
| Neither first-seen frame exceeds k | 19 of 56; 33.93% | 19 of 48; 39.58% |
| At least one first-seen frame exceeds 32 | 24 of 51; 47.06% | 22 of 61; 36.07% |
| Both first-seen frames fall within 1–32 | 37 of 99; 37.37% | 34 of 89; 38.20% |

Taken literally on the supplied frame numbering, a first sighting after k implies that the object was not visible at k: this applies to 42 of 61 v3 errors and 37 of 56 nf errors. These are **trace claims, not verified visibility**. A first sighting before k does not establish visibility at k.
Errors show modest concentration in the later-first-seen group for v3, but none for nf. Neither type supplies frame-k visual evidence beyond asserting the relation.

**Answer bias.**

| Distribution | v3 truth | v3 prediction | nf truth | nf prediction |
|---|---:|---:|---:|---:|
| A | 75 of 150 | 50 of 150 | 75 of 150 | 71 of 150 |
| B | 75 of 150 | 100 of 150 | 75 of 150 | 79 of 150 |
| Near | — | — | 64 of 150 | 56 of 150 |
| Far | — | — | 86 of 150 | 94 of 150 |

For v3, A truths become B answers on 43 of 75 items; B truths become A answers on 18 of 75. Selected word frequencies, truth/prediction, are bed: 6 of 150 / 6 of 150; cabinet: 5 of 150 / 4 of 150; whiteboard: 4 of 150 / 4 of 150; table: 2 of 150 / 5 of 150; monitor: 0 of 150 / 4 of 150; all other words: 133 of 150 / 127 of 150.
For nf, Near truths become Far answers on 32 of 64 items; Far truths become Near answers on 24 of 86. These are wrong stated relations, not errors in translating the relation into an option.
There are 0 of 150 v3 farthest questions, so closest/farthest instruction reversal is untested.

**Twins.** No nf item has a same-room, same-frame, same-object-pair counterpart: 0 of 150 items qualify. Object pairs recur across different frames for 8 of 150 items; swapped roles occur among 4 of those 8. They are not mirrored twins, so inverse-answer consistency would be invalid to score. Left/right and up/down were outside this assignment.

**3. Examples**

These excerpts are verbatim; questions are shortened. Every example is from the VSTI relative dev set.

**Wrong distance order:**
- `05d8b6f6c2a4fd426e6173be`: Closest of mirror/mixer glass at frame 31? Truth A, mirror; answer B, mixer glass.  
  “Step 3: locate the mixer glass, first seen in frame 68.” … “the objects are mixer glass, then mirror.”
- `10e5f5a767e02d77f8bfe14e`: Closest of office table/desk lamp at frame 23? Truth A, office table; answer B, desk lamp.  
  “Step 4: ordered nearest to farthest from the camera viewpoint of frame 23, the objects are desk lamp, then office table.”
- `12e30aecc8fbebde8bb63561`: Closest of hallway/storage rack at frame 20? Truth A, hallway; answer B, storage rack.  
  “Step 2: locate the hallway, first seen in frame 28.” … “the objects are storage rack, then hallway.”

**Wrong near/far relation:**
- `0bf2a6e28720478fd29be3c1`: At frame 24, is cable raceway Near/Far compared to dustpan? Truth A, Near; answer B, Far.  
  “Step 4: from the camera viewpoint of frame 24, the dustpan is nearer than the cable raceway.”
- `0e2afcecf4d5c12c5710d3f3`: At frame 28, is cooking pot Near/Far compared to jacket? Truth B, Near; answer A, Far.  
  “Step 4: from the camera viewpoint of frame 28, the jacket is nearer than the cooking pot.”
- `0f4aa3c680bbd78205524f3a`: At frame 31, is file cabinet Near/Far compared to backpack? Truth A, Far; answer B, Near.  
  “Step 4: from the camera viewpoint of frame 31, the file cabinet is nearer than the backpack.”

The zero-count modes have no examples.

**4. Step 544 against step 200**

| Transition | v3 | nf |
|---|---:|---:|
| Right to wrong | 22 of 150 | 29 of 150 |
| Wrong to right | 28 of 150 | 46 of 150 |
| Wrong to wrong | 39 of 150 | 27 of 150 |
| Right to right | 61 of 150 | 48 of 150 |

For v3, step 544 uses “find the camera (first seen in frame k)” and unsupported metric distances on 150 of 150 items. Step 200 replaces these with object Locate lines and a verbal order on 150 of 150. Mean think length rises from 61.4 to 89.6 tokens. Among wrong-to-right items, it rises from 61.2 to 89.6; among right-to-wrong items, from 61.3 to 89.6.

For nf, step 544 starts by finding the camera on 140 of 150 items, states metric distances on 146 of 150, and omits at least one queried object name from its think block on 107 of 150. Among improved items, that omission occurs on 29 of 46; among regressed items, on 18 of 29. Step 200 compares both queried objects on 150 of 150. Mean think length remains similar: 88.9 versus 89.1 tokens.

For example, the old trace for `0bf2a6e28720478fd29be3c1` concludes “So the camera is near the dustpan,” accidentally earning the correct label while omitting cable raceway. The new trace addresses the actual comparison but gets it wrong. Improved template compliance therefore does not guarantee improved geometry.

**5. Hypotheses**

Training evidence comes from the named `STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json` in `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`.

**HYPOTHESIS — wrong distance order:** `camera_obj_rel_dist_v3|vsti_rel_v4|None` teaches a fluent order without requiring evidence that connects object sightings to camera k. The sample contains later-first-seen citations on 7 of 20 rows; 20 of 20 are kept. Row 156785 says “take the camera viewpoint of frame 19,” then “locate the pull up bar, first seen in frame 25,” then “the objects are pull up bar, then weight rack.” This supports a weak grounding hypothesis, not a proven cause.

**HYPOTHESIS — wrong near/far relation:** `obj_obj_relative_pos_nf|vsti_rel_v4|None` repairs the queried-object roles but still supervises an asserted relation without the viewpoint transfer needed to justify it. Later-first-seen citations occur on 8 of 20 sampled rows; 19 of 20 are kept. Kept row 160687 says “take the camera viewpoint of frame 17,” “locate the sofa, first seen in frame 27,” and “the bathtub is nearer than the sofa.”

The sampled targets contain out-of-range frame citations on 0 of 20 rows per family. Thus, those samples do not establish that training targets directly supplied the model’s frame indices above 32. The trace ruling permits first-seen or best-view citations; a citation outside k is not itself a ruling violation.

**6. Label or scoring defects**

None found in the available text checks. Option decoding matches the recorded score on 150 of 150 items per type; ground-truth fields disagree on 0 of 150 per type.
The frame indices above 32 are trace defects under the stated input numbering, not demonstrated label defects. I did not inspect RGB frames or independently verify spatial labels.

**7. Three changes**

These are proposals. The affected-error counts are candidate ceilings, not predicted recoveries, and overlap.

1. **Reword Locate lines in both families to make the frame reference verifiable.** Review all kept rows: 1,978 of 1,998 v3 rows and 1,982 of 2,000 nf rows. Use supplied-frame indices; cite frame k when supported, otherwise distinguish an identifying view from the requested camera viewpoint without inventing visibility. This targets the later-first-seen claims accompanying 42 of 61 v3 errors and 37 of 56 nf errors. **I am least sure this improves accuracy:** nf errors do not concentrate in that group.
2. **Add approximately 600 v3 rows with controlled option-order reversals and closest-point evidence**, in `camera_obj_rel_dist_v3|vsti_rel_v4|None`. Keep the object order and answer consistent when options swap; retain the question’s closest-point criterion. This addresses the B-selection asymmetry accompanying 43 of 61 v3 errors. Guess: some are positional shortcuts; the traces cannot establish how many.
3. **Add approximately 600 nf rows as same-frame role-swapped pairs**, in `obj_obj_relative_pos_nf|vsti_rel_v4|None`, balancing Near/Far and their option letters. Supervise the inverse relation when object roles swap, with grounded object evidence. This could address up to 56 of 56 nf errors because all are relation errors; recoverable yield is unknown. Existing dev items cannot test same-frame twin consistency.

**8. Not established**

The traces do not establish actual visibility at k, whether first-seen indices refer to another frame numbering, or whether the model visually uses k. Supplied-frame mappings and object visibility annotations would settle the first two; controlled viewpoint substitutions would test the third.
The report cannot separate incorrect perception, incorrect viewpoint transfer, and a plausible relation written after choosing an answer. Matched visual interventions and training ablations would distinguish them.
No causal recovery estimate or visual label audit is established. The checkpoint comparison is retained because it is explicitly requested and measures behavior.

**Appendix — CLASSIFIER**

```python
import re
import sys
from collections import Counter

sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

T = ["camera_obj_rel_dist_v3", "obj_obj_relative_pos_nf"]
rows = K.vsti("R1", 200, types=T)
modes = ["wrong_order", "wrong_near_far", "answer_mismatch",
         "runaway", "missing_or_unparsed"]

for typ in T:
    items = [x for x in rows if x["type"] == typ]
    counts, costs = Counter(), Counter()
    for x in items:
        text = x["text"].split("</think>")[0]
        opts = {s[3:]: s[0] for s in x["options"]}
        assert x["pred"] == x["pred_on"]
        assert x["score"] == float(x["pred"] == x["gt"])
        if x["forced_close"]:
            mode = "runaway"
        elif x["pred"] not in opts.values():
            mode = "missing_or_unparsed"
        else:
            if typ == T[0]:
                m = re.search(r"the objects are (.+?), then (.+?)\.", text)
                assert m and set(m.groups()) == set(opts)
                rel = opts[m[1]]
                s = re.search(r"So the (.+?) is closest", text)
                assert s and opts[s[1]] == rel
            else:
                q = re.search(
                    r"is (.+?) \[Near/Far\] compared to (.+?)\?",
                    x["question"])
                m = re.search(
                    r", the (.+?) is nearer than the (.+?)\.", text)
                assert q and m and set(q.groups()) == set(m.groups())
                rel = opts["Near" if m[1] == q[1] else "Far"]
                s = re.search(
                    r"So the (.+?) is (nearer|farther) than the (.+?) relative",
                    text)
                assert s and (s[1], s[3]) == q.groups()
                assert opts["Near" if s[2] == "nearer" else "Far"] == rel
            mode = ("answer_mismatch" if x["pred"] != rel else
                    "wrong_order" if typ == T[0] else "wrong_near_far")
        if x["score"] < 1:
            counts[mode] += 1
            costs[mode] += 1 - x["score"]
    assert sum(counts.values()) == sum(x["score"] < 1 for x in items)
    for mode in modes:
        print("vsti", typ, mode,
              f"{counts[mode]} of {len(items)}",
              f"cost={100 * costs[mode] / len(items):.2f} points")
```