**1. Question and answer**

1. **Which relation component fails?** At step 200, dev-S1 hard errors split into 11 left/right-only, 14 front/back-only and 1 both-axis error among 150 items. R0-dev toward splits into 25, 16 and 5 among 121 items; left/right is its largest component.
2. **Does the model favor particular relations or letters?** It overpredicts front quadrants: 121 of 150 dev-S1 answers versus 110 front truths, and 107 of 121 R0-dev answers versus 98 front truths. Truth-position A has the lowest hard accuracy in both sets at step 200, but these observations do not establish a causal letter bias.
3. **Do its stated angles explain the errors?** All 826 step-544 traces state an angle consistent with their answer. Of the 69 R0-dev items wrong at all three checkpoints, 40 lie within 25 degrees of an answer boundary by that angle; 29 do not.
4. **Is its layout consistent across questions?** Step 200 satisfies 255 of 263 testable dev-S1 side constraints and 11 of 14 R0-dev constraints, improving from 243 of 263 and 9 of 14. These are class-name consistency checks; repeated instances prevent treating them as definitive tests of one physical layout.
5. **Does instance multiplicity predict errors?** The counting join flags only 17 of 450 dev-S1 items, with accuracy falling from 12 of 17 to 11 of 17. It matches no object class on any of the 376 R0-dev items, so multiplicity there remains unmeasured.
6. **Where do errors concentrate?** Across all rooms, 5 of 43 dev-S1 rooms contain 30 of 54 errors; 22 of 97 R0-dev rooms contain 58 of 115. Only dev-S1 shows clear excess concentration under the random-allocation check; sampled vocabulary and timing do not identify a general explanation for R0-dev’s gap.
7. **What should vehicle N change?** Test balanced hard-quadrant rows, clearer medium rear-band rows, and instance-verified triangle counterparts. Their measured ceilings are small and overlap; no table establishes that changing wording alone will repair perception or spatial reasoning.

**2. Evidence**

All results use B2048 scores and toward items only. `S` means dev-S1; `R` means R0-dev. Overall accuracy is **397/450 versus 396/450** on S and **253/376 versus 261/376** on R, at steps 544 and 200 respectively.
Trace sources are those loaded by [san_kit.py](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py): under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/`, builds `a8102c3207b` (200), `a5d2d909067` (100), and `adff67f7ae9` (544), using the applicable `fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl` files. S at 544 uses `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
Training evidence comes from `STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json` under `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`, plus the named v7 index and SQLite store. Timing comes from `K.timing('R1',200,set)`. I used the assigned record lines 229–235 and the direction trace ruling.

**Prices.** A bracket `[T; B]` gives type points and benchmark-proxy points lost by that cell. Unpriced correct or zero-count cells cost zero. S type denominators are 150, with benchmark divisor 24. R type denominators include both facing subtypes: 192 easy/hard and 194 medium; ReVSI prices instead use toward leaf denominators 126 easy and 121 hard, then divide by 28. Medium has no ReVSI leaf.

| Hard set/step | Left/right only | Front/back only | Both |
|---|---:|---:|---:|
| S 544 | 9/150 [6.000; 0.250] | 11/150 [7.333; 0.306] | 4/150 [2.667; 0.111] |
| S 200 | 11/150 [7.333; 0.306] | 14/150 [9.333; 0.389] | 1/150 [0.667; 0.028] |
| R 544 | 21/121 [10.938; 0.620] | 17/121 [8.854; 0.502] | 5/121 [2.604; 0.148] |
| R 200 | 25/121 [13.021; 0.738] | 16/121 [8.333; 0.472] | 5/121 [2.604; 0.148] |

**Easy confusion.** Each truth column lists answers in **left, right** order.

| Set/step | Truth left: answers L, R | Truth right: answers L, R |
|---|---|---|
| S 544 | 73/81; 8/81 [5.333; 0.222] | 5/69 [3.333; 0.139]; 64/69 |
| S 200 | 75/81; 6/81 [4.000; 0.167] | 4/69 [2.667; 0.111]; 65/69 |
| R 544 | 54/72; 18/72 [9.375; 0.510] | 16/54 [8.333; 0.454]; 38/54 |
| R 200 | 56/72; 16/72 [8.333; 0.454] | 12/54 [6.250; 0.340]; 42/54 |

