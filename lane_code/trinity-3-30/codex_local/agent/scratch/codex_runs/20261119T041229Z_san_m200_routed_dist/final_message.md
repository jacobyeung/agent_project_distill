## 1. Scope

Step 200 improves mainly through unit conversion, not better gap estimates. I audited all calling `object_abs_distance` items in dev-S1 and classified every item with stored `score < 1`.

| Recomputed measure | Step 544 | Step 200 |
|---|---:|---:|
| Stored-score MRA, full type | 28.27% on 150 of 150 | 50.27% on 150 of 150 |
| Items receiving full credit | 20 of 150 | 26 of 150 |
| Calling items; their stored-score MRA | 149 of 150; 28.46% | 88 of 150; 54.20% |
| MRA recomputed against loader `gt` | 28.33% | 50.67% |

**Scoring distinction:** `K.routed().score` uses stored scores against the manifest’s `answer`, whereas `K.routed().gt` exposes `ground_truth`. These labels differ on 140 of 150 items. Below, **displayed truth** means `gt`; **scored truth** means manifest `answer`. Failure costs use the requested stored score.

Files: let `P=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route`. Step 200 used `P/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`. Step-544 distance comes from `P/out3s/bases/b1/work/ret/metadata/reads/1/metadata/journals/3/0/items.jsonl`; the loader also reads read-0 journals 0–4. Labels came through its manifests, including `P/out3s/A/src/items/devs1_routed.json`.

| Component | Step 544 | Step 200 |
|---|---|---|
| **Placement** | Correct call sequence and question operands: 149 of 149 callers. Served: 447 of 447 calls. Malformed/unserved: 0 of 447; extra calls: 0 of 149 items. | Correct sequence and operands: 88 of 88 callers. Served: 264 of 264 calls. Malformed/unserved: 0 of 264; extra calls: 0 of 88 items. |
| **Head accuracy** | Numeric gap: 142 of 149 callers. Printed-gap MRA: **61.83% displayed / 61.69% scored**. Counting missing gaps as zero gives 58.93% / 58.79%. | Numeric gap: 85 of 88 callers. Printed-gap MRA: **65.06% displayed / 65.29% scored**. Counting missing gaps as zero gives 62.84% / 63.07%. |
| **Usage** | Answer follows converted gap: 68 of 142 numeric outputs. Departures: 74 of 142; helped 4 of 74, hurt 60 of 74, tied 10 of 74. | Answer follows converted gap: 72 of 85 numeric outputs. Departures: 13 of 85; helped 1 of 13, hurt 12 of 13, tied 0 of 13. |

Usage equality allows a difference of 0.011 requested units from the gap converted and rounded to two decimals. Step-544 departures therefore include small rounding differences.

| Asked unit | Step 544: numeric outputs among callers; head MRA displayed/scored | Step 200: numeric outputs among callers; head MRA displayed/scored |
|---|---|---|
| Metres | 42 of 43; 60.71% / 59.76% | 35 of 36; 60.57% / 60.29% |
| Feet | 43 of 46; 62.33% / 62.09% | 30 of 30; 61.33% / 61.67% |
| Inches | 31 of 32; 51.29% / 51.94% | 8 of 9; 76.25% / 77.50% |
| Centimetres | 26 of 28; 75.38% / 75.77% | 12 of 13; 80.00% / 80.83% |

| Displayed truth in metres | Step 544: coverage; MRA; mean absolute error | Step 200: coverage; MRA; mean absolute error |
|---|---|---|
| Below 0.5 m | 6 of 142; 28.33%; 0.878 m | 3 of 85; 33.33%; 1.159 m |
| 0.5–2 m inclusive | 59 of 142; 60.68%; 0.372 m | 31 of 85; 57.74%; 0.396 m |
| Above 2 m | 77 of 142; 65.32%; 0.834 m | 51 of 85; 71.37%; 0.726 m |

Grounding prints frames and one box for 291 of 298 grounds at step 544 and 173 of 176 at step 200; the remaining 7 of 298 and 3 of 176 say `not seen`. Both grounded names match the question on 149 of 149 and 88 of 88 callers. Multiple boxes appear in 0 of 291 and 0 of 173 successful grounds. The visible pair is B1/B2; the text does **not** establish how many physical instances exist or which hidden instance pair was selected.

Every gap uses `rule="box_grid_5cm"`: 149 of 149 at step 544 and 88 of 88 at step 200, including all right and wrong items. The phrase “taken over every pair of instances” is boilerplate, not an instance-selection receipt.

