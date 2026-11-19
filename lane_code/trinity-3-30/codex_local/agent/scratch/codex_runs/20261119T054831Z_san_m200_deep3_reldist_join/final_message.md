**Question and answer**

1. **Does instance multiplicity explain the errors?** The counting join does not establish that. Step 200 answers correctly on 78 of 102 flagged dev-S1 items versus 32 of 48 unflagged items; R0-dev supplies confirmed per-class multiplicity for only 3 of 279 items.
2. **Do absolute-distance measurements separate the truth from the model’s pick?** The join reaches 49 of 150 dev-S1 items, but only 6 have measurements for two candidates. None of the wrong items has measurements for both its truth candidate and its pick; R0-dev has 0 of 279 room-and-pair matches.
3. **Are errors concentrated at small stated margins?** Step 544 supplies four numeric distances on 429 of 429 traces. Its margin is below 25% on 53 of the 131 step-200 errors; on 33 of the 62 adjacent-rank errors, its numbers also put the truth second from the requested endpoint.
4. **Do three checkpoints improve the answer?** Majority voting answers 109 of 150 dev-S1 and 191 of 279 R0-dev items correctly, versus step 200’s 110 of 150 and 188 of 279. All three choose one common wrong option on 58 of 429 items.
5. **Are room-level orders consistent?** Shared-candidate orders agree on 65 of 69 eligible dev-S1 pairs and 1 of 1 R0-dev pair. No truth constraints conflict; reciprocal-reference pairs provide a weak test because each pair shares only one symmetric distance.
6. **Is the distance head precise enough?** Its printed gap lies within 25% of truth on 58 of 85 numeric responses. Under the independence assumptions below, it would order the endpoint pair correctly on an estimated 80.2% of 349 evaluable items; this is neither measured relative-distance accuracy nor a routing gain.
7. **What should vehicle N change?** Prioritize source-supported comparisons between endpoint candidates. Treat instance handling as a gated subset, and require direct comparative evidence before increasing routed relative-distance training.

**Evidence**

All scores below use B2048. These are dev-set proxies, not official benchmark results.

