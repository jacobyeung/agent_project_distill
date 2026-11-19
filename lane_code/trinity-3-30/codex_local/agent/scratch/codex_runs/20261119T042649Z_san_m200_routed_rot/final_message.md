## 1. Scope

All observed losses come from printed head values disagreeing with labels. Calls and answer usage are correct throughout.

I analyzed **150 of 150 dev-S1 items per type at each step**. The loader identifies these returns as **G3T/tower**, so these are not verified B2048 results.

| Type | Step 544 score | Step 200 score | Fully correct, 544 | Fully correct, 200 |
|---|---:|---:|---:|---:|
| camera_rotation | 75.60 MRA | 76.27 MRA | 84 of 150 | 88 of 150 |
| camera_movement_direction | 94.67% | 94.67% | 142 of 150 | 142 of 150 |

Scores were recomputed from `K.routed` returns. Under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/`, the camera source files are:
- Step 200: `out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`.
- Step 544: `out3s/bases/b1/work/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`.
The loader also reads a baseline read-1 journal for distance; those items were excluded.

| Type, step | Placement: called / correct frame arguments | Head accuracy, ignoring final answer | Usage: answer follows response |
|---|---|---|---|
| Rotation, 544 | 150 of 150 / 150 of 150 | 75.60 MRA; full credit on 84 of 150 | 150 of 150 |
| Rotation, 200 | 150 of 150 / 150 of 150 | 76.27 MRA; full credit on 88 of 150 | 150 of 150 |
| Movement, 544 | 150 of 150 / 150 of 150 | 142 of 150 correct | 150 of 150 |
| Movement, 200 | 150 of 150 / 150 of 150 | 142 of 150 correct | 150 of 150 |

For each table row, unserved calls, malformed calls, extra calls, and answer departures each affect **0 of 150**. Departures help **0 of 150** and hurt **0 of 150**.

Each type has one question template after substituting frame numbers:

| Template and units | Coverage at each step | Score, 544 / 200 |
|---|---|---|
| “What is the signed camera rotation in degrees between frame …? Positive means left; use (-180, 180].” | 150 of 150 rotation items; degrees | 75.60 / 76.27 |
| “During the sequence between frame …, what was the primary consistent direction … relative to its orientation at the start?” | 150 of 150 movement items; categorical answer, displacement printed in metres | 94.67 / 94.67 |

Movement options are always `A. backward`, `B. right`, `C. left`, `D. forward`, on **150 of 150** items.

## 2. Failure modes at step 200

“Head disagreement” identifies the observable source of loss against the supplied label; it does not independently establish that the physical label is correct.

| Primary mode | Definition | Rotation count; cost | Movement count; cost |
|---|---|---|---|
| Rotation head disagreement | The printed angle loses MRA, and the answer copies it faithfully. | 62 of 150; **23.73 points** | 0 of 150; 0 points |
| Movement head disagreement | The printed displacement selects the wrong labelled direction, and the answer follows that selection. | 0 of 150; 0 points | 8 of 150; **5.33 points** |

These modes cover **62 of 62** wrong rotation items and **8 of 8** wrong movement items. Misplacement, missing calls, answer inconsistency, and format failures each explain **0 of 150** items in either type.

The rotation response is labelled signed yaw, positive left, wrapped to `(-180,180]`, in degrees. This matches the question’s stated convention; the traces do not describe accumulated total rotation.

| Truth-angle magnitude | Coverage | Wrong, 544 / 200 | MRA, 544 / 200 | Mean absolute error, 544 / 200 |
|---|---|---|---|---|
| Below 15° | 55 of 150 | 41 of 55 / 42 of 55 | 47.82 / 48.55 | 2.89° / 2.87° |
| Below 20° | 59 of 150 | 45 of 59 / 45 of 59 | 48.98 / 49.83 | 3.39° / 3.34° |
| Above 90° | 34 of 150 | 1 of 34 / 1 of 34 | 99.71 / 99.71 | 1.97° / 1.97° |

The below-20° group accounts for **29.6 of 35.6 lost MRA units (83.15%)** at step 200, versus **30.1 of 36.6 (82.24%)** at step 544. The first two angle groups overlap.
At each step, opposite nonzero signs occur on **4 of 150** items. Differences exceeding 180° occur on **0 of 150**; wrong-unit answers occur on **0 of 150**.

Movement uses `backward=-dz`, `right=dx`, `left=-dx`, `forward=dz`, then selects the largest component and its option letter. This reproduces **150 of 150** answers at each step, without ties. The complete step-200 wrong-item audit follows; every row is head disagreement, with correct usage.

| Item ID | Printed dx, dz (m) | Printed direction / labelled direction |
|---|---:|---|
| devs1cam-25a2d02602e3865726da5f94f1043f19 | +0.66, −2.94 | backward / right |
| devs1cam-5603d546987bf298034c320fd4030fe0 | +0.02, −0.14 | backward / left |
| devs1cam-5f9724339c1393d9cbdc605c301b0b26 | +1.68, +3.67 | forward / left |
| devs1cam-60346f2b71cd2003c082cc86d8a56989 | +4.83, +5.90 | forward / right |
| devs1cam-76a1b5c5f08da424b5aae4b83b7bdecc | +2.21, +2.94 | forward / backward |
| devs1cam-edac661ee29d27f72c954830838ec6e3 | +3.07, +4.04 | forward / right |
| devs1cam-f5316bf5ff16257d9587548f1c67ec83 | −0.62, −0.52 | left / backward |
| devs1cam-f9f52c52e877443c3053641748c4cdaf | +1.13, −1.00 | right / backward |

## 3. Examples

All examples are step-200 dev-S1 items. Questions are shortened; quoted trace excerpts are verbatim.

**Rotation head disagreement**
- `devs1cam-0a369d6600f61cc6c3e15cb9e954e689`: “What is the signed camera rotation in degrees between frame 3 and frame 16 of 32?” Truth −4; answer −1.  
  Trace: `turn = -1 deg` … `The camera rotation is -1 degree; positive yaw means left.`
- `devs1cam-99ed25e0197022edda2c4fa4364a72fd`: “What is the signed camera rotation in degrees between frame 20 and frame 25 of 32?” Truth −3; answer −45.  
  Trace: `turn = -45 deg` … `The camera rotation is -45 degrees; positive yaw means left.`
- `devs1cam-ef0396683f20d945e6898535e381ad21`: “What is the signed camera rotation in degrees between frame 24 and frame 30 of 32?” Truth 59; answer −100.  
  Trace: `turn = -100 deg` … `The camera rotation is -100 degrees; positive yaw means left.`

**Movement head disagreement**
- `devs1cam-25a2d02602e3865726da5f94f1043f19`: “During the sequence between frame 6 and frame 17 of 32, what was the primary consistent direction …?” Truth B/right; answer A/backward.  
  Trace: `dx = +0.66 m, dy = +0.22 m, dz = -2.94 m, distance = 3.02 m` … `The largest is backward. That matches option A.`
- `devs1cam-5603d546987bf298034c320fd4030fe0`: “During the sequence between frame 20 and frame 24 of 32, what was the primary consistent direction …?” Truth C/left; answer A/backward.  
  Trace: `dx = +0.02 m, dy = +0.13 m, dz = -0.14 m, distance = 0.19 m` … `The largest is backward. That matches option A.`
- `devs1cam-5f9724339c1393d9cbdc605c301b0b26`: “During the sequence between frame 7 and frame 13 of 32, what was the primary consistent direction …?” Truth C/left; answer D/forward.  
  Trace: `dx = +1.68 m, dy = -0.22 m, dz = +3.67 m, distance = 4.04 m` … `The largest is forward. That matches option D.`

## 4. Step 544 against step 200

“Right” means score equals one.

| Type | Right→wrong | Wrong→right | Wrong→wrong | Right→right |
|---|---|---|---|---|
| Rotation | 4 of 150 | 8 of 150 | 58 of 150 | 80 of 150 |
| Movement | 0 of 150 | 0 of 150 | 8 of 150 | 142 of 150 |

All **12 of 12** rotation flips retain the same trace wording after numeric substitution and the same token length. The printed angle changes, and the answer follows it. For example, `devs1cam-d7d4eb0b26a31f804d5dc4dd6094fbe3`, truth 5°, changes from 5°/MRA 1 to 6°/MRA 0.6.
Rotation outputs average 89.95 versus 89.93 tokens; movement outputs average 203.61 at both steps. Rotation gains 0.67 points; movement gains none.

## 5. Hypotheses

**HYPOTHESIS—rotation:** Pose-estimation error, amplified by relative scoring near zero, causes most loss. Some errors are substantially larger: −3° becomes −45°, and 59° becomes −100°. The candidate family is `camera_rotation|UNKNOWN|UNKNOWN`; its pool and retrace provenance are not established.
The routing exemplar in `TRACE_RULING_20261115.md` teaches faithful copying: `<turn from=2 to=21>` … `turn = +136 deg` … `The camera rotation is 136 degrees; positive yaw means left.` It supports the observed usage, not a causal claim about head training.

**HYPOTHESIS—movement:** Pose/displacement error causes the label disagreement; an alternative is that endpoint displacement does not match the label’s “primary consistent direction” definition. The candidate family is `camera_movement_direction|UNKNOWN|UNKNOWN`.
The ruling’s exemplar states `left = -dx = -1.73 m; forward = dz = 6.41 m` and `The largest is forward. That matches option B.` The tested traces implement this rule correctly.

Neither assigned type appears among **38 of 38** families inspected in the supplied sample/count files, or in the supplied type index. I therefore cannot quote a verified store-v7 target for either family; the quotations above are ruling exemplars.

## 6. Label or scoring defects

No confirmed label or scoring defects were found. The scoring implementation reproduces the rotation scores on **150 of 150** items at each step.
Zero-truth items `devs1cam-6bd803a39f1f3b9b0f22b07f2906bd8a`, `devs1cam-a17deabef59ec32bfe7813f347d1a308`, and `devs1cam-f845406344eee35d8e87003a3737fd89` each print −1° at step 200 and receive zero credit: **3 of 150** items cost 2.00 points. This is the scorer’s explicit zero-target rule, not a demonstrated bug.
The movement disagreements above require reference trajectories before distinguishing head errors from label-definition problems.

## 7. Three changes for vehicle N

The row quantities below are **guesses**, and the recoverable counts are ceilings, not predicted gains. Use training scenes, not these dev items.
1. **Add approximately 1,500 small-angle rotation rows** to `camera_rotation|UNKNOWN|UNKNOWN`, emphasizing near-zero and signed turns with accurate pose supervision. These target **45 of 150** wrong items and at most **19.73 points**. Text-only copying changes cannot correct a frozen head.
2. **Add approximately 500 rotation recovery/direct rows** to that family for real head failures at magnitudes of at least 20°, preserving actual responses and supervising frame-based final estimates. These target **17 of 150** wrong items and at most **4.00 points**. **This is the least certain change:** no successful direct recovery was measured.
3. **Add approximately 2,000 movement recovery/direct rows** to `camera_movement_direction|UNKNOWN|UNKNOWN`, after checking reference displacement against the direction labels. Retain the existing component mapping. These target **8 of 150** wrong items and at most **5.33 points**; adding more mapping demonstrations addresses no observed usage failure.

## 8. Not established

The supplied data do not establish B2048 performance for these routed returns, the camera training rows’ pool/retrace identities, whether pose heads receive training gradients, or the head’s underlying yaw computation. The corresponding evaluation metadata, routed-row manifest/targets, and training configuration would settle those questions.
Reference poses and framewise trajectories would distinguish physical head errors from label-definition errors. Direct-arm results on the paired dev items would test whether the proposed recovery rows can help.

## Appendix: CLASSIFIER

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This block was executed and reproduces the section-2 counts and costs.

```python
import os, sys, re
from collections import Counter, defaultdict
os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
types = ["camera_rotation", "camera_movement_direction"]
rows = K.routed(200, types=types)
S = K._scorer().scorers
from evalpath.run import official
counts, costs, totals = Counter(), defaultdict(float), Counter()
for r in rows:
    group = (r["set"], r["type"])
    totals[group] += 1
    if r["score"] == 1:
        continue
    calls = r["calls"]
    mode = None
    if not calls:
        mode = "No call"
    else:
        c = calls[0]
        q = re.search(r"between frame (\d+) and frame (\d+)", r["question"])
        expected = "turn" if r["type"] == "camera_rotation" else "move"
        a = re.fullmatch(r"<" + expected + r" from=(\d+) to=(\d+)>", c["call"])
        v = S.printed(c)
        if not a or a.groups() != q.groups():
            mode = "Call misplaced"
        elif not c["served"] or v is None or len(calls) != 1:
            mode = "Call service or format failure"
        else:
            if expected == "turn":
                head = v["turn"]
                faithful = float(r["answer"]) == head
                hs = official.official_mra(head, float(r["gt"]))
            else:
                head, _ = S.option_scores(r, v)
                faithful = r["answer"] == head
                hs = float(head == r["gt"])
            if not faithful:
                mode = "Answer departs from response"
            else:
                assert abs(hs - r["score"]) < 1e-9
                mode = ("Rotation head disagreement" if expected == "turn"
                        else "Movement head disagreement")
    counts[group + (mode,)] += 1
    costs[group + (mode,)] += 100 * (1 - r["score"]) / 150
for key, n in sorted(counts.items()):
    print(*key, f"{n} of {totals[key[:2]]}", f"{costs[key]:.4f} points")
assert sum(counts.values()) == sum(r["score"] < 1 for r in rows)
```