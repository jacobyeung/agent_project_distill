**Question and answer**

1. **Where does each wrong trace first diverge from the truth?** Of 29 wrong items, 26 first diverge at turn 1, two at turn 2, and one at turn 3. The table below records the position, heading statement, and mistaken relation for every wrong item.
2. **Do later lines track the incoming heading?** All 89 multi-turn traces name the preceding destination and say “keep that heading”; none explicitly names the incoming direction. This single group scores 35 of 46 on two-turn routes and 32 of 43 on three-turn routes; there is no isolation-only comparison group.
3. **Do nearby options explain the wrong choices?** Exactly 210 of 389 distractors differ from the truth in one turn, and 16 of 29 wrong answers select such a neighbour. All 29 wrong answers share the trace’s first turn, but that first turn uniquely identifies an option on only 17 of 29 wrong items.
4. **Does the answer follow the trace?** The selected option matches the complete written sequence on 150 of 150 items, including 29 of 29 wrong items. No option-match failure occurs, so behaviour when no option matches is unobserved.
5. **What changes across checkpoints?** Step 200 loses 12 of 118 items that step 544 answered correctly and recovers 15 of its 32 errors. All three checkpoints miss 13 of 150 items; eight of those 13 receive the same option throughout.
6. **What do 300 training rows teach?** All 300 sampled rows use the same per-turn template, including implicit heading continuity on 211 of 211 later steps. The sample contains fewer multi-turn routes than dev: 139 of 300 versus 89 of 150.
7. **What should vehicle N change?** Test explicit initial orientation and explicit incoming-direction statements, using only the question’s route and existing qualitative labels. Correcting first turns alone could recover at most 13 of 150 items; correcting later turns alone could recover at most three of 150. These are error-set ceilings, not predicted gains.

**Evidence**

All results use dev-S1 and B2048 scores. Step-200 ON16k and B2048 answers agree on 150 of 150 items; none of these 150 items is force-closed.

The files are:

- Step 200: [ON16k traces](/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/0/items_a0.jsonl) and [B2048 scores](/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl).
- Step 100: [ON16k traces](/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a5d2d909067/fetched/x/main/a0/results/0/items_a0.jsonl) and [B2048 scores](/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a5d2d909067/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl).
- Step 544: [B2048 traces and scores](/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl).
- Training: [rows.sqlite](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite), sampled through [family index ranges](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json); family totals come from [template counts](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json).
- Interpretation follows the Answer and route sections of the [trace ruling](/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md). I read the first-wave report’s opening findings.

| Route length | Step 544 correct | Step 100 correct | Step 200 correct | First error at turn 1 | At turn 2 | At turn 3 |
|---|---:|---:|---:|---:|---:|---:|
| One turn | 48 of 61 | 53 of 61 | 54 of 61 | 7 of 61 | — | — |
| Two turns | 36 of 46 | 34 of 46 | 35 of 46 | 11 of 46 | 0 of 46 | — |
| Three turns | 34 of 43 | 34 of 43 | 32 of 43 | 8 of 43 | 2 of 43 | 1 of 43 |
| All routes | 118 of 150 | 121 of 150 | 121 of 150 | 26 of 150 | 2 of 150 | 1 of 150 |

Every turn line parsed: 282 of 282 name the question’s correct next destination. Every later line names the preceding destination correctly: 132 of 132 transitions. However, zero of those 132 lines independently specifies the incoming direction; “keep that heading” supplies continuity wording without an explicit direction check.

The following table gives each wrong item’s first incorrect line. IDs are unique prefixes. **†** marks the 12 items answered correctly at step 544. “Implicit” means the line says “keep that heading.”

