**1. Question and answer**

1. **Is displacement error additive or multiplicative?** Neither model alone explains it. At both steps, 47 of 150 truths are ≤0.5 m and cost 11.47 type points; their errors suggest a short-motion noise floor, while absolute errors also grow with distance. This is a hypothesis, not an identified physical cause.

2. **Do nearby frames fail more?** Displacement MRA is lower for gaps of 1–2 sampled frames: 63.89/65.00 at steps 544/200, on 18 of 150 items. Rotation shows no consistent adjacent-frame penalty. Timing metadata matches 0 of 450 routed items, so elapsed seconds cannot be tested.

3. **Does rotation use the wrong convention?** The response prints signed yaw, positive left, in the question’s requested range; all 150 answers per step copy it. Four of 150 predictions have opposite nonzero signs, but no substantial error resembles a wrap or supplement within 5°.

4. **What explains the eight wrong movement directions?** At both steps, 7 of 8 select a different axis from the label and 1 of 8 selects the opposite direction on the same axis. Five of 8 have horizontal components within a factor of 1.5; so do 22 of 142 correct items. Near-diagonal motion identifies sensitivity, not a proven label defect.

5. **Are errors stable across checkpoints and clustered by room?** Displacement errors retain their sign on 131 of 150 items, with Spearman correlation 0.973; rotation retains its sign on 129 of 150, with correlation 0.939. At step 200, room means explain 27.59% of signed-relative displacement variance on 145 items and 7.18% of rotation variance on 143 nonzero-truth items.

6. **Do displacement and rotation errors coincide on shared frame pairs?** There are 0 shared displacement–rotation pairs at either step. One pair overlaps displacement with movement direction, and two overlap rotation with movement direction; these cannot establish error correlation.

7. **What most limits printed motion?** Small-angle rotation and short displacement contain the largest recoverable-loss ceilings: 19.73 rotation points on 59 of 150 items and 11.47 displacement points on 47 of 150 at step 200. Global scale correction offers little held-out improvement; frame separation and convention do not explain those ceilings independently.

**2. Evidence**

All measurements use dev-S1 camera rows from `K.routed(544/200)`. Let `P=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route`. Returns are `P/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` and `P/out3s/bases/b1/work/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`. Labels come from their routed manifests through the loader.

Scores below use the accepted scorer. These are routed G3T returns; the loader does not establish a separate B2048 arm. Every paired cell lists **544 / 200**. A type point equals one percentage point averaged over that type’s 150 items.

Displacement bands use signed error `printed − truth`; relative error divides by truth. “Over/under” gives counts with the band denominator; omitted items are exact matches.

| Truth band | Items | MRA, 544 / 200 | Median signed metres | Median signed relative error | Over, 544 / 200 | Under, 544 / 200 |
|---|---:|---:|---:|---:|---:|---:|
| <0.25 m | 31 of 150 | 58.06 / 57.74 | +0.020 / +0.020 | +10.53% / +10.53% | 18/31 / 18/31 | 8/31 / 7/31 |
| 0.25–0.5 m | 16 of 150 | 73.75 / 74.38 | +0.010 / +0.010 | +2.20% / +3.03% | 9/16 / 11/16 | 4/16 / 4/16 |
| >0.5–1 m | 30 of 150 | 87.67 / 87.33 | +0.010 / +0.020 | +1.19% / +2.67% | 16/30 / 17/30 | 13/30 / 10/30 |
| >1–2 m | 24 of 150 | 89.58 / 88.33 | +0.045 / +0.065 | +3.56% / +3.94% | 15/24 / 17/24 | 7/24 / 7/24 |
| >2 m | 49 of 150 | 93.67 / 93.06 | −0.020 / +0.010 | −0.67% / +0.43% | 18/49 / 26/49 | 28/49 / 22/49 |

Median absolute errors across these bands are **0.030/0.030, 0.020/0.030, 0.040/0.040, 0.085/0.085, and 0.120/0.110 m**, with the respective item counts above. Thus, a constant relative error or constant metre error is insufficient.

For MRA ≥0.9, absolute error must be ≤10% of truth, apart from floating-point boundary effects. The 47 short moves require **0.010–0.049 m**, with median tolerance **0.020 m**; 24 of 47 fall below 0.9 at each step.

I fitted `corrected=max(0, a×printed+b)` by least squares in metres. Leave-one-room-out fits exclude every item from the evaluated room. Each score covers 150 items; calibrated values are unrounded.

