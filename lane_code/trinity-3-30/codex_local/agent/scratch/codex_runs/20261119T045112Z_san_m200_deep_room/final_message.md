**1. Question and answer**

1. **How do scores vary with room size and units, and do answers regress toward a typical size?** Step 200 scores 64.40 MRA on 134 items, versus 33.88 for their median-truth constant. Answers track truth (Pearson r = 0.827, n = 134), but compress its range: all 9 of 134 rooms above 60 m² are underestimated.

2. **Does the trace determine the number, and do landmark repetitions or frame choices explain errors?** None of 134 traces contains a numeric area derivation; all 134 list exactly three landmarks. Repeated object names occur in 19 of 134 and frame-1-only lists in 14 of 134, but both groups score better than their complements; neither flag establishes an error mechanism.

3. **Are square-feet conversions written and correct?** Conversions appear in 0 of 7 traces. One of 7 answers plausibly retains square-metre magnitude; multiplying that answer by 10.7639 raises its MRA from 0 to 60, but still leaves an estimation error.

4. **Which checkpoint is closer on the 19 items without a step-544 call-cap finish?** Step 200 scores 65.26 versus 46.32 MRA on those 19 items. Among 18 numeric step-544 answers, step 200 is closer on 11 of 18; the remaining step-544 item has a malformed answer.

5. **Do 40 training rows derive area, and what does the ruling require?** All 40 sampled rows place an unsupported-by-arithmetic estimate after `</think>`, as the ruling explicitly requires for direct numeric types. Their lists contain two or three landmarks; 38 of 40 sampled rows remain in training.

6. **Which change should vehicle N prioritize?** Unit repair offers the clearest small, measurable correction: one candidate item among 134. A calibrated scale-and-area head could address a much larger error pool, particularly the 9 large rooms, but these reads establish no head gain; adding a numeric derivation without metric evidence would fabricate support.

**2. Evidence**

Scores below are MRA percentages. I use scored `gt`, normalize square-feet quantities to m² for physical-size statistics, and define signed error as prediction minus truth.

**Source files and scope.** Evaluation results come through `san_kit.py` from these paths beneath `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/`:

- Part B, step 200: `r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`.
- Part B, step 544: `r1route/out3s/bases/b2/work/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`.
- Part A: corresponding `out3/A4/ret/` and `out3s/bases/b1/work/ret/` journal files loaded by `K.routed`.
- These are **G3T routed-reader outputs**, without separate B2048/ON16k arms or `forced_close` flags. Part A’s 36 of 36 IDs also occur in B; their generated texts match on only 20 of 36, so A is reported separately rather than pooled.

**Truth bands and units**

| Group | B items | B step 544 → 200 MRA | B mean signed error, m² | A items | A step 544 → 200 MRA |
|---|---:|---:|---:|---:|---:|
| Under 15 m² | 39 of 134 | 2.82 → 70.77 | −0.05 | 4 of 36 | 25.00 → 62.50 |
| 15–<30 m² | 53 of 134 | 3.21 → 65.85 | −3.02 | 14 of 36 | 0.00 → 74.29 |
| 30–60 m² | 33 of 134 | 18.18 → 67.27 | −6.29 | 18 of 36 | 17.78 → 62.22 |
| Over 60 m² | 9 of 134 | 0.00 → 17.78 | −48.78 | 0 of 36 | — |
| Square metres asked | 127 of 134 | 6.69 → 63.86 | −6.30 | 29 of 36 | 13.45 → 66.21 |
| Square feet asked | 7 of 134 | 4.29 → 74.29 | −1.13 | 7 of 36 | 4.29 → 70.00 |
| All | 134 of 134 | 6.57 → 64.40 | −6.03 | 36 of 36 | 11.67 → 66.94 |

For B, predictions fall below truth on 104 of 134 items and above truth on 30 of 134. Median signed error is −2.60 m²; median relative error is −15.78%; mean absolute error is 7.42 m² (n = 134).

| Signed relative-error band | B items |
|---|---:|
| Below −50% | 6 of 134 |
| −50% to <−25% | 34 of 134 |
| −25% to <−5% | 53 of 134 |
| −5% to <+5% | 23 of 134 |
| +5% to <+25% | 14 of 134 |
| +25% to <+50% | 3 of 134 |
| At least +50% | 1 of 134 |

B’s median truth is 20.85 m² and median prediction is 18.405 m² (n = 134). The fitted relationship is prediction ≈ 6.96 + 0.518 × truth; metre-only correlation remains 0.833 (n = 127). This supports range compression and downward bias, not a constant-answer explanation.

