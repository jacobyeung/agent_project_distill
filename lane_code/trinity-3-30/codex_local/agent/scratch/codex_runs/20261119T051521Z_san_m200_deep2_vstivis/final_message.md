**1. Question and answer**

1. **Do the dev items carry visibility metadata?** None of the 900 dev exports carries `first_seen`, `frame_n_share`, `instances`, bearings or geometry values. The available manifests contain frame inventories and source references, so this read cannot measure dev accuracy against true visibility.
2. **How does accuracy vary with the model’s stated first-seen frame?** The table below separates claims before, at, after and beyond frame k. Step 200 supplies object claims on 900 of 900 items; step 544 supplies any on only 230 of 900. These are model claims, not visibility ground truth.
3. **Can visibility or geometry predict training answers?** Choosing the largest visible share answers 404 of 900 camera rows correctly. When exactly one candidate meets the visibility floor, that candidate is correct on 159 of 301 rows. Geometry comparison rules reproduce 300 of 300 labels in each of LR, NF and UD.
4. **Does temporal proximity help?** At step 200, accuracy is 89 of 153 when the answered object’s stated first-seen frame is within two frames of k, versus 322 of 563 at larger valid separations. In training, the correct camera answer first appears within two frames of k on 133 of 900 rows.
5. **Do first-seen lists remain stable across the 59 truth-changing pairs?** No. Shared objects’ stated first-seen frames change on 34 of 59 pairs, including 7 of 8 pairs with identical candidate sets. All 59 pairs use identical input frame lists.
6. **Which rows support an “in view at frame k” line?** At the stored floor of 0.002, all objects qualify on 112 of 1,800 sampled rows, some qualify on 712 of 1,800, and none qualify on 976 of 1,800. Zero share and positive share below the floor need different wording.

**2. Evidence**

All accuracies use B2048 scores. Frame claims come from ON16k text. The arms agree on 900 of 900 step-200 answers and 899 of 900 step-544 answers. The single step-544 runaway is wrong; step 200 has zero runaways among 900 items.

Sources:
- Dev: `K.vsti('R1',200)` and `K.vsti('S1',544)` through [san_kit.py](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py). `K.SOURCES` names the ON16k and B2048 `items_a0.jsonl` files under `h1vsti/kit/build/{a35f73e87f0,acb2faedd41}/fetched/x/r6/a0/results/`.
- Metadata: [R6.json](/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/launcher/R6.json), both build configurations, and both compact `r6/ITEMS.jsonl` exports.
- Training: [FAMILY_INDEX_RANGES.json](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json), `vqa/rows.sqlite`, and [STORE_V7_TEMPLATE_COUNTS.json](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json). Samples use `random.Random(200)` separately per family, without replacement, with 300 primary keys and at most 200 keys per query.

**Metadata actually present.** Raw dev rows contain question/options/answers, type, room/scene identifiers, `frame_refs`, FPS, source and anchor indices, total frame count, generation and scoring fields. Nested `media` contains indices, timestamps, metadata, layout and a pixel hash. It provides no object annotations.

Compact exports contain scores, predictions, source qids/line numbers and trace hashes; object provenance appears in zero of 900 rows at either checkpoint. The manifest registers 900 items across 68 rooms and points to `b62c14e9.jsonl` plus a frame archive at a remote `/project/community/...` location. Those source assets were not accessed. Thus, absence is established for the inspected exports, not every upstream source.

**Accuracy by stated first-seen class.** An item enters a column if **any queried object** has that claim; columns overlap. “After” means k < f ≤ 32. “No claim” means no queried-object first-seen claim; the base’s “camera first seen at k” does not count as an object localization.

| Step | Type | f = k | f < k | k < f ≤ 32 | f > 32 | No claim |
|---|---|---|---|---|---|---|
| 544 | v1 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 37 of 150 |
| 544 | v2 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 48 of 150 |
| 544 | v3 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 83 of 150 |
| 544 | LR | 4 of 6 | 10 of 17 | 7 of 13 | 6 of 9 | 62 of 119 |
| 544 | NF | 5 of 10 | 45 of 86 | 17 of 30 | 10 of 20 | 4 of 8 |
| 544 | UD | 4 of 9 | 24 of 37 | 6 of 9 | 7 of 16 | 57 of 93 |
| 200 | v1 | 3 of 8 | 40 of 112 | 28 of 74 | 36 of 79 | 0 of 0 |
| 200 | v2 | 5 of 12 | 36 of 103 | 26 of 63 | 25 of 71 | 0 of 0 |
| 200 | v3 | 6 of 8 | 59 of 101 | 34 of 56 | 27 of 51 | 0 of 0 |
| 200 | LR | 8 of 11 | 66 of 100 | 40 of 49 | 36 of 57 | 0 of 0 |
| 200 | NF | 4 of 6 | 64 of 100 | 33 of 55 | 39 of 61 | 0 of 0 |
| 200 | UD | 4 of 6 | 84 of 104 | 43 of 50 | 48 of 54 | 0 of 0 |