| Fit | Step-544 `(a,b)` | MRA fit / held-out room | Step-200 `(a,b)` | MRA fit / held-out room |
|---|---|---:|---|---:|
| Unchanged | (1,0) | 82.33 / 82.33 | (1,0) | 81.87 / 81.87 |
| Offset | (1,+0.036400) | 75.60 / 75.40 | (1,+0.018867) | 78.73 / 78.07 |
| Scale | (1.043820,0) | 79.07 / 78.93 | (1.035455,0) | 78.47 / 78.27 |
| Both | (1.064627,−0.086228) | 74.40 / 73.87 | (1.057211,−0.090693) | 73.20 / 72.67 |

Least squares prioritizes large metre errors, so I also selected corrections directly for MRA. Offset search was ±0.1 m in 0.001-m steps; scale search was 0.8–1.2 in 0.001 steps; the joint grid used 0.002 m and 0.005 scale steps. Ties favored proximity to identity.

| MRA-selected fit; 150 items each | Best 544 `(a,b)` | MRA fit / held-out room | Best 200 `(a,b)` | MRA fit / held-out room |
|---|---|---:|---|---:|
| Offset | (1,−0.004) | 82.80 / 82.60 | (1,−0.004) | 82.13 / 81.47 |
| Scale | (0.985,0) | 82.93 / 82.87 | (0.969,0) | 82.67 / 82.07 |
| Both | (0.985,0) | 82.93 / 82.33 | (0.970,−0.004) | 82.73 / 82.00 |

Rounding the held-out scale predictions to centimetres gives **82.47/82.33 MRA on 150 items**. These small gains do not support scale as the main limitation. The first-wave room-specific oracle’s 85.40 MRA remains an in-sample result; its leave-one-item-out result is a different validation scheme.

Rotation bands use absolute truth magnitude; signed error remains `printed − truth`.

| Truth magnitude | Items | MRA, 544 / 200 | Median signed error, degrees | Mean absolute error, degrees |
|---|---:|---:|---:|---:|
| Zero | 3 of 150 | 0.00 / 0.00 | −1 / −1 | 1.33 / 1.00 |
| >0–<10° | 45 of 150 | 47.11 / 48.44 | 0 / 0 | 3.18 / 3.11 |
| 10–<20° | 11 of 150 | 70.00 / 69.09 | 0 / 0 | 4.82 / 4.91 |
| 20–<45° | 27 of 150 | 85.56 / 87.04 | +1 / +1 | 3.07 / 2.89 |
| 45–90° | 30 of 150 | 91.67 / 92.00 | 0 / 0 | 7.93 / 7.83 |
| >90° | 34 of 150 | 99.71 / 99.71 | −1 / −1 | 1.97 / 1.97 |

Observed printed angles span **−165° to +159° at 544** and **−162° to +158° at 200**, each over 150 items. Answers apply no additional sign or wrapping transformation. Opposite-sign `(truth,prediction)` pairs are identical across steps: **(−5,+7), (−8,+2), (+9,−2), (+59,−100)**. Their cost is 2.67 points per step; an oracle that corrects only signs recovers 2.20 points on those four items.

No prediction has an error exceeding 5° while lying within 5° of `360−|truth|` or `180−|truth|`: **0 of 150 per step**. Near-90° coincidences within smaller tolerances do not establish a supplement error.

For the three zero-truth items, these are the verbatim responses:

| Item ID suffix | Frames | Step 544 | Step 200 |
|---|---|---|---|
| `2906bd8a` | 8–17 | `turn = -1 deg` | `turn = -1 deg` |
| `47d1a308` | 1–2 | `turn = +1 deg` | `turn = -1 deg` |
| `3737fd89` | 20–24 | `turn = -2 deg` | `turn = -1 deg` |

Snapping printed `|yaw|≤1°` to zero changes 8/10 of 150 items at steps 544/200. It improves 2/3 items and harms 1/2, yielding **76.27/77.53 MRA on 150 items**, gains of 0.67/1.27 points. A ±2° rule harms 5 of 150 at each step and gains only 0.27 points.

| Sampled-frame gap | Displacement items | Displacement MRA, 544 / 200 | Median signed metres | Rotation items | Rotation MRA, 544 / 200 | Median signed degrees |
|---|---:|---:|---:|---:|---:|---:|
| 1–2 | 18 of 150 | 63.89 / 65.00 | +0.010 / +0.010 | 34 of 150 | 72.65 / 75.00 | +1 / 0 |
| 3–6 | 45 of 150 | 81.11 / 80.22 | 0 / +0.010 | 30 of 150 | 72.67 / 71.33 | 0 / 0 |
| 7–15 | 52 of 150 | 86.92 / 86.54 | −0.005 / +0.010 | 52 of 150 | 80.77 / 81.35 | 0 / 0 |
| ≥16 | 35 of 150 | 86.57 / 85.71 | +0.020 / +0.040 | 34 of 150 | 73.24 / 74.12 | 0 / 0 |

