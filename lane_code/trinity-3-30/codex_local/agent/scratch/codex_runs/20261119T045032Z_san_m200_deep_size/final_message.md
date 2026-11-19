**Question and answer**

1. **How much training support does each dev class have?** The deterministic sample contains 3,000 of 9,778 family rows and 784 classes. Classes with at least five sampled rows cover 50 of 150 dev-S1 items and 113 of 293 R0-dev items.
2. **Is the model a class-prior regressor?** The class median approaches step 200 on those supported items: 66.00 versus 67.40 MRA on dev-S1 and 50.80 versus 55.75 on R0-dev. However, residual correlations are 0.699 and 0.718; the answers contain variation beyond this class median, although these observations cannot establish that video supplies it.
3. **Does step 200 repeat one answer per class?** Sometimes: R0-dev doors receive 210 cm on 8 of 8 items, and keyboards receive 45 cm on 5 of 6. Other classes vary substantially; windowsills have six distinct answers on 6 of 6 items.
4. **Do sample-unseen classes perform worse?** Step 200 scores 70.60 MRA on 50 sample-unseen dev-S1 items versus 68.60 on 100 seen items. R0-dev scores are 57.36 on 106 unseen items versus 59.09 on 187 seen items; absence from this sample does not mean absence from training.
5. **Does a prediction floor explain small-object loss?** An observed floor exists: 0 of 293 R0-dev answers are below 10 cm. But only 5 of 88 small-object truths fall below that floor; 23 of 88 predictions instead overshoot to at least 30 cm.
6. **Would the deployed box head improve size answers?** The audited comparison remains unfavorable: 50.69 versus 73.10 MRA on 58 matched items using identical labels and scoring. A replacement head must exceed that direct-answer score with verified instance matches; the current join does not establish instance identity.

**Evidence**

I sampled primary keys without replacement using seed 200 and queries of at most 200 keys. All 3,000 sampled rows belong to `object_size_estimation|r1g|rows_rebuild_d0_v1`; all ask for centimetres. The supplied template counts retain 9,778 of 9,778 family rows. Classes are exact lowercased noun phrases with question wording removed; synonyms and plurals remain separate.

All scores below use B2048 predictions, `gt`, and the requested inclusive MRA thresholds, with numerical tolerance at boundaries. Measurements use centimetres: inches ×2.54, feet ×30.48, metres ×100. Stored scores differ from this calculation on 11 of 150 step-200 dev-S1 items and 5 of 293 R0-dev items. Dev-S1 has differing truth fields; threshold-boundary arithmetic also matters. Stored overall scores remain 69.40 and 58.29, respectively.

| Set and class support | Items | Training median MRA | Step 544 MRA | Step 200 MRA |
|---|---:|---:|---:|---:|
| dev-S1, all | 150 of 150 | Undefined for unseen classes | 68.80 | 69.27 |
| dev-S1, ≥1 sampled row | 100 of 150 | 59.70 | 68.00 | 68.60 |
| dev-S1, ≥5 sampled rows | 50 of 150 | 66.00 | 69.00 | 67.40 |
| dev-S1, no sampled row | 50 of 150 | Undefined | 70.40 | 70.60 |
| R0-dev, all | 293 of 293 | Undefined for unseen classes | 59.18 | 58.46 |
| R0-dev, ≥1 sampled row | 187 of 293 | 53.21 | 61.82 | 59.09 |
| R0-dev, ≥5 sampled rows | 113 of 293 | 50.80 | 60.00 | 55.75 |
| R0-dev, no sampled row | 106 of 293 | Undefined | 54.53 | 57.36 |

The following Pearson correlations compare predictions with training medians and prediction residuals with truth residuals. Each residual subtracts the same training class median.

