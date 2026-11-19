**1. Question and answer**

**1. Do checkpoints repeat the same wrong candidate?** Yes. Step 544 and step 200 agree on the wrong candidate on 75 of 103 shared errors; step 100 and step 200 agree on 93 of 113. This supports persistent error mechanisms, but does not identify which cue causes them.

**2. Do question position, object size, or training class pairs predict the model’s choice?** None provides consistent evidence of a shortcut across both dev sets. Among items with observed training pairs, the raw class-pair prior matches the model and truth equally often: 49 of 163 each. Coverage limits the size test substantially.

**3. Does step 200 preserve step 544’s distance ranking?** Often, including on wrong answers. Mean Spearman correlation is 0.730 on 40 wrong dev-S1 items and 0.571 on 91 wrong R0-dev items; corresponding correct-item means are 0.860 and 0.800. These compare two model outputs, not an order against geometric truth.

**4. Does farthest behave differently from closest?** The correct endpoint appears on 127 of 186 closest items and 61 of 93 farthest items. Their endpoint-relative truth-rank distributions are similar; step 200 answers the first element on 0 of 93 farthest questions.

**5. Does the trace apply the duplicate-instance instruction?** No explicit application appears on 150 of 150 dev-S1 traces. One wording, present on 5 of 150 questions, is: “When multiple objects are present, measure to the closest.” The instructions have multiple paraphrases.

**6. What could a comparison line fix without a head?** A perfect comparison of the two candidates nearest the requested endpoint could recover 62 of 131 errors, provided the selected object maps to its answer option. An honest training line needs evidence for both candidate instances and their relative nearest-surface distances; the endpoint label alone is insufficient.

**2. Evidence**

All model-answer counts use B2048. Step-200 B2048 and full-generation predictions agree on 429 of 429 items; forced closure affects 0 of 429.