**Medium confusion.** Each truth column lists answers in **left, right, back** order.

| Set/step | Truth left: answers L, R, B | Truth right: answers L, R, B | Truth back: answers L, R, B |
|---|---|---|---|
| S 544 | 72/78; 5/78 [3.333; 0.139]; 1/78 [0.667; 0.028] | 3/63 [2.000; 0.083]; 60/63; 0/63 | 5/9 [3.333; 0.139]; 2/9 [1.333; 0.056]; 2/9 |
| S 200 | 71/78; 6/78 [4.000; 0.167]; 1/78 [0.667; 0.028] | 4/63 [2.667; 0.111]; 59/63; 0/63 | 4/9 [2.667; 0.111]; 3/9 [2.000; 0.083]; 2/9 |
| R 544 | 40/62; 21/62 [10.825; 0]; 1/62 [0.515; 0] | 12/50 [6.186; 0]; 38/50; 0/50 | 4/17 [2.062; 0]; 8/17 [4.124; 0]; 5/17 |
| R 200 | 40/62; 18/62 [9.278; 0]; 4/62 [2.062; 0] | 8/50 [4.124; 0]; 42/50; 0/50 | 5/17 [2.577; 0]; 6/17 [3.093; 0]; 6/17 |

**Relation shares.** Vector orders are L/R for easy, L/R/B for medium, and FL/FR/BL/BR for hard; each numerator has the displayed denominator.

| Set/level | Truth shares | Step-544 answer shares | Step-200 answer shares |
|---|---|---|---|
| S easy | 81/150, 69/150 | 78/150, 72/150 | 79/150, 71/150 |
| S medium | 78/150, 63/150, 9/150 | 80/150, 67/150, 3/150 | 79/150, 68/150, 3/150 |
| S hard | 57/150, 53/150, 23/150, 17/150 | 67/150, 54/150, 16/150, 13/150 | 62/150, 59/150, 14/150, 15/150 |
| R easy | 72/126, 54/126 | 70/126, 56/126 | 68/126, 58/126 |
| R medium | 62/129, 50/129, 17/129 | 56/129, 67/129, 6/129 | 53/129, 66/129, 10/129 |
| R hard | 44/121, 54/121, 12/121, 11/121 | 47/121, 49/121, 17/121, 8/121 | 56/121, 51/121, 8/121, 6/121 |

**Accuracy by truth letter.** Each cell gives **544; 200**.

| Set/level | A | B | C | D |
|---|---|---|---|---|
| S easy | 70/76; 71/76 | 67/74; 69/74 | — | — |
| S medium | 37/42; 38/42 | 40/45; 40/45 | 57/63; 54/63 | — |
| S hard | 28/36; 26/36 | 31/39; 31/39 | 37/41; 37/41 | 30/34; 30/34 |
| R easy | 44/59; 47/59 | 48/67; 51/67 | — | — |
| R medium | 28/42; 27/42 | 28/45; 32/45 | 27/42; 29/42 | — |
| R hard | 17/27; 14/27 | 21/36; 21/36 | 26/34; 23/34 | 14/24; 17/24 |

**Angle bins.** The forms are “lies 30 degrees left of straight ahead” and, for medium back, “lies 156 degrees from straight ahead.” Boundaries are 0/180 for easy, multiples of 90 for hard, and 0/±135 for medium; 180 is inside medium’s back region. Bins are `<10`, `[10,25]`, `(25,45]`, and `>45`. No angle falls in the first bin: 0/826.