A independently scores 66.94 versus 48.61 for its median-truth constant of 28.52 m²; correlation is 0.797 (n = 36). Both constants use the evaluated set’s own median and are descriptive baselines, not held-out fitted predictors.

**Every question template.** Wording is preserved except newline whitespace. Each cell gives item count and step-200 MRA.

| Question template | B: n of 134; MRA | A: n of 36; MRA |
|---|---:|---:|
| What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space. | 116; 63.53 | 18; 65.56 |
| State the room size in terms of square meters. If multiple rooms are shown, estimate their combined dimensions. | 2; 45.00 | 2; 45.00 |
| Could you provide the dimensions of the room using square meters? If multiple rooms appear, estimate their total space. | 2; 90.00 | 2; 90.00 |
| In terms of square feet, what’s the room's size? If multiple rooms appear, estimate their total area. | 2; 50.00 | 2; 50.00 |
| What's the room dimension in square feet? For multiple rooms, provide an estimate of their total area. | 2; 75.00 | 2; 70.00 |
| What is the total size of the room expressed in square meters? Estimate combined dimensions if multiple rooms are visible. | 1; 40.00 | 1; 40.00 |
| What's the area measurement of the room in square meters? Estimate the total size if multiple rooms are shown. | 1; 40.00 | 1; 40.00 |
| Can you specify the room size in square meters? If several rooms are presented, estimate the combined area. | 1; 80.00 | 1; 80.00 |
| What is the room's size in square meters? Provide the combined size if more than one room is depicted. | 1; 100.00 | 1; 100.00 |
| What's the measurement of the room in square feet? Estimate combined space if multiple rooms are visible. | 1; 90.00 | 1; 90.00 |
| Could you provide the room dimensions in square meters? If multiple rooms are displayed, please estimate their total size. | 1; 50.00 | 1; 50.00 |
| What's the room size in square meters? If multiple rooms appear, calculate the combined area. | 1; 60.00 | 1; 60.00 |
| Can you specify the room size in square feet? If several rooms are presented, estimate the combined area. | 1; 90.00 | 1; 70.00 |
| In terms of square meters, what’s the room's size? If multiple rooms appear, estimate their total area. | 1; 100.00 | 1; 100.00 |
| Could you estimate the room size in square feet? When multiple rooms are present, provide the total area. | 1; 90.00 | 1; 90.00 |

**Trace structure and its relationship to errors**

| B trace group | Items | Step-200 MRA |
|---|---:|---:|
| Repeated object name within the landmark list | 19 of 134 | 69.47 |
| No repeated object name | 115 of 134 | 63.57 |
| Every listed frame is frame 1 | 14 of 134 | 77.86 |
| At least one later frame | 120 of 134 | 62.83 |
| Observable looping | 0 of 134 | No loss |
| Exactly three landmark entries | 134 of 134 | 64.40 |

“Repeated object” means repeated normalized name, not verified repeated physical instance. B contains three distinct names on 115 of 134 traces, two on 13 of 134, and one on 6 of 134. All 134 finish `eos`, with total output lengths of 61–88 tokens.

Landmark count has no variance. For B, correlations with prediction / absolute relative error are −0.130/−0.080 for distinct names, −0.004/+0.059 for distinct frames, and −0.009/+0.054 for maximum cited frame (each n = 134). These metadata do not explain the numeric errors.

A has repeated names on 6 of 36 and frame-1-only lists on 6 of 36; all 36 list three landmarks and finish `eos`. Its maximum-frame correlations are −0.431 with prediction and +0.186 with absolute relative error (n = 36), showing that the associations are not stable across these overlapping reads.

No numbers except frame indices appear before `</think>` on 134 of 134 B traces or 36 of 36 A traces. In B, 6 repeated-text groups cover 14 of 134 items; 3 of those 6 groups produce different answers despite identical think text. For example, `room_scene0155_02` answers 30.55 and `vsi590k_059477` answers 33.65 from identical landmark-and-relation text.

**Square-feet audit**

| B item suffix | Truth, ft² | Answer, ft² | MRA |
|---|---:|---:|---:|
| `058535` | 164 | 18.56 | 0 |
| `058599` | 201 | 184.85 | 90 |
| `059183` | 225 | 230.40 | 100 |
| `059475` | 378 | 401.11 | 90 |
| `059494` | 447 | 488.88 | 90 |
| `059529` | 156 | 188.82 | 60 |
| `059531` | 291 | 264.08 | 90 |

