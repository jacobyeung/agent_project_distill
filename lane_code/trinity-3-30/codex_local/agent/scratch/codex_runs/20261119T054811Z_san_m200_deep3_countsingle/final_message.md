**Question and answer**

1. **How do counts change across checkpoints, outside step-200 loops?** On the same 122 of 150 dev-S1 items, MRA is 71.48 / 63.28 / 68.28 at steps 544 / 100 / 200. On 225 of 287 R0-dev single items, it is 65.51 / 64.98 / 71.96; non-looping undercounts cost 1.45 VSI and 1.01 ReVSI benchmark proxy points.
2. **Does the model beat a class prior?** Step 200 trails both always-2 and the sampled training-class mode on both cohorts. It nevertheless beats always-2 on every truth bin above 2, and several classes show positive answer–truth correlation.
3. **Are wrong answers stable?** All three checkpoints give the same wrong answer on 17 of 53 dev-S1 errors and 35 of 82 R0-dev errors. The three-way median scores 71.23 on 122 dev-S1 items and 71.29 on 225 R0-dev items; shared errors do not by themselves distinguish visual failures from shared learned biases.
4. **Do nearby listed frames identify overcounts?** No: among answers of 3 or 4 with at least two frame citations, nearby frames occur on 11 of 11 dev-S1 overcounts versus 7 of 7 correct items, and 13 of 15 R0-dev overcounts versus 14 of 14 correct items.
5. **Which trace forms survive outside loops?** First-seen inventories appear on 122 of 122 dev-S1 and 219 of 225 R0-dev items. Only 6 of 225 R0-dev items use procedure-only text; their MRA is 66.67, so the proposed vehicle’s form remains sparsely tested.
6. **Do single and multiple questions agree about the same class?** They agree on 4 of 10 same-room pairs. The single answer is nearer the single-item truth on 5 of 10 pairs, the multiple trace on 1 of 10, and they tie on 4 of 10.
7. **Which classes lose most, and does sampled training coverage help?** Chairs lead dev-S1 losses; office chairs lead R0-dev losses. Classes absent from the sample actually score higher, but this is a descriptive comparison confounded by class difficulty and literal label matching.
8. **What should vehicle N change?** Keep procedure-only traces, balance answers within classes, and add verified larger-count examples. These changes target 27 of 122 dev-S1 and 57 of 225 R0-dev non-looping undercounts; their recoverable-loss ceilings are 1.45 and 1.01 benchmark proxy points, not predicted gains.

**Evidence**

All scores below are B2048 MRA on a 0–100 scale. Except the explicit runaway row, cohorts exclude items force-closed at step 200; earlier checkpoints retain their recorded answers on those same items. Step-200 B2048 and ON16k answers agree on 347 of 347 cohort items.

Sources: let `P=/scratch/jjyeung/orch_n30` and `H=P/cont_ops16/work/c15/h1read/kit/build`. `san_kit` read step 100 under `H/a5d2d909067/fetched/x`, step 200 under `H/a8102c3207b/fetched/x`, and R0-dev step 544 under `H/adff67f7ae9/fetched/x`, using `{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Dev-S1 step 544 came from `P/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
Training evidence comes from the supplied `rows.sqlite`, `FAMILY_INDEX_RANGES.json`, exclusion records `n.json` and `z.json`, and `STORE_V7_TEMPLATE_COUNTS.json`. I read coordinator lines 212–219 and the named first-wave counting report. No official benchmark items were used.

**Confusion tables.** Each `answer:count` entry means that count **of the row’s N items**. Truth ≥5 pools larger truths; answer values remain unbinned.