Among short displacements, adjacent versus other gaps score **51.67/53.33 on 12 items**, versus **67.43/66.86 on 35**. Above 0.5 m, they score **88.33/88.33 on 6**, versus **91.13/90.41 on 97**. Broad truth stratification reduces the apparent gap penalty but does not eliminate it.

For rotations below 20°, adjacent gaps score **54.44/58.89 on 18 items**, versus **46.59/45.85 on 41**. This contradicts a general adjacent-frame rotation failure. `K.timing('R1',200,'dev-S1')` returns 1,339 entries, but matches **0 of 150 IDs for each camera type**.

All 150 movement vectors per step were parsed. The following table lists every wrong item; “near” means `max(|dx|,|dz|)≤1.5×min(|dx|,|dz|)`. IDs are unique suffixes of the supplied dev IDs.

| ID suffix | `(dx,dy,dz)` at 544 | `(dx,dy,dz)` at 200 | Prediction / label, both steps | Classification |
|---|---|---|---|---|
| `43f1043f19` | (.64,.17,−2.91) | (.66,.22,−2.94) | backward / right | Wrong axis |
| `0fd4030fe0` | (.02,.13,−.14) | (.02,.13,−.14) | backward / left | Wrong axis; labelled component also has wrong sign |
| `05c301b0b26` | (1.69,−.21,3.63) | (1.68,−.22,3.67) | forward / left | Wrong axis; labelled component also has wrong sign |
| `3c082cc86d8a56989` | (4.74,−.62,5.83) | (4.83,−.52,5.90) | forward / right | Wrong axis; near |
| `3b7bdecc` | (2.20,−.03,2.93) | (2.21,−.06,2.94) | forward / backward | Opposite sign on same axis; near |
| `38ec6e3` | (3.03,.42,4.03) | (3.07,.35,4.04) | forward / right | Wrong axis; near |
| `1c67ec83` | (−.61,.35,−.53) | (−.62,.37,−.52) | left / backward | Wrong axis; near |
| `1748c4cdaf` | (1.12,−.09,−.99) | (1.13,−.10,−1.00) | right / backward | Wrong axis; near |

Near-diagonal counts are **5 of 8 wrong and 22 of 142 right**, at both steps. There are no exact horizontal ties among 150 items. Positive scalar calibration cannot change the dominant direction.

Room variance uses `error/|truth|`, excludes zero truths, and retains rooms with at least two eligible items. The descriptive between-room sum-of-squares shares are **27.33%/27.59% for displacement, 145 items in 31 rooms**, and **7.29%/7.18% for rotation, 143 items in 30 rooms**. They are not causal variance estimates.

Pair matching uses room plus unordered frame pair. Displacement, rotation and movement have **150, 149 and 150 unique pairs**, respectively; rotation contains one duplicate. At both steps, **0 displacement pairs match rotation**, **1 matches movement**, **2 rotation pairs match movement**, and **0 pairs occur in all three types**. All three corresponding movement answers are correct.

**3. What this changes for vehicle N**

The following ranked quantities are **proposed pilot sizes, not measured requirements**. The supplied v7 index contains 17 types and the template file contains 38 families; **none contains these three motion types**. Existing exact routing-family keys therefore remain unverified. Proposed keys below name new families.

1. **Prioritize small-angle head supervision.** Add **2,000 proposed rows** under `camera_rotation|vehicleN_small_yaw|pose_supervised_v1`, including stationary, small signed turns and controls. Train the pose/yaw head against training-scene geometry; text supervision alone has no demonstrated mechanism to repair these values. This targets 45 of 150 imperfect items below 20°, costing 19.73 points at step 200. Failure means that band remains near 49.83 MRA on its 59 items, even if call accuracy stays perfect.

2. **Prioritize short metric translations next.** Add **2,000 proposed rows** under `camera_displacement|vehicleN_short_motion|pose_supervised_v1`, spanning short moves at both nearby and distant sampled frames. Target head accuracy within 10% of displacement, rather than subtracting a universal offset. This targets 33 imperfect items among 47 short moves, with an 11.47-point ceiling. Failure means centimetre errors and short-band MRA remain unchanged.

3. **Add direction supervision around diagonal motion and sign failures.** Add **1,000 proposed rows** under `camera_movement_direction|vehicleN_diagonal_motion|pose_supervised_v1`, balanced with clearly dominant-axis controls. Five of eight failures are near diagonal, a 3.33-point ceiling, but 22 correct items would be exposed to any blanket rule change. Failure means direction errors persist or those controls regress.

4. **Keep scale work a small calibration study.** Add **500 proposed multi-pair training rows** under `camera_displacement|vehicleN_metric_scale|scale_supervised_v1` only if training-room calibration warrants them. The present global correction gains just 0.20 held-out type points before rounding on 150 items; room-specific in-sample improvement does not establish transferable recovery. Failure means held-out-room gains remain negligible.