Files: direct traces came through `san_kit` from `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/{a8102c3207b,a5d2d909067,adff67f7ae9}/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`; step-544 dev-S1 came from `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.

Routed traces came through `K.routed` from the journals beneath `cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/` and `r1route/out3s/bases/b1/work/ret/metadata/reads/`. Training evidence came from `dist_diag/work/q2/STORE_V7_{SAMPLES20,TEMPLATE_COUNTS}.json`. I read the coordinator’s assigned lines 242–246 once.

**1. Multiplicity**

I matched lower-cased, singularized class names within each room. “Several” requires a per-class count of at least two, either directly recorded or obtained by subtracting a known class count from a two-class total. An unmatched class remains unknown.

| Flag defining the item group | dev-S1: correct 544 → 200 | R0-dev: correct 544 → 200 |
|---|---:|---:|
| No confirmed several-class among reference or candidates | 33 of 48 → 32 of 48 | 179 of 276 → 186 of 276 |
| Reference counted as several | 1 of 1 → 1 of 1 | 0 of 0 → 0 of 0 |
| Truth candidate counted as several | 34 of 49 → 37 of 49 | 0 of 0 → 0 of 0 |
| Step-200 pick counted as several | 32 of 45 → 37 of 45 | 0 of 0 → 0 of 0 |
| Another candidate counted as several | 59 of 82 → 65 of 82 | 2 of 3 → 2 of 3 |
| Any reference/candidate counted as several | 73 of 102 → 78 of 102 | 2 of 3 → 2 of 3 |

These groups overlap. “Another candidate” excludes both the truth and step-200 pick. Using each checkpoint’s own pick gives 34 of 49 at step 544 and 37 of 45 at step 200 on dev-S1.

The counting inputs contain 150 of 150 single-category dev-S1 questions, and 287 single-category plus 98 multiple-category questions among 385 R0-dev questions. Subtraction resolves 15 additional R0-dev room–class counts; 81 of 98 multiple-category questions still contain unresolved classes.

A permissive flag—**mentioned in a counting question whose total is at least two**—produces a much larger R0-dev table, but does not certify multiplicity:

| Permissive R0-dev flag | Correct 544 → 200 |
|---|---:|
| No flagged class | 115 of 182 → 122 of 182 |
| Reference flagged | 12 of 16 → 10 of 16 |
| Truth candidate flagged | 27 of 35 → 28 of 35 |
| Step-200 pick flagged | 26 of 37 → 28 of 37 |
| Another candidate flagged | 34 of 49 → 35 of 49 |
| Any class flagged | 66 of 97 → 66 of 97 |

Coverage is the principal limitation. Counting questions mention only 159 of 750 dev-S1 reference/candidate occurrences and 111 of 1,395 R0-dev occurrences. No item has all five roles covered: 0 of 150 and 0 of 279.

The unmatched-name sets are exhaustively characterized as follows: dev-S1 has unmatched occurrences for 55 of its 56 normalized names—all except **kettle**. R0-dev has unmatched occurrences for 410 of 422 names—all except **3d printer, air vent, flip chart, hanger, post it note, rug, sill, standing lamp, tea set, toilet brush holder, tray, window sill**. The classifier prints both literal lists. I did not merge synonyms or correct spelling.

Counts disagree numerically on 12 of 114 repeated dev-S1 room–class keys, although every value remains at least two. Thus these flags establish room-level multiplicity, not which instances appear in the relative-distance clip.

**2. Measured-distance join**

I normalized room prefixes (`d1/scannet`, `d2/scannetpp`, `d3/arkitscenes`), matched unordered class pairs, and converted truth values to metres. Seven duplicated absolute-distance pairs have differing numeric truths; none supplies the two-candidate rows below.

The join covers 55 of 600 dev-S1 reference–candidate relationships. Each table row represents one relative-distance item; head choices are restricted to the two measured candidates.

| Relative item | Measured candidates and truth distances, metres | Smaller true distance | Head 544 chooses | Head 200 chooses | Truth/pick distance ratio |
|---|---|---|---|---|---|
| `vsi590k_207581` | bed 1.560; table 0.710 | table | bed | unavailable | unavailable |
| `vsi590k_210374` | bed 1.548; bookshelf 3.542 | bed | bed | bed | unavailable |
| `vsi590k_282389` | refrigerator 1.830; tv 5.431 | refrigerator | refrigerator | refrigerator | unavailable |
| `vsi590k_283002` | dishwasher 0.942; tv 3.958 | dishwasher | dishwasher | unavailable | unavailable |
| `vsi590k_284005` | table 2.629; chair 3.730 | table | table | unavailable | 1.000; truth and pick are table |
| `vsi590k_287191` | stool 4.176; tv 3.958 | tv | stool | stool | unavailable |

Step 544 orders these measured pairs correctly on 4 of 6 items; step 200 does so on 2 of 3 items with both gaps printed. These pairs are not necessarily the question’s two nearest candidates. No wrong-answer truth/pick ratio is available.

**3. Model-stated margins**

I sorted step-544 distances toward the requested endpoint and defined the margin as `abs(d1−d2)/min(d1,d2)`. A zero versus positive distance has infinite margin. Numeric labels remain distinct here: options such as “book” and “books” are not collapsed.

| Set | Margin | Correct 544 | Correct 200 |
|---|---|---:|---:|
| dev-S1 | Below 10% | 2 of 4 | 1 of 4 |
| dev-S1 | 10% to below 25% | 11 of 23 | 15 of 23 |
| dev-S1 | 25% to below 50% | 10 of 20 | 13 of 20 |
| dev-S1 | At least 50% | 83 of 103 | 81 of 103 |
| R0-dev | Below 10% | 14 of 27 | 11 of 27 |
| R0-dev | 10% to below 25% | 20 of 47 | 21 of 47 |
| R0-dev | 25% to below 50% | 22 of 41 | 22 of 41 |
| R0-dev | At least 50% | 125 of 164 | 134 of 164 |

Small margins contain 11 of 40 dev-S1 errors and 42 of 91 R0-dev errors: 53 of 131 combined. They therefore identify a difficult stratum, but leave 78 of 131 errors outside it.

Among step-200 adjacent errors, step 544 numerically ranks truth second from the endpoint on 14 of 22 dev-S1 and 19 of 40 R0-dev items. These 33 of 62 cases have an unambiguous second rank; for farthest questions, “second” means second-largest distance.

**4. Votes**

| Set | Step 544 | Step 100 | Step 200 | Majority, ties → 200 | Any checkpoint right | All wrong | One common wrong pick |
|---|---:|---:|---:|---:|---:|---:|---:|
| dev-S1 | 106 of 150 | 100 of 150 | 110 of 150 | 109 of 150 | 123 of 150 | 27 of 150 | 21 of 150 |
| R0-dev | 181 of 279 | 178 of 279 | 188 of 279 | 191 of 279 | 213 of 279 | 66 of 279 | 37 of 279 |

Majority voting changes the benchmark proxies by **−0.08 VSI points** and **+0.19 ReVSI points**. An oracle selecting any correct checkpoint could recover 13 of 40 and 25 of 91 current errors; no deployable selector is established.

**5. Within-room consistency**

| Test | dev-S1 | R0-dev |
|---|---:|---:|
| Same reference, at least two shared candidates: trace-order agreement | 65 of 69 pairs | 1 of 1 pair |
| Same pairs: compatible truth constraints | 69 of 69 pairs | 1 of 1 pair |
| Reciprocal references: compatible trace constraints | 49 of 49 pairs | 36 of 36 pairs |
| Reciprocal references: compatible truth constraints | 49 of 49 pairs | 36 of 36 pairs |

Truth supplies an endpoint, not a complete ordering. Both truth candidates belong to the shared candidate set on only 37 of 69 dev-S1 pairs and 0 of 1 R0-dev pair. There are **no conflicting truth-pair IDs** to list.

The four dev-S1 trace disagreements are `074716/074719`, `194267/194281`, `283002/287191`, and `287191/287195`, each with prefix `vsi590k_`. They involve 3 distinct wrong items; one disagreeing pair has both answers correct.

For reciprocal references A and B, the two questions share distance A–B but otherwise constrain different distances. Their pairwise compatibility is consequently weak evidence of geometric consistency.

**6. Head precision and estimated ordering**

| Step-200 absolute-distance diagnostic | Result |
|---|---:|
| Numeric printed gap | 85 of 150 items |
| Within ±25% of truth | 58 of 85 numeric responses |
| Median absolute log(gap/truth) | 0.1104, n=85 |
| Gap/truth quartiles | 0.918 / 1.038 / 1.160, n=85 |
| Gap/truth range | 0.0056 to 7.0866, n=85 |

**Estimate:** I independently sampled two multiplicative errors from these 85 observed gap/truth ratios and applied them to each item’s step-544 endpoint distances. This assumes transferable errors, independent errors between candidates, and model-stated distances equal to true distances; ties receive half credit.

Estimated pair-order accuracy is **82.9% on 135 dev-S1 items** and **78.4% on 214 R0-dev items**, or **80.2% on 349 combined**. I excluded 80 of 429 items whose endpoint pair includes a zero distance. Using the six measured pairs instead gives **83.8%, n=6**, but those are not necessarily endpoint pairs.

Shared reference errors could correlate candidate measurements. Moreover, the observed error distribution excludes items without numeric responses. Neither assumption is validated by this estimate.

**Prices of the overlapping diagnostic groups**

These are ceilings from current lost scores, not predicted recoveries. ReVSI uses closest/farthest denominators of 186 and 93 and equal subtype weights.

| Group | dev-S1 errors; type points; VSI points | R0-dev closest/farthest errors; leaf points; ReVSI points |
|---|---|---|
| All errors | 40 of 150; 26.67; **3.33** | 59 of 186 / 32 of 93; 31.72 / 34.41; **4.72** |
| Truth adjacent to endpoint | 22 of 150; 14.67; **1.83** | 26 of 186 / 14 of 93; 13.98 / 15.05; **2.07** |
| Step-544 margin below 25% | 11 of 150; 7.33; **0.92** | 19 of 186 / 23 of 93; 10.22 / 24.73; **2.50** |
| Confirmed several-class present | 24 of 150; 16.00; **2.00** | 0 of 186 / 1 of 93; 0.00 / 1.08; **0.08** |
| Same wrong pick at all checkpoints | 21 of 150; 14.00; **1.75** | 28 of 186 / 9 of 93; 15.05 / 9.68; **1.77** |
| Wrong item participating in order disagreement | 3 of 150; 2.00; **0.25** | 0 of 186 / 0 of 93; 0.00 / 0.00; **0.00** |
| Recoverable by checkpoint oracle | 13 of 150; 8.67; **1.08** | 12 of 186 / 13 of 93; 6.45 / 13.98; **1.46** |

Relative-distance runaways occur on 0 of 150 dev-S1 and 0 of 279 R0-dev items; their priced loss is zero.

**What this changes for vehicle N**

1. **Reword 2,000 of 20,665 retained rows in `object_rel_distance|w1g|rows_rebuild_d0_v1` to substantiate the endpoint comparison.** The quantity is a **guess**. Require source-supported candidate locations and a comparison of nearest surfaces; the adjacent group supplies a ceiling of 22 dev-S1 and 40 R0-dev recoveries, worth 1.83 and 2.07 benchmark points. Gate: a controlled training ablation must improve this group without reducing overall accuracy; fluent comparisons with unchanged wrong endpoints fail the gate.

   Example renderer wording, with annotation-filled placeholders: “Bag: frame {f}, {region}. Bookshelf: frame {f1}, {region1}. Boxes: frame {f2}, {region2}. The nearest bookshelf–bag pair has a smaller gap than the nearest boxes–bag pair. The closest is bookshelf, option A.” The renderer must locate the remaining candidates too; it must not invent the locations or comparison.

2. **Reword up to 500 of 20,665 rows in that family to teach instance minima explicitly.** This quantity and its benefit are **guesses**. Example: “For each candidate class, use the smallest gap across the permitted reference–candidate instance pairs. Compare those smallest gaps.” For farthest questions, select the largest of those minima. The observed flagged-error ceiling is 24 dev-S1 items and 1 R0-dev item, worth 2.00 and 0.08 points, overlapping recommendation 1. Gate: first verify multiplicity and the intended instance rule in the actual training clip; unchanged performance on verified duplicate cases would reject the hypothesis.

3. **Add zero routed relative-distance rows on the strength of this analysis alone.** The unresolved ceiling remains 40 dev-S1 and 91 R0-dev errors, worth 3.33 and 4.72 points; demonstrated recovery from this join is zero. Gate: obtain same-item endpoint measurements, then show that printed gaps beat direct ordering on held-out rooms while counting missing responses. The current 2-of-3 measured-pair result cannot pass that gate.

**Refuted**

No verified count in the coordinator’s assigned record is contradicted. Two stronger interpretations fail: a two-category total cannot certify each category’s multiplicity, and majority voting does not consistently improve both sets. The permissive multiplicity flag expands R0-dev coverage from 3 to 97 items without establishing additional duplicate instances.

**Not established**

These joins do not separate instance confusion from inaccurate perception. That requires instance identities, the sampled RGB frames, and distances for the truth and competing candidate in the same clip. Unmatched counting names are missing evidence, not evidence of singleton objects.

The margin estimates cannot validate routing because step-544 numbers are generated assertions. Full truth rankings would strengthen the consistency test; paired head measurements would establish ordering precision. Training-row quantities and recovery rates remain hypotheses.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the multiplicity tables, margins, votes, unmatched-name lists, and head-error summary without writing files.

```python
import sys, re, math, statistics as S
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
def norm(s):
    p=s.lower().strip().split(); w=p.pop()
    special={"shelves":"shelf","knives":"knife","leaves":"leaf","clothes":"clothes",
             "glasses":"glass","boxes":"box","dishes":"dish","switches":"switch",
             "mattress":"mattress","thermos":"thermos","shorts":"shorts"}
    p.append(special.get(w,w[:-3]+"y" if w.endswith("ies") else
                        w[:-1] if w.endswith("s") and not w.endswith("ss") else w))
    return " ".join(p)