| Set; truth; N | Step 544 answers | Step 100 answers | Step 200 answers |
|---|---|---|---|
| dev-S1; 2; 76 | 2:63, 3:8, 4:3, 5:1, 10:1 | 2:56, 3:15, 4:4, 38:1 | 1:1, 2:61, 3:11, 5:2, 8:1 |
| dev-S1; 3; 25 | 2:14, 3:9, 4:1, 12:1 | 2:15, 3:6, 4:1, 35:1, 38:1, 40:1 | 2:16, 3:5, 4:3, 8:1 |
| dev-S1; 4; 10 | 2:5, 3:1, 4:3, 10:1 | 2:2, 3:3, 4:2, 5:1, 38:1, 73:1 | 2:3, 3:2, 4:3, 8:2 |
| dev-S1; ≥5; 11 | 2:1, 3:1, 5:2, 6:2, 7:1, 10:2, 24:1, 27:1 | 2:1, 3:1, 6:2, 8:1, 13:1, 38:3, 39:1, 108:1 | 2:2, 4:3, 8:4, 108:1, 112:1 |
| R0-dev; 2; 145 | 2:118, 3:15, 6:1, 10:3, 11:2, 12:4, 13:1, 102:1 | 2:116, 3:14, 4:3, 6:1, 8:1, 31.8:1, 32:1, 34:3, 38:2, 71:1, 72:1, 195:1 | 1:1, 2:126, 3:13, 4:4, 6:1 |
| R0-dev; 3; 47 | 2:32, 3:6, 4:3, 6:2, 10:3, 102:1 | 2:29, 3:8, 4:1, 6:1, 34:2, 36:1, 38:3, 49:1, 103:1 | 2:33, 3:10, 4:3, 10:1 |
| R0-dev; 4; 16 | 2:8, 3:1, 4:1, 5:1, 6:1, 10:2, 12:2 | 2:6, 3:3, 4:2, 5:1, 34:1, 38:2, 48:1 | 2:10, 3:1, 4:5 |
| R0-dev; ≥5; 17 | 2:8, 3:1, 5:1, 6:3, 10:2, 12:1, 13:1 | 2:3, 3:2, 4:1, 5:1, 6:2, 10:1, 32:2, 34:1, 38:1, 44:1, 48:1, 387:1 | 2:8, 3:2, 4:2, 5:2, 10:1, 11:1, 360:1 |

**MRA by truth and predictor.** Class predictors use all 2,000 sampled rows, lowercase literal class names, smallest-value mode ties, conventional medians, and fallback 2 for absent classes.

| Set; truth; N | 544 | 100 | 200 | Always 2 | Class mode | Class median |
|---|---:|---:|---:|---:|---:|---:|
| dev-S1; 2; 76 | 83.95 | 75.66 | 81.84 | 100.00 | 95.26 | 72.50 |
| dev-S1; 3; 25 | 60.00 | 49.60 | 50.40 | 40.00 | 40.00 | 43.60 |
| dev-S1; 4; 10 | 41.00 | 46.00 | 45.00 | 10.00 | 20.00 | 45.00 |
| dev-S1; ≥5; 11 | 39.09 | 24.55 | 36.36 | 0.00 | 0.00 | 23.64 |
| R0-dev; 2; 145 | 82.41 | 80.97 | 87.86 | 100.00 | 95.52 | 78.48 |
| R0-dev; 3; 47 | 42.55 | 42.55 | 51.91 | 40.00 | 44.26 | 60.21 |
| R0-dev; 4; 16 | 19.38 | 31.25 | 41.25 | 10.00 | 21.88 | 37.50 |
| R0-dev; ≥5; 17 | 28.24 | 22.35 | 20.59 | 0.00 | 0.00 | 11.18 |
| dev-S1; all; 122 | 71.48 | 63.28 | 68.28 | 71.31 | 69.18 | 59.92 |
| R0-dev; all; 225 | 65.51 | 64.98 | 71.96 | 73.51 | 72.36 | 66.67 |

The model beats the class mode on truths ≥3 in both sets. Against the class median, it wins on dev-S1 truths 2, 3 and ≥5, ties at 4, and wins on R0-dev truths 2, 4 and ≥5. Using only the 433 sampled kept rows gives mode/median MRA 60.82/52.70 on 122 dev-S1 items and 72.58/68.62 on 225 R0-dev items.
Replacing cohort answers with always-2 would gain only 0.308 VSI and 0.087 ReVSI benchmark proxy points; replacing them with the class mode would gain 0.092 and 0.022. These are measured substitutions, not training-gain estimates.