Sources:
- Let `H` denote `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build`.
- Step 200: `H/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 100: the same suffix under `H/a5d2d909067`.
- Step 544 R0-dev: the same `a7` suffix under `H/adff67f7ae9`.
- Step 544 dev-S1: `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
- Training samples: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite`, using `FAMILY_INDEX_RANGES.json` in its parent directory.
- Family totals: `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json`.
- First-wave comparison: `/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T041209Z_san_m200_rel_dist/final_message.md`.

**Choice stability, restricted to items wrong at both checkpoints**

| Set | Compared with step 200 | Same wrong candidate | Different wrong candidate |
|---|---|---:|---:|
| dev-S1 | Step 544 | 26 of 31 | 5 of 31 |
| R0-dev | Step 544 | 49 of 72 | 23 of 72 |
| dev-S1 | Step 100 | 30 of 34 | 4 of 34 |
| R0-dev | Step 100 | 63 of 79 | 16 of 79 |

Stable choices dominate. Nevertheless, changed choices on 23 of 72 shared R0-dev errors show that instability remains material.

**Candidate priors**

I sampled 2,000 of 9,778 size rows and 3,000 of 20,665 relative-distance rows, uniformly without replacement using seed 200 and primary-key queries. Every sampled row belonged to the requested family. The supplied counts mark 9,778 of 9,778 size rows and 20,665 of 20,665 distance rows as kept.

Class matching lowercases names and removes leading articles; it does not merge synonyms or subclasses. Size means the class median of the longest dimension in centimeters.

The raw pair predictor selects the candidate with the most sampled answer occurrences for that reference class. The conditional predictor divides those wins by appearances alongside that reference. Both use closest-answer training statistics even on farthest questions; neither is a learned farthest prior.

Ties use the first candidate named in the question. Size and conditional-pair predictions select among observed classes/pairs; wholly uncovered items fall back to that first candidate. Thus their all-item scores include a fallback, and partially covered size predictions mean **largest observed class**, not necessarily largest candidate.

| Predictor | Set | Truth, all items | Model, all items | Truth, covered items | Model, covered items |
|---|---|---:|---:|---:|---:|
| First candidate in question | dev-S1 | 41 of 150 | 45 of 150 | 41 of 150 | 45 of 150 |
| First candidate in question | R0-dev | 82 of 279 | 68 of 279 | 82 of 279 | 68 of 279 |
| Largest observed class median | dev-S1 | 42 of 150 | 38 of 150 | 42 of 139 | 36 of 139 |
| Largest observed class median | R0-dev | 80 of 279 | 76 of 279 | 80 of 272 | 76 of 272 |
| Raw class-pair answer count | dev-S1 | 48 of 150 | 51 of 150 | 32 of 104 | 36 of 104 |
| Raw class-pair answer count | R0-dev | 85 of 279 | 70 of 279 | 17 of 59 | 13 of 59 |
| Conditional class-pair win rate | dev-S1 | 43 of 150 | 47 of 150 | 27 of 104 | 32 of 104 |
| Conditional class-pair win rate | R0-dev | 89 of 279 | 75 of 279 | 21 of 59 | 18 of 59 |

“Covered” means at least one candidate has an observed class or pair. Complete size coverage exists on only 2 of 150 dev-S1 and 30 of 279 R0-dev items. On those subsets, size predicts truth/model on 0/0 of 2 and 9/13 of 30, respectively. The sample lacks exact names including “chair” and “door.”

Complete pair coverage exists on 34 of 150 dev-S1 and 2 of 279 R0-dev items. Conditional rates predict truth and model equally often there: 10 of 34 each and 0 of 2 each.

The small dev-S1 excess does not replicate on R0-dev. For raw counts on covered dev-S1 items, the prior matches only the model on 9 of 104 and only truth on 5 of 104; R0-dev reverses this, with 4 of 59 versus 8 of 59. These results do not establish memorized class-pair dependence.

**Full-order agreement with step 544**

All four metre values parse on 429 of 429 step-544 traces. I computed per-item Spearman correlation using average ranks for tied distances, then averaged across items.

| Set and step-200 outcome | Mean correlation | Identical ranking without ties | Step-544 distance ties |
|---|---:|---:|---:|
| dev-S1 correct | 0.860; 110 items | 55 of 110 | 8 of 110 |
| dev-S1 wrong | 0.730; 40 items | 17 of 40 | 0 of 40 |
| R0-dev correct | 0.800; 188 items | 81 of 188 | 18 of 188 |
| R0-dev wrong | 0.571; 91 items | 23 of 91 | 10 of 91 |

Agreement on wrong items supports persistent rankings. It does not validate step 544’s invented metre values.

**Truth ranks and closest/farthest behavior**

Ranks below run from nearest to farthest in the step-200 trace.

| Set/question | Truth at rank 1 | Truth at rank 2 | Truth at rank 3 | Truth at rank 4 |
|---|---:|---:|---:|---:|
| dev-S1 closest | 110 of 150 | 22 of 150 | 12 of 150 | 6 of 150 |
| R0-dev closest | 127 of 186 | 26 of 186 | 20 of 186 | 13 of 186 |
| R0-dev farthest | 9 of 93 | 9 of 93 | 14 of 93 | 61 of 93 |

Read from the requested endpoint, R0-dev closest has counts 127/26/20/13 of 186, versus farthest’s 61/14/9/9 of 93. This is approximate symmetry, not identical distributions.

The model answers rank 1 on 186 of 186 closest items and rank 4 on 92 of 93 farthest items. The exception answers rank 2; none answers rank 1. Farthest questions occur on 0 of 3,000 sampled training rows.

Duplicate instructions occur on 150 of 150 dev-S1 questions and 0 of 279 R0-dev questions. Step-200 traces mention instances, duplicates, multiplicity, or nearest/closest points on 0 of 429 items. The first-wave finding that only the reference receives a Locate line remains consistent with these traces. This establishes missing written handling, not missing internal reasoning.

**3. What this changes for vehicle N**

All proposed quantities below are **guesses**, not measured dose requirements. All changes target `object_rel_distance|w1g|rows_rebuild_d0_v1`; no rows were changed.

1. **Reword about 2,000 rows to compare the two endpoint candidates and bind the winner to its option.** Prioritize cases with verified candidate identities and a supported comparison. The oracle ceiling is 22 of 150 dev-S1 items and 40 of 279 R0-dev items: 62 of 131 errors. One of those requires repairing answer binding as well as comparison.

   Illustrative wording, usable only when the source supports each clause: “The pillow is seen in frame {p}; the bed is seen in frame {b}. The pillow lies beside the backpack; the bed lies beyond the pillow. The pillow is nearer to the backpack than the bed. The question asks for the closest: pillow, option B.”

   The row must supply source-backed frames, persistent instance identities, and evidence for the nearest-surface comparison across views. Verified geometry may establish the relation during construction, but the direct trace must express it in words. Do not derive a comparison from the winning label alone or restore unprinted metres. **Failure signal:** comparison language appears, but truth remains at the adjacent rank and accuracy does not improve.

2. **Reword about 3,000 rows to locate all candidates and resolve actual duplicate instances before ordering.** This targets the remaining displaced-order errors: 18 of 150 dev-S1 and 51 of 279 R0-dev items. Their combined ceiling is 69 of 131 errors, but the share caused by localization or duplicates is unknown.

   Add an instance-selection sentence only when the source establishes multiple instances and which one has the nearest relevant surface. Follow the trace ruling by omitting unsupported frame citations. **Failure signal:** additional Locate lines appear without reducing errors where truth lies beyond the endpoint pair.

3. **Add about 1,000 farthest twins with independently verified farthest labels.** Keep scenes, candidates, and option order paired with closest versions. Do not create a farthest label merely by taking the last element of an unverified training trace.

   This addresses the sampled coverage gap, but offers **no demonstrated endpoint-selection gain**: step 200 already chooses the last element on 92 of 93 farthest items. The relevant error population is 32 of 93 farthest items; recovery is unknown and overlaps the first two proposals. **Failure signal:** the farthest truth-rank distribution and accuracy remain unchanged.

The trace constraints come from the Answer and relative-distance sections of `/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md`: source-supported Locate lines, verbal relations, and no unprinted measurements.

**4. Refuted**

The prompt’s claim that the answer follows the wrong endpoint on **131 of 131** errors is false. It does so on **130 of 131**. The first-wave report already records the exception correctly.

On `d6eea8cb010f2e223a6eb0a0`, the order is stool, router, picture, panel. The trace selects panel, but the answer names router; truth is picture. Consequently, the 62-item comparison ceiling requires correct option binding. The other 61 adjacent-rank errors already follow their selected endpoint.

No other first-wave numerical finding tested here was contradicted. “Training rows are all closest” remains a sample-supported statement, not a verified census.

**5. Not established**

Stable wrong choices do not establish their cause. The tested priors provide no consistent cross-set explanation, and sparse exact-class coverage weakens the size and pair tests. Broader training samples or a predeclared class taxonomy would settle coverage; option permutations and controlled visual interventions would test causal dependence.

The full geometric order, actual duplicate counts, candidate visibility, and nearest-surface relations remain unverified. Instance annotations and RGB/geometry review would distinguish localization errors from comparison errors and establish whether proposed comparison lines are honest.

Training gains remain unmeasured. A controlled row-form comparison with matched examples and training weight is needed to turn the oracle ceilings into recovery estimates.

**Appendix — CLASSIFIER**

```python
import sys, re, json, sqlite3, random, statistics, resource
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_AS, (3*1024**3, 3*1024**3))
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
B = "/scratch/jjyeung/orch_n30/"
def norm(x): return re.sub(r"^(?:the|a|an)\s+", "", x.lower().strip().rstrip("."))
def opts(r): return {x[0]: norm(x[3:]) for x in r["options"]}
def candidates(r): return [norm(x) for x in re.search(r"\(([^()]*)\)", r["question"])[1].split(",")]
def order(r):
    line = next(x for x in r["text"].splitlines() if x.startswith("Step 2:"))
    return [norm(x) for x in re.split(r",\s*(?:then\s+)?", line.rsplit(":", 1)[1])]
