**1. Question and answer**

**1. How is the printed gap wrong?** At step 200, 52 of 85 numeric gaps overestimate truth and 33 of 85 underestimate it; mean signed relative error is +14.67%. Step 544 has **142 numeric gaps among 149 callers**, with 72 overestimates and 70 underestimates.

**2. Does the response reveal its error?** Fewer than three grounding frames identifies worse gaps at both steps: 60.33 versus 77.92 MRA at step 200, and 55.27 versus 73.88 at step 544. Class-size outliers also score worse, but sparse class coverage limits that result; thin boxes and disjoint frame sets do not identify worse gaps.

**3. Did only scale change?** No: only 1 of 88 shared callers has all printed centres compatible with pure rescaling within rounding tolerance. Frame sets change on 14 of 88 items, and box sizes change beyond scale and axis permutation; these responses establish changes in grounding and geometry, but cannot isolate the responsible checkpoint component.

**4. Do multiple instances explain the errors?** The responses cannot establish instance multiplicity: all 173 successful grounds at step 200 and all 291 at step 544 print one box each. B1/B2 identify the two returned boxes, not demonstrated multiple instances of either class; a minimum-over-instances bias remains untested.

**5. Would a response-triggered direct fallback help?** **Computed by me:** replacing low-frame-coverage answers with the step-200 no-call average accuracy by unit lowers step-200 callers from 54.20 to **35.86 MRA**, while an oracle reaches **82.16**. The response identifies weak evidence, but the available direct-answer proxy is too inaccurate to exploit it.

**6. What do geometry-from-truth rows omit, and what recovery does the ruling allow?** All 747 unit rows use ground-truth geometry and masks, and 0 of 747 contain `not seen`; these rows do not expose deployed grounding mistakes or teach recovery from them. The ruling explicitly permits direct recovery after a real failure status; it does **not clearly permit overriding a successful numeric response solely because a heuristic flags it**.

**2. Evidence**

All scores below are MRA on a 0–100 scale. Truth is the current loader’s scored `gt`, converted to metres using the question’s unit. Signed relative error is `(gap − truth) / truth`; missing gaps are excluded from gap statistics.

Sources:
- **Returns:** `K.routed(200/544, types=['object_abs_distance'])`, through [san_kit.py](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py). Step 200 uses `cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`; step-544 distance uses `out3s/bases/b1/work/ret/metadata/reads/1/metadata/journals/3/0/items.jsonl`, under the same `r1route` root.
- **Class sizes:** [rows.sqlite](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite), with primary keys from [FAMILY_INDEX_RANGES.json](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json). I sampled 2,000 of 9,778 size rows with `random.Random(0)`, in batches of at most 200 keys; the index values are the actual zero-based keys.
- **Training and ruling:** [packed.jsonl](/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl), the supplied template counts, and the Answer/grammar/fallback sections of [TRACE_RULING_20261115.md](/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md).
- **Comparison:** the [first-wave routed-distance report](/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T041229Z_san_m200_routed_dist/final_message.md).

**Gap error by truth band**

| Step; truth band | Numeric items | Gap MRA | Mean signed relative error | Median signed relative error | Under / over |
|---|---:|---:|---:|---:|---:|
| 200; all | 85 of 88 callers | 65.29 | +14.67% | +3.85% | 33 / 52 of 85 |
| 200; below 0.5 m | 3 of 85 | 26.67 | +316.60% | +330.61% | 0 / 3 of 3 |
| 200; 0.5–2 m | 31 of 85 | 57.42 | +24.69% | +8.70% | 9 / 22 of 31 |
| 200; above 2 m | 51 of 85 | 72.35 | −9.18% | +1.36% | 24 / 27 of 51 |
| 544; all | 142 of 149 callers | 61.69 | +11.29% | +0.33% | 70 / 72 of 142 |
| 544; below 0.5 m | 5 of 142 | 16.00 | +351.76% | +324.46% | 0 / 5 of 5 |
| 544; 0.5–2 m | 59 of 142 | 60.17 | +12.31% | +1.31% | 28 / 31 of 59 |
| 544; above 2 m | 78 of 142 | 65.77 | −11.30% | −1.91% | 42 / 36 of 78 |

Small true gaps suffer large relative overestimates, while the longest-distance band has negative mean relative error at both steps. This is not a uniform multiplicative bias.

**Response checks**