**Loss pricing.** Type/leaf denominators remain all 150 dev-S1 or 287 R0-dev single items. Benchmark points divide these losses by 8 or 14, respectively.

| Mode | dev-S1 items; type / benchmark points | R0-dev single items; leaf / benchmark points |
|---|---|---|
| Non-looping overcount | 26 of 150; 14.20 / 1.775 | 25 of 287; 7.84 / 0.560 |
| Non-looping undercount | 27 of 150; 11.60 / 1.450 | 57 of 287; 14.15 / 1.010 |
| Runaway, including full-credit closures | 28 of 150; 17.87 / 2.233 | 62 of 287; 20.59 / 1.471 |
| Answer 2 below truth; overlaps undercounts | 21 of 150; 9.53 / 1.192 | 51 of 287; 12.82 / 0.916 |
| Same wrong answer at all checkpoints; overlaps above | 17 of 150; 7.73 / 0.967 | 35 of 287; 8.57 / 0.612 |

**Training sample and forms.** A seed-200 shuffle of counting primary keys yielded 2,000 single-category rows among 3,552 inspected rows; queries contained at most 200 primary keys. All 2,000 sampled qids are distinct. The sample contains 1,627 of 2,000 rows from `object_counting|r1g|rows_rebuild_d0_v1` and 373 of 2,000 from `object_counting|b12_cntapp_gt_v1|None`.

| Sample partition | Answer 1 | Answer 2 | Answer 3 | Answer ≥4 |
|---|---:|---:|---:|---:|
| All 2,000 | 2 of 2,000 | 1,115 of 2,000 | 364 of 2,000 | 519 of 2,000 |
| Kept 433 | 1 of 433 | 194 of 433 | 85 of 433 | 153 of 433 |
| Removed 1,567 | 1 of 1,567 | 921 of 1,567 | 279 of 1,567 | 366 of 1,567 |

The manifest retains 2,617 of 20,669 counting rows, all in `object_counting|r1g|rows_rebuild_d0_v1`; that family contains 9,253 rows before exclusions. It retains 0 of 10,177 `b12_cntapp_gt_v1` rows and 0 of 1,239 rows across the four gap families. The manifest provides family totals, not separate totals for the four lexical forms below.
Each quotation is the complete think-body of one kept training row; its family is the retained r1g family above.

| Kept wording, verbatim | Sample frequency | SQLite key; trained answer |
|---|---:|---|
| “Step 1: find the distinct instances of box; count each once across the frames.” | 115 of 433 | 51532; 4 |
| “Step 1: find each distinct cabinet, across the frames, and count it once.” | 111 of 433 | 99587; 3 |
| “Step 1: locate the distinct instances of cabinet; count each once across the frames.” | 111 of 433 | 87814; 4 |
| “Step 1: locate each distinct rug, across the frames, and count it once.” | 96 of 433 | 67234; 2 |

At step 200, visibility-list-then-count traces occur on 0 of 347 cohort items. The dev-S1 first-seen form covers all 122 items, with the truth scores shown above. R0-dev first-seen traces score 72.10 on 219 items: truth 2, 87.61 on 142; truth 3, 53.04 on 46; truth 4, 37.33 on 15; truth ≥5, 21.88 on 16.
R0-dev procedure-only traces score 100.00 on 3 truth-2 items, 0.00 on 1 truth-3 item, 100.00 on 1 truth-4 item, and 0.00 on 1 truth-11 item. Their 2 of 6 errors cost 0.697 leaf points and 0.050 ReVSI points, already included above.

**Stability and frame evidence.** Among the 36 dev-S1 errors whose answers differ across checkpoints, only step 544 is fully right on 10 of 36, only step 100 on 4 of 36, both on 5 of 36, and neither on 17 of 36. Corresponding R0-dev counts are 5, 7, 4 and 31 of 47. Among unchanged errors, the shared answer is 2 on 14 of 17 dev-S1 and 30 of 35 R0-dev items.

