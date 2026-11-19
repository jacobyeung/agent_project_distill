**1. Scope**

I classified all 340 of 674 wrong items, using the recorded B2048 scores. I read all 219 of 219 non-runaway wrong traces and examined 5 of 176 force-closed traces closely; the remaining runaway analysis was programmatic.

| Type and set | Coverage | Step 544 | Step 200 |
|---|---:|---:|---:|
| Object counting, dev-S1 | 150 of 150 | 62.80 | 56.33 |
| Object counting, R0-dev | 385 of 385 | 50.78 | 53.74 |
| R0-dev single | 287 of 385 | 57.39 | 57.42 |
| R0-dev multiple | 98 of 385 | 31.43 | 42.96 |
| Relative count, dev-S1 | 139 of 139 | 61.87 | 64.75 |

These scores were recomputed with `san_kit`. Source root `H` is `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build`.
Step 200 files were `H/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Step 544 R0-dev files were `H/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
Step 544 dev-S1 came from `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`. No official benchmark items were used.

**2. Failure modes at step 200**

Each cell gives the number of wrong items and its cost in type-specific percentage points. Runaway takes precedence over other modes.

| Primary mode | Definition | Counting dev-S1 | Counting R0-dev | Relative count dev-S1 |
|---|---|---:|---:|---:|
| Runaway | B2048 force-closes the trace; the answer loses credit. | 27 of 150; 17.87 | 78 of 385; 19.53 | 16 of 139; 11.51 |
| Undercount | The trace states a count below truth, and the answer follows it. | 27 of 150; 11.60 | 70 of 385; 12.34 | 0 of 139; 0 |
| Overcount | The trace states a count above truth, and the answer follows it. | 26 of 150; 14.20 | 61 of 385; 13.87 | 0 of 139; 0 |
| Unstated count | The trace only instructs itself to count; its unsupported answer is wrong. | 0 of 150; 0 | 2 of 385; 0.52 | 0 of 139; 0 |
| Wrong category counts | The comparison follows the inventory, but contradicts the labelled relation. | 0 of 150; 0 | 0 of 385; 0 | 29 of 139; 20.86 |
| List/comparison contradiction | The comparison contradicts the number of listed entries. | 0 of 150; 0 | 0 of 385; 0 | 4 of 139; 2.88 |
| **Total wrong** | Each wrong item appears once. | **80 of 150; 43.67** | **211 of 385; 46.26** | **49 of 139; 35.25** |

No separate answer-versus-trace contradiction appeared among the 219 of 219 non-runaway wrong traces. The comparison contradictions occur *inside* the reasoning; their answers follow the erroneous comparison.

The grouped signed-error distribution below includes every non-runaway numeric item. Error means answer minus truth.

| Set/subtype | ≤−3 | −2 | −1 | 0 | +1 | +2 | ≥+3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| dev-S1 | 2 of 122 | 4 of 122 | 21 of 122 | 69 of 122 | 17 of 122 | 0 of 122 | 9 of 122 |
| R0-dev | 11 of 302 | 13 of 302 | 47 of 302 | 169 of 302 | 43 of 302 | 9 of 302 | 10 of 302 |
| R0 single | 9 of 225 | 11 of 225 | 37 of 225 | 143 of 225 | 16 of 225 | 4 of 225 | 5 of 225 |
| R0 multiple | 2 of 77 | 2 of 77 | 10 of 77 | 26 of 77 | 27 of 77 | 5 of 77 | 5 of 77 |

Undercounts outnumber overcounts by 27 of 53 versus 26 of 53 on dev-S1, and 71 of 133 versus 62 of 133 on R0-dev, including the unsupported estimates. The answer is exactly 2 in 21 of 27 dev-S1 undercounts and 55 of 71 R0-dev undercounts.
The following cells give undercounts / overcounts within each non-runaway truth bin. Truth 1 occurs in 0 of 122 dev-S1 items and 0 of 302 R0-dev items.