Step 200 has **0 of 85** numeric gaps equal to zero. Step 544 has **1 of 142**: `vsi590k_045786`, desk–table, prints `0.00 m`; displayed truth is 2.6 ft = 0.79248 m, scored truth 2.5 ft = 0.762 m. Overlapping boxes are not established as its cause. Mean signed error is −0.177 m at step 544 and −0.083 m at step 200; nevertheless, 52 of 85 step-200 gaps are high and 33 of 85 are low. Large underestimates drive the negative mean.

## 2. Failure modes at step 200

Each wrong item receives exactly one primary mode. Usage errors take precedence over an inaccurate numeric head; failed grounds receive their own mode. Costs are assigned losses, **not guaranteed recoverable gains**.

| Mode | Definition | dev-S1 count | Cost on full type |
|---|---|---:|---:|
| No call | Known coverage failure: 62 of 150 omit tools; 55 of 62 lose credit. | 55 of 150 | 22.8667 points |
| Head value copied | The printed gap loses credit against scored truth; the answer follows it. | 54 of 150 | 17.3333 points |
| Missing unit conversion | Metres are answered directly: centimetres on 11 of 12 cases, feet on 1 of 12. | 12 of 150 | 7.9333 points |
| Conversion arithmetic | The trace uses the correct factor but computes the product incorrectly. | 1 of 150 | 0.2667 points |
| Failed ground; unsupported answer | `not seen` becomes zero or an invented measurement/conversion. | 2 of 150 | 1.3333 points |
| **Total** | All stored-score failures are classified. | **124 of 150** | **49.7333 points** |

Among callers, 69 of 88 lose credit: faithful head errors account for 54 of 69; departures from a full-credit head account for 5 of 69; departures from an already inaccurate head account for 8 of 69; failed-ground answers account for 2 of 69. Misplacement and missing/unparsed answers each affect 0 of 88 callers. All 88 of 88 calling traces finish with `eos`.

**Centimetres:** 11 of 13 callers copy metres: `vsi590k_042674`, `042690`, `044593`, `046212`, `161841`, `164784`, `164817`, `169469`, `251506`, `251967`, `253040`—all suffixes carry the `vsi590k_` prefix. `vsi590k_161834` is 1 of 13 and answers zero after `not seen`; `vsi590k_256028` is 1 of 13 and correctly converts 3.62 m to 362 cm. Thus 12 of 13 fail to convert correctly, but only 11 of 13 demonstrably answer metres.

The omitted feet conversion, `vsi590k_163095`, accidentally helps: its stored score is 0.1, versus 0 for correctly converting its inaccurate 2.24 m gap. The arithmetic slip, `vsi590k_252282`, answers 10.89 instead of 10.99 ft, reducing score from 0.7 to 0.6. A wrong factor appears in 1 of 3 failed-gap traces, `vsi590k_165307`; no numeric response supports its calculation.

**Computed by me, using scored truth:** (a) making all 85 of 85 available-gap answers equal gap × correct factor, while retaining the 3 of 88 missing-gap answers, raises calling MRA from **54.20% to 64.20%**. Assigning zero to missing outputs instead gives **63.07%**. (b) replacing those available gaps with perfect values while preserving each observed answer/gap multiplier gives **84.09%**, retaining the missing-gap answers. If the remaining 3 of 88 also receive correct answers, it becomes **86.36%**. These are conditional calculations, not simulated model generations; usage after newly successful grounds is unobserved.

## 3. Examples

All examples are dev-S1. Truth is shown as **displayed / scored**. Quotes reproduce trace text; shortened questions retain the original words.

- **Head value copied — `vsi590k_046210`.** Q: “State the distance from the closest point on the mirror to the nearest point on the door in meters.” Truth: 1.3 / 1.25 m; answer: 2.72.
  Trace: `distance 2.72 m` … `The box distance is 2.72 m.`
- **Head value copied — `vsi590k_050630`.** Q: “Determine the shortest distance between the backpack and the keyboard in meters.” Truth: 6.1 / 6.12 m; answer: 2.72.
  Trace: `distance 2.72 m` … `The box distance is 2.72 m.`
- **Head value copied — `vsi590k_161799`.** Q: “…what's the gap between the laptop and the toilet expressed in meters?” Truth: 3.0 / 3.04 m; answer: 0.27.
  Trace: `distance 0.27 m` … `The box distance is 0.27 m.`
- **Missing conversion — `vsi590k_042690`.** Q: “…what's the extent between the refrigerator and the desk in centimeters?” Truth: 120.0 / 124.3 cm; answer: 1.22.
  Trace: `distance 1.22 m` … `The box distance is 1.22 m.` … `<answer>1.22</answer>`