| Item | First wrong turn | Position and heading stated there | Next waypoint and claimed side | Truth turn |
|---|---|---|---|---|
| q02e8b23 | 1 of 1 | Counter, facing sink | Step stool right | Back |
| q034e450 | 1 of 1 | Desk, facing bathroom vanity | Chair behind | Right |
| q05b8d41 | 1 of 2 | Tables, facing bookshelf | Chairs behind | Left |
| q06d5172† | 1 of 3 | Chair(s), facing wall thermostat | Letter tray behind | Left |
| q1257561 | 1 of 3 | Keyboard, facing desk | Power bank behind | Right |
| q1cc287a | 1 of 3 | Shopping bag, facing tennis bag | Scale right | Back |
| q1ee19b7† | 1 of 2 | Table, facing bedsheet | Standing lamp right | Back |
| q3242e9e† | 1 of 3 | Wardrobe, facing coffee table | Bed right | Back |
| q34e1bc7 | 1 of 3 | Bed, facing sofa | TV behind | Right |
| q393452f† | 1 of 2 | Mug, facing trash can | Table behind | Left |
| q3969a8e† | 1 of 3 | Trash can, facing curtain rail | Standing lamp right | Left |
| q3bf82f8 | 1 of 2 | Faces shelf from monitor, then advances to shelf | Drink carton right | Left |
| q3caafaa | 1 of 2 | Hand towel, facing wall mirror | Rug behind | Right |
| q4c20249† | 1 of 3 | Blanket, facing thermos | Bed right | Left |
| q5e6d73d | 1 of 2 | Faces sofa from chair, then advances to sofa | Table right | Left |
| q619c0b4 | 2 of 3 | Shelf, incoming heading implicit | Drink carton right | Left |
| q6b98c4b | 1 of 2 | Curtain, facing electric piano | Standing lamp right | Left |
| q941eed8† | 2 of 3 | Desk, incoming heading implicit | Chair(s) right | Left |
| q9eb6886 | 1 of 1 | Shelf, facing sink | Oven right | Back |
| qa13b050 | 1 of 2 | Chairs, facing television | Tables left | Right |
| qaad2b56† | 1 of 2 | Bedside table, facing trash can | Bed right | Back |
| qabac9b9 | 1 of 1 | Window sill, facing window frame | Heater left | Back |
| qad42143† | 1 of 1 | Heater, facing blinds | Curtain rail right | Back |
| qc7003a4 | 1 of 2 | Shoe rack, facing rug | Door behind | Right |
| qc805bcf | 1 of 1 | Air humidifier, facing file organizer | Bed right | Back |
| qda4db4a† | 1 of 1 | Trash bin, facing desk | Cabinet right | Back |
| qdc85563† | 1 of 2 | Shoe rack, facing wine bottle | Door behind | Right |
| qe532cf1 | 1 of 3 | Folded blanket, facing monitor | Bed behind | Right |
| qfef7557† | 3 of 3 | Trash can, incoming heading implicit | Radiator right | Left |

The 12 regressions comprise four with only the first turn wrong, six with first and later turns wrong, and two with only later turns wrong. Thus, regressions do not isolate a heading-update failure.

| Disjoint failure mode | Items | Recoverable score ceiling if that mode were fully corrected |
|---|---:|---:|
| Only first turn wrong | 13 of 150 | 8.67 points over 150 items |
| First and later turns wrong | 13 of 150 | 8.67 points over 150 items; both require correction |
| Only later turns wrong | 3 of 150 | 2.00 points over 150 items |
| Runaway | 0 of 150 | 0.00 points over 150 items |

All 13 first-turn-only errors confuse back with a side. Later errors are left/right swaps in 19 of 19 erroneous later turns. Among multi-turn items with a correct first turn, 67 of 70 complete the route correctly.

| Route length | One-turn-neighbour distractors | Wrong answers selecting a neighbour |
|---|---:|---:|
| One turn | 122 of 122 | 7 of 7 |
| Two turns | 54 of 138 | 4 of 11 |
| Three turns | 34 of 129 | 5 of 11 |
| All routes | 210 of 389 | 16 of 29 |

Among wrong items, the trace’s first turn matches one option on 17 of 29, two options on nine of 29, and three options on three of 29. The complete sequence matches the selected option on all 29; first-turn agreement therefore does not establish first-turn-only selection. The wrong answer retains the truth’s first turn on three of 29 items.