| Set/level | 10–25° accuracy, 544; 200 | 25–45° accuracy, 544; 200 | Above 45° accuracy, 544; 200 | Step-200 relation agrees with old angle |
|---|---|---|---|---|
| S easy | 26/33; 29/33 | 47/48; 46/48 | 64/69; 65/69 | 143/150 |
| S medium | 28/35; 26/35 | 61/68; 61/68 | 45/47; 45/47 | 142/150 |
| S hard | 52/70; 49/70 | 74/80; 75/80 | 0/0; 0/0 | 138/150 |
| R easy | 18/30; 22/30 | 30/33; 30/33 | 44/63; 46/63 | 106/126 |
| R medium | 31/58; 31/58 | 33/46; 37/46 | 19/25; 20/25 | 106/129 |
| R hard | 44/76; 43/76 | 34/45; 32/45 | 0/0; 0/0 | 94/121 |

The persistent-error subset contains 17 easy, 24 medium and 28 hard items; respectively 5/17, 15/24 and 20/28 lie within 25 degrees. Its ceiling is **1.308 ReVSI points**, while all 115 toward errors cost **2.151**. The near-boundary step-200 errors cost **0.944 VSI points** on 34/450 S items and **1.201 ReVSI points** on 68/376 R items, including 27 unweighted medium errors. These are self-asserted angles, not measured geometric margins.

**Question parsing and consistency.** The question-only parser covers 450/450 S items across 74 paraphrase forms and 376/376 R items. Its patterns extract `A … facing/looking/oriented … B … C`, reverse the first two names for `Facing B from A` and `Looking at B from … A`, handle `With A next to me and B ahead`, and remove repeated B in `which side of B is C`. The appendix gives the exact parser.
Groups use room plus the unordered three class names: S has 86 repeated groups containing 236/450 items; R toward has 8 containing 19/376. Side checks use permutation parity, including cyclic equality and exchange reversal; medium back hides the side, so evaluable denominators vary.

| Constraint | Truths satisfy | Step 544 satisfies | Step 200 satisfies |
|---|---:|---:|---:|
| S side parity | 262/264 | 243/263 | 255/263 |
| R side parity | 14/14 | 9/14 | 11/14 |
| S front/back, same observer with faced/target exchanged | 11/11 | 10/11 | 10/11 |
| R front/back exchange | 0/0 | 0/0 | 0/0 |

On the fixed easy/hard side comparisons, S satisfies 110/118 at 544 and 114/118 at 200; R satisfies 5/8 and 7/8. S has only 54 groups with an easy/hard constraint, of which 47/54 and 50/54 satisfy every tested constraint; R has 4/6 and 5/6.
The truth violations are **`vsi590k_022853` / `vsi590k_035573`** and **`vsi590k_035564` / `vsi590k_035573`**, all in `d1/scene0250`, involving door, trash bin and towel. The latter pair has identical roles but opposite side truths. Counting gives two towels, and the clips differ in length; this is a label-or-instance ambiguity, not grounds to flip a label. Excluding multiplicity-flagged items leaves truth consistency **256/256**, versus model consistency **236/255** and **247/255**.

**Multiplicity.** I joined exact class names to single-class counting questions, excluding multi-class totals.

| Set/group | Step 544 accuracy | Step 200 accuracy |
|---|---:|---:|
| S: at least one class counted ≥2 | 12/17 | 11/17 |
| S: no such flag | 385/433 | 385/433 |
| R: at least one class counted ≥2 | 0/0 | 0/0 |
| R: no such flag | 253/376 | 261/376 |

S supplies 150/150 parsable counting questions; R supplies 287/385 single-class questions. Despite room overlap, R has 0 matching room/class operands. S flags the observer on 5/450 items, faced object on 5/450, and target on 7/450; these groups do not overlap. No item has all three classes counted. “No flag” therefore means unmeasured multiplicity, not confirmed uniqueness. The six flagged S errors split 1 easy, 1 medium and 4 hard, costing 0.667, 0.667 and 2.667 type points, or **0.167 VSI points** altogether.

**Timing.** Bands use within-set item tertiles, retaining ties. Length is `total_frames/fps`; spacing is `K.timing`’s mean sampled-frame interval.