| Set; shared answer | Overcounts with duplicate / within-2 frames | Correct items with duplicate / within-2 frames |
|---|---|---|
| dev-S1; 3 | 7 of 8 / 8 of 8 | 5 of 5 / 5 of 5 |
| dev-S1; 4 | 3 of 3 / 3 of 3 | 2 of 2 / 2 of 2 |
| R0-dev; 3 | 7 of 9 / 7 of 9 | 10 of 10 / 10 of 10 |
| R0-dev; 4 | 6 of 6 / 6 of 6 | 4 of 4 / 4 of 4 |

These comparisons require at least two explicit frame citations. Larger overcount answers lack eligible correct controls. For truth≥3 undercounts, citations are available on 25 of 26 dev-S1 items: median first-to-last span 5, range 0–96.4; 12 of 25 spans are ≤2. R0-dev has citations on 50 of 56: median span 0, range 0–89; 38 of 50 spans are ≤2. These are literal cited numbers, not verified sampled-frame indices or elapsed times.
Among items non-looping at both steps with frame citations at both, steps 100 and 200 repeat the exact ordered frame list on 30 of 91 dev-S1 and 64 of 162 R0-dev items; list lengths agree on 69 of 91 and 137 of 162. For `vsi590k_050949`, both list `[1,1]` and answer 2 against truth 3. Frame lists alone therefore cannot establish instance identity.

**Cross-question consistency.** All 77 of 77 non-looping multiple traces expose parseable per-category addition operands. Joining them to non-looping singles by room and literal class yields 10 pairs involving 10 singles and 9 multiples; timing metadata matches on 10 of 10 pairs. Agreement occurs on 4 of 10, but 3 of those 4 agreements are wrong against the single truth.
Single answers score 47.00 on these 10 pairs; multiple-trace category counts score 27.00 against the same truths. The six disagreements contain three wrong single answers, costing 0.976 single-leaf points or 0.070 ReVSI points, overlapping the earlier modes. Example: bottle truth 5 receives single answer 5 but multiple-trace count 2.

**Within-class Spearman correlation.** Each row covers all non-looping step-200 items of that class. “Undefined” means truth or answer is constant; distinct-answer counts are stated out of N.

| Set; class; N | Answer–truth ρ | Distinct answers |
|---|---:|---:|
| dev-S1; chair; 20 | 0.717 | 6 of 20 |
| dev-S1; door; 7 | 0.373 | 3 of 7 |
| dev-S1; sofa; 17 | 0.118 | 3 of 17 |
| dev-S1; table; 15 | 0.639 | 4 of 15 |
| dev-S1; trash bin; 6 | −0.316 | 2 of 6 |
| dev-S1; window; 7 | Undefined | 4 of 7 |
| R0-dev; blanket; 5 | −0.408 | 2 of 5 |
| R0-dev; box; 5 | Undefined | 1 of 5 |
| R0-dev; chair; 6 | 0.984 | 3 of 6 |
| R0-dev; door; 7 | 0.568 | 4 of 7 |
| R0-dev; heater; 7 | Undefined | 1 of 7 |
| R0-dev; jacket; 5 | 0.186 | 2 of 5 |
| R0-dev; office chair; 6 | 0.686 | 5 of 6 |
| R0-dev; pillow; 5 | 1.000 | 2 of 5 |
| R0-dev; power sockets; 6 | Undefined | 1 of 6 |
| R0-dev; shelf; 5 | 0.825 | 3 of 5 |
| R0-dev; table; 6 | 0.557 | 3 of 6 |
| R0-dev; trash can; 5 | 1.000 | 2 of 5 |

**Ten largest class losses per set.** Each cell states wrong items of class items, then type/leaf and benchmark points. These losses exclude loops and overlap the mode table.

