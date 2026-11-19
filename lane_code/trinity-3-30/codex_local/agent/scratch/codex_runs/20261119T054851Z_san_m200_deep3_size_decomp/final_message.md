## Question and answer

1. **How much size loss comes from class calibration versus instance variation?** On classes with at least three items, oracle calibration raises MRA by 7.58 points on dev-S1 (120 of 150 items) and 10.21 on R0-dev (97 of 293). Replacing each prediction with the model’s class median changes MRA by only +0.50 and −0.62, respectively; instance variation contributes little net accuracy under this test.
2. **Are errors stable across checkpoints?** Errors retain the same nonzero sign on 109 of 150 dev-S1 items and 237 of 293 R0-dev items. The three-answer geometric mean scores 70.20 and 60.55 MRA; it slightly beats every dev-S1 checkpoint but loses to step 100 on R0-dev.
3. **How much do units and alternative truths matter?** An explicitly defined unit-swap heuristic flags 6 of 150 old answers and 2 of 150 current answers, but neither current flag proves a conversion error. The two truths differ on 78 of 150 dev-S1 items; step 200 scores 69.27 against `gt` and 69.53 against `gt_released`.
4. **Does relative size follow its trace and agree with absolute size?** Answers follow the trace’s stated selection on 138 of 138 determinate traces; 12 of 150 traces supply no conclusion. All 27 numeric traces follow their stated ratio, but only 20 of 27 matched numeric-trace/absolute-answer pairs agree within a factor of 1.25.
5. **Does the deployed box head add useful size information?** Across the reconstructed 58 pairs, its log-error correlation with direct answers is 0.283; unconditional geometric fusion and the requested agreement switch both lose. An exploratory agreement-gated geometric mean gains only 0.033 VSI proxy points.
6. **Are small objects missed by more centimetres or mainly by ratio?** Small objects score 76.25 MRA on dev-S1 (8 of 150 items) and 47.95 on R0-dev (88 of 293), despite smaller absolute errors than larger objects. Training contains 497 of 3,000 sampled answers under 30 cm, below R0-dev’s proportion.
7. **What should vehicle N change?** Prioritize small-instance contrasts, dedicated size-order rows, and repeated-class calibration examples. Unit augmentation has a smaller demonstrated ceiling, and the box head does not justify broad replacement of direct size answers.

## Evidence

**Scoring convention.** Counterfactual comparisons below use centimetres and the specified MRA thresholds, with a `1e-12` boundary tolerance. Stored scores differ slightly: step 200 is 69.40 on dev-S1 and 58.29 on R0-dev, versus recomputed 69.27 and 58.46. **Every loss price uses stored `score`**, as requested; prices overlap and must not be added across diagnostic partitions.

**Files.** Direct results come through `san_kit.py` from `cont_ops16/work/c15/h1read/kit/build/{a8102c3207b,a5d2d909067,adff67f7ae9}/fetched/x/{main,a7}/a0/results/`, under `/scratch/jjyeung/orch_n30/`; these supply step 200, step 100, and the available step-544 returns. Step-544 dev-S1 comes from `evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl` under the same root.
Training counts come from the named `FAMILY_INDEX_RANGES.json`, `rows.sqlite`, and `STORE_V7_TEMPLATE_COUNTS.json`. I read the coordinator’s lines 237–240 once and the named first-wave size report. The box analysis uses `SIZE_BOXHEAD_JOIN.json`, its adjacent join script, and `K.routed(200, types=['object_abs_distance'])`; nothing was changed.

**Class decomposition.** Classes use normalized object names from questions. Calibration fits one positive multiplier per class on these same dev items; this is an oracle, not a deployable estimate. The model median includes the evaluated prediction; the truth median excludes the evaluated item.

| Set and cohort | Items | (a) Model | (b) Oracle class scale | (c) Leave-one-out truth median | (d) Model class median |
|---|---:|---:|---:|---:|---:|
| dev-S1, all | 150 of 150 | 69.27 | 79.93 | Undefined for 12 singletons | 69.27 |
| dev-S1, leave-one-out available | 138 of 150 | 68.55 | 78.19 | 71.30 | 68.55 |
| dev-S1, classes with ≥3 items | 120 of 150 | 70.08 | 77.67 | 72.58 | 70.58 |
| R0-dev, all | 293 of 293 | 58.46 | 87.34 | Undefined for 132 singletons | 57.24 |
| R0-dev, leave-one-out available | 161 of 293 | 60.62 | 76.96 | 55.59 | 58.39 |
| R0-dev, classes with ≥3 items | 97 of 293 | 63.51 | 73.71 | 62.16 | 62.89 |