- **Missing conversion — `vsi590k_046212`.** Q: “…the trash bin to the nearest point on the door in centimeters.” Truth: 130.0 / 129.3 cm; answer: 1.32.
  Trace: `distance 1.32 m` … `The box distance is 1.32 m.` … `<answer>1.32</answer>`
- **Missing conversion — `vsi590k_164817`.** Q: “…how far apart are the bookshelf and the printer in centimeters?” Truth: 350.0 / 354.2 cm; answer: 3.59.
  Trace: `distance 3.59 m` … `The box distance is 3.59 m.` … `<answer>3.59</answer>`
- **Arithmetic — `vsi590k_252282`, the sole case, 1 of 1.** Q: “…distance separating the nearest points of the stove and the stool, measured in feet?” Truth: 13.8 / 13.7 ft; answer: 10.89.
  Trace: `distance 3.35 m` … `Converting to feet: 3.35 x 3.28084 = 10.89.`
- **Failed ground — `vsi590k_161834`.** Q: “…gap between the printer and the slippers expressed in centimeters?” Truth: 680.0 / 676.4 cm; answer: 0.
  Trace: `slippers: not seen` … `not seen` … `The box gap is not seen, so I find the box gap to be null.`
- **Failed ground — `vsi590k_165307`.** Q: “Determine the shortest distance between the door and the shoe rack in inches.” Truth: 90.6 / 90.1 in; answer: 11.24.
  Trace: `shoe rack: not seen` … `not seen` … `Converting to inches: 114.17 x 0.0984252 = 11.24.`

Those are all 2 of 2 wrong failed-ground cases. The remaining case, `vsi590k_165318`, also invents a measurement after `shoe rack: not seen`, but its answer 3.39 receives full credit against 3.49; it is not a third failure example.

## 4. Step 544 against step 200

Across dev-S1, right→wrong occurs on 5 of 150, wrong→right on 11 of 150, wrong→wrong on 119 of 150, and right→right on 15 of 150. Among shared callers, the corresponding counts are 1 of 88, 4 of 88, 68 of 88, and 15 of 88.

Call strings match on **88 of 88** shared callers. Complete response sequences match on **0 of 88**; gap-response text matches on **10 of 88**, including the 3 of 88 shared `not seen` responses. Among paired numeric gaps, step 200 is closer to displayed truth on 27 of 85, step 544 on 51 of 85, and ties occur on 7 of 85. Against scored truth, those counts are 29 of 85, 49 of 85, and 7 of 85.

On shared numeric outputs, printed-gap MRA falls from **68.00% to 65.06%** against displayed truth, or **67.18% to 65.29%** against scored truth. Yet shared-caller answer MRA rises from **36.25% to 54.20%**.

All 4 of 4 calling wrong→right flips add feet conversion: `vsi590k_163648`, `163815`, `252500`, `253363`. For example, `252500` changes from gap/answer 3.16 m/3.16 to 3.23 m/10.59 ft. The sole calling regression, `vsi590k_169442`, copies a worse gap: 3.52 m becomes 3.71 m, reducing score from 1 to 0.9. These traces retain the same call form; mean calling length falls from 337.8 to 316.8 tokens.

The remaining flips—4 of 5 regressions and 7 of 11 improvements—stop calling and use direct traces. Most are shorter, although 2 of 7 improvements contain long repeated lists. Their outcomes do not demonstrate improved head accuracy.

## 5. Hypotheses

I read the supplied unit file line by line and the supplied store samples/counts. Define **U** as `object_abs_distance|None|None`, with `provenance.family="units"` in `r1_ops6/cp/out/units/packed.jsonl`. The literal pool/retrace fields are absent. The v7 family index contains no `object_abs_distance` family.

- **HYPOTHESIS—copied head errors:** supervision with annotation-derived boxes teaches confident copying without exposing deployed grounding errors. All 747 of 747 U rows identify masks and geometry as `gt`. Row `a0_units_vsi590k_047478` prints `distance 2.55 m` and concludes `Converting to feet: 2.55 x 3.28084 = 8.37.` This supports a supervision mismatch, not proof of its causal effect.
- **HYPOTHESIS—missing conversion:** coverage is unit-specific. U contains feet on 683 of 747 rows, inches on 64 of 747, and centimetres on 0 of 747. Its target `Converting to inches: 1.24 x 39.3701 = 48.82.` closely matches the successful inference form; centimetre callers usually retain the metric closing sentence.
- **HYPOTHESIS—arithmetic:** U teaches generated arithmetic text without enforcing its result. The correct target above contrasts with `3.35 x 3.28084 = 10.89`; the factor is understood, but the multiplication is not reliable.
- **HYPOTHESIS—failed grounds:** U supplies successful measurement examples, with `not seen` in 0 of 747 targets. The same `distance 2.55 m` → conversion target offers no example of how to continue after a missing operand. This fits both fabricated-value failures.