| Set/subtype | Truth 2 | Truth 3 | Truth 4 | Truth ≥5 |
|---|---|---|---|---|
| dev-S1 | 1 of 76 / 14 of 76 | 16 of 25 / 4 of 25 | 5 of 10 / 2 of 10 | 5 of 11 / 6 of 11 |
| R0-dev | 1 of 189 / 42 of 189 | 37 of 62 / 11 of 62 | 14 of 24 / 3 of 24 | 19 of 27 / 6 of 27 |
| R0 single | 1 of 145 / 18 of 145 | 33 of 47 / 4 of 47 | 11 of 16 / 0 of 16 | 12 of 17 / 3 of 17 |
| R0 multiple | 0 of 44 / 24 of 44 | 4 of 15 / 7 of 15 | 3 of 8 / 3 of 8 | 7 of 10 / 3 of 10 |

Truth ≥5 accounts for **36.64% of all lost dev-S1 MRA and 30.88% of all lost R0-dev MRA**. Among non-runaways alone, those shares are 18.09% and 19.63%. R0 single/multiple shares are respectively 34.86%/22.18% overall and 21.39%/16.83% among non-runaways.
**List usage:** Literal list length matches the answer in 122 of 122 dev-S1 inventories and 294 of 296 R0-dev inventories. R0-dev has no inventory in 6 of 302 non-runaways. Restricting to explicit frame citations gives mismatches in 0 of 107 dev-S1 items and 2 of 247 R0-dev items. Both R0 exceptions use phrases such as “2 in frame 8,” so an entry may denote multiple instances.
**Repeated citations:** Within a category, frames repeat in 68 of 107 framed dev-S1 traces, 185 of 247 framed R0-dev traces, and 29 of 33 framed relative-count traces. Distinct cited frame values differ by exactly one in 11 of 107, 6 of 247, and 9 of 33, respectively. These are citation statistics, **not verified duplicate-object counts**.
**Multiple:** Both categories are listed and their stated counts are added correctly in 77 of 77 non-runaways. Arithmetic failures occur in 0 of 77; wrong totals occur in 51 of 77. At least one category count must therefore be wrong on each of those 51 items. The two literal-entry discrepancies above are `4f6900b92e1ccf0eeb5b9db8` and `ef56c8255e82c98f1be043c0`.
**Runaway exposure:** Force closure affects 28 of 150 dev-S1 counting items, 83 of 385 R0-dev counting items, and 65 of 139 relative-count items. Of these, 1 of 28, 5 of 83, and 49 of 65 still receive full credit.
For counting truth bins 2/3/4/≥5, runaway rates are 5 of 81 / 1 of 26 / 4 of 14 / 18 of 29 on dev-S1, and 19 of 208 / 17 of 79 / 10 of 34 / 37 of 64 on R0-dev. Frequent dev-S1 categories include chairs, 9 of 28; doors, 5 of 12; and tables, 4 of 18. R0 single examples include windows, 6 of 10; boxes, 5 of 10; door frames, 5 of 5; and paper, 4 of 7.
**Repetition onset:** Defining onset mechanically as the first repeated identical entry in the first inventory, it occurs at entry 2/3/5/6 in 16 of 28 / 7 of 28 / 1 of 28 / 1 of 28 dev-S1 runaways. R0 positions 2/3/4 account for 67 of 83 / 5 of 83 / 1 of 83. The remaining inventories have no exact duplicate, sometimes because their instance numbers keep increasing. This operational onset does not establish where visual duplication begins.
**Prefix counterfactual, computed by me:** I counted distinct explicit frames before the first repeated frame, separately per category, requiring every requested category to be present. This is possible for 19 of 28 dev-S1 and 58 of 83 R0-dev runaways; only 1 of 19 and 2 of 58 prefix counts equal truth. Replacing eligible answers gives whole-set MRA **57.07** and **54.34**. An oracle that keeps the original answer whenever substitution hurts gives the labelled **upper bounds 57.07 and 54.81**, over those two answer choices—not over all possible repairs.
B2048 answers are at least 30 on 22 of 28 dev-S1 and 60 of 83 R0-dev runaways; medians are 38 and 36. All 111 of 111 numeric runaways hit ON16k’s cap. Relative count usually loops while listing a category: 49 of 65 traces contain one inventory, 15 of 65 contain two, and 1 of 65 contains three; only 1 of 65 reaches “compare the counts.”

**3. Examples**

Questions are shortened where indicated by an ellipsis; quoted trace excerpts are verbatim. The unstated-count mode has only 2 of 2 examples available.