All IDs above have prefix `vsi590k_`. Written conversion is absent on 7 of 7, so no conversion arithmetic can be checked. **Unit-confusion hypothesis:** `058535` gives 18.56 against a truth equivalent to 15.24 m²; multiplying its answer by 10.7639 gives 199.78 ft² and MRA 60. Multiplication worsens the other 6 of 7 answers to MRA 0. The same candidate fails in A: 18.86 against 164, also reaching MRA 60 after multiplication.

**Uncapped step-544 comparison**

On the 19 uncapped B items, step 200 wins by MRA on 10 of 19, loses on 6 of 19, and ties on 3 of 19. Among the 18 numeric comparisons, it has smaller absolute error on 11 of 18 versus 7 of 18 for step 544. Median absolute errors are 5.21 versus 5.04 m² respectively (n = 18), so step 200 does not dominate every summary.

The malformed step-544 answer is `room_scene0587_01`; its score rises from 0 to 100. Another old answer is 7,536 m² against 85.77; excluding that outlier, mean absolute error falls from 6.54 to 5.13 m² on the remaining 17 numeric items. A’s uncapped subset improves from 60.00 to 65.71 MRA (n = 7), with step 200 closer on 4 of 7.

**Training and ruling audit**

I fetched 40 evenly spaced primary keys across `[195471,195901]` from `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite`, using the range in `FAMILY_INDEX_RANGES.json`. Checking `cp/out/records/n.json` and `z.json` leaves 38 of 40 kept; keys 195724 and 195845 are excluded for `outside_native_training_division`.

All 40 belong to `room_size_estimation|r1_room_traced|None`; 38 of 40 list three landmarks and 2 of 40 list two. Repeated names occur on 0 of 40; frame-1-only lists on 3 of 40; square-feet questions on 7 of 40; metric derivations on 0 of 40.

`dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json` reports 425 of 431 rows kept: 352 of 425 metre rows and 73 of 425 feet rows. The sampled targets are bounded in practice, but their text states no hard maximum.

`TRACE_RULING_20261115.md`, Answer and §2.1–2.2, requires room rows to stay direct, cite one frame per object, and put the numeric estimate only after `</think>`. It permits a room head when an in-artifact metric-scale and room-area path beats direct on reserve rooms. Thus, absent area arithmetic follows the ruling; a relation between landmarks does not supply metric area.

**3. What this changes for vehicle N**

The following disjoint accounting prices observed errors; it does **not** attribute them causally to training rows.

| B error group | Imperfect items | Sum of `1−score` | Lost MRA points over 134 items |
|---|---:|---:|---:|
| Candidate missing feet conversion | 1 of 134 | 1.0 | 0.75 |
| Rooms above 60 m² | 9 of 134 | 7.4 | 5.52 |
| Other unresolved estimation errors | 101 of 134 | 39.3 | 29.33 |
| Total | 111 of 134 | 47.7 | 35.60 |

1. **First, repair unit consistency in `room_size_estimation|r1_room_traced|None`.** Reword the existing 73 kept feet rows across varied question templates and add 73 matched metre rows, using their existing source areas. These proposed volumes are a guess. Preserve the same bounded visual evidence across each pair and change the answer’s unit. This targets 1 of 134 observed candidates; simple conversion recovers **0.45 overall MRA points**, not the full 0.75-point loss. Failure would appear as another roughly tenfold unit discrepancy or metre-like feet answer.

2. **Second, test a calibrated head for the larger error pool.** The non-unit pool contains 110 of 134 imperfect items, including all 9 large rooms; its available loss is 34.85 points, an upper bound rather than a predicted gain. Keep all 425 direct rows and add **0 production head rows until the reserve-room gate passes**. If it passes, propose about 2,000 head-response rows under a new `room_size_estimation|room_head_verified|None` family, consistent with the ruling’s minority-path guidance. This allocation is a guess. Failure means no reserve-room improvement, persistent large-room bias, unserved calls, or renewed call-cap finishes.

3. **Third, make the direct list explicitly bounded without inventing a derivation.** Reword the 425 kept rows to use at most three distinct, source-supported landmarks and omit unverified “farthest apart” claims. This could improve trace validity, but **no numeric fix count is established**: the flagged duplicate/frame-1 groups already score better. Drop 0 rows solely because their list repeats a category or cites only frame 1. Failure means repeated identities persist or trace cleanup leaves numeric error unchanged.

One proposed direct target, retaining row 195471’s source facts and answer, is: `<think>The question asks for the combined floor area in square meters. Seen: shelf in frame 11; whiteboard in frame 1; table in frame 1. I estimate the combined floor area from these views.</think> 17.51`. This wording is explicitly an estimate, not a geometric derivation.