Step 200 makes an above-32 object claim on 373 of 900 items, including 162 of 375 wrong items. It supplies no first-seen claim at k on 354 of 375 wrong items. Neither association establishes the cause of an error.

**Accuracy by |f − k|.** For camera questions, f belongs to the predicted object. For LR/NF/UD, it belongs to the grammatical subject being compared; those answers are relations, not selected objects. Invalid citations are excluded from distance bins.

| Step | Type | 0 | 1–2 | 3–8 | 9–16 | 17–31 | Outside 1–32 | Missing |
|---|---|---|---|---|---|---|---|---|
| 544 | v1 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 37 of 150 |
| 544 | v2 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 48 of 150 |
| 544 | v3 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 0 of 0 | 83 of 150 |
| 544 | LR | 1 of 2 | 2 of 5 | 5 of 7 | 3 of 5 | 3 of 5 | 3 of 5 | 64 of 121 |
| 544 | NF | 3 of 5 | 3 of 5 | 6 of 9 | 7 of 9 | 8 of 13 | 4 of 7 | 46 of 102 |
| 544 | UD | 4 of 6 | 8 of 11 | 2 of 6 | 3 of 8 | 10 of 12 | 5 of 12 | 57 of 95 |
| 200 | v1 | 2 of 5 | 9 of 24 | 14 of 36 | 7 of 27 | 14 of 37 | 11 of 21 | 0 of 0 |
| 200 | v2 | 3 of 7 | 7 of 17 | 11 of 33 | 11 of 30 | 13 of 35 | 11 of 28 | 0 of 0 |
| 200 | v3 | 6 of 7 | 15 of 24 | 22 of 33 | 16 of 32 | 18 of 33 | 12 of 21 | 0 of 0 |
| 200 | LR | 6 of 7 | 13 of 20 | 23 of 30 | 24 of 31 | 16 of 23 | 23 of 39 | 0 of 0 |
| 200 | NF | 1 of 3 | 12 of 17 | 20 of 26 | 14 of 30 | 22 of 34 | 25 of 40 | 0 of 0 |
| 200 | UD | 3 of 5 | 12 of 17 | 23 of 28 | 30 of 37 | 24 of 28 | 32 of 35 | 0 of 0 |

**Training visibility and temporal proximity.** “In view” below means share ≥ 0.002. All 1,800 sampled rows contain the four requested provenance fields. None of 1,800 has a first-seen value above 32.

| Family shorthand | Every object in view | Some | None | Correct camera object, or relation subject, within 2 of k | Full-store kept rows |
|---|---|---|---|---|---|
| v1 | 2 of 300 | 167 of 300 | 131 of 300 | 43 of 300 | 1,930 of 1,951 |
| v2 | 5 of 300 | 139 of 300 | 156 of 300 | 41 of 300 | 1,957 of 1,983 |
| v3 | 26 of 300 | 84 of 300 | 190 of 300 | 49 of 300 | 1,978 of 1,998 |
| LR | 34 of 300 | 134 of 300 | 132 of 300 | 76 of 300 | 1,978 of 1,998 |
| NF | 23 of 300 | 93 of 300 | 184 of 300 | 51 of 300 | 1,982 of 2,000 |
| UD | 22 of 300 | 95 of 300 | 183 of 300 | 42 of 300 | 1,974 of 1,996 |

Among the 1,785 sampled rows retained after `n/z` exclusions, every/some/no object meets the floor on 111/709/965 rows, respectively. Both relation objects first appear within two frames of k on 34 of 300 LR, 21 of 300 NF and 14 of 300 UD rows.

All objects have **exactly zero** share on 914 of 1,800 rows; at least one has zero share on 1,655 of 1,800. Positive but subfloor shares occur on 121 of 1,800 rows. Merely requiring positive share makes every object eligible on 145 of 1,800, versus 112 of 1,800 at the floor.

**Training shortcut rules.** Largest share beats smallest share in all three camera samples. Ties select the first candidate in question order.

| Family | Largest-share accuracy | Unique-largest accuracy | Largest-share tie | Only in-view object is correct |
|---|---|---|---|---|
| v1 | 100 of 300 | 67 of 181 | 119 of 300 | 43 of 109 |
| v2 | 133 of 300 | 85 of 155 | 145 of 300 | 56 of 108 |
| v3 | 171 of 300 | 78 of 116 | 184 of 300 | 60 of 84 |