| Set and support | Items | 544: answer / residual correlation | 200: answer / residual correlation |
|---|---:|---:|---:|
| dev-S1, ≥1 row | 100 of 150 | −0.056 / 0.135 | 0.415 / 0.413 |
| dev-S1, ≥5 rows | 50 of 150 | 0.688 / 0.712 | 0.714 / 0.699 |
| R0-dev, ≥1 row | 187 of 293 | 0.782 / 0.782 | 0.823 / 0.718 |
| R0-dev, ≥5 rows | 113 of 293 | 0.747 / 0.799 | 0.791 / 0.718 |

The positive residual correlation survives removing the three largest absolute truth residuals: 0.634 on 47 dev-S1 items and 0.430 on 110 R0-dev items from the ≥5-row cohorts. This weakens the claim that a few extreme items explain the result.

The sample contains 143 of 784 classes with at least five rows. The table lists all 64 such classes appearing in either dev set. Each entry gives **sample rows of 3,000; median [25th, 75th percentile] in cm**. The appendix computes statistics for all 784 classes.

| Class: rows; median [quartiles] | Class: rows; median [quartiles] |
|---|---|
| air purifier: 6; 67 [57, 96.5] | backsplash: 5; 147 [101, 151] |
| bathroom cabinet: 6; 86 [81.8, 139.8] | bathtub: 11; 167 [158, 175] |
| bedside table: 18; 60 [53.2, 67.2] | blanket: 9; 87 [67, 185] |
| book: 9; 28 [22, 30] | bottle: 8; 20 [18.5, 25.5] |
| box: 6; 43 [26.8, 62.2] | cabinet: 39; 128 [100.5, 212] |
| cable duct: 16; 310.5 [166, 346.8] | cardboard box: 14; 53.5 [36.5, 68] |
| ceiling light: 9; 78 [70, 142] | clothes hanger: 5; 171 [122, 171] |
| counter: 12; 123.5 [66.2, 270.8] | curtain: 52; 220 [193, 246.2] |
| curtain rod: 11; 205 [134.5, 228.5] | desk: 46; 137 [126.5, 159.5] |
| desk lamp: 12; 61 [52, 69] | dishwasher: 10; 82 [72.8, 83.8] |
| dustpan: 5; 46 [38, 85] | faucet: 19; 24 [19, 27.5] |
| fire extinguisher: 9; 66 [64, 67] | frying pan: 6; 44.5 [43.2, 48] |
| intercom: 10; 23 [16.2, 28.5] | jacket: 29; 86 [80, 100] |
| kitchen counter: 41; 208 [149, 259] | ladder: 13; 186 [113, 240] |
| mattress: 36; 199 [165.5, 204] | mirror: 18; 152.5 [119, 170.5] |
| mug: 12; 12 [11, 14] | nightstand: 5; 60 [59, 68] |
| notebook: 6; 33 [27, 38.2] | office chair: 37; 106 [99, 117] |
| oven: 27; 71 [63.5, 75] | paper: 19; 34 [30, 42.5] |
| paper towel dispenser: 15; 49 [47.5, 52] | picture: 19; 74 [50.5, 113.5] |
| plant pot: 5; 16 [16, 23] | router: 16; 26 [22, 31] |
| rug: 40; 154 [97.5, 246.5] | shelf: 31; 160 [94.5, 206] |
| shower curtain: 13; 205 [187, 212] | sink: 65; 61 [58, 69] |
| soap dispenser: 6; 23 [20.8, 28.2] | sofa: 7; 176 [126.5, 231.5] |
| speaker: 9; 24 [19, 27] | stool: 12; 55 [44, 62.5] |
| storage cabinet: 30; 221 [200.8, 227.2] | storage rack: 22; 119 [102.5, 180] |
| stove: 21; 62 [59, 65] | toilet paper: 9; 15 [13, 25] |
| towel: 15; 84 [76, 106] | trash bin: 7; 46 [35, 55.5] |
| tray: 7; 41 [36, 45.5] | trolley: 9; 85 [73, 87] |
| umbrella: 11; 68 [36, 73] | vase: 6; 23 [20.8, 25.2] |
| wardrobe: 47; 232 [212, 242.5] | washing machine: 8; 87.5 [86.8, 97.2] |
| window: 74; 167.5 [126.5, 211] | window sill: 21; 334 [175, 347] |
| windowframe: 7; 176 [159.5, 180.5] | windowsill: 68; 228.5 [122.2, 344.5] |