**4. Refuted or qualified**

- A constant “typical room” explanation is insufficient: step 200 scores 64.40 versus 33.88 for the median constant, with r = 0.827 (n = 134).
- Missing feet coverage is not a family-wide absence: 73 of 425 kept training rows ask for feet; 6 of 7 B feet outputs have the appropriate magnitude.
- The first-wave `rows_b` report’s “unbounded” description concerns the question’s lack of a landmark bound. It does not describe observed expansion: 40 of 40 audited targets have at most three entries, and 134 of 134 B generations have exactly three, with 0 observed loops.
- The 19 uncapped step-544 items are not 19 valid numeric completions: 1 of 19 is malformed. The generic B2048/ON16k description also does not apply to these routed-reader records.

**5. Not established**

RGB trace text cannot verify object identity, cited-frame correctness, room boundaries, hidden connected spaces, or metric scale. It cannot distinguish learned visual calibration from memorized scene priors, nor establish that a rewritten trace causes better answers.

Settling those questions requires source-frame inspection, verified room footprints and metric scale, and controlled training comparisons on reserve rooms. A valid area derivation needs measured geometry or calibrated head outputs; adding length-times-width prose alone supplies neither.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the central score, compression, trace, unit, and uncapped-comparison findings.

```python
import sys, re
from collections import Counter
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

def mra(pred, truth):
    return sum(abs(pred-truth)/truth < 1-k/100
               for k in range(50, 100, 5))/10

for part in ("B", "A"):
    rows = K.routed(200, types=["room_size_estimation"], part=part)
    old = K.routed(544, types=["room_size_estimation"], part=part)
    factor = np.array([10.7639 if "square feet" in r["question"]
                       else 1.0 for r in rows])
    truth = np.array([float(r["gt"]) for r in rows])/factor
    pred = np.array([float(r["answer"]) for r in rows])/factor
    scores = np.array([r["score"] for r in rows])
    print(part, "n", len(rows), "MRA", 100*scores.mean())
    print("correlation", np.corrcoef(truth, pred)[0, 1],
          "median truth", np.median(truth),
          "constant MRA",
          100*np.mean([mra(np.median(truth), g) for g in truth]))
    print("under/over", int(sum(pred < truth)), int(sum(pred > truth)),
          "signed-error median", np.median(pred-truth),
          "relative-error median", np.median((pred-truth)/truth))
    for lo, hi in ((0, 15), (15, 30), (30, 60), (60, np.inf)):
        ix = (truth >= lo) & (truth < hi)
        print("band", lo, hi, "n", int(ix.sum()),
              "MRA", 100*scores[ix].mean() if ix.any() else None)
    counts, lengths = Counter(), Counter()
    for r in rows:
        body = r["text"].split("</think>")[0]
        line = re.search(r"Seen:\s*([^\n]+)", body).group(1)
        pairs = re.findall(
            r"(?:^|;\s*)(.*?)(?: first seen)? in frame (\d+)", line)
        names = [o.strip().lower() for o, f in pairs]
        frames = [int(f) for o, f in pairs]
        lengths[len(pairs)] += 1
        counts["repeated_name"] += len(names) > len(set(names))
        counts["frame1_only"] += bool(frames) and set(frames) == {1}
        counts["nonframe_number"] += bool(
            re.search(r"\d", re.sub(r"frame \d+", "", body)))
        counts["non_eos"] += r["finish"] != "eos"
        if "square feet" in r["question"]:
            p, g = float(r["answer"]), float(r["gt"])
            print("feet", r["id"], "truth/pred", g, p,
                  "MRA before/after multiplication",
                  r["score"], mra(p*10.7639, g))
    print("trace counts", counts, "landmark lengths", lengths)
    pairs = [(o, n) for o, n in K.paired(old, rows)
             if o["finish"] != "max_calls"]
    print("uncapped n", len(pairs), "old/new MRA",
          [100*np.mean([pair[j]["score"] for pair in pairs])
           for j in (0, 1)])
    closer = Counter()
    for o, n in pairs:
        try:
            pold = float(o["answer"])
        except ValueError:
            closer["old_nonnumeric"] += 1
            continue
        g, pnew = float(n["gt"]), float(n["answer"])
        eo, en = abs(pold-g), abs(pnew-g)
        closer["new" if en < eo else "old" if eo < en else "tie"] += 1
    print("absolute-error comparison", closer)
```