| Set/band | Video length, seconds | Frame spacing, seconds | Accuracy 544; 200 |
|---|---|---|---|
| S short | ≤109.875 | ≤3.543011 | 140/154; 137/154 |
| S middle | (109.875,195.533333] | (3.543011,6.306989] | 148/160; 148/160 |
| S long | >195.533333 | >6.306989 | 109/136; 111/136 |
| R short | ≤120.466667 | ≤3.885484 | 87/127; 85/127 |
| R middle | (120.466667,177.466667] | (3.885484,5.724194] | 88/124; 94/124 |
| R long | >177.466667 | >5.724194 | 78/125; 82/125 |

Coverage is 450/450 and 376/376. Length and spacing produce identical memberships, so these data cannot separate their effects.

**Sampled training vocabulary.** The 360 family-sample rows supply 113 names; the primary-key sample supplies 408; their union contains 422. The latter uses seed 200 to select 2,000 direction keys below 105000 from the supplied index; all 2,000 fetched rows belong to `w1g`. This samples a prefix containing 49,857 candidate keys, rather than the complete 49,901-row family. Presence is established; absence from this sample is not absence from training.

| Set / number of names in sampled vocabulary | Accuracy 544 | Accuracy 200 |
|---|---:|---:|
| S / all three | 397/450 | 396/450 |
| R / zero | 12/19 | 13/19 |
| R / one | 58/84 | 55/84 |
| R / two | 102/157 | 110/157 |
| R / three | 81/116 | 83/116 |

For R, observer present/absent accuracy is **170/250 versus 83/126** at 544 and **178/250 versus 83/126** at 200. Faced-object values are **170/256 versus 83/120**, then **179/256 versus 82/120**; target values are **165/240 versus 88/136**, then **167/240 versus 94/136**. These comparisons do not support vocabulary-only repair.

**Rooms at step 200.** The binomial null uses each set’s overall error probability: 54/450 for S and 115/376 for R. Below, `E` is expected errors. Within rooms containing at least five items, **4/29 S rooms hold 26/50 errors**, and **8/35 R rooms hold 24/48**.

| S room: wrong/items; E | S room: wrong/items; E | S room: wrong/items; E |
|---|---|---|
| d2/ca3b651c23: 9/21; 2.52 | d3/venue472621: 7/11; 1.32 | d3/venue382318: 5/22; 2.64 |
| d2/d6bb698875: 5/22; 2.64 | d2/e35232b92f: 4/16; 1.92 | d1/scene0515: 3/47; 5.64 |
| d3/venue435364: 2/6; 0.72 | d3/venue381619: 2/10; 1.20 | d2/aaa9c251de: 2/21; 2.52 |
| d2/80ffca8a48: 2/5; 0.60 | d3/venue470341: 1/13; 1.56 | d3/venue423308: 1/16; 1.92 |
| d2/eb8ef9b4cc: 1/12; 1.44 | d2/e7ccd75e5d: 1/17; 2.04 | d2/e667e09fe6: 1/15; 1.80 |
| d2/ad562ce09b: 1/14; 1.68 | d2/307e3262f1: 1/18; 2.16 | d2/17c5e6a336: 1/13; 1.56 |
| d1/scene0666: 1/6; 0.72 | d3/venue472640: 0/6; 0.72 | d3/venue464761: 0/16; 1.92 |
| d3/venue437424: 0/6; 0.72 | d2/6a217fbcb0: 0/8; 0.96 | d2/3ce6d36ab5: 0/12; 1.44 |
| d2/37c9538a2b: 0/20; 2.40 | d2/260db9cf5a: 0/13; 1.56 | d1/scene0642: 0/9; 1.08 |
| d1/scene0380: 0/10; 1.20 | d1/scene0166: 0/8; 0.96 | — |

