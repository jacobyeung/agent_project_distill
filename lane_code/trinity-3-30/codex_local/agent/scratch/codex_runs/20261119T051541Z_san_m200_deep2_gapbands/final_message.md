**1. Question and answer**

1. **How does gap error vary with true distance, and is it a scale or offset error?** Short distances are hardest: all 5 of 5 gaps below 0.5 m at step 544 and all 3 of 3 at step 200 overestimate truth. A single scale helps slightly when rooms are held out; a single offset hurts, and neither explains most errors.
2. **Do the printed boxes reproduce the gap, and would another distance rule help?** Oriented-box distances agree within 5 cm on 142 of 142 numeric gaps at step 544 and 85 of 85 at step 200. Centre distance scores substantially worse; subtracting projected half-extents produces almost no aggregate improvement.
3. **Are box sizes plausible against training-class medians?** Among classes with at least five returned boxes and an exact training-class match, 36 of 147 boxes at step 544 and 18 of 73 at step 200 are outliers. Their items score worse, but several reference medians come from only one or two training rows.
4. **Which classes and grounding patterns predict errors?** Low frame coverage is the clearest repeated association: fewer than three frames scores 55.27 MRA on 93 items versus 73.88 on 49 at step 544, and 60.33 on 61 versus 77.92 on 24 at step 200. Sharing a frame does not improve accuracy.
5. **Does fixed-math scale explain error, and is there a room effect?** Scale terciles show no monotonic relationship. Rooms explain 60.2% and 72.9% of observed signed-relative-error variance, but those shares fall to 31.7% and 30.8% after excluding singleton rooms.
6. **Are errors stable between checkpoints?** Errors have the same sign on **82 of 85 shared numeric gaps**, with Spearman correlation **0.973**. This supports persistent scene/grounding errors over independently varying call outcomes, without identifying the responsible component.
7. **What should head-accuracy work prioritize?** Prioritize grounding coverage and instance/box quality. Changing the distance rule has little aggregate value, and global scale correction recovers only 0.73 and 1.00 points on the full 150-item type under room-held-out evaluation.

**2. Evidence**

All MRA scores below use the **printed gap**, scored truth converted into metres, and the ten specified relative-accuracy thresholds. Step 544 has 142 numeric gaps among 149 callers; step 200 has 85 among 88. These conditional samples differ; they are not the all-item counterfactual scores in the brief.

Sources: [loader](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py), its step-544 read-1 and step-200 read-0 routed returns; [size-row index](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json), [SQLite store](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite), and [family counts](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json). Prior findings came from the named reports’ answer sections and [Q5](/scratch/jjyeung/orch_n30/san_dd_dist/REPORT.md:77). No official benchmark items were used.

**Truth bands and distance rules.** “Projected” means centre distance minus both boxes’ support half-extents projected onto the joining direction, clipped at zero. Counts written `a/b` mean “a of b.”

| Step | Truth, m | Items | Over / under | Median signed relative error | Gap MRA | Centre MRA | Projected MRA |
|---|---|---:|---|---:|---:|---:|---:|
| 544 | <0.5 | 5/142 | 5/5; 0/5 | +324.5% | 16.00 | 0.00 | 20.00 |
| 544 | 0.5–1 | 16/142 | 12/16; 4/16 | +7.2% | 46.88 | 6.25 | 45.00 |
| 544 | 1–2 | 43/142 | 19/43; 24/43 | −3.0% | 65.12 | 20.00 | 62.09 |
| 544 | 2–4 | 53/142 | 28/53; 25/53 | +0.6% | 66.04 | 50.19 | 66.79 |
| 544 | >4 | 25/142 | 8/25; 17/25 | −4.1% | 65.20 | 62.40 | 65.20 |
| 200 | <0.5 | 3/85 | 3/3; 0/3 | +330.6% | 26.67 | 0.00 | 33.33 |
| 200 | 0.5–1 | 4/85 | 4/4; 0/4 | +24.5% | 52.50 | 0.00 | 52.50 |
| 200 | 1–2 | 27/85 | 18/27; 9/27 | +8.0% | 58.15 | 18.15 | 56.30 |
| 200 | 2–4 | 32/85 | 20/32; 12/32 | +3.5% | 73.75 | 55.94 | 75.00 |
| 200 | >4 | 19/85 | 7/19; 12/19 | −2.7% | 70.00 | 65.79 | 71.05 |