- **Runaway:** `vsi590k_050956`, dev-S1. “How many door(s) do we have in this room?” Truth 2; answer 13. Trace: “doorframe (left); doorframe (left); doorframe (left)”.
- **Runaway:** `022bf0575cbf5e5bdd69bde9`, R0-dev. “How many shelf(s) do we have in this room?” Truth 4; answer 38. Trace: “frame 87.4; frame 87.4; frame 87.4”.
- **Runaway:** `2f133aacd40c9195a02d8ade`, R0-dev. “…air vent(s) and towel(s)…?” Truth 4; answer 2. Trace: “air vent in ceiling; air vent in ceiling.” Then: “towel in left; towel in left; towel in left”.
- **Undercount:** `vsi590k_050949`, dev-S1. “Could you indicate how many pillow(s) are present?” Truth 3; answer 2. Trace: “frame 1 (left); frame 1 (left).” / “So the count is 2.”
- **Undercount:** `vsi590k_051253`, dev-S1. “…total numberof trash bin(s)…?” Truth 3; answer 2. Trace: “frame 4 (right); frame 27 (right).” / “So the count is 2.”
- **Undercount:** `0425fba1f35e9d2e109a2272`, R0-dev. “How many soap bottle(s) do we have in this room?” Truth 3; answer 2. Trace: “frame 2; frame 11.” / “So the count is 2.”
- **Overcount:** `vsi590k_050944`, dev-S1. “How many door(s) can we find in this area?” Truth 2; answer 3. Trace: “door 1 (left); door 2 (left); door 3 (left).”
- **Overcount:** `vsi590k_051075`, dev-S1. “Tell me how many window(s) are located here.” Truth 2; answer 3. Trace: “frame 1; frame 1; frame 1.” / “So the count is 3.”
- **Overcount:** `01cab3799a70727955e7d9d6`, R0-dev. “…boiler(s) and cable raceway(s)…?” Truth 2; answer 3. Trace: “boiler in frame 12.” / “cable raceway in frame 12; cable raceway in frame 12.” / “Step 3: add them: 1 + 2 = 3.”
- **Unstated count:** `1e5f0536780bb43f4474380c`, R0-dev. “How many book(s) do we have in this room?” Truth 11; answer 2. Trace: “Step 1: locate each distinct book, across the frames, and count it once.”
- **Unstated count:** `aa81f2245f58aa133b0bdcfc`, R0-dev. “How many cabinet(s) do we have in this room?” Truth 3; answer 10. Trace: “Step 1: find each distinct cabinet, across the frames, and count it once.”
- **Wrong category counts:** `vsi590k_087520`, dev-S1. “…table(s)…desk(s)…?” Truth C, equal; answer B, fewer. Trace: “Step 3: compare the counts: 4 is less than 8.”
- **Wrong category counts:** `vsi590k_087604`, dev-S1. “…desk(s)…lamp(s)?” Truth A, equal; answer C, fewer. Trace: “Step 3: the count of desk is 3; the count of lamp is 4.”
- **Wrong category counts:** `vsi590k_087760`, dev-S1. “…chair(s) relative to monitor(s)?” Truth B, equal; answer C, more. Trace: “Step 3: compare the counts: 3 (chair) > 2 (monitor).”
- **List/comparison contradiction:** `vsi590k_180766`, dev-S1. “…ceiling light(s) as monitor(s)…?” Truth C, more; answer A, equal. Trace: “1 in frame 1; 2 in frame 7; 3 in frame 11.” / “2 in frame 6; 3 in frame 28.” / “Step 3: compare the counts: 3 equals 3.”
- **List/comparison contradiction:** `vsi590k_270842`, dev-S1. “…table(s)…sofa(s)…?” Truth B, more; answer A, equal. Trace: “kitchen counter (right); dining table (right); side table (right).” / “left; right.” / “Step 3: compare the counts: table count equals sofa count.”
- **List/comparison contradiction:** `vsi590k_271473`, dev-S1. “…stove(s)…table(s)…?” Truth B, fewer; answer A, equal. Trace: “kitchen counter (right).” / “kitchen counter (middle); kitchen counter (right); table (right).” / “Step 3: compare the counts: stove count equals table count.”

**4. Step 544 against step 200**

“Right” means full credit. Contributions partition paired score changes by whether the *step-200* item force-closes; they are descriptive, not causal estimates.