Some frequent dev classes have weak sampled priors: bed has 3 of 3,000 rows, median 211 cm and range 206–215; table has 2, median 189 and range 143–235; refrigerator has 1 at 90; door has 1 at 210. These thin estimates help explain why the ≥1-row and ≥5-row comparisons differ.

All classes with at least five dev items follow. Distinct answers are counted **after centimetre conversion**, rounded to six decimals; ranges use `gt`.

| Set / class | Distinct answers of class items | Step-200 answer range, cm | Truth range, cm |
|---|---:|---:|---:|
| dev-S1 / bathtub | 5 of 7 | 168–204.52 | 161.54–191.90 |
| dev-S1 / bed | 8 of 14 | 180.59–216.71 | 203–231.65 |
| dev-S1 / chair | 5 of 5 | 79–109 | 73.15–108 |
| dev-S1 / desk | 4 of 6 | 101–198.12 | 139.20–253.60 |
| dev-S1 / refrigerator | 8 of 9 | 86–212.45 | 147.20–271.27 |
| dev-S1 / sofa | 5 of 7 | 80.01–213.66 | 79.50–204.22 |
| dev-S1 / stool | 5 of 5 | 43–74 | 50.04–64 |
| dev-S1 / stove | 6 of 7 | 57.91–77.42 | 56–85.34 |
| dev-S1 / table | 10 of 13 | 46.02–304 | 85.34–424.94 |
| dev-S1 / toilet | 5 of 6 | 45–80.01 | 51–93.30 |
| dev-S1 / tv | 12 of 14 | 74–131 | 61–115.82 |
| R0-dev / cabinet | 5 of 9 | 44–240 | 42–126 |
| R0-dev / door | 1 of 8 | 210–210 | 209–309 |
| R0-dev / keyboard | 2 of 6 | 44–45 | 27–51 |
| R0-dev / sink | 4 of 6 | 49–66 | 55–65 |
| R0-dev / telephone | 3 of 5 | 24–37 | 22–39 |
| R0-dev / toilet | 4 of 5 | 36–78 | 47–89 |
| R0-dev / window | 5 of 5 | 134–211 | 107–310 |
| R0-dev / windowsill | 6 of 6 | 104–592 | 96–707 |

For the 88 small R0-dev items, truth and answer medians are 21 and 23 cm. Recomputed MRA is 48.18; stored MRA is 47.95.

| Measurement interval, cm | Truths | Step-200 answers |
|---|---:|---:|
| Below 10 | 5 of 88 | 0 of 88 |
| 10 to below 20 | 34 of 88 | 29 of 88 |
| 20 to below 30 | 49 of 88 | 36 of 88 |
| 30 to below 50 | 0 of 88 | 13 of 88 |
| 50 to below 100 | 0 of 88 | 5 of 88 |
| At least 100 | 0 of 88 | 5 of 88 |

The five sub-10-cm items score 4.00 MRA and cost 1.64 points over all 293 R0-dev items. By comparison, the 23 small items answered at ≥30 cm score 12.61 MRA and cost 6.86 points. The observed floor therefore cannot explain most of the small-object loss. Training includes 24 of 3,000 answers below 10 cm and 473 of 3,000 below 30 cm.

I reran `size_boxhead_join.py` in memory with its final file-writing statement excluded. It reproduces the supplied 50.7/73.6 scores on 58 items. Its box score uses `gt`, whereas its direct comparator uses stored `score`; harmonizing both gives the following results.

| Step-200 join audit | Items | Box MRA | Direct MRA |
|---|---:|---:|---:|
| Both scored against `gt` | 58 of 150 | 50.69 | 73.10 |
| Both scored against `gt_released` | 58 of 150 | 50.34 | 73.79 |
| Only one distinct box length per room/class; `gt` | 47 of 150 | 50.00 | 70.21 |