Each check fires if either operand satisfies it. “Rest” includes items whose class median is unavailable. The thin-box check excludes classes treated as potentially flat: mirrors, doors, windows, curtains, rugs/mats/carpets, pictures/paintings/posters, boards, keyboards, laptops, paper, towels, blankets, pillows/cushions, slippers/shoes, books, cutting boards, monitors and televisions. This class distinction is an analyst assumption.

| Check | Step 200 flagged | Gap MRA: flagged / rest | Step 544 flagged | Gap MRA: flagged / rest |
|---|---:|---:|---:|---:|
| Non-flat box dimension below 0.10 m | 48 of 85 | 68.33 / 61.35, n=48/37 | 76 of 142 | 65.13 / 57.73, n=76/66 |
| Longest edge outside 0.5–2× class median | 10 of 85 | 52.00 / 67.07, n=10/75 | 29 of 142 | 54.83 / 63.45, n=29/113 |
| Either object grounded in fewer than three frames | 61 of 85 | 60.33 / 77.92, n=61/24 | 93 of 142 | 55.27 / 73.88, n=93/49 |
| Objects share no listed frame | 67 of 85 | 68.21 / 54.44, n=67/18 | 108 of 142 | 62.04 / 60.59, n=108/34 |
| Gap equals zero | 0 of 85 | — / 65.29, n=0/85 | 1 of 142 | 0.00 / 62.13, n=1/141 |
| Centre distance violates either requested bound | 0 of 85 | — / 65.29, n=0/85 | 0 of 142 | — / 61.69, n=0/142 |
| Any check above | 79 of 85 | 63.80 / 85.00, n=79/6 | 132 of 142 | 60.53 / 77.00, n=132/10 |

All 2,000 sampled size rows parsed successfully, yielding 611 exact class names. At least one operand has a matching median on 44 of 85 step-200 items and 81 of 142 step-544 items; both operands match on only 7 of 85 and 13 of 142. Among assessable but unflagged items, MRA is 64.12, n=34, and 60.19, n=52. No semantic alias merging was imposed.

Some medians are especially weak: the heater median is 1.295 m from 2 sampled rows, and the lamp median is 0.85 m from 1 sampled row. Thus the size-check result is descriptive evidence, not a validated rejection rule.

The centre test uses Euclidean centre distance and the sum of both box half-diagonals. Its zero flags mean the returned geometry is internally consistent under these necessary bounds; they do not establish correct objects or dimensions.

**What changed across checkpoints**

| Comparison | Result on shared callers |
|---|---|
| Identical call strings | 88 of 88 |
| Changed frame sets / changed best frame | 14 of 88 / 7 of 88 |
| Changed yaw / printed centres / printed sizes | 80 of 88 / 88 of 88 / 81 of 88 |
| All centre coordinates compatible with scale-only change | 1 of 88 |
| All printed size coordinates compatible with scale-only change | 38 of 88 |
| Sorted box dimensions compatible with scale, allowing axis permutation | 110 of 173 successful paired grounds |
| Centre-to-centre distance compatible with scale within rounding bounds | 78 of 85 numeric pairs |
| Shared numeric-gap MRA, 544 → 200 | 67.18 → 65.29, n=85 |

The following statistics first compute one ratio per item; coordinate and dimension rows use the median component ratio within each item. Centre components below 0.05 m in absolute value are excluded from division.

| Ratio, 200 / 544 | Items | Minimum / Q1 / median / Q3 / maximum |
|---|---:|---|
| Scale | 88 of 88 | 0.99815 / 1.00995 / 1.01219 / 1.01454 / 1.03745 |
| Centre coordinates | 88 of 88 | 0.88980 / 1.00000 / 1.00719 / 1.01711 / 1.25575 |
| Box dimensions | 88 of 88 | 0.35762 / 1.00000 / 1.00359 / 1.02036 / 1.04969 |
| Printed gap | 85 of 85 numeric pairs | 0.94212 / 1.00667 / 1.01235 / 1.01829 / 1.62745 |
| Centre distance divided by scale ratio | 85 of 85 numeric pairs | 0.87110 / 0.99821 / 1.00046 / 1.00204 / 1.23142 |

