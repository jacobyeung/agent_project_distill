**1. Scope**

Camera-displacement loss comes entirely from inaccurate printed distances: step 200 correctly calls and faithfully uses the tool on 150 of 150 dev-S1 items.

| Dev-S1 routed camera displacement | Step 544 | Step 200 |
|---|---:|---:|
| Items audited | 150 of 150 | 150 of 150 |
| Recomputed MRA | 82.33% | 81.87% |
| Items with score < 1 | 78 of 150 | 81 of 150 |

I recomputed scores using `K.routed` and its accepted MRA scorer. These are G3T routed returns; the loader does not provide separate B2048 and ON16k scores for them.
With `P=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route`, the camera returns are `P/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` for step 200 and `P/out3s/bases/b1/work/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl` for step 544. Labels come from the corresponding `out3s/A/src/items/devs1_routed.json` and `out3s/bases/b1/src/items/devs1_routed.json` manifests.

| Audit part | Measurement | Step 544 | Step 200 |
|---|---|---:|---:|
| Placement | Exactly one call, with both frame arguments matching the question | 150 of 150 | 150 of 150 |
| Placement | Unserved, malformed, misplaced, or extra calls | 0 of 150 each | 0 of 150 each |
| Head accuracy | Printed distance MRA, ignoring the answer | 82.33% | 81.87% |
| Head accuracy | Printed distance receives full credit | 72 of 150 | 69 of 150 |
| Usage | Answer equals printed distance | 150 of 150 | 150 of 150 |
| Usage | Departures that help / hurt / tie | 0 of 150 each | 0 of 150 each |

**2. Failure modes at step 200**

| Mode | Definition | Dev-S1 count | Cost on this type |
|---|---|---:|---:|
| Head wrong, used faithfully | The correct call prints a distance with MRA < 1; the answer copies it. | 81 of 150 | 18.13 points |

This classifies all 81 of 81 imperfect items: 7 of 81 receive zero credit and 74 of 81 receive partial credit. No-call failures, misplaced calls, answer departures, and format failures each affect 0 of 150 items. All 150 of 150 finish with `eos`.

**3. Examples**

- **devs1cam-67f88213f397025d9200d63060fd70bf**, dev-S1. Question: “Approximately how far (in meters) did the camera move between frame 6 and frame 7 of 32?”
  Truth: **0.10 m**. Answer: **0.57 m**. MRA: **0.0**.
  Verbatim response: “dx = +0.52 m, dy = -0.04 m, dz = -0.23 m, distance = 0.57 m”
  Verbatim usage: “The printed distance is 0.57 m, so the camera moved about 0.57 m.”
- **devs1cam-1e82b04d17a1e723669d4385fef93ebe**, dev-S1. Question: “Approximately how far (in meters) did the camera move between frame 20 and frame 30 of 32?”
  Truth: **8.48 m**. Answer: **7.07 m**. MRA: **0.7**.
  Verbatim response: “dx = +4.65 m, dy = +0.19 m, dz = +5.32 m, distance = 7.07 m”
  Verbatim usage: “The printed distance is 7.07 m, so the camera moved about 7.07 m.”
- **devs1cam-0020d0cefc26c693abeb6c4e5951cc07**, dev-S1. Question: “Approximately how far (in meters) did the camera move between frame 18 and frame 23 of 32?”
  Truth: **3.15 m**. Answer: **2.99 m**. MRA: **0.9**.
  Verbatim response: “dx = -1.04 m, dy = -0.03 m, dz = -2.81 m, distance = 2.99 m”
  Verbatim usage: “The printed distance is 2.99 m, so the camera moved about 2.99 m.”

**4. Step 544 against step 200**

| Paired outcome, where “right” means MRA = 1 | Count |
|---|---:|
| Right to wrong | 7 of 150 |
| Wrong to right | 4 of 150 |
| Wrong to wrong | 74 of 150 |
| Right to right | 65 of 150 |