Keep the faithful response-use trace concise. One exact example, using the documented training response, is: `<think><move from=1 to=25><tool_response>dx = -0.21 m, dy = +0.28 m, dz = -0.07 m, distance = 0.35 m</tool_response>The displacement is 0.35 m.</think>0.35`. Actual responses must come from the artifact’s head; this wording does not authorize replacing incorrect head outputs with labels.

| Suspected limit, ranked by evidence and potential | Step-200 loss it could explain | Training-free test that prices it |
|---|---|---|
| Small-angle precision/noise, **hypothesis** | Up to 19.73 rotation points; 59 of 150 items, 45 imperfect | Rescore unrounded yaw and training-selected zero thresholds; current ±1° test gains 1.27 points but harms 2 items. |
| Short-translation noise, **hypothesis** | Up to 11.47 displacement points; 47 of 150 items, 33 imperfect | Compare unrounded translations and reference-pose substitutions while holding scale fixed. |
| Scale | Global held-out correction gains 0.20 points on 150 items; room oracle is optimistic | Freeze calibration from disjoint training rooms and evaluate printed, rounded outputs. |
| Frame separation, **association only** | Adjacent bins contain 4.20 displacement and 5.67 rotation lost points, on 18/34 items | Match truth magnitude and room across frame-gap bins; obtain timestamps. These losses overlap the precision groups. |
| Rotation convention | No demonstrated wrap/supplement loss; four sign errors cost 2.67 points | Recompute signed yaw from reference poses with the stated convention; oracle sign repair gains only 2.20 points. |

**4. Refuted**

Under the requested factor-of-1.5 definition, **5 of 8**, not four, wrong movement items are near diagonal at both steps. “Two large components” without a numerical definition may describe a different subset.

All three zero-truth answers are −1° at step 200, but at step 544 they are **−1°, +1°, −2°**. The other first-wave aggregate findings checked here hold.

**5. Not established**

These traces do not identify pose noise, scale error, rounding or label error separately. Unrounded poses, reference geometry, actual routed training records and camera-item timestamps would settle those distinctions. They also do not establish that near-diagonal labels are ambiguous, that direct camera reasoning would recover failures, or that proposed row quantities would improve the heads.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the short-motion loss ceilings, direction counts and held-out scale result.

```python
import os, sys, re
os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import numpy as np
import san_kit as K

types = ["camera_displacement", "camera_rotation", "camera_movement_direction"]
thresholds = 1 - np.array([.5 + i * (.95 - .5) / 9 for i in range(10)])
for step in (544, 200):
    all_rows = K.routed(step, types=types)
    groups = {t: [r for r in all_rows if r["type"] == t] for t in types}
    for t, cutoff in zip(types[:2], (.5, 20)):
        rr = groups[t]
        selected = [r for r in rr if (
            abs(float(r["gt"])) <= cutoff if t == types[0]
            else abs(float(r["gt"])) < cutoff)]
        print(step, t, "selected/total", len(selected), len(rr),
              "imperfect", sum(r["score"] < 1 for r in selected),
              "type_points_lost",
              sum(1-r["score"] for r in selected)*100/len(rr))
    rr = groups[types[2]]
    counts = dict(near_wrong=0, near_right=0, wrong_axis=0, opposite=0)
    for r in rr:
        x, y, z = map(float, re.findall(
            r"d[xyz] = ([+\-\d.]+)", r["calls"][0]["response"]))
        near = max(abs(x), abs(z)) <= 1.5 * min(abs(x), abs(z))
        counts["near_wrong" if r["score"] < 1 else "near_right"] += int(near)
        if r["score"] < 1:
            a, g = r["answer"], r["gt"]
            counts["wrong_axis"] += int((a in "BC") != (g in "BC"))
            counts["opposite"] += int(
                (a, g) in [("A","D"),("D","A"),("B","C"),("C","B")])
    print(step, "movement", counts)
    rr = groups[types[0]]
    p = np.array([float(re.search(r"distance = ([\d.]+)",
                  r["calls"][0]["response"])[1]) for r in rr])
    g = np.array([float(r["gt"]) for r in rr])
    rooms = np.array([r["room"] for r in rr])
    scales = np.array(sorted(
        np.linspace(.8, 1.2, 401), key=lambda a: abs(a-1)))
    error = abs(scales[:, None]*p-g)/g
    scores = sum(error <= threshold for threshold in thresholds)/10
    cv = np.zeros(len(rr))
    for room in set(rooms):
        test = rooms == room
        best = np.argmax(scores[:, ~test].mean(axis=1))
        cv[test] = scores[best, test]
    print(step, "scale_MRA", "in_sample", scores.mean(axis=1).max()*100,
          "leave_one_room_out", cv.mean()*100, "n", len(rr))
```