| dev-S1 class; errors; type / benchmark | R0-dev class; errors; leaf / benchmark |
|---|---|
| Chair; 13 of 20; 6.200 / 0.775 | Office chair; 5 of 6; 1.533 / 0.110 |
| Sofa; 7 of 17; 3.600 / 0.450 | Cabinet; 3 of 4; 0.871 / 0.062 |
| Table; 7 of 15; 3.200 / 0.400 | Door; 3 of 7; 0.871 / 0.062 |
| Window; 3 of 7; 1.867 / 0.233 | Table; 3 of 6; 0.871 / 0.062 |
| Door; 4 of 7; 1.867 / 0.233 | Box; 3 of 5; 0.767 / 0.055 |
| Trash bin; 3 of 6; 1.400 / 0.175 | Paper; 3 of 3; 0.732 / 0.052 |
| Towel; 2 of 3; 1.267 / 0.158 | Blanket; 3 of 5; 0.732 / 0.052 |
| Plant; 2 of 2; 1.067 / 0.133 | Heater; 2 of 7; 0.662 / 0.047 |
| Pillow; 2 of 2; 1.000 / 0.125 | Jacket; 2 of 5; 0.662 / 0.047 |
| Table lamp; 2 of 4; 1.000 / 0.125 | Mouse; 2 of 3; 0.662 / 0.047 |

Classes absent from the training sample score 88.00 on 5 dev-S1 items versus 67.44 on 117 covered items; R0-dev scores are 82.83 on 53 absent-class items versus 68.60 on 172 covered items. “Absent” means absent from this sample under literal naming, not absent from training.

| Sampled class share of answers >3 | dev-S1 MRA; N | R0-dev MRA; N |
|---|---|---|
| 0 | 87.65; 17 | 78.33; 60 |
| >0 to 25% | 67.96; 54 | 77.10; 31 |
| >25% to 50% | 57.27; 22 | 56.00; 70 |
| >50% | 61.25; 24 | 71.82; 11 |

**What this changes for vehicle N**

All row quantities below are **proposed guesses**. Use training scenes only. Ceilings overlap and cannot be added; none estimates the intervention’s expected gain.
1. **Balance answers within classes in the 2,617 kept r1g rows.** Reweight counts 2, 3 and ≥4 toward equal exposure, with matched classes across count bins where available. This targets all 27 of 122 dev-S1 and 57 of 225 R0-dev undercounts, capped at 11.60/1.450 and 14.15/1.010 type/benchmark points. Keep wording such as `<think>Step 1: locate the distinct instances of chair; count each once across the frames.</think> 3`. **Gate:** truth-3/4 MRA must rise and answer-2 undercounts must fall without offsetting truth-2 losses.
2. **Add 1,200 verified count≥4 procedure-only rows to `object_counting|r1g|rows_rebuild_d0_v1`.** Proposed split: 600 answer-4 and 600 answer≥5 rows, prioritizing adequately represented classes rather than creating class–answer shortcuts. This targets 18 errors among 21 dev-S1 truth≥4 items and 26 among 33 R0-dev items; ceilings are 8.33/1.042 and 7.98/0.570 type/benchmark points. **Gate:** score those fixed cohorts and within-class correlations; more large answers without better MRA fails.
3. **Reword the kept procedure rows to distinguish objects from views, without an inventory.** Example: `<think>Step 1: locate the distinct chairs. Count separate chairs individually, including chairs visible together; count repeated views of one chair only once.</think> 2`. This could address 26 of 122 dev-S1 and 25 of 225 R0-dev overcounts, capped at 14.20/1.775 and 7.84/0.560 type/benchmark points. **Gate:** require procedure adoption and lower overcount loss; repeated-frame frequency is not a valid gate.
4. **Add 400 verified singleton rows to the same r1g family, paired with existing examples of the same classes at counts 2 and 3.** Only 2 of 2,000 sampled rows answer 1. There are 0 truth-1 items in either analysis cohort, so singleton accuracy has no measured gain ceiling here; any benefit to the 14 dev-S1 and 18 R0-dev truth-2 overcounts is a **guess**, capped at 8.60/1.075 and 5.82/0.416 type/benchmark points. **Gate:** add a training-disjoint singleton dev slice and reject any rise in answer-1 undercounts on current truths≥2.

**Refuted**

A pure class-prior account is too strong: within-class answer–truth correlation reaches 0.717 on 20 dev-S1 chairs and 0.984 on 6 R0-dev chairs. Conversely, positive correlation does not establish accurate instance tracking.
Duplicate-frame pruning is contradicted by the matched-answer controls: duplicates occur on all 21 of 21 eligible correct answers of 3 or 4 across both sets. The first-wave inventory-building recommendation also conflicts with the current procedure-only ruling; it should not be implemented in this vehicle.
The prompt’s 7.12 ReVSI-point counting loss concerns both counting leaves. Single-category losses here total 3.04 ReVSI points; these denominators must not be interchanged.