Call strings match on 150 of 150 pairs. Complete responses match on 15 of 150; printed distances and final answers match on 38 of 150. Scores improve on 7 of 150, decline on 14 of 150, and remain unchanged on 129 of 150.
Trace wording after replacing numbers matches on 150 of 150 pairs. Token lengths also match on 150 of 150, ranging from 159 to 166. All 11 of 11 full-credit flips change between MRA 0.9 and 1.0; none changes the reasoning form.
Scale changes on 150 of 150 pairs, with a median increase of 1.12%. Every distance change—150 of 150—is compatible with that scale change after allowing both printed distances their 0.005 m rounding uncertainty. This supports scale drift as an explanation for the checkpoint difference; it does not prove unchanged poses.

The following table relates printed-distance error to frame gap, truth size, and the item’s scale value. Relative error is `abs(printed−truth)/truth`.

| Stratum | Step-544 count | Step-200 count | MRA 544 / 200 | Median relative error, 200 |
|---|---:|---:|---:|---:|
| Frame gap 1–3 | 30 of 150 | 30 of 150 | 65.00 / 65.67% | 11.23% |
| Frame gap 4–7 | 42 of 150 | 42 of 150 | 86.19 / 85.00% | 5.08% |
| Frame gap 8–15 | 43 of 150 | 43 of 150 | 87.21 / 86.98% | 4.22% |
| Frame gap 16–31 | 35 of 150 | 35 of 150 | 86.57 / 85.71% | 5.59% |
| Truth ≤ 0.5 m | 47 of 150 | 47 of 150 | 63.40 / 63.40% | 10.53% |
| Truth > 0.5–1 m | 30 of 150 | 30 of 150 | 87.67 / 87.33% | 6.17% |
| Truth > 1–2 m | 24 of 150 | 24 of 150 | 89.58 / 88.33% | 5.48% |
| Truth > 2 m | 49 of 150 | 49 of 150 | 93.67 / 93.06% | 2.71% |
| Scale ≤ 2 | 39 of 150 | 36 of 150 | 84.62 / 83.33% | 5.86% |
| Scale > 2–4 | 85 of 150 | 88 of 150 | 81.65 / 81.82% | 5.55% |
| Scale > 4–8 | 23 of 150 | 23 of 150 | 83.04 / 81.74% | 2.71% |
| Scale > 8 | 3 of 150 | 3 of 150 | 66.67 / 66.67% | 19.54% |

Small movements dominate the loss: truths ≤ 0.5 m account for 33 of 81 imperfect items and **11.47 of 18.13 lost points**. Scale magnitude alone shows no monotonic relationship with error.

A constant room multiplier does not explain all errors. Printed/truth ratios span more than 0.10 in 25 of 31 rooms containing multiple items. In `scannetpp/21c5ee0ca5`, 4 of 4 items share scale 2.6683, yet their ratios range from 0.8303 to 5.7000.

**Computed by me:** multiplying each distance by its room’s median `truth/printed` raises MRA to **85.20% at step 544** and **85.40% at step 200**. This is the requested optimistic scale-fix diagnostic, not a mathematical maximum or a deployable calibration.
At step 200 it fully repairs 24 of 81 imperfect items, damages 10 of 69 full-credit items, and leaves 67 of 150 imperfect. Singleton rooms contain 5 of 150 items and receive exact calibration by construction. Excluding them gives 84.90%; fitting each factor without the evaluated item gives only **79.79%** on 145 of 150 items.

Units and wording offer no comparison here: meters occur on 150 of 150 items; centimeters and feet each occur on 0 of 150. The sole template is “Approximately how far (in meters) did the camera move between frame {a} and frame {b} of 32?” Its MRA is 82.33% / 81.87%, with missing calls or conversion errors on 0 of 150 items.

**5. Hypotheses**

**HYPOTHESIS—head error:** imperfect pose estimates, amplified by small true movements, explain much of the persistent loss; room-scale bias explains a smaller component. The within-room ratio variation and modest oracle gain support this interpretation, but do not isolate pose from scale or rounding.

**HYPOTHESIS—training mismatch:** ground-truth response replay teaches faithful copying without exposing camera rows to deployed head error. The trace ruling identifies camera training responses as recorded ground-truth poses and quotes this target: “`<move from=1 to=25><tool_response>dx = -0.21 m, dy = +0.28 m, dz = -0.07 m, distance = 0.35 m</tool_response>` … `The printed distance is 0.35 m, so the camera moved about 0.35 m.`”