All 58 joins match the exact parsed class. Unit handling is correct, but 23 of 58 pool multiple calls and 11 of 58 pool different lengths. For example, one television join pools 202, 202 and 61 cm. No instance IDs establish which box answers the size question. Boxes fall within 25% of truth on 31 of 58 items, versus 47 of 58 direct answers. Boxes beat direct answers on 14 of 58; an oracle choosing between them scores 80.52 MRA, but that oracle is not a deployable selector. The script’s step-544 row also compares against **step-200 direct answers**.

Sources: training statistics come from `r1_ops6/store/a2_vqa_v7/{FAMILY_INDEX_RANGES.json,vqa/rows.sqlite}` and retention from `dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json`, beneath `/scratch/jjyeung/orch_n30`. Dev predictions come through `san_kit`: step 200 uses `cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}`; step-544 R0-dev uses `adff67f7ae9/fetched/x/a7`; step-544 dev-S1 uses `evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`. The join sources are `swarm_an/work/verify/{size_boxhead_join.py,SIZE_BOXHEAD_JOIN.json}` and the routed returns loaded by `K.routed`.

**What this changes for vehicle N**

1. **Reword 2,000 existing rows in `object_size_estimation|r1g|rows_rebuild_d0_v1` around contrasting instances of the same class.** The row budget is a **guess**. Require annotated instance identity, longest-axis selection and a visible comparison, rather than another generic instruction to estimate. A hypothetical, annotation-dependent trace is: “Step 1: locate the cabinet beside the door. Step 2: its vertical edge is longest. Step 3: in the view showing both at similar depth, the cabinet reaches about halfway up the door.” Keep the numeric measurement in the answer. This could address some of 105 of 150 dev-S1 and 229 of 293 R0-dev imperfect answers; those counts are ceilings, not predicted recoveries. Failure would appear as unchanged same-class error despite richer traces.
2. **Allocate 800 of those 2,000 rewrites to small instances, including 200 below 10 cm, if training annotations support them.** Both allocations are **guesses**; use training scenes only. Target the 75 of 88 imperfect small R0-dev items, whose stored loss costs 15.63 points overall, especially the 23 severe overshoots. Failure would appear as continued ≥30-cm answers for small instances or systematic underestimation of larger same-class objects.
3. **Keep direct size answers as the majority; make any head rows an audited exploration experiment.** For the ruling’s approximately 2,000 exploratory rows, use proposed family `object_size_estimation|vehicleN_size_head|deployed_response_checked`, actual deployed responses, verified instance matches, and direct recovery when the head fails. The recoverable cohort demonstrated here is only 14 of 58 head-better items; the oracle advantage is 7.41 points on those 58, not an expected gain. Reject a broad routing change if held-out instance-matched head answers still fail to beat direct answers.

**Refuted**

Close aggregate MRA does not establish a pure class-prior regressor: residual correlations remain positive on both sets. A universal “small-object floor” explanation is also insufficient: only 5 of 88 small truths fall below the observed floor. The first-wave repetition findings stand, but its distinct-answer counts used requested-unit pairs; centimetre-normalized counts differ. Its stored scores remain valid as stored scores; they are not identical to recomputation from the loader’s `gt`.

**Not established**

These traces do not prove visual scale use, true training-unseen classes, or correct box-instance joins. Resolve those questions with fixed-question video swaps, same-class instance-controlled tests, a complete training class/alias inventory, and instance-ID-matched box evaluation. Training-row counts include paraphrases; the sample contains 2,527 distinct scene/class/answer combinations among 3,000 rows. No files were changed.

**Appendix — CLASSIFIER**

Run with `/usr/bin/python3`. This reproduces coverage, predictor scores, correlations and the small-object floor; `med` and `spread` hold every sampled class’s statistics.