| Type/set | Right→wrong | Wrong→right | Wrong→wrong | Runaway-group contribution | Remaining contribution |
|---|---:|---:|---:|---:|---:|
| Counting dev-S1 | 16 of 150 | 8 of 150 | 64 of 150 | −3.87 points | −2.60 points |
| Counting R0-dev | 30 of 385 | 48 of 385 | 181 of 385 | −3.84 points | +6.81 points |
| Relative count dev-S1 | 19 of 139 | 23 of 139 | 30 of 139 | +4.32 points | −1.44 points |

Counting traces change from visibility lists followed by cross-frame matching to direct instance lists. Among non-runaway right→wrong flips, median thinking length falls from 130 to 48 tokens on dev-S1 and 145.5 to 72 on R0-dev. Among non-runaway wrong→right flips, it falls from 161 to 39 and 223.5 to 48.5. Shortening accompanies both improvement and deterioration.
For `vsi590k_050945`, step 544 matches two towels across frames; step 200 lists “bathroom” three times. Conversely, `11c0d5a729b975346e5e7eb6` changes from two faucets plus two holders to one of each, correcting the total from 4 to 2.
Relative-count flips show changed inventories rather than answer-letter failures: `vsi590k_087520` changes table/desk counts from 4/4 to 4/8. Its 65 of 139 force closures, versus 5 of 139 at step 544, do not explain a score decline: the score rises despite them.

**5. Hypotheses**

Training evidence comes from `STORE_V7_SAMPLES20.json`, `STORE_V7_TEMPLATE_COUNTS.json`, and `FAMILY_INDEX_RANGES.json` at the supplied paths. The manifest contains 0 relative-count families. Counting retains 2,617 of 20,669 rows after the listed exclusions.

- **HYPOTHESIS—runaway:** Repeated, weakly distinguished entries teach continuation without an identity-based stopping condition. Family `object_counting|r1g|rows_rebuild_d0_v1`, row `q33755eb910d23334b77c85ff-p1`, trains “frame 7; frame 7; frame 8; frame 10; frame 15; frame 25.” This row is excluded; the hypothesis concerns the learned form.
- **HYPOTHESIS—undercount:** Generic counting instructions and weak instance descriptions encourage incomplete inventories. The same family’s retained row `qd88b08be8cf5e2cc852360e3` trains “locate the distinct instances of box; count each once across the frames.” Its answer is 8, but it supplies no inventory to supervise completeness.
- **HYPOTHESIS—overcount:** Frame/region citations inadequately distinguish identities. Family `object_counting|b12_cntapp_gt_v1|None`, row `b12ct_6fff8737bb49ffaf4de85180`, includes “frame 3 (right); frame 3 (right)”. Such repetitions can represent legitimate separate instances; the text does not explain their distinction.
- **HYPOTHESIS—unstated count:** The retained generic form directly teaches omission of the intermediate count. The retained box row quoted above exhibits precisely that structure; 2 of 6 non-runaway R0 traces using this structure answer incorrectly.
- **HYPOTHESIS—wrong category counts:** Relative count transfers an imperfect numeric inventory procedure without dedicated comparison rows. The manifest has no `relative_count|pool|retrace` family; the nearest evidence is `object_counting|b12_cntapp_gt_v1|None`, row `b12ct_f46a022bd149e12c691c6b12`: “frame 6 (left); frame 21 (left)” and “frame 9 (left); frame 15 (left).”
- **HYPOTHESIS—list/comparison contradiction:** Missing dedicated comparison supervision permits independently generated lists and conclusions. That same counting row teaches “Step 3: add them: 2 + 2 = 4.” It supplies addition supervision, not list-to-count-to-comparison consistency.

**6. Label or scoring defects**

A possible scoring-boundary defect affects 2 of 150 dev-S1 and 6 of 385 R0-dev items: relative error 0.20 receives 0.6, whereas inclusive mathematical thresholds give 0.7. IDs are `vsi590k_169698`, `vsi590k_172684`, `09ac0afb1bc8cc8f01b23168`, `16ae5c36b1137c9f8eabfa41`, `79dec2c046fe12d9110d9414`, `97609ab3525a38087ca7cf71`, `ac0df2085761d1db2dacbf7d`, and `f79cb56860aef9b9cd345127`. Floating-point thresholds are a **hypothesis**; correcting these would add 0.13 and 0.16 points. All reported primary scores retain the file values.
Possible label inconsistencies occur in 11 of 118 dev-S1 room/category groups. For example, `vsi590k_053628` labels tables in `d1/scene0155` as 2, while `vsi590k_053633` labels them as 3; `vsi590k_053627` and `vsi590k_053632` label chairs there as 16 and 15. Different video subsets could explain this, so these are flags, not established label errors.