def ref(r):
    patterns = [r"(?:closest to|nearest to|nearest|farthest from|smallest distance to)\s+the\s+([^?.]+)",
                r"\) to the ([^,?.]+)", r"gaps from the (.+?) to these objects", r"distances to the ([^,]+),"]
    for p in patterns:
        m = re.search(p, r["question"], re.I)
        if m: return re.split(r",| when | from their | based on ", norm(m[1]))[0]
D = {(s,t): K.direct(run,t,s,types=["object_rel_distance"])
     for s in ["dev-S1","R0-dev"] for run,t in [("S1",544),("R1",100),("R1",200)]}
for s in ["dev-S1","R0-dev"]:
    for t in [544,100]:
        z = [(o,n) for o,n in K.paired(D[s,t],D[s,200]) if o["score"] == n["score"] == 0]
        print("same wrong",s,t,sum(opts(o)[o["pred"]]==opts(n)[n["pred"]] for o,n in z),"of",len(z))
    for far in [False,True]:
        z = [r for r in D[s,200] if ("farthest" in r["question"]) == far]
        if not z: continue
        ranks = Counter(order(r).index(opts(r)[r["gt"]])+1 for r in z)
        ans = Counter(order(r).index(opts(r)[r["pred"]])+1 for r in z)
        print("ranks",s,"farthest" if far else "closest",len(z),sorted(ranks.items()),"answers",sorted(ans.items()))