| R room prefixes sharing the same result | Wrong/items | Expected errors |
|---|---:|---:|
| 0e4aa362, 05fd7f36 | 4/5 each | 1.53 each |
| ee982791, 223194fe, 21c5ab83 | 3/5 each | 1.53 each |
| 912b8641 | 3/6 | 1.84 |
| fa846f02, f93c5312, f49f6bdd, e7af47df, e67eca1c, 7db2902f, 26920501 | 2/5 each | 1.53 each |
| 87244ee2 | 2/6 | 1.84 |
| ec3ea16c, e1053810, c06052db, be5826f0, acc12914, a37ec73a, 98497f7b, 8bfe0570, 86d95d2d, 7e2bfd33, 3282a94d | 1/5 each | 1.53 each |
| 0e69c591 | 1/6 | 1.84 |
| ebead2a0, d1d02a95, cd87d375, a6e58095, 71914937, 63236513, 5f5449c6 | 0/5 each | 1.53 each |
| 87e00c79, 2a6b8fc0 | 0/6 each | 1.84 |

Pearson dispersion is 80.48 across the 29 eligible S rooms and 44.32 across the 35 eligible R rooms. Uniformly reallocating each set’s observed error count to its items, with seed 200, exceeds those statistics on **0/5,000** and **519/5,000** trials. The null’s central 95% interval for rooms holding half of all errors is 6–10 for S and 21–26 for R, versus observed counts of 5 and 22. Repeated questions and unequal level mixtures limit this descriptive null.

**3. What this changes for vehicle N**

All row quantities below are **proposed trial sizes**, not measured optimal doses. Let `F(level)` denote `object_rel_direction_<level>|w1g|rows_rebuild_d0_v1`. Keep direct qualitative traces; add no unsupported angle measurements.
1. **Reword and balance 2,000 rows from F(hard), with 500 per quadrant.** This is the strongest targeted hypothesis: select verified instances and state front/back separately from left/right. The front/back-only ceiling is 14/150 S items, **9.333 type / 0.389 VSI points**, and 16/121 R items, **8.333 type / 0.472 ReVSI points**. Illustrative wording: “Seen: the desk beside the window in frame {a}; the chair in frame {b}; the lamp in frame {c}. I stand at that desk and face that chair. The lamp is behind me. It is to my left. I keep this heading. The lamp is back-left.” Fill frames and distinguishing details only from verified training evidence. **Gate:** front/back-only loss must fall without increasing side-only loss; compare against the same balanced rows with the existing wording.
2. **Reword and rebalance 2,000 rows from F(medium): 1,000 back, 500 left, 500 right.** State the question’s rear band explicitly after localization. The ceiling is the 8/150 S and 15/129 R back-versus-side errors: **5.333 and 7.732 type points**, **0.222 VSI points**, and **zero ReVSI points**. **Gate:** improve back recall from 2/9 and 6/17 without increasing false-back answers from 1/141 and 4/112. This tests a rear-band hypothesis; it does not assume the underlying visual relation is already correct.
3. **Add 2,700 instance-verified counterpart rows from the three F families: 900 per level.** Use 300 training triangles, with `(A,B,C)`, `(A,C,B)` and `(B,C,A)` at each level, and independently derived labels. Current truth-consistent constraint violations touch six wrong S items—one easy, one medium, four hard—and three wrong R easy items. Their ceilings are **0.167 VSI** and **0.085 ReVSI points**; type costs are **0.667/0.667/2.667** on S and **1.563 easy points** on R. **Gate:** improve the fixed eligible constraints and individual accuracy; turning a medium answer into an untestable back answer must not count as a consistency gain.
These ceilings overlap and are not additive forecasts. The tables support **no vocabulary-only or letter-only row change**. Direction runaways account for **0/826 items and zero points**, so a token-budget repair has no measured opportunity here.

**4. Refuted**

No verified first-wave count was contradicted. Two scope distinctions matter: R0-dev has **18 repeated groups when toward and away are combined, but only 8 toward groups**; and the **2.151-point** ceiling belongs to all toward errors, while the **69 persistent errors cost 1.308 points**. The new truth conflicts establish a class-instance ambiguity that the first-wave checks did not test.

**5. Not established**

These tables cannot distinguish missed objects, wrong instance selection, incorrect room layout, or incorrect geometric reasoning. Resolve that distinction with instance identities and verified frame evidence on the persistent errors and conflicting triple. An option-order shuffle would test letter causality; measured bearings would test real boundary proximity. The proposed row changes remain hypotheses until a matched training ablation improves the next read.