The implicated documented family is **camera_displacement / routing**. Its exact `question_type|pool|retrace` key is **not established**: camera displacement appears in 0 of 17 indexed v7 types and 0 of 38 sampled v7 families. Camera rows also account for 0 of 747 rows in `units/packed.jsonl`. I cannot attribute an exact current family key from those files.

**6. Label or scoring defects**

I found floating-point threshold defects on 1 of 150 items at each step:
- Step 200, `devs1cam-13e0fc3df819bbe48fd3e13644508b18`: truth 0.22, answer 0.33. Exact decimal error is 50%; inclusive thresholds give MRA 0.1, but floating-point error gives 0.0.
- Step 544, `devs1cam-cf9d3b7294f89a136f222539ba3fcc15`: truth 0.16, answer 0.12. Exact decimal error is 25%; inclusive thresholds give 0.6, but the stored score is 0.5.

Each defect costs 0.067 type points. Reported totals retain the accepted scorer. No label inconsistency was found: accepted and item-field truths match on 150 of 150 step-200 items. I did not independently validate geometric labels.

**7. Three changes for vehicle N**

The following keys are **proposed new families**, not verified existing keys. Row quantities are guesses; potential recoveries overlap.
1. **Add short-motion head supervision:** `camera_displacement|vehicleN_short_motion|pose_supervised_v1`, about **2,000 rows**. Pair nearby frames and emphasize small metric displacements. This targets 33 of 81 imperfect items costing 11.47 points. It requires training the relevant heads; rewriting faithful answer text alone cannot repair them.
2. **Add consistent metric-scale supervision across frame pairs:** `camera_displacement|vehicleN_room_scale|scale_supervised_v1`, about **1,000 rows**. Use training-room metric labels with multiple frame pairs per clip. The optimistic diagnostic fully repairs 24 of 81 imperfect items, but its 3.53-point net gain and harms limit the claim.
3. **Add real-head failure/direct-answer pairs:** `camera_displacement|vehicleN_own_head|hindsight_direct_v1`, about **2,000 rows**. Print actual checkpoint responses and retain grounded direct traces only where independently verified. This could target the 57 of 81 imperfect items not fully repaired by room rescaling. **Least certain:** direct recovery is demonstrated on 0 of 81 here, so no numerical gain is established.

**8. Not established**

The traces do not separate pose error, scale error, frame sampling, and centimeter rounding. Unrounded translations, reference poses, true scale, and clip identities would settle that distinction. Actual routed training records are needed to establish the current family key and exposure to own-head errors. Camera questions in centimeters and feet, plus direct-camera returns, are needed to test conversion and fallback proposals.

**Appendix — CLASSIFIER**

```python
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import re
from collections import defaultdict

rows = K.routed(200, types=["camera_displacement"])
S = K._scorer().scorers
from evalpath.run import official

groups = defaultdict(list)
for r in rows:
    if r["score"] == 1:
        continue
    cs = r["calls"]
    if not cs:
        mode = "no call"
    elif len(cs) != 1:
        mode = "extra calls"
    else:
        c = cs[0]
        qargs = re.search(
            r"frame (\d+) and frame (\d+)", r["question"])
        cargs = re.fullmatch(
            r"<move from=(\d+) to=(\d+)>", c["call"])
        p = S.printed(c)
        if (not c["served"] or p is None or not cargs
                or not qargs or cargs.groups() != qargs.groups()):
            mode = "call misplaced/unserved/malformed"
        else:
            value = p["distance"] * S.unit_factor(r["question"])
            try:
                answer = float(r["answer"])
            except (ValueError, TypeError):
                answer = None
            if answer is None:
                mode = "format failure"
            elif answer != value:
                mode = "answer departs"
            else:
                head_score = official.official_mra(
                    value, float(r["gt"]))
                assert head_score == r["score"] < 1
                mode = "head wrong, used faithfully"
    groups[(r["set"], mode)].append(r)

assert sum(map(len, groups.values())) == sum(
    r["score"] < 1 for r in rows)
for (setname, mode), members in sorted(groups.items()):
    total = sum(r["set"] == setname for r in rows)
    cost = 100 * sum(1 - r["score"] for r in members) / total
    print(f"{setname}: {mode}: {len(members)} of {total}; "
          f"cost {cost:.2f} points")
```