Allowing the answer to be *any tied maximum* yields 186 of 300, 230 of 300 and 262 of 300. Those inflated counts include every all-zero row; they do not show useful visibility prediction.

The best tested geometry rules are: LR chooses Right when subject bearing minus reference bearing is positive; NF chooses Near when the subject’s listed distance is smaller; UD chooses Up when its listed vertical scalar is larger. Each answers 300 of 300 correctly. These are label-generating geometry rules, **not visibility-only rules or demonstrated RGB reasoning**.

**The 59 pairs.** Both true winners must belong to the shared candidate set, and k must differ. These pairs are dependent observations.

| Check | Result |
|---|---|
| Shared-object first-seen map changes | 34 of 59 pairs |
| Individual shared-object frame claim changes | 46 of 143 comparisons |
| Shared ranking changes | 20 of 59 pairs |
| Highest-ranked shared object changes | 18 of 59 pairs |
| Neither shared frames nor shared ranking changes | 18 of 59 pairs |
| First-seen map changes with identical candidate sets | 7 of 8 pairs |
| Candidate presentation order changes in that stricter subset | 8 of 8 pairs |

Text beyond Step 1 changes on 59 of 59 pairs, even after normalizing numerical frame references. Candidate differences confound most pairs. Among identical-set pairs, semantic frame claims or rankings change on 7 of 8; the remaining pair changes presentation. The 41 of 59 pairs with an unchanged shared winner contain 34 distinct wrong dev items.

**Truthful wording from real sampled rows.** These examples supply visibility/localization lines; they do not invent a cross-frame reconstruction.

- **Every object:** Row `152263`, qid `vstirel_a31d82a6174d1ec37803d3ce`, has k=5 and shares `{refrigerator: 0.19010416666666666, shelf: 0.022122395833333332, sink: 0.04795572916666667, stove: 0.027799479166666665}`. All first-seen frames are 2. Wording: **“In frame 5, the refrigerator, shelf, sink and stove are in view.”**
- **Some objects:** Row `152156`, qid `vstirel_20b8fe198d16043b2c209168`, has k=4 and shares `{bed: 0.0, chair: 0.0, table: 0.039700520833333336, tv: 0.0}`. Wording: **“The table is in view in frame 4. The bed is out of view there; it is seen in frame 2. The chair and TV are out of view there; they are seen in frame 8.”** The answer is bed, although table alone is visible.
- **No objects:** Row `152126`, qid `vstirel_d5718a41a608d53c68ab744f`, has k=24 and zero shares for clothes, coffee table, bottle and shelf. Wording: **“None of these objects is in view in frame 24. I locate the clothes in frame 17, coffee table in frame 10, bottle in frame 29 and shelf in frame 6.”** The answer is shelf.
- **Subfloor exception:** Row `152166` records bed share `0.0005338541666666666` at k=3. “Out of view” would overstate this. Use **“Only a small part of the bed is visible in frame 3; I locate it in frame 1.”**

**3. What this changes for vehicle N**

**1. Re-render visibility and require evidence for the frame-k relation.** Review all 11,799 of 11,926 kept rows across `camera_obj_rel_dist_v{1,2,3}|vsti_rel_v4|None` and `obj_obj_relative_pos_{lr,nf,ud}|vsti_rel_v4|None`. The table gives each family’s count. Render separate lines for zero, positive-subfloor and above-floor shares, followed by the type-specific relation; retain geometry numbers builder-side.

For example: **“The table is in view in frame 4. The bed is out of view there; it is seen in frame 2.”** A subsequent comparison from the frame-4 camera needs verified cross-frame correspondence and viewpoint evidence. Visibility wording alone does not supply that evidence. Do not blanket-drop offscreen questions.

This could address the unsupported relation form accompanying 354 of 375 errors, a ceiling of 39.33 points over 900 dev items. **Expected recovery is unknown.** Failure would be accurate visibility wording followed by the same wrong relation, or continued unsupported localization at k.

**2. Add controlled same-video pairs across k and candidate order.** **Budget guess:** add 100 pairs per camera family, totaling 600 new rows, with fixed candidate order for the k intervention and separate option-permutation controls. Preserve each object’s verified first-seen frame across all variants.

The current stale-winner pairs contain 34 wrong items, a ceiling of 3.78 points over 900 items. Failure would be continued first-seen changes on fixed-input controls or no improvement over 18 of 59 truth-changing winner responses. These ceilings overlap proposal 1.