Coordinate changes alone can reflect a changed reference orientation. Nevertheless, changed frame selections and non-scaling box dimensions refute a scale-only explanation. For example, on `vsi590k_163648`, scale rises by a factor of 1.01136, while the door changes from frames `{27}` to `{9,27}` and from size `1.02 × 0.10 × 2.24` m to `0.47 × 0.02 × 0.57` m.

**Instances**

The ground parser accounts for 176 of 176 ground responses at step 200: 173 contain one box and 3 report failure. It accounts for 298 of 298 at step 544: 291 contain one box and 7 report failure. Multiple boxes appear in 0 of 173 and 0 of 291 successful grounds, so no defensible single-instance/multiple-instance error comparison is available.

**Fallback calculations — computed by me**

The first-wave report does not tabulate no-call accuracy by unit. I computed it from the same returns: centimetres 71.33 MRA, n=15; inches 43.75, n=24; feet 25.63, n=16; metres 34.29, n=7. These are averages on different items, not observed fallback answers.

For each flag, I replace the flagged numeric item’s final-answer score with that unit average, or with 100 for the oracle. Every unflagged answer and every missing-gap answer retains its observed score. Both checkpoints use the same step-200 direct proxy.

| Trigger | Step 200 proxy / oracle, n=88 callers | Step 544 proxy / oracle, n=149 callers |
|---|---:|---:|
| No replacement | 54.20 / 54.20 | 28.46 / 28.46 |
| Thin box | 41.49 / 76.14 | 33.02 / 62.82 |
| Class-size outlier | 52.11 / 59.66 | 31.04 / 42.48 |
| Fewer than three frames | 35.86 / 82.16 | 33.03 / 72.08 |
| No shared frame | 35.34 / 84.32 | 34.63 / 78.72 |
| Zero gap | 54.20 / 54.20 | 28.63 / 29.13 |
| Centre-bound violation | 54.20 / 54.20 | 28.46 / 28.46 |
| Any check | 36.34 / 93.64 | 38.13 / 91.41 |

**3. What this changes for vehicle N**

1. **Add 2,000 alternative-path rows in proposed family `object_abs_distance|deployed_pairs|response_correct_route_else_direct`.** This quota is a proposal. Follow Answer item 6: use an independent direct trace when the deployed response is wrong, and retain correct routed examples. Do not turn low frame coverage into an automatic override. The low-coverage group contains 49 of 85 numeric items with imperfect gaps and loses 24.2 score-equivalents, or 16.13 full-type points; this is an error budget, not predicted recovery. The proposal fails if paired direct reads remain below routed accuracy on these items.

2. **Add 400 real-failure rows in proposed family `object_abs_distance|deployed_recovery|failed_ground_to_direct`.** This quota is a proposal. The observed target is 2 of 88 callers that answer incorrectly after missing geometry, with a ceiling of 1.33 full-type points; preserve the correct answer on the remaining 1 of 3 failed-gap cases. Failure would appear as zeros, invented measurements, repeated calls, or refusals after `not seen`.

The following is a verbatim **proposed trace**, using the actual responses and scored answer of dev item `vsi590k_161834`; it is a format example, **not a training item to admit**. Its check is the zero-frame/no-box special case of insufficient grounding. It satisfies the ruling’s explicit real-failure condition; a successful-but-suspicious numeric response does not have that same authorization.

```text
<think>
<ground obj="printer" mode="box">
<tool_response>
printer: frames 1,4,5,7,11,14,16 (best 7)
B1: f1 centre (0.63, -0.58, 1.13) m
size 0.43 x 0.10 x 0.17 m
yaw -98 deg (0 = +x; positive +x toward -z about +y)
</tool_response>
<ground obj="slippers" mode="box">
<tool_response>
slippers: not seen
</tool_response>
The slippers have no returned box, so the required pair is incomplete.
The printer is located in frame 7.
The question asks for the gap between the nearest points in centimeters; I estimate it directly from the frames.
</think>
<answer>676.4</answer>
```

3. **Reword the instance claim in the 747 unit candidates, family `object_abs_distance|None|None`, provenance family `units`.** Replace the unsupported explanation with: “The tool returned the box gap.” Add instance-count and selected-pair receipts before claiming that every instance pair was evaluated. This fixes unsupported wording on 747 of 747 candidates, with **zero established score gain**. All 747 currently record `training_admitted=false`, so this file alone does not establish training exposure.

**4. Refuted**