ix = json.load(open(B+"r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json"))["families"]
con = sqlite3.connect("file:"+B+"r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro",uri=True)
T = {}
for typ,n,pool in [("object_size_estimation",2000,"r1g"),("object_rel_distance",3000,"w1g")]:
    ids = [i for a,b in ix[typ] for i in range(a,b+1)]
    ids = sorted(random.Random(200).sample(ids,n)); rr = []
    for j in range(0,n,200):
        batch = ids[j:j+200]
        for i,raw in con.execute("select i,row from rows where i in ("+",".join("?"*len(batch))+")",batch):
            r = json.loads(raw)
            assert (r["question_type"],r["pool"],r["retrace"]["rule"]) == (typ,pool,"rows_rebuild_d0_v1")
            rr.append(dict(question=r["student_input"]["question"],options=r["student_input"].get("options",[]),
                           target=r["target"],answer=r["answer"]))
    T[typ] = rr
con.close()
sizes = defaultdict(list); wins = Counter(); present = Counter()
for r in T["object_size_estimation"]:
    m = re.search(r"Step 1: find (.+?)(?:, first seen|\.\n)",r["target"])
    assert m and "centimeter" in r["question"]
    sizes[norm(m[1])].append(float(r["answer"]))
med = {c: statistics.median(v) for c,v in sizes.items()}
for r in T["object_rel_distance"]:
    a = ref(r); assert a is not None
    for c in opts(r).values(): present[a,c] += 1
    wins[a,opts(r)[r["answer"]]] += 1
print("training farthest",sum("farthest" in r["question"].lower() for r in T["object_rel_distance"]),"of",3000)
def prior(r,k):
    cs = candidates(r)
    if k == "first": return cs[0],True,True
    known = [c in med if k=="size" else (ref(r),c) in present for c in cs]
    if k == "paircount": return max(cs,key=lambda c:wins[ref(r),c]),any(known),all(known)
    vals = [med[c] if k=="size" else wins[ref(r),c]/present[ref(r),c]
            for c,ok in zip(cs,known) if ok]
    scores = iter(vals)
    v = [next(scores) if ok else float("-inf") for ok in known]
    return cs[v.index(max(v))],any(known),all(known)
for s in ["dev-S1","R0-dev"]:
    for k in ["first","size","paircount","pair"]:
        pp = [(r,prior(r,k)) for r in D[s,200]]
        for mode in ["all","covered","full"]:
            z = [(r,p) for r,p in pp if mode=="all" or p[1 if mode=="covered" else 2]]
            print("prior",s,k,mode,"N",len(z),"truth",sum(p[0]==opts(r)[r["gt"]] for r,p in z),
                  "model",sum(p[0]==opts(r)[r["pred"]] for r,p in z))
```