- **(a)−(d):** Instance-varying answers gain 0.00/1.23 MRA on all dev-S1/R0-dev items, and −0.50/+0.62 on their respective ≥3-item cohorts.
- **(b)−(a):** Oracle scales recover 10.67/28.87 MRA on all items, but singleton fitting inflates those gains; the ≥3-item gains are 7.58/10.21.
- **(c)−(a):** The leave-one-out truth median gains 2.75 MRA on 138 dev-S1 items but loses 5.03 on 161 R0-dev items; on ≥3-item classes, the changes are +2.50/−1.34.

On the ≥3-item cohorts, the remaining MRA loss after calibration is 22.33 for dev-S1 and 26.29 for R0-dev. This is **loss that class scaling cannot remove**, not a proven measure of instance-perception error. An all-item leave-one-out class median cannot be defined without inventing a fallback for singleton classes.

**Checkpoint stability.** Correlations use signed natural-log prediction/truth errors.

| Set | Same nonzero sign | Exact at all three | Correlation: 544–100 / 544–200 / 100–200 | MRA: 544 / 100 / 200 | Geometric-mean MRA |
|---|---:|---:|---|---|---:|
| dev-S1 | 109 of 150 | 1 of 150 | 0.350 / 0.282 / 0.656 | 68.80 / 68.93 / 69.27; n=150 | 70.20; n=150 |
| R0-dev | 237 of 293 | 5 of 293 | 0.910 / 0.886 / 0.929 | 59.18 / 61.02 / 58.46; n=293 | 60.55; n=293 |

The known step-544 printer answer, 41 when metres were requested, strongly affects dev-S1 correlations. Excluding that one item raises 544–100 and 544–200 correlations to 0.613 and 0.528 on 149 items.

**Units.** The diagnostic flags an answer when its native prediction/truth ratio lies outside `[1/3, 3]`, but exactly one interpretation in another unit places it within `[2/3, 1.5]`. This uses truth and identifies **unit-like errors**, not confirmed conversion mistakes.

| Requested unit | Items | Stored MRA 544 / 200 | Recomputed MRA 544 / 200 | Flags 544 / 200 | MRA after flagged conversions 544 / 200 |
|---|---:|---|---|---|---|
| Centimetres | 38 of 150 | 72.63 / 73.16 | 72.11 / 73.16 | 1 / 1 of 38 | 73.16 / 74.74 |
| Inches | 47 of 150 | 68.51 / 61.49 | 68.30 / 60.64 | 0 / 0 of 47 | 68.30 / 60.64 |
| Feet | 31 of 150 | 60.32 / 71.29 | 60.97 / 71.94 | 4 / 0 of 31 | 72.90 / 71.94 |
| Metres | 34 of 150 | 72.35 / 74.41 | 72.94 / 74.41 | 1 / 1 of 34 | 74.12 / 77.06 |

Only 1 of 6 old flags explicitly prints a different unit: the printer says “41 cm” and answers 41 to a metre question. The two current flags are the heater, 66 cm versus 222.1 cm, and ceiling light, 1.22 m versus 0.4 m; both print the requested unit and could instead be instance-scale errors.
Converting the current flags raises recomputed MRA from 69.27 to 70.27 on 150 items. Their stored loss ceiling is **1.33 type / 0.167 VSI points**; the conversion recovers 0.125 VSI proxy points. The six old flags carry 4.00 type / 0.500 VSI points.
A separate training-median screen, requiring at least three sampled training examples per class, flags **0 of 48 supported current dev-S1 items**. The current unit diagnosis is therefore weak.
The two truths differ on **78 of 150** items. Recomputed step-200 MRA is **69.27 against `gt` and 69.53 against `gt_released`**, compared with stored 69.40; 11 of 150 stored scores differ from the former computation and 2 of 150 from the latter. R0-dev has 5 of 293 threshold-boundary discrepancies under the tolerant computation.

**Relative-size trace forms and prices.**