**3. Enforce sampled-frame citations and test their consistency.** Apply the 1–32 citation constraint to the same six families; do not convert first-seen frames into visibility labels. Impossible object citations accompany 162 of 375 errors, a ceiling of 18.00 points over 900 items. **No causal recovery estimate is established.** Failure would be legal-looking citations with unchanged answers, or first-seen claims that still change under question-only interventions.

**4. Refuted**

The literal interpretation that only Step 1 changes is false: text beyond it changes on 59 of 59 pairs, and shared first-seen claims change on 34 of 59. The expected invariance is violated even on 7 of 8 identical-candidate pairs.

“Below the visibility floor” cannot uniformly mean “out of view”: 121 of 1,800 sampled rows contain positive subfloor shares. Training visibility also cannot establish that the dev model’s first-seen claims are honest. No supplied dev score or the verified 18-of-59 winner-change count is contradicted.

**5. Not established**

True dev visibility, first-seen accuracy and the causal cost of bad citations remain unknown. Joining the exported source qids to the dev builder’s instance annotations would settle the first two. Fixed-video interventions on k, candidate order and trace wording would test causality. Full-store visibility counts require a separately authorized census; the eligibility counts here describe the sample.

**Appendix — CLASSIFIER**

This reproduces the training visibility counts, camera visibility rules and the 59-pair comparison.

```python
import sys, json, sqlite3, random, re, itertools
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
base = "/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7"
idx = json.load(open(base + "/FAMILY_INDEX_RANGES.json"))["families"]
db = sqlite3.connect("file:" + base + "/vqa/rows.sqlite?mode=ro", uri=True)
total = Counter()
for typ in sorted(t for t in idx if t.startswith(("camera_obj_rel", "obj_obj_relative"))):
    keys = [i for a, b in idx[typ] for i in range(a, b + 1)]
    ids = sorted(random.Random(200).sample(keys, 300))
    out = Counter()
    for start in range(0, 300, 200):
        batch = ids[start:start + 200]
        sql = "select i,row from rows where i in (" + ",".join("?" * len(batch)) + ")"
        for i, raw in db.execute(sql, batch):
            r = json.loads(raw)
            assert r["question_type"] == typ
            p = r["provenance"]
            shares = p["frame_n_share"]
            nv = sum(v >= p["visibility_floor"] for v in shares.values())
            out["all" if nv == len(shares) else "some" if nv else "none"] += 1
            if typ.startswith("camera"):
                opts = [s[3:] for s in r["student_input"]["options"]]
                answer = opts[ord(r["answer"]) - 65]
                out["only_visible_n"] += nv == 1
                out["only_visible_correct"] += nv == 1 and shares[answer] >= p["visibility_floor"]
                out["largest_share_correct"] += answer == max(opts, key=shares.get)
                out["answer_within2"] += abs(p["first_seen"][answer] - p["camera_frame"]) <= 2
    assert sum(out[x] for x in ("all", "some", "none")) == 300
    total.update(out)
    print(typ, dict(out))
print("TRAIN_TOTAL", dict(total))
rows = K.vsti("R1", 200)
def objs(r):
    return [x[3:] for x in r["options"]]
def frame(r):
    return int(re.search(r"frame (\d+) of 32", r["question"], re.I).group(1))
def first(r):
    return {a: int(re.search(r"locate the " + re.escape(a) +
            r", first seen in frame (\d+)", r["text"], re.I).group(1)) for a in objs(r)}
def truth(r):
    return objs(r)[ord(r["gt"]) - 65]
def order(r):
    return re.search(r"the objects are (.*?)\.\n", r["text"]).group(1).split(", then ")
counts = Counter()
camera = [r for r in rows if r["type"].startswith("camera")]
for a, b in itertools.combinations(camera, 2):
    shared = set(objs(a)) & set(objs(b))
    if a["room"] != b["room"] or frame(a) == frame(b) or len(shared) < 2:
        continue
    if truth(a) not in shared or truth(b) not in shared or truth(a) == truth(b):
        continue
    counts["pairs"] += 1
    changed = any(first(a)[x] != first(b)[x] for x in shared)
    counts["first_seen_changes"] += changed
    aa = [x for x in order(a) if x in shared]
    bb = [x for x in order(b) if x in shared]
    counts["winner_changes"] += aa[0] != bb[0]
    counts["order_changes"] += aa != bb
    if set(objs(a)) == set(objs(b)):
        counts["same_candidates"] += 1
        counts["same_candidates_first_seen_changes"] += changed
print("DEV_PAIRS", dict(counts))
```