**Not established**

The analysis does not establish whether individual errors come from missed objects, category confusion, identity merging, or learned answer bias. Annotated instances linked to the sampled RGB frames would settle those distinctions. Shared checkpoint errors are not independent evidence of a visual cause.
Procedure-only gains remain unmeasured beyond 6 R0-dev traces. A fixed-item next-checkpoint comparison must report both form adoption and MRA. Same-room pairs have matching timing metadata, but exact media identity still needs verification; sample-based class coverage also needs alias normalization before making coverage claims.

**Appendix — CLASSIFIER**

```python
import sys, json, random, sqlite3, re, statistics, resource, socket
from collections import Counter, defaultdict
assert socket.gethostname().split(".")[0] == "trinity-3-30"
sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
P = "/scratch/jjyeung/orch_n30/"
sys.path.insert(0, P + "swarm_an/kit")
import san_kit as K

def cls(q):
    p = q.lower().split("(s)")[0].strip()
    for pat in [r".*?how many ",
                r".*?(?:number\s*of|numberof|count of|quantity of) ",
                r"^count (?:all |the )?"]:
        m = re.match(pat, p)
        if m:
            return p[m.end():].strip()
    raise ValueError(q)

def mra(p, t):
    err = abs(float(p) - float(t)) / float(t)
    return sum(err <= 1 - (.5 + .05*k) for k in range(10)) / 10

def mode(v):
    c = Counter(v)
    return min(c, key=lambda x: (-c[x], x))

removed = set()
for name in ["n", "z"]:
    with open(P + "r1_ops6/cp/out/records/" + name + ".json") as f:
        for line in f:
            if line.strip():
                removed.add(json.loads(line)["row_key"])
with open(P + "r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json") as f:
    ranges = json.load(f)["families"]["object_counting"]
ids = [i for a, b in ranges for i in range(a, b + 1)]
random.Random(200).shuffle(ids)
db = sqlite3.connect(
    "file:" + P + "r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro",
    uri=True)
sample = []
for start in range(0, len(ids), 200):
    batch = ids[start:start + 200]
    sql = "select i,row from rows where i in (" + ",".join("?"*len(batch)) + ")"
    got = dict(db.execute(sql, batch))
    for i in batch:
        r = json.loads(got[i])
        q = r["student_input"]["question"]
        if q.count("(s)") == 1:
            sample.append((cls(q), float(r["answer"]), r["qid"] not in removed))
            if len(sample) == 2000:
                break
    if len(sample) == 2000:
        break
db.close()
train = defaultdict(list)
for c, a, kept in sample:
    train[c].append(a)
print("sample, kept, answer2:", len(sample), sum(x[2] for x in sample),
      sum(x[1] == 2 for x in sample))
for ds, divisor in [("dev-S1", 8), ("R0-dev", 14)]:
    allrows = K.direct("R1", 200, ds, types=["object_counting"])
    single = [r for r in allrows if ds == "dev-S1" or r["subtype"] == "single"]
    rows = [r for r in single if not r["forced_close"]]
    predictors = [lambda r: 2,
                  lambda r: mode(train.get(cls(r["question"]), [2])),
                  lambda r: statistics.median(train.get(cls(r["question"]), [2]))]
    print(ds, "cohort", len(rows), "of", len(single),
          "model", 100*statistics.mean(r["score"] for r in rows),
          "priors", [100*statistics.mean(mra(f(r), r["gt"]) for r in rows)
                     for f in predictors])
    for label, group in [
        ("over", [r for r in rows if float(r["pred"]) > float(r["gt"])]),
        ("under", [r for r in rows if float(r["pred"]) < float(r["gt"])]),
        ("loop", [r for r in single if r["forced_close"]])]:
        tp = 100*sum(1-r["score"] for r in group)/len(single)
        print(ds, label, len(group), "of", len(single), tp, tp/divisor)
```