The five persistent errors whose options change are `q34e1bc7` C/A/A, `q3bf82f8` B/C/C, `q619c0b4` C/B/B, `q9eb6886` C/C/A, and `qc7003a4` C/D/D, in step-544/100/200 order. Step 100 and step 200 exchange nine correct-to-wrong and nine wrong-to-correct items out of 150, despite equal aggregate accuracy.

The training sample uses seed 200 over the supplied inclusive index ranges, with two primary-key queries. All 300 rows belong to `route_planning|dose_route_direct|None`; the family-count file reports 8,894 of 8,894 rows kept.

| Training property | Sample evidence | Dev comparison |
|---|---:|---:|
| One-turn routes | 161 of 300 | 61 of 150 |
| Two-turn routes | 67 of 300 | 46 of 150 |
| Three-turn routes | 72 of 300 | 43 of 150 |
| Per-turn lines plus final turn list | 300 of 300 | 150 of 150 |
| Explicit incoming direction on later lines | 0 of 211 transitions | 0 of 132 transitions |
| “Keep that heading” on later lines | 211 of 211 transitions | 132 of 132 transitions |
| Written sequence matches answer | 300 of 300 | 150 of 150 |
| Turn following “turn back” | 45 of 211 transitions | See conditional result below |

All 45 sampled continuations after “turn back” use the ordinary heading phrase; none explains the reversal. They nevertheless match their supervised answer sequences on 45 of 45 rows. On dev, 20 of 21 multi-turn items with both true and predicted first turn equal to back are correct, so the data do not establish a general failure after turning back.

**What this changes for vehicle N**

These are ranked proposals, not changes made. All use `route_planning|dose_route_direct|None`.

1. **Reword the initial orientation in the 300-of-300-row pilot.** Explicitly anchor forward to the question’s facing object and describe back as the opposite direction. **Hypothesis:** this could address the 13 of 150 first-turn-only errors, worth at most 8.67 points; correcting the other 13 first-turn errors still leaves later errors. Failure would be unchanged back/side confusion or losses among previously correct items.
2. **Reword later steps in the 139-of-300 multi-turn pilot rows.** Name the incoming segment using the preceding departure and current waypoint, including the 45 sampled continuations after back. **Hypothesis:** this could recover the three of 150 later-only errors, worth at most 2.00 points; the broader affected set is 16 of 150 items, of which 13 also need first-turn repair. Failure would be explicit direction wording with unchanged later-turn errors, or new waypoint/heading contradictions.
3. **Test a route-length-balanced pilot through sampling.** Replace 39 of 300 one-turn draws with 25 two-turn and 14 three-turn source rows, yielding 122/92/86 of 300 draws, exactly matching the dev proportions. This is a proposed sampling count; improvement is unestablished. Failure would be unchanged multi-turn accuracy or an offsetting single-turn loss.

For sampled training row `i=148465`, the combined wording can truthfully use the question’s named waypoints and existing qualitative turn labels:

> `<think>`  
> Step 1: I stand at the coffee table facing the playstation. That facing direction is forward. The bed is behind me, so I turn back and face the opposite direction.  
> Step 2: I go forward to the bed. My incoming heading is from the coffee table toward the bed. In that heading, the table is to my left, so I turn left.  
> Step 3: I go forward to the table. My incoming heading is from the bed toward the table. In that heading, the lamp is to my left, so I turn left.  
> The turns are: back, left, left.  
> `</think>`  
> B

This adds no angle, coordinate, measurement, or object-specific frame claim. The question supplies the movement segments; the existing row supplies the qualitative relations.

**Refuted**

No verified numerical claim in the prompt or the first-wave opening findings is contradicted. The evidence does refute an interpretation that later-turn mistakes usually occur after an otherwise correct prefix: only three of 16 items with later errors have a correct first turn. Missing post-back examples are also not the explanation: 45 of 300 sampled training rows contain them.

**Not established**

The traces do not reveal whether the model internally updates its heading or chooses an option before composing a consistent explanation. Their agreement cannot establish causal reasoning. Controlled training comparisons and option-order interventions on these dev items would distinguish those explanations.