for dataset in ("dev-S1","R0-dev"):
    data=K.direct("R1",200,dataset,["object_rel_distance","object_counting"])
    rows=[r for r in data if r["type"]=="object_rel_distance"]
    counts=[r for r in data if r["type"]=="object_counting"]
    old={r["id"]:r for r in K.direct("S1",544,dataset,["object_rel_distance"])}
    middle={r["id"]:r for r in K.direct("R1",100,dataset,["object_rel_distance"])}
    known={}; totals=[]; mentioned=set()
    for c in counts:
        q=c["question"].lower()
        names=(re.findall(r"(?:among the | and )(.+?)\(s\)",q) if
               "altogether among the " in q else
               re.findall(r"(?:how many |numberof |(?:number|count|quantity) of )(.+?)\(s\)",q))
        keys=[(c["room"],norm(n)) for n in names]; mentioned.update(keys)
        if len(keys)==1: known[keys[0]]=float(c["gt"])
        else: totals.append((keys,float(c["gt"])))
    for _ in range(len(totals)+1):
        for keys,total in totals:
            unknown=[k for k in keys if k not in known]
            if len(unknown)==1: known[unknown[0]]=total-sum(known[k] for k in keys if k in known)
    groups={k:[] for k in ("none","ref","truth","pick200","others")}
    bins=[[],[],[],[]]; lowwrong=0; vote=oracle=common=0; unmatched=set()
    for r in rows:
        o=old[r["id"]]; opts=[x[3:].lower().strip() for x in r["options"]]
        tail=r["question"].split(")")[-1]
        ref=re.search(r"(?:closest to|nearest to|nearest|farthest from| to) the (.+?)(?:[?,.]| when| using| from)",tail)[1]
        ref=ref.split(" based on")[0]; names=[ref]+opts
        keys=[(r["room"],norm(n)) for n in names]
        unmatched.update(norm(n) for n,k in zip(names,keys) if k not in mentioned)
        flags=[known.get(k,-1)>=2 for k in keys]
        truth="ABCD".index(r["gt"]); pick="ABCD".index(r["pred"])
        marks=[not any(flags),flags[0],flags[truth+1],flags[pick+1],
               any(flags[i+1] for i in range(4) if i not in (truth,pick))]
        for k,v in zip(groups,marks):
            if v: groups[k].append((o["score"],r["score"]))
        vals={k.lower():float(v) for k,v in re.findall(r"(?:each:|;)\s*(.*?)\s+([0-9]+(?:\.[0-9]+)?)\s*m\b",o["text"])}
        assert all(c in vals for c in opts)
        ordered=sorted(vals.values(),reverse=r["subtype"]=="farthest")
        x,y=ordered[:2]; margin=abs(x-y)/min(x,y) if min(x,y)>0 else (0 if x==y else math.inf)
        b=0 if margin<.1 else 1 if margin<.25 else 2 if margin<.5 else 3
        bins[b].append((o["score"],r["score"]))
        lowwrong+=int(r["score"]==0 and margin<.25)
        predictions=[o["pred"],middle[r["id"]]["pred"],r["pred"]]
        winner=next((p for p in predictions if predictions.count(p)>=2),r["pred"])
        vote+=winner==r["gt"]; oracle+=r["gt"] in predictions
        common+=r["gt"] not in predictions and len(set(predictions))==1
    report=lambda rr:(len(rr),sum(x[0] for x in rr),sum(x[1] for x in rr))
    print(dataset,"multiplicity n/correct544/correct200",{k:report(v) for k,v in groups.items()})
    print("bins n/correct544/correct200",[report(b) for b in bins],"low-margin errors",lowwrong)
    print("majority/any/common-wrong",vote,oracle,common)
    print("unmatched names",len(unmatched),"; ".join(sorted(unmatched)))
ratios=[]
for r in K.routed(200,types=["object_abs_distance"]):
    unit=next(u for u in ("centimeters","inches","meters","feet") if u in r["question"].lower())
    truth=float(r["gt"])*{"centimeters":.01,"inches":.0254,"meters":1,"feet":.3048}[unit]
    for c in r["calls"]:
        m=re.search(r"distance\s+([0-9]+(?:\.[0-9]+)?)\s*m\b",c["response"])
        if c["family"]=="gap" and m: ratios.append(float(m[1])/truth)
print("gap ratios n/median absolute log/within25",len(ratios),
      S.median(abs(math.log(x)) for x in ratios),sum(.75<=x<=1.25 for x in ratios))
```