By absolute error, the closest of gap/centre/projected wins respectively **0/0/5, 7/1/8, 20/6/17, 11/17/25, 3/14/8** items across the five bands at step 544; step 200 gives **0/0/3, 1/0/3, 8/2/17, 5/9/18, 3/9/7**. Each triplet sums to its band’s item count.

**Calibration.** I maximized training MRA over all scalar threshold intervals, breaking ties toward no correction. Each held-out prediction uses a fit excluding that entire room; offsets clip distances at zero.

| Step; items | Correction | Fitted parameter | Original MRA | In-sample MRA | Leave-one-room-out MRA |
|---|---|---:|---:|---:|---:|
| 544; 142 | Multiply gap | 0.97502 | 61.69 | 62.61 | 62.46 |
| 544; 142 | Add metres | +0.00575 | 61.69 | 62.04 | 60.70 |
| 200; 85 | Multiply gap | 0.93756 | 65.29 | 67.29 | 67.06 |
| 200; 85 | Add metres | −0.06222 | 65.29 | 65.88 | 64.47 |

The oriented-box calculation uses printed centres, dimensions and yaw. Median absolute gap disagreement is 0.0050 m on 142 items and 0.0047 m on 85; maxima are 0.0455 and 0.0479 m. Continuous-box MRA is 61.97 and 65.29 respectively, so grid/rounding effects explain little.
Across all numeric items, centre/projected MRA is **36.48/60.99 on 142** and **41.53/65.65 on 85**. Interpreting “along the line” instead as ray intersections with the boxes gives 54.08 and 56.59 MRA, also worse.

**Class size and class accuracy.** I sampled 3,000 of 9,778 size rows uniformly by primary key with seed 200544; all parsed as centimetres. All belong to `object_size_estimation|r1g|rows_rebuild_d0_v1`, whose 9,778 rows are kept according to the supplied counts. Class matching is exact, without inferred aliases.
In the table, size cells contain **median longest side in metres; small/large counts among boxes**. Small means below half the training median; large means above twice it. A dash means no exact training match or fewer than five boxes at that step. MRA includes only numeric-gap items; lone successful boxes from failed pairs still count toward box statistics.

| Class | Training median m (rows) | Step 544 box size; small/large | Step 200 box size; small/large | Gap MRA 544 (items) | Gap MRA 200 (items) |
|---|---|---|---|---|---|
| bed | 2.06 (1) | 1.38; 3/23, 0/23 | 1.47; 2/11, 0/11 | 52.61 (23) | 60.00 (11) |
| blanket | 1.85 (7) | 0.96; 2/6, 0/6 | — | 53.33 (6) | — |
| bucket | — | 0.14; — (5 boxes) | — | — (<5 items) | — |
| chair | 1.05 (2) | 0.78; 5/17, 0/17 | 0.62; 4/9, 0/9 | 64.71 (17) | 78.89 (9) |
| computer mouse | — | 0.09; — (8 boxes) | 0.09; — (5 boxes) | 71.25 (8) | 52.00 (5) |
| dishwasher | 0.83 (12) | 0.85; 0/6, 0/6 | 0.78; 0/5, 0/5 | 63.33 (6) | 70.00 (5) |
| door | — | 1.22; — (11 boxes) | 1.12; — (8 boxes) | 64.00 (10) | 54.29 (7) |
| headphones | — | 0.19; — (7 boxes) | 0.19; — (6 boxes) | 71.43 (7) | 68.33 (6) |
| heater | 1.76 (1) | 0.20; 12/15, 0/15 | 0.41; 7/10, 0/10 | 40.00 (15) | 51.00 (10) |
| microwave | 0.59 (1) | 0.32; 0/6, 0/6 | — | 56.00 (5) | — |
| mirror | 1.59 (16) | 1.50; 1/6, 0/6 | — | 50.00 (6) | — |
| monitor | — | 0.51; — (6 boxes) | — | 78.33 (6) | — |
| printer | 0.41 (2) | 0.43; 0/7, 0/7 | 0.43; 0/6, 0/6 | 75.00 (6) | 72.00 (5) |
| refrigerator | 0.90 (1) | 1.12; 3/22, 0/22 | 1.07; 2/17, 0/17 | 75.00 (22) | 77.65 (17) |
| sofa | 2.79 (4) | 1.66; 1/5, 0/5 | — | 88.00 (5) | — |
| stool | 0.46 (9) | 0.48; 0/7, 0/7 | — | 42.86 (7) | — |
| stove | 0.615 (18) | 0.57; 0/13, 2/13 | 0.58; 0/10, 0/10 | 55.38 (13) | 66.00 (10) |
| table | 1.89 (2) | 0.99; 7/14, 0/14 | 0.43; 3/5, 0/5 | 35.71 (14) | 54.00 (5) |
| toilet | — | 0.66; — (9 boxes) | 0.67; — (7 boxes) | 44.44 (9) | 51.43 (7) |
| tv | — | 0.68; — (19 boxes) | 0.71; — (16 boxes) | 72.63 (19) | 68.13 (16) |