The 300-row sample establishes a sampled length mismatch, not the exact full-store distribution. A bounded primary-key census would settle that distribution. Neither the current rows nor this read verifies the underlying visual geometry independently of the supplied answers.

**Appendix — CLASSIFIER**

```python
import sys, re, json, random, sqlite3
from collections import Counter
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

def load(run, step):
    return K.direct(run, step, "dev-S1", types=["route_planning"])

a, b, c = load("R1", 200), load("R1", 100), load("S1", 544)
b, c = {r["id"]: r for r in b}, {r["id"]: r for r in c}

def seq(s):
    return tuple(re.findall(r"turn (left|right|back)", s.lower()))

def lines(r):
    return re.findall(r"^Step \d+:.*", r["text"].split("</think>")[0], re.M)

def turns(r):
    return tuple(t for line in lines(r) for t in seq(line))

def opts(r):
    return {s[0]: seq(s) for s in r["options"]}

def errors(r):
    return [i+1 for i, (x,y) in enumerate(zip(turns(r), opts(r)[r["gt"]]))
            if x != y]

wrong = [r for r in a if not r["score"]]
print("First error by (length,index):",
      Counter((len(turns(r)), errors(r)[0]) for r in wrong))
print("Answer matches:", sum(turns(r)==opts(r)[r["pred"]] for r in a), "of", len(a))
print("Later-only:", sum(errors(r)[0]>1 for r in wrong), "of", len(a))
print("Any later error:", sum(any(i>1 for i in errors(r)) for r in wrong), "of", len(a))
print("One-turn wrong neighbours:", sum(len(errors(r))==1 for r in wrong), "of", len(wrong))
print("No matching option:", sum(turns(r) not in opts(r).values() for r in a), "of", len(a))
for n in (1,2,3):
    rs = [r for r in a if len(turns(r))==n]
    print("Length", n, "correct", sum(r["score"] for r in rs), "of", len(rs))
    if n > 1:
        print("Heading phrase:",
              sum(all("keep that heading" in l for l in lines(r)[1:]) for r in rs),
              "of", len(rs))
    print("Neighbour distractors:",
          sum(sum(x!=y for x,y in zip(s,opts(r)[r["gt"]]))==1
              for r in rs for s in opts(r).values()),
          "of", sum(len(r["options"])-1 for r in rs))
persistent = [r for r in wrong if not b[r["id"]]["score"] and not c[r["id"]]["score"]]
print("544 regressions:", sum(bool(c[r["id"]]["score"]) for r in wrong), "of", len(a))
print("All-three wrong:", len(persistent), "of", len(a))
print("Same option:", sum(r["pred"]==b[r["id"]]["pred"]==c[r["id"]]["pred"]
                          for r in persistent), "of", len(persistent))
p = "/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/"
ranges = json.load(open(p+"FAMILY_INDEX_RANGES.json"))["families"]["route_planning"]
ids = random.Random(200).sample([i for lo,hi in ranges for i in range(lo,hi+1)], 300)
con = sqlite3.connect("file:"+p+"vqa/rows.sqlite?mode=ro", uri=True)
rows = []
for k in range(0,300,150):
    part = ids[k:k+150]
    sql = "select i,row from rows where i in ("+",".join("?" for _ in part)+")"
    rows += [json.loads(s) for _,s in con.execute(sql, part)]
con.close()
ls = [re.findall(r"^Step \d+:.*", r["target"], re.M) for r in rows]
ts = [tuple(t for l in row for t in seq(l)) for row in ls]
print("Training lengths:", Counter(map(len,ts)), "of", len(rows))
print("Training multi-turn:", sum(len(t)>1 for t in ts), "of", len(rows))
print("Keep-heading transitions:", sum("keep that heading" in l for row in ls for l in row[1:]),
      "of", sum(len(row)-1 for row in ls))
print("Back followed by turn:", sum(t=="back" for row in ts for t in row[:-1]),
      "of", sum(len(row)-1 for row in ls))
```