```python
import sys, json, sqlite3, random, re, statistics as st
from collections import defaultdict
sys.dont_write_bytecode = True
P = "/scratch/jjyeung/orch_n30"
sys.path.insert(0, P + "/swarm_an/kit")
import san_kit as K
def cls(q):
    q = q.lower().strip().replace("’", "'")
    if q.startswith("measure the "):
        return q[12:].split(" along its ")[0]
    return re.split(r",|\?| in |'s| is | measures | measured| using ",
                    re.split(r"(?:of|for) the ", q)[-1])[0].strip()
def unit(q):
    q = q.lower()
    if re.search(r"centimet|\bcm\b", q): return 1.
    if "inch" in q: return 2.54
    if re.search(r"\bfeet\b|\bfoot\b|\bft\b", q): return 30.48
    if re.search(r"\bmeters?\b|\bmetres?\b", q): return 100.
    raise ValueError(q)
def mra(p, g):
    return sum(abs(p-g)/g <= 1-t/100+1e-12
               for t in range(50, 100, 5))/10
def corr(x, y):
    a, b = st.mean(x), st.mean(y)
    return sum((u-a)*(v-b) for u,v in zip(x,y))/(
        sum((u-a)**2 for u in x)*sum((v-b)**2 for v in y))**.5
ranges = json.load(open(P+"/r1_ops6/store/a2_vqa_v7/"
                       "FAMILY_INDEX_RANGES.json"))["families"]["object_size_estimation"]
ids = sorted(random.Random(200).sample(
    [i for a,b in ranges for i in range(a,b+1)], 3000))
db = sqlite3.connect("file:"+P+"/r1_ops6/store/a2_vqa_v7/vqa/"
                     "rows.sqlite?mode=ro", uri=True)
train = defaultdict(list)
for k in range(0, 3000, 200):
    batch = ids[k:k+200]
    for i, raw in db.execute("select i,row from rows where i in ("+
                            ",".join("?"*len(batch))+")", batch):
        r = json.loads(raw)
        assert (r["pool"],r["retrace"]["rule"]) == ("r1g","rows_rebuild_d0_v1")
        q = r["student_input"]["question"]
        train[cls(q)].append(float(r["answer"])*unit(q))
db.close()
med = {c:st.median(v) for c,v in train.items()}
def quant(v,p):
    v=sorted(v); k=(len(v)-1)*p; j=int(k)
    return v[j]+(k-j)*(v[min(j+1,len(v)-1)]-v[j])
spread = {c:(min(v),max(v),*[quant(v,p) for p in (.25,.5,.75)])
          for c,v in train.items()}
print("sample rows/classes", sum(map(len,train.values())), len(train))
for se in ("dev-S1", "R0-dev"):
    new = K.direct("R1",200,se,types=["object_size_estimation"])
    old = {r["id"]:r for r in K.direct("S1",544,se,types=["object_size_estimation"])}
    rr = [(cls(r["question"]), float(r["gt"])*unit(r["question"]),
           float(old[r["id"]]["pred"])*unit(r["question"]),
           float(r["pred"])*unit(r["question"])) for r in new]
    for label, sub in (("all",rr), ("seen",[r for r in rr if r[0] in med]),
          ("ge5",[r for r in rr if len(train.get(r[0],[]))>=5]),
          ("unseen",[r for r in rr if r[0] not in med])):
        prior = (100*st.mean(mra(med[c],g) for c,g,o,p in sub)
                 if label in ("seen","ge5") else None)
        print(se,label,len(sub),"MRA",prior,
              *[100*st.mean(mra(r[k],r[1]) for r in sub) for k in (2,3)])
        if label in ("seen","ge5"):
            for k in (2,3):
                print("correlations",k,corr([r[k] for r in sub],
                      [med[r[0]] for r in sub]),
                      corr([r[k]-med[r[0]] for r in sub],
                           [r[1]-med[r[0]] for r in sub]))
    if se == "R0-dev":
        small = [r for r in rr if r[1]<30]
        print("small n/MRA/min answer/below30 answers",len(small),
              100*st.mean(mra(r[3],r[1]) for r in small),
              min(r[3] for r in rr),sum(r[3]<30 for r in small))
```