| Trace form | Items | Correct answers | Loss: type / requested VSI proxy |
|---|---:|---:|---:|
| Two stated sizes | 27 of 150 | 27 of 27 | 0 / 0 |
| Explicit size ordering | 56 of 150 | 54 of 56 | 1.33 / 0.167 |
| Qualitative size comparison | 52 of 150 | 42 of 52 | 6.67 / 0.833 |
| Distance-template contamination | 3 of 150 | 2 of 3 | 0.67 / 0.083 |
| Instruction to compare, without conclusion | 12 of 150 | 10 of 12 | 1.33 / 0.167 |
| **Total** | **150 of 150** | **135 of 150** | **10.00 / 1.250** |

All 27 numeric traces select the answer implied by their stated sizes. Their absolute-size joins yield **27 response pairs across 16 relative questions and 17 room/object names**: median stated/direct ratio **1.00**, with **20 of 27** within a factor of 1.25 and **22 of 27** within 1.5.
Some room/object names have multiple absolute-size questions. Taking their median first gives **20 comparisons**, median ratio **0.989**, with **15 of 20** within 1.25; thus the agreement is substantial but not universal.
Both true sizes are available through absolute-size joins for **14 of 150 relative questions**. All 14 answers match the true ordering across all 23 possible truth-pair combinations; four also have numeric traces. Another 23 questions can be checked only against their stated ratio, and all 23 follow it.
A concrete inconsistency is the refrigerator in `d3/venue472621`: two relative traces state 104 cm and 185 cm, while the median absolute answer is 173.52 cm. Both relative answers are correct, so this inconsistency has **zero observed relative-size loss**.

**Box head.** The supplied JSON contains aggregates, not item pairs. Reconstructing its join reproduces **58 items, 50.69 head MRA and 73.62 stored direct MRA**; recomputed direct MRA is 73.10. Log-error correlation is **0.283 on 58 pairs**.

| Truth band/cohort | Items | Direct MRA | Head MRA | Geometric mean | Head if within 1.5×, else direct | Stored loss: type / VSI |
|---|---:|---:|---:|---:|---:|---:|
| All joined | 58 of 150 | 73.10 | 50.69 | 61.90 | 68.10 | 10.20 / 1.275 |
| Under 50 cm | 6 of 58 | 55.00 | 55.00 | 45.00 | 45.00 | 1.87 / 0.233 |
| 50–150 cm | 33 of 58 | 75.45 | 59.39 | 67.88 | 73.64 | 5.27 / 0.658 |
| Above 150 cm | 19 of 58 | 74.74 | 34.21 | 56.84 | 65.79 | 3.07 / 0.383 |
| Predictions agree within 1.5× | 39 of 58 | 76.67 | 69.23 | 77.69 | 69.23 | 6.00 / 0.750 |

No truth band favors the raw head. **Exploratory:** geometric fusion only on the 39 agreeing pairs, otherwise direct, scores **73.79 on 58 items**, improving 14 and worsening 13; its net gain is **0.033 VSI proxy points**.
The head individually beats direct on **14 of 58** items. Perfect hindsight selection reaches **80.52 MRA**, a **0.358 VSI-point gain**; those 14 items carry **4.87 type / 0.608 VSI points** of current loss. Neither hindsight nor the exploratory gate establishes a transferable selector.

**Small objects and absolute errors.** Scores and prices here use stored scores; absolute errors use `gt` converted to centimetres.

| Set / truth band | Items | Items below full credit | MRA | Median absolute error | Loss: type / benchmark |
|---|---:|---:|---:|---:|---:|
| dev-S1, <30 cm | 8 of 150 | 5 of 8 | 76.25 | 1.77 cm | 1.27 / 0.158 |
| dev-S1, 30–100 cm | 65 of 150 | 46 of 65 | 67.54 | 7.93 cm | 14.07 / 1.758 |
| dev-S1, >100 cm | 77 of 150 | 54 of 77 | 70.26 | 20.20 cm | 15.27 / 1.908 |
| R0-dev, <30 cm | 88 of 293 | 75 of 88 | 47.95 | 5.50 cm | 15.63 / 2.233 |
| R0-dev, 30–100 cm | 117 of 293 | 91 of 117 | 63.16 | 7.00 cm | 14.71 / 2.101 |
| R0-dev, >100 cm | 88 of 293 | 63 of 88 | 62.16 | 38.00 cm | 11.37 / 1.624 |