- The prompt’s “149 numeric gaps at step 544” is incorrect: 142 of 149 callers print numbers.
- The prompt’s 68.0 → 65.1 comparison uses the first-wave report’s displayed labels. With current scored truth, the shared 85-item comparison is **67.18 → 65.29**.
- The first-wave statement that loader `gt` exposes the unscored label is stale: the current loader explicitly selects scored `answer`.
- Pure scale drift is insufficient: only 1 of 88 centre responses fits it, and 14 of 88 items change grounding frames.
- B1/B2 and “every pair of instances” do not establish multiplicity in any of the 464 successful ground responses examined.

**5. Not established**

These returns cannot isolate depth, pose, association, box fitting, and scale as separate causes. Fixed-frame geometry, selected-instance identities, and aligned annotated boxes would settle that attribution.

The flag comparisons are descriptive and share rooms and objects; they are not independent held-out validation. Class medians need broader coverage, and fallback needs paired direct answers on the **same** flagged items. Training manifests must establish whether the 747 candidate unit rows were actually consumed.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python -B`. This reproduces numeric-gap counts, the low-frame check, its fallback calculation, and the scale-only centre test.

```python
import os, sys, re, math, statistics as S
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
FACT = {"centimeters": .01, "inches": .0254, "feet": .3048, "meters": 1}
def parse(r):
    r = dict(r)
    r["u"] = next(u for u in FACT if u in r["question"].lower())
    r["t"] = float(r["gt"]) * FACT[r["u"]]
    r["g"], r["boxes"] = None, []
    for c in r["calls"]:
        text = c["response"] or ""
        if c["family"] == "gap":
            m = re.fullmatch(r"distance ([\d.]+) m", text.strip())
            if m: r["g"] = float(m[1])
        if c["family"] == "ground":
            f = re.search(r"frames ([\d,]+) \(best (\d+)\)", text)
            p = re.search(r"centre \(([^)]+)\) m", text)
            r["boxes"].append({
                "frames": set(map(int, f[1].split(","))) if f else set(),
                "centre": list(map(float, p[1].split(","))) if p else []})
    r["few"] = any(len(b["frames"]) < 3 for b in r["boxes"])
    if r["g"] is not None:
        r["err"] = (r["g"] - r["t"]) / r["t"]
        r["mra"] = sum(abs(r["err"]) < 1-k/100 for k in range(50,100,5))/10
    return r
rows = {s: [parse(r) for r in K.routed(s, types=["object_abs_distance"])]
        for s in (200, 544)}
no = [r for r in rows[200] if not r["calls"]]
direct = {u: S.mean(r["score"] for r in no if r["u"] == u) for u in FACT}
for s, rr in rows.items():
    callers = [r for r in rr if r["calls"]]
    numeric = [r for r in rr if r["g"] is not None]
    flagged = [r for r in numeric if r["few"]]
    other = [r for r in numeric if not r["few"]]
    print(s, "callers/numeric:", len(callers), len(numeric),
          "gap MRA:", round(100*S.mean(r["mra"] for r in numeric), 4),
          "under/over:", sum(r["err"]<0 for r in numeric),
          sum(r["err"]>0 for r in numeric))
    print("few frames:", len(flagged), "flagged/unflagged gap MRA:",
          *[round(100*S.mean(r["mra"] for r in v),4) for v in (flagged,other)])
    flag = lambda r: r["g"] is not None and r["few"]
    print("answer baseline/direct-proxy/oracle:",
          round(100*S.mean(r["score"] for r in callers),4),
          round(100*S.mean(direct[r["u"]] if flag(r) else r["score"]
                           for r in callers),4),
          round(100*S.mean(1 if flag(r) else r["score"] for r in callers),4))
old = {r["id"]: r for r in rows[544]}
pairs = [(old[n["id"]], n) for n in rows[200] if n["calls"]]
consistent, frame_change = 0, 0
for o,n in pairs:
    ratio = n["scale"]/o["scale"]
    coords = [(x,y) for a,b in zip(o["boxes"],n["boxes"])
              for x,y in zip(a["centre"],b["centre"])]
    consistent += all(abs(y-ratio*x) <= .005*(1+ratio)+1e-8 for x,y in coords)
    frame_change += any(a["frames"] != b["frames"]
                        for a,b in zip(o["boxes"],n["boxes"]))
print("shared callers/centres compatible with scale/changed frames:",
      len(pairs), consistent, frame_change)
```