Eligible classes cover 147 of 291 returned boxes at step 544 and 73 of 173 at step 200. Small/large totals are **34/147 and 2/147**, versus **18/73 and 0/73**.
Items containing an eligible outlier score **43.71 MRA on 35**, versus **67.57 on the other 107**, at step 544; step 200 gives **62.35 on 17** versus **66.03 on 68**. “Other” includes unassessable classes; restricting it to pairs with both classes assessable gives 64.38 on 16 and 76.25 on 8.

**Grounding frames.** “Rarer” means the operand with fewer listed frames.

| Group | Step 544: MRA (items) | Step 200: MRA (items) |
|---|---:|---:|
| Rarer operand: 1 frame | 54.00 (65) | 61.71 (41) |
| Rarer operand: 2 frames | 58.21 (28) | 57.50 (20) |
| Rarer operand: 3–5 frames | 70.00 (33) | 72.35 (17) |
| Rarer operand: ≥6 frames | 81.88 (16) | 91.43 (7) |
| Any shared listed frame | 60.59 (34) | 54.44 (18) |
| No shared listed frame | 62.04 (108) | 68.21 (67) |
| Same best frame | 26.67 (3) | 40.00 (2) |
| Different best frames | 62.45 (139) | 65.90 (83) |

**Fixed-math scale.** These are equal-count rank terciles; tied scales can cross a boundary.

| Step | Scale range | Items | Gap MRA | Median signed relative error |
|---|---|---:|---:|---:|
| 544 | 1.431–2.267 | 48/142 | 63.75 | +1.93% |
| 544 | 2.328–3.221 | 47/142 | 58.51 | −3.02% |
| 544 | 3.221–7.667 | 47/142 | 62.77 | −0.44% |
| 200 | 1.480–2.151 | 29/85 | 73.10 | +4.20% |
| 200 | 2.151–3.309 | 28/85 | 58.57 | +4.29% |
| 200 | 3.309–7.657 | 28/85 | 63.93 | −1.29% |

Scale versus signed-relative-error Spearman correlation is −0.048 on 142 items and −0.131 on 85. The field’s magnitude is not evidence that its estimate is wrong.
Room variance shares use weighted between-room sums of squares divided by total sums of squares. They are **60.2% across 46 rooms/142 items** and **72.9% across 36 rooms/85 items** for relative error; for metre error they are **33.4% and 50.8%**. Excluding singleton rooms gives relative-error shares of **31.7% across 28 rooms/124 items** and **30.8% across 20 rooms/69 items**.
Only 10 of 28 multi-item rooms at step 544 and 11 of 20 at step 200 have uniformly signed errors. Within-room pairs agree in sign on 215 of 387 and 77 of 120 pairs. For example, `venue435364` underestimates on 5 of 5 and 4 of 4 items; `scene0515` overestimates on only 6 of 18 and 2 of 4.
On the same 85 numeric items, gap MRA is **67.18 at step 544 versus 65.29 at step 200**: 7 improve, 11 worsen, and 67 tie. Signed-metre-error rank correlation is 0.976; signed-relative-error correlation is 0.973.