A seed-9 sample of **3,000 of 9,778 size-family primary keys** contains **497 of 3,000 answers under 30 cm (16.57%)**, versus **8 of 150 dev-S1 items (5.33%)** and **88 of 293 R0-dev items (30.03%)**. All 3,000 sampled training questions request centimetres. Small-object undercoverage is therefore supported for R0-dev, not dev-S1.

## What this changes for vehicle N

All proposed row budgets and causal benefits below are **guesses**. Use training scenes and verified annotations; do not manufacture reference objects or endpoints. Existing size family: `object_size_estimation|r1g|rows_rebuild_d0_v1`, with **9,778 of 9,778 rows kept**.

1. **Add 2,000 small-instance contrast rows** in proposed family `object_size_estimation|vehicleN_small|instance_scale_v1`. Target the **75 of 293 R0-dev** and **5 of 150 dev-S1** small-object failures; ceilings are **2.233 ReVSI / 0.158 VSI points**. Example template: “The [object] is visible in frame [verified frame]. Its longest axis runs from [endpoint] to [endpoint]. Compared with [verified reference] at similar depth, it is [relation]. Answer in centimeters.” **Gate:** small-object MRA must improve from 47.95 on R0-dev without worsening larger-object accuracy; unchanged errors would refute the proposed benefit.
2. **Add 1,500 dedicated comparison rows** in proposed family `relative_size_object|vehicleN_size_pairs|direct_size_order`, balanced between shorter and longer questions. Target **15 of 150 failures**, ceiling **10.00 type / 1.250 VSI proxy points**; the supplied inventory has no dedicated relative-size family. Example: “Order the objects by their longest dimension: bucket, then trash can. The question asks for the longer: trash can.” **Gate:** eliminate the 12 unfinished comparisons and three distance-template intrusions while improving the 13 wrong explicit selections; cleaner wording alone is insufficient.
3. **Reword 1,000 existing size rows as same-class contrasts**, with varied true lengths and verified longest-axis evidence. The oracle improves **47 of 120 dev-S1** and **38 of 97 R0-dev** supported-class items, while worsening 21 and 12; its net ceilings are **0.758 VSI / 0.483 ReVSI points**. The whole cohorts carry **23.80 type / 2.975 VSI** and **12.08 type / 1.726 ReVSI** points of current loss. Example: “Use the visible endpoints of this cabinet’s longest axis. Compare this instance with [verified reference], then answer in centimeters.” **Gate:** the repeated-class calibration gap must shrink without losing within-class accuracy; evaluate held-out rooms.
4. **Add 400 paired unit variants**, 100 per requested unit, in proposed family `object_size_estimation|vehicleN_units|direct_unit_v1`. The current evidence targets only **2 of 150 suspected errors**, ceiling **1.33 type / 0.167 VSI points**, with no confirmed conversion failure. Example: “The requested unit is feet. Estimate the longest dimension and express the final answer in feet.” **Gate:** the same training-derived instance must yield equivalent physical lengths across all four units; new inconsistent answers would reject the change.
5. **Replace first-seen boilerplate across the 9,778 existing size rows with one bounded localization clause.** This targets the single R0-dev runaway, **1 of 293**, priced at **0.341 type / 0.049 ReVSI points**; its overlap with the small-object cohort must not be counted twice. Example: “The keyboard is visible in frame [verified frame]. Estimate its longest dimension in centimeters.” **Gate:** zero size runaways at the next read; the causal connection remains a guess.

**Box supervision:** propose **zero additional head-based size rows** until a held-out-room selector beats direct. The observed hindsight gain is only **0.358 VSI points**, and the tested deployable head-switch rule loses; the exploratory geometric gate’s **0.033-point** gain is too weak to establish a training benefit.

## Refuted

- **“The answer follows the trace on every relative-size item” is too strong:** 12 of 150 traces provide no selection. Consistency is established for the other 138.
- **A single class prior explains all size behavior:** replacing answers with the model median loses only 1.23 MRA on all 293 R0-dev items, but the leave-one-out truth median loses 5.03 on the 161 eligible items; neither result supports a universal perfect-prior account.
- **Small-object failures mean larger centimetre errors:** R0-dev median errors are 5.50 cm below 30 cm versus 38.00 cm above 100 cm.
- **The supplied `gt` exactly reproduces stored scores:** it does not under the stated tolerant MRA calculation. This is a reproducibility discrepancy, not proof of which scorer input or numerical convention caused it.

## Not established