**7. Three changes for vehicle N**

1. **Reword replacements for removed counting rows**, across the existing counting families, to identify objects with short distinguishing descriptions and an explicit completed inventory. **GUESS: about 3,000 rows.** This targets the 121 of 340 wrong items classified as runaway. That is exposure, not a predicted recovery; the prefix experiment shows that stopping alone seldom restores truth.
2. **Strengthen inventory supervision** in `object_counting|r1g|rows_rebuild_d0_v1` and `object_counting|b12_cntapp_gt_v1|None`, balancing small totals, larger totals, repeated views, and separate objects sharing a frame. **GUESS: reword about 2,600 retained rows and add about 1,200 verified totals rows.** This targets 186 of 340 non-runaway numeric errors. I am least sure of this change’s yield because the traces cannot distinguish missed objects from category or identity errors.
3. **Add a dedicated family**, proposed as `relative_count|vehicle_N_dev_train|finite_compare_v1`, with explicit category counts, the computed comparison, and its option mapping. **GUESS: about 2,000 rows.** This targets 33 of 340 non-runaway relative-count errors. Merely following the literal inventories would correct 3 of 4 comparison-contradiction items; the other errors still require better counts. These target counts overlap with training effects and are not additive recovery forecasts.

**8. Not established**

The traces do not establish which repeated or adjacent frame citations refer to the same physical object. Instance annotations and the exact sampled frames would settle that. Force closure also misses completed inflation: non-runaway answers include 112 for truth 16, 108 for truth 15, and 360 for truth 10.
Exact per-category truths are absent from relative-count rows. Same-room numeric rows provide unambiguous candidate counts for 6 of 33 non-runaway wrong comparisons, but video identity is not verified; for example, they suggest desk/lamp truth 4/4 against the trace’s 3/4. Exact clip joins would make those diagnoses reliable. Training-row causes and intervention gains remain hypotheses.

**Appendix — CLASSIFIER**

```python
import sys
import resource
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

# These exceptions rest on reading the complete non-runaway traces.
UNSTATED = {
    "1e5f0536780bb43f4474380c",
    "aa81f2245f58aa133b0bdcfc",
}
CONTRADICTION = {
    "vsi590k_087681",  # 25 listed entries per category; claims fewer.
    "vsi590k_180766",  # Three versus two entries; claims equal.
    "vsi590k_270842",  # Three versus two entries; claims equal.
    "vsi590k_271473",  # One versus three entries; claims equal.
}
MODES = [
    "Runaway", "Undercount", "Overcount", "Unstated count",
    "Wrong category counts", "List/comparison contradiction",
]

def classify(r):
    if r["forced_close"]:
        return "Runaway"
    if r["id"] in UNSTATED:
        return "Unstated count"
    if r["type"] == "relative_count":
        return ("List/comparison contradiction"
                if r["id"] in CONTRADICTION else "Wrong category counts")
    return "Undercount" if float(r["pred"]) < float(r["gt"]) else "Overcount"

for dataset in ["dev-S1", "R0-dev"]:
    types = ["object_counting"]
    if dataset == "dev-S1":
        types.append("relative_count")
    rows = K.direct("R1", 200, dataset, types=types)
    for typ in types:
        group = [r for r in rows if r["type"] == typ]
        wrong = [r for r in group if r["score"] < 1]
        counts, losses = Counter(), defaultdict(float)
        for r in wrong:
            mode = classify(r)
            counts[mode] += 1
            losses[mode] += 1 - r["score"]
        print(dataset, typ)
        for mode in MODES:
            print(f"{mode}: {counts[mode]} of {len(group)}; "
                  f"{100 * losses[mode] / len(group):.2f} points")
        assert sum(counts.values()) == len(wrong)
        print(f"TOTAL: {len(wrong)} of {len(group)}; "
              f"{100 * sum(losses.values()) / len(group):.2f} points")
```