**Ranked error budgets and tests without training.** Type points below divide recoverable item scores by all 150 questions. Budgets overlap and must not be added.

| Priority | Candidate limitation | Step 544 | Step 200 | Test that would price its causal contribution |
|---|---|---|---|---|
| 1 | Sparse grounding coverage | 75 imperfect of 93 low-coverage gaps; 27.73 points remaining | 49 imperfect of 61; 16.13 points remaining | Hold instance and geometry method fixed; recompute with additional verified views. Separately test the 7/149 and 3/88 callers without numeric gaps. |
| 2 | Wrong instance or box | 32 imperfect of 35 size-flagged items; 13.13 points remaining | 15 imperfect of 17; 4.27 points remaining | Substitute verified instance masks, then verified boxes, separately. Size flags are proxies; attribution is a **guess**. |
| 3 | Closest-point rule | Oracle selection among three distances helps 46/142; +6.67 points | Helps 29/85; +3.40 points | Compare annotated object-surface gaps with annotated-box gaps. The oracle budgets do not establish a rule defect. |
| 4 | Global scale | Room-held-out correction improves 32/142 and hurts 21/142; net +0.73 points | Improves 30/85 and hurts 26/85; net +1.00 point | Recompute with independently verified scene scale; keep masks, instances and box fitting fixed. |

Wrong boxes could explain more than the flagged subset: the total numeric-gap deficit is 36.27 points across 104 imperfect of 142 items and 19.67 across 62 of 85. Assigning that entire residual to grounding would be a **guess**.

**3. What this changes for vehicle N**

1. **Proposed, untested: add 2,000 training-scene examples in `box_3d|deployed_multiview|instance_consistent_v1`.** Supervise verified instance identity and full-box geometry across available views, with emphasis on objects the deployed grounder supports in fewer than three frames. Exact proposed trace template: `Locate the {object} in frames {verified_frames}. These views show the same instance. Predict its full box in the requested camera coordinates.` This targets the 75/93 and 49/61 imperfect low-coverage gaps; those are ceilings, not predicted fixes. It fails if matched low-coverage gap MRA does not improve. Confirm that these targets actually train the deployed grounding head; text supervision alone may not.
2. **Proposed, untested: add 1,000 examples in `box_3d|deployed_instance_audit|verified_full_box_v1`.** Use verified masks and boxes for small returned boxes and ambiguous instances; do not replace geometry with class medians. Exact proposed trace template: `Locate the {object} in frame {verified_frame}. Use the instance identified by the verified mask and predict its full box.` This targets at most the 32/35 and 15/17 imperfect size-flagged items. It fails if instance/box substitution helps offline but the trained head retains the same errors.
3. **Proposed: re-render the 747 unit rows reported by `deep_disthead` using deployed responses, under `object_abs_distance|deployed_units|faithful_gap_v1`.** The retained count depends on response correctness and real failure statuses. For a successful response, use: `The printed gap is {gap_m} metres. Convert it to {asked_unit} using {factor}.` This repairs training/deployment mismatch; it does **not** establish recovery of any head-error points.
4. **Keep the box-to-box rule and add zero generic offset-correction rows.** A projected-distance replacement changes full-type scores by −0.67 points at step 544 and +0.20 at step 200. Treat scale calibration as an offline held-out experiment before changing rows; its measured gains are small.

The existing `box_3d|None|rows_rebuild_d0_v1` family contains 3,813 kept rows, and `object_size_estimation|r1g|rows_rebuild_d0_v1` contains 9,778. The proposed additions above are quotas, not observed requirements or demonstrated fixes.

**4. Refuted**