These interventions do not identify how much visual information the model uses: oracle calibration fits dev truths, medians optimize neither MRA nor instance identification, and item-level leave-one-out can retain another question about the same room/object. Held-out-room calibration and controlled training ablations would settle transfer.
Name-based joins do not prove that two questions refer to the same physical instance. Instance annotations would settle that ambiguity; scorer code would settle the truth/boundary discrepancies. The two current unit flags require visual scale evidence before being called conversion failures.

## Appendix: CLASSIFIER

Run with `/usr/bin/python3`. This reproduces the decomposition, stability, small-object scores, and training proportion.

```python
import sys, re, math, json, sqlite3, random, statistics as S
from collections import defaultdict
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
def cls(q):
    q = q.lower().strip().replace('’', "'")
    if q.startswith('measure the '): return q[12:].split(' along its ')[0]
    return re.split(r",|\?| in |'s| is | measures | measured| using ",
                    re.split(r'(?:of|for) the ', q)[-1])[0].strip()
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 1.
    if 'inch' in q: return 2.54
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 30.48
    return 100.
def mra(p, g):
    return sum(abs(p-g)/g <= 1-t/100+1e-12 for t in range(50,100,5))/10
def corr(x,y):
    a,b = S.mean(x),S.mean(y)
    return sum((u-a)*(v-b) for u,v in zip(x,y))/math.sqrt(
        sum((u-a)**2 for u in x)*sum((v-b)**2 for v in y))
for se in ['dev-S1','R0-dev']:
    runs = [K.direct(r,n,se,types=['object_size_estimation'])
            for r,n in [('S1',544),('R1',100),('R1',200)]]
    rows=runs[2]; groups=defaultdict(list); maps=[{x['id']:x for x in r} for r in runs]
    for x in rows:
        x['p']=float(x['pred'])*unit(x['question'])
        x['g']=float(x['gt'])*unit(x['question'])
        groups[cls(x['question'])].append(x)
    for v in groups.values():
        e=sorted({x['g']/x['p']*(1+s*(1-t/100))
                  for x in v for s in [-1,1] for t in range(50,100,5)})
        fs=[1.]+e+[(a+b)/2 for a,b in zip(e,e[1:])]
        f=max(fs,key=lambda f:sum(mra(x['p']*f,x['g']) for x in v))
        for x in v:
            other=[y['g'] for y in v if y['id']!=x['id']]
            x['abcd']=[mra(x['p'],x['g']),mra(x['p']*f,x['g']),
                       mra(S.median(other),x['g']) if other else None,
                       mra(S.median(y['p'] for y in v),x['g'])]
    for label,rr in [('all',rows),('LOO',[x for x in rows if x['abcd'][2]!=None]),
                     ('ge3',[x for v in groups.values() if len(v)>=3 for x in v])]:
        print(se,label,'n',len(rr),'a,b,c,d',[
            (sum(x['abcd'][j]!=None for x in rr),
             round(100*S.mean(x['abcd'][j] for x in rr if x['abcd'][j]!=None),3))
            for j in range(4)])
    es=[[math.log(float(m[x['id']]['pred'])/float(x['gt'])) for x in rows] for m in maps]
    strict=sum(all(z>0 for z in t) or all(z<0 for z in t) for t in zip(*es))
    print(se,'sign',strict,len(rows),'correlations',[corr(es[a],es[b])
          for a,b in [(0,1),(0,2),(1,2)]],'geomean MRA',
          100*S.mean(mra(math.exp(S.mean(t)),1.) for t in zip(*es)))
    sm=[x for x in rows if x['g']<30]
    print(se,'small',len(sm),len(rows),'stored MRA',100*S.mean(x['score'] for x in sm))
p='/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
ranges=json.load(open(p+'/FAMILY_INDEX_RANGES.json'))['families']['object_size_estimation']
keys=[i for a,b in ranges for i in range(a,b+1)]
ids=sorted(random.Random(9).sample(keys,3000)); small=n=0
db=sqlite3.connect('file:'+p+'/vqa/rows.sqlite?mode=ro',uri=True)
for start in range(0,3000,200):
    batch=ids[start:start+200]
    for i,raw in db.execute('select i,row from rows where i in ('+
                           ','.join('?'*len(batch))+')',batch):
        r=json.loads(raw); n+=1
        small+=float(r['answer'])*unit(r['student_input']['question'])<30
db.close()
print('training under 30 cm',small,'of',n)
```