These are evidence from packed candidate rows: `training_admitted` is false on 747 of 747. Their final training membership cannot be established from this file alone.

## 6. Label or scoring defects

The loader/scorer label mismatch changes 19 of 150 step-544 scores and 38 of 150 step-200 scores. All 150 of 150 stored scores at each step reproduce against manifest `answer`. This is a confirmed reporting-contract mismatch; I cannot determine which label should govern the experiment.

At step 200, 6 of 150 items lose stored credit despite full credit against displayed truth: `vsi590k_042645`, `163082`, `163793`, `163811`, `251447`, `251453`. Among callers, `163811` answers 0.21 against displayed/scored 0.20/0.19, yielding 1.0/0.8; `251447` answers 16.14 against 15.4/15.1, yielding 1.0/0.9. Thus 2 of 54 “head value copied” failures depend entirely on the label choice.

No additional ground-truth defect was established from the text alone.

## 7. Three changes for vehicle N

1. **Add about 2,000 unit rows to U**, emphasizing centimetres and varied question wording; require one explicit factor/product line and a matching answer. Include arithmetic validation when constructing targets. Correcting the centimetre omissions improves 11 of 69 calling failures and fully repairs 5 of 69, worth **5.87 type points**. Correcting the arithmetic improves another 1 of 69 by **0.067 points**. Correcting the omitted feet conversion alone does not help its inaccurate head.
2. **Rebuild about 2,000 routed/direct training pairs** in a proposed `object_abs_distance|deployed_pairs|response_correct_route_else_direct` family. Use deployed responses on training scenes, retaining routed targets where measurements agree and direct targets where they fail, as the ruling specifies. This targets 54 of 69 faithful-copy failures, although only 52 of 54 also fail displayed truth. Their assigned ceiling is **17.33 type points**. **I am least sure of this change:** language rows may not repair inaccurate boxes, scale, or instance selection.
3. **Add about 400 failure-recovery rows** in a proposed `object_abs_distance|deployed_recovery|failed_ground_to_direct` family. After an actual missing-operand response, require a bounded direct answer grounded in visible frames; prohibit invented tool measurements and fabricated conversions. This targets 2 of 69 calling failures, with a ceiling of **1.33 type points**; preserve the already correct outcome on the remaining 1 of 3 missing-gap items.

## 8. Not established

The traces do not identify physical instance multiplicity, the selected instance pair, or whether box fit, depth, scale, or association causes each bad gap. Grounding receipts with instance identities and annotated geometry would settle those questions; repeated “every pair” prose does not.

Actual performance after changing head responses requires rerunning generation. Packed-row admission and training exposure require the final training manifest. Routed returns identify arm `tower`; the loader does not expose paired B2048/ON16k traces or `forced_close`, so I did not infer those flags.

## Appendix: CLASSIFIER

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the section-2 counts and costs without reading the SQLite store.

```python
import os, sys
from collections import defaultdict
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

rows = K.routed(200, types=["object_abs_distance"])
sc = K._scorer().scorers

def classify(r):
    if r["score"] == 1:
        return None
    if not r["calls"]:
        return "No call"
    gaps = [sc.printed(c) for c in r["calls"] if c["family"] == "gap"]
    gaps = [v["distance"] for v in gaps if v is not None]
    if not gaps:
        return "Failed ground; unsupported answer"
    gap = gaps[-1]
    factor = sc.unit_factor(r["question"])
    answer = float(r["answer"])
    if abs(answer - round(gap * factor, 2)) > .011:
        if factor != 1 and answer == gap:
            return "Missing unit conversion"
        return "Conversion arithmetic"
    return "Head value copied"

totals = defaultdict(int)
groups = defaultdict(list)
for r in rows:
    totals[r["set"]] += 1
    name = classify(r)
    if name:
        groups[r["set"], name].append(r)
for (setname, name), group in sorted(groups.items()):
    n = totals[setname]
    loss = 100 * sum(1-r["score"] for r in group) / n
    print(setname, name, f"{len(group)} of {n}", f"{loss:.4f} points")
print("All wrong:", sum(r["score"] < 1 for r in rows), "of", len(rows))
```