- “Step 200’s higher conditional head MRA demonstrates improved geometry” is unsupported: on the same 85 gaps, MRA falls from 67.18 to 65.29.
- A global offset or centre-distance replacement does not explain the deficit: offsets lose held-out MRA, and centres score 36.48/41.53 versus gaps’ 61.69/65.29.
- The first-wave statement that loader `gt` exposes the released label is stale for this loader: its code returns scored `answer`, with released labels separate. Accordingly, the below-0.5-m step-544 band contains 5 items, not the earlier report’s 6.
- The verified claims about low frame coverage and box/gap consistency survive this analysis.

**5. Not established**

Wrong-instance frequency, true box-size error, causal room-scale error, and the benefit of extra views remain unmeasured. Verified instance masks, object geometry, independent scene scale, and controlled substitutions would separate them. The training-class sample is too sparse to justify size-based rejection, and these associations do not establish a reliable direct-answer fallback trigger.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces gap MRA, calibration results, and cross-step error agreement.

```python
import os, sys, re
os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

def mra(p, t):
    e = abs(np.asarray(p)-np.asarray(t))[...,None]/np.asarray(t)[...,None]
    return (e < (1-np.arange(50,100,5)/100)).mean(axis=-1)*100

def fit(g, t, kind):
    d = 1-np.arange(50,100,5)/100
    lo, hi = t[:,None]*(1-d), t[:,None]*(1+d)
    if kind == "scale":
        z = g > 0
        bounds = np.r_[(lo[z]/g[z,None]).ravel(),(hi[z]/g[z,None]).ravel()]
        base = 1.
    else:
        bounds = np.r_[(lo-g[:,None]).ravel(),(hi-g[:,None]).ravel()]
        base = 0.
    b = np.unique(bounds); candidates = np.r_[base,(b[:-1]+b[1:])/2]
    best = (-1,0,base)
    for c in np.array_split(candidates,max(1,len(candidates)//100)):
        p = c[:,None]*g if kind == "scale" else np.maximum(0,g+c[:,None])
        for v,a in zip(mra(p,t).mean(axis=1),c):
            best = max(best,(round(float(v),10),-abs(a-base),float(a)))
    return best[2]

D = {}
for step in (544,200):
    rows = []
    for r in K.routed(step,types=["object_abs_distance"]):
        gaps = [re.search(r"distance ([0-9.]+) m",c["response"] or "")
                for c in r["calls"] if c["family"] == "gap"]
        gaps = [m for m in gaps if m]
        if not gaps: continue
        q = r["question"].lower()
        u = next(v for word,v in [("centimeter",.01),("inches",.0254),
                 ("feet",.3048),("meters",1),("metres",1)] if word in q)
        rows.append((r["id"],r["room"],float(gaps[-1][1]),float(r["gt"])*u))
    D[step] = rows
    g,t = np.array([(r[2],r[3]) for r in rows]).T
    rooms = np.array([r[1] for r in rows])
    print(step,"numeric",len(rows),"gap MRA",mra(g,t).mean())
    for kind in ("scale","offset"):
        a = fit(g,t,kind); cv = np.zeros(len(g))
        pred = a*g if kind == "scale" else np.maximum(0,g+a)
        for room in set(rooms):
            z = rooms == room; b = fit(g[~z],t[~z],kind)
            cv[z] = b*g[z] if kind == "scale" else np.maximum(0,g[z]+b)
        print(kind,"parameter",a,"train",mra(pred,t).mean(),
              "leave-one-room-out",mra(cv,t).mean(),"n",len(g))

a,b = ({r[0]:r for r in D[s]} for s in (544,200))
ids = sorted(a.keys() & b.keys())
x,y = [np.array([(d[i][2]-d[i][3])/d[i][3] for i in ids]) for d in (a,b)]
def rank(x):
    return np.array([sum(x<v)+(sum(x==v)-1)/2 for v in x])
print("same error sign",sum(np.sign(x)==np.sign(y)),"of",len(ids))
print("Spearman signed relative error",np.corrcoef(rank(x),rank(y))[0,1])
```