**Appendix — CLASSIFIER**

```python
import sys, re, itertools
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
types = ['object_rel_direction_' + x for x in ('easy', 'medium', 'hard')]
def rows(run, step, dataset):
    return [r for r in K.direct(run, step, dataset, types=types)
            if dataset == 'dev-S1' or r['subtype'] == 'toward']
def relation(r, key='pred'):
    return next(o[3:].strip().lower() for o in r['options'] if o[0] == r[key])
def names(q):
    q = re.sub(r'\bthe (?:place of|standpoint of|viewpoint at|point of|location of|spot of|position of|perspective of standing at) the ', 'the ', q, flags=re.I)
    q = re.sub(r'which side of the .*? is the ', 'is the ', q, flags=re.I)
    end = r',|;|\.|\?|:|—| and | looking | facing | oriented | next to me| ahead\b| as my location| from | while | is | would | be | situated | located | found | placed | positioned | appear\b| sit | lies?\b| to | on\b| in\b| at | relative | front-| back-| behind\b'
    ns = tuple(re.split(end, x, flags=re.I)[0].strip().lower()
               for x in re.split(r'\bthe ', q, flags=re.I)[1:4])
    return (ns[1], ns[0], ns[2]) if re.match(r'^(Facing|Looking at) ', q, re.I) else ns
def parity(ns):
    return sum(ns[i] > ns[j] for i in range(3) for j in range(i+1, 3)) % 2
def angle(r):
    m = re.search(r'lies\s+(\d+(?:\.\d+)?)\s+degrees(?:(?:\s+(left|right)\s+of)|(?:\s+from)) straight ahead', r['text'], re.I)
    return float(m[1]) * (-1 if m[2] == 'right' else 1)
def margin(r):
    level = r['type'].split('_')[-1]
    boundaries = {'easy': [0, 180], 'medium': [0, 135, -135],
                  'hard': [0, 90, -90, 180]}[level]
    return min(abs((angle(r)-b+180) % 360-180) for b in boundaries)
for dataset in ('dev-S1', 'R0-dev'):
    old, new = rows('S1', 544, dataset), rows('R1', 200, dataset)
    for step, rs in ((544, old), (200, new)):
        bits = Counter()
        for r in rs:
            if not r['type'].endswith('hard') or r['score']:
                continue
            truth, pred = relation(r, 'gt').split('-'), relation(r).split('-')
            lr, fb = truth[1] != pred[1], truth[0] != pred[0]
            bits['both' if lr and fb else 'LR' if lr else 'FB'] += 1
        print(dataset, step, 'hard wrong components', dict(bits))
    groups = defaultdict(list)
    for r in new:
        groups[r['room'], tuple(sorted(names(r['question'])))].append(r)
    groups = {g: rs for g, rs in groups.items() if len(rs) > 1}
    pairs = [p for rs in groups.values() for p in itertools.combinations(rs, 2)]
    print(dataset, 'repeated triples', len(groups), 'pairs', len(pairs))
    for key, rs in (('gt', new), ('pred', old), ('pred', new)):
        lookup = {r['id']: r for r in rs}
        good = total = 0
        for x, y in pairs:
            rx, ry = relation(lookup[x['id']], key), relation(lookup[y['id']], key)
            if 'back' in (rx, ry):
                continue
            equal = parity(names(x['question'])) == parity(names(y['question']))
            ok = (rx.split('-')[-1] == ry.split('-')[-1]) == equal
            total += 1
            good += ok
            if key == 'gt' and not ok:
                print('truth conflict', x['id'], y['id'])
        print(dataset, key, rs[0]['step'], 'LR consistent', good, 'of', total)
    if dataset == 'R0-dev':
        middle = {r['id']: r for r in rows('R1', 100, dataset)}
        sticky = [(o, n) for o, n in K.paired(old, new)
                  if not o['score'] and not n['score'] and not middle[n['id']]['score']]
        print('always wrong', len(sticky), 'within25', sum(margin(o) <= 25 for o, n in sticky),
              'same wrong relation', sum(relation(o) == relation(n) for o, n in sticky))
```