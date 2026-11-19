**1. Question and answer**

**1. Which convention do the traces use?** They mix valid indices, out-of-range numbers, decimals, and prose locations. The mixture does not consistently resolve with training: appearance-order citations exceed 32 on 100 of 246 items at step 544, 105 of 246 at step 100, and 100 of 246 at step 200; VSTI increases from 64 of 900 to 373 of 900.

**2. Are numbers above 32 seconds?** The requested timestamp test does **not** support that interpretation. At step 200, appearance-order citations match their own sampled timestamps on 17 of 153 distinct values, versus 42 of 153 against mismatched-item timestamps; VSTI matches on 36 of 513 versus 100 of 513.

**3. Does the appearance-order answer follow its trace?** Not reliably. Averaging tied best options reproduces scores of **54.9% from stated frames, 56.0% from written order, and 62.2% from actual answers**, each over 246 items; 45 of 76 items whose written order matches no option nevertheless receive the correct answer.

**4. Does interpreting queried frame k incorrectly hurt VSTI?** These results do not establish that mechanism. All 900 of 900 traces repeat the requested k correctly, no videos have spacing under 2 seconds, and the comparisons between longer and shorter videos show no consistent accuracy penalty.

**5. Are training citations valid, and are long videos represented?** All 2,426 of 2,426 numeric frame citations in the 600-row sample are integers within 1–32. Long videos occur in 302 of 600 sampled rows, but only 42 of 111 sampled VSTI rows versus 630 of 900 VSTI dev items; this stratified sample does not establish population proportions.

**6. What is the cheapest convention repair?** Render existing citations as **“sampled frame k of 32”**, and identify input frames with the same indices. At step 400, measure citation validity alongside answer accuracy and trace–answer agreement; cleaner citations alone would not demonstrate better grounding.

**2. Evidence**

All results below use the supplied dev sets. Scores are B2048; citations come from `K.text`, which generally contains ON16k text. Step-544 dev-S1 and facing traces contain only B2048 text. R1 step-100 facing and VSTI traces are unavailable through the supplied loader.

Sources are under `/scratch/jjyeung/orch_n30/`: direct returns use `cont_ops16/work/c15/h1read/kit/build/{adff67f7ae9,a5d2d909067,a8102c3207b}/fetched/x/`; VSTI uses `h1vsti/kit/build/{acb2faedd41,a35f73e87f0}/fetched/x/`; facing step 200 uses `h1face/kit/build/a2e46c0504e/fetched/x/`. Within those directories, `a0/results/0/items_a0.jsonl` supplies traces and `a0/results/budget_2048/0/items_a0.jsonl` supplies scored answers where available. Step-544 dev-S1/facing files are under `evalx27/work/pull/x27/res/e193/merged/{main,away,forward}/results/budget_2048/0/`.

**Citation census.** Every five-number cell gives **(numeric citation, all numeric citations valid integer indices, any value >32, any decimal notation, prose location in a frame slot), each out of N traces**. Categories overlap; prose locations can coexist with numeric citations. The parser includes numeric lists following “frame,” and excludes text after `</think>`. “Direction E/M/H” abbreviates the easy/medium/hard types; V1–V3 and LR/NF/UD are the six VSTI types.

| Set/type | N | Step 544 | R1 step 100 | R1 step 200 |
|---|---:|---|---|---|
| dev-S1 counting | 150 | (148,8,139,25,0) | (127,83,36,3,1) | (126,88,34,8,14) |
| dev-S1 direction E | 150 | (0,0,0,0,0) | (1,1,0,0,0) | (0,0,0,0,0) |
| dev-S1 direction M | 150 | (0,0,0,0,0) | (0,0,0,0,0) | (0,0,0,0,0) |
| dev-S1 direction H | 150 | (0,0,0,0,0) | (0,0,0,0,0) | (0,0,0,0,0) |
| dev-S1 relative distance | 150 | (31,26,5,1,120) | (61,44,16,0,97) | (59,40,19,1,100) |
| dev-S1 object size | 150 | (16,15,1,0,134) | (58,46,11,1,98) | (54,39,15,4,105) |
| dev-S1 relative count | 139 | (81,15,65,27,33) | (33,17,8,0,78) | (74,55,14,8,47) |
| dev-S1 relative object size | 150 | (18,14,4,0,138) | (5,1,4,0,29) | (4,1,2,0,14) |
| dev-S1 route planning | 150 | (0,0,0,0,0) | (0,0,0,0,0) | (0,0,0,0,0) |
| R0-dev appearance order | 246 | (246,146,100,0,0) | (246,141,105,0,0) | (246,146,100,0,0) |
| R0-dev counting | 385 | (380,5,375,60,6) | (288,205,80,4,62) | (307,221,82,20,102) |
| R0-dev direction E | 192 | (0,0,0,0,0) | (68,5,63,0,0) | (74,7,67,0,0) |
| R0-dev direction M | 194 | (0,0,0,0,0) | (80,5,75,0,0) | (72,11,61,0,0) |
| R0-dev direction H | 192 | (0,0,0,0,0) | (56,8,48,0,0) | (54,8,46,0,0) |
| R0-dev relative distance | 279 | (50,35,4,11,239) | (128,99,29,0,161) | (141,104,37,5,154) |
| R0-dev object size | 293 | (70,64,6,2,223) | (127,105,21,0,187) | (125,107,18,2,188) |
| Away E | 50 | (0,0,0,0,0) | unavailable | (49,11,38,2,0) |
| Away M | 50 | (0,0,0,0,0) | unavailable | (50,9,41,4,0) |
| Away H | 50 | (0,0,0,0,0) | unavailable | (48,6,42,3,0) |
| Forward E | 50 | (0,0,0,0,0) | unavailable | (34,9,25,2,0) |
| Forward M | 50 | (0,0,0,0,0) | unavailable | (32,6,26,2,0) |
| Forward H | 50 | (0,0,0,0,0) | unavailable | (17,0,17,2,0) |
| VSTI V1 | 150 | (150,145,5,0,0) | unavailable | (150,71,79,0,0) |
| VSTI V2 | 150 | (150,148,2,0,0) | unavailable | (150,79,71,0,0) |
| VSTI V3 | 150 | (150,147,3,0,0) | unavailable | (150,99,51,0,0) |
| VSTI LR | 150 | (145,132,13,0,0) | unavailable | (150,93,57,0,0) |
| VSTI NF | 150 | (150,126,24,0,0) | unavailable | (150,89,61,0,0) |
| VSTI UD | 150 | (142,125,17,0,0) | unavailable | (150,96,54,0,0) |

The valid-index column is stricter than merely lying numerically within 1–32: fractional numbers fail it. Prose-slot counts identify forms such as “first seen in the left” or “first appearance: left”; they do not establish that the location itself is wrong.

**Timestamp test.** Each value is counted once per item. A hit means distance ≤0.6 seconds from any of the item’s 32 timestamps. The baseline cyclically reassigns timestamps within each type after sorting IDs, using offset `N//2+1`. Below, **(own hits, shuffled hits)/N** means both counts are out of N distinct item–value pairs. The index interpretation succeeds on **0 of N** values above 32.

| Set/type | >32: step 544 | >32: step 100 | >32: step 200 | Step-200 values 1–32 on long videos: (own, shuffled, valid index)/N |
|---|---|---|---|---|
| dev-S1 counting | (396,290)/1835 | (4,12)/44 | (14,59)/3474 | (13,14,67)/67 |
| dev-S1 relative count | (183,180)/1137 | (57,44)/1908 | (64,62)/1926 | (18,22,146)/146 |
| dev-S1 relative distance | (0,1)/5 | (0,0)/16 | (1,0)/19 | (0,4,15)/15 |
| dev-S1 object size | (0,0)/1 | (2,0)/11 | (4,0)/15 | (0,3,9)/9 |
| dev-S1 relative object size | (0,1)/4 | (0,0)/5 | (0,1)/3 | (1,1,1)/1 |
| R0-dev appearance order | (17,49)/166 | (20,44)/157 | (17,42)/153 | (74,100,536)/536 |
| R0-dev counting | (1393,1348)/8638 | (10,16)/94 | (8,21)/103 | (49,35,178)/181 |
| R0-dev direction E | none | (13,26)/144 | (11,21)/138 | (9,10,42)/42 |
| R0-dev direction M | none | (24,32)/158 | (16,14)/116 | (16,14,57)/57 |
| R0-dev direction H | none | (13,24)/105 | (10,19)/90 | (12,5,41)/41 |
| R0-dev relative distance | (0,1)/4 | (0,10)/29 | (3,10)/37 | (9,10,42)/42 |
| R0-dev object size | (0,1)/6 | (0,1)/21 | (0,3)/18 | (14,4,45)/45 |
| Away E | none | unavailable | (11,8)/80 | (4,8,11)/11 |
| Away M | none | unavailable | (11,17)/87 | (6,11,27)/30 |
| Away H | none | unavailable | (16,10)/84 | (5,8,15)/16 |
| Forward E | none | unavailable | (5,5)/59 | (2,4,5)/5 |
| Forward M | none | unavailable | (5,14)/56 | (3,6,17)/17 |
| Forward H | none | unavailable | (6,8)/36 | (1,5,8)/8 |
| VSTI V1 | (0,0)/5 | unavailable | (11,27)/133 | (42,74,320)/320 |
| VSTI V2 | (0,0)/2 | unavailable | (6,18)/106 | (39,76,284)/284 |
| VSTI V3 | (1,2)/3 | unavailable | (4,12)/63 | (30,57,240)/240 |
| VSTI LR | (1,3)/17 | unavailable | (5,12)/71 | (44,52,235)/235 |
| VSTI NF | (6,9)/26 | unavailable | (4,18)/72 | (43,56,245)/245 |
| VSTI UD | (1,5)/25 | unavailable | (6,13)/68 | (45,64,244)/244 |

These low values look more compatible with indices than sampled timestamps, without proving correct visual grounding. Appearance-order values occupy bins 1–8, 9–16, 17–24, and 25–32 on respectively **180, 184, 120, and 52 of 536** pairs. Excluding repeated queried-k citations, VSTI first-seen values occupy those bins on **340, 227, 230, and 170 of 967** pairs; only **157 of 967** match timestamps.

Decimals do not rescue the seconds hypothesis: step-544 counting has timestamp matches on **0 of 100** fractional values in dev-S1 and **1 of 213** in R0-dev, versus shuffled matches on **15 of 100** and **31 of 213**. The cited example “frame 118.9” exists, but decimal syntax is not evidence of a correct timestamp.

Counting runaways remain one separately priced mode: at step 200, dev-S1 counting has **28 of 150** runaways costing **17.87 score points**; R0-dev counting has **83 of 385** costing **19.53 points**; relative count has **65 of 139** costing **11.51 points**. Excluding runaways, >32 timestamp matches remain **4 of 41**, **8 of 96**, and **32 of 205**, respectively. These losses overlap other diagnostics and must not be added to them.

**Appearance-order consistency.** “Best agreeing option” maximizes agreement over six object pairs. Averaging ties gives **54.88% over 246 items** from frames and **55.96% over 246** from written order; choosing the first tied letter instead gives **57.32%** and **58.13%**, explaining why tie handling matters. Actual answers score **153 of 246**.

| Check | Result |
|---|---|
| Frame-derived order / written order exactly equals chosen option | 134 of 246 / 170 of 246 |
| Written order contradicts sorting its own frames | 41 of 246 |
| Answer’s first object equals frame-earliest / written-first object | 231 of 246 / 231 of 246 |
| Frame / written / answer pairwise agreement with truth | 1155 of 1476 / 1176 of 1476 / 1240 of 1476 pairs |
| Among unmatched orders: correct answer | 45 of 76 |
| Among unmatched orders: answer preserves written first / written last | 61 of 76 / 31 of 76 |
| Among unmatched orders: answer starts with frame-earliest object | 62 of 76 |
| Among unmatched orders: answer is among pairwise-best written-order options | 64 of 76 |
| Among unmatched orders: predicted A / B / C / D | 18 of 76 / 20 of 76 / 16 of 76 / 22 of 76 |
| Among unmatched orders: frame / answer pairwise agreement with truth | 304 of 456 / 366 of 456 pairs |

The answer often preserves the trace’s first object, but its remaining ordering contains information absent from—or contradictory to—the stated chronology. This establishes inconsistency, not the model’s hidden causal computation.

**VSTI queried-frame comparison.** There are **0 of 900** items with spacing under 2 seconds. The available comparison is spacing 2–4 seconds against >4 seconds. Cells show correct items at **544; 200**. Low k means k≤16.

| Type | Spacing 2–4 s | Spacing >4 s | Long, low k | Long, high k |
|---|---|---|---|---|
| V1 | 10/50; 17/50 | 27/100; 40/100 | 17/52; 23/52 | 10/48; 17/48 |
| V2 | 17/45; 18/45 | 31/105; 38/105 | 15/45; 19/45 | 16/60; 19/60 |
| V3 | 24/47; 25/47 | 59/103; 64/103 | 25/47; 30/47 | 34/56; 34/56 |
| LR | 24/41; 30/41 | 57/109; 75/109 | 31/51; 38/51 | 26/58; 37/58 |
| NF | 23/44; 23/44 | 54/106; 71/106 | 31/48; 32/48 | 23/58; 39/58 |
| UD | 32/43; 35/43 | 57/107; 89/107 | 29/49; 40/49 | 28/58; 49/58 |

High k performs worse at step 200 in V1–V3 and LR, but better in NF and UD. Although **615 of 900** traces assign some object a first-seen number larger than k, that contradiction cannot identify the attended frame while the numbering convention itself is unreliable.

**Training sample.** I selected 600 primary keys from `STORE_V7_SAMPLES20.json`, using seed 200: 19 rows from each of the first six alphabetically sorted eligible families and 18 from each remaining family. I fetched those keys from `rows.sqlite` in three queries of 200 keys. This covers **33 of 33** requested families, but inherits the supplied sample’s selection and is not a uniform store sample.

| Sample group | Rows with spacing <2 s | Rows with spacing 2–4 s | Rows with spacing >4 s |
|---|---|---|---|
| Appearance, `w1g|rows_rebuild_d0_v1` | 2/19 | 4/19 | 13/19 |
| Appearance, `b12_cntapp_gt_v1|None` | 0/19 | 5/19 | 14/19 |
| `first_seen_frame|b12_cntapp_gt_v1|None` | 2/19 | 5/19 | 12/19 |
| Counting, six pools | 12/108 | 40/108 | 56/108 |
| V1, `vsti_rel_v4|None` | 6/19 | 3/19 | 10/19 |
| V2, `vsti_rel_v4|None` | 3/19 | 8/19 | 8/19 |
| V3, `vsti_rel_v4|None` | 4/19 | 10/19 | 5/19 |
| LR, `vsti_rel_v4|None` | 4/18 | 7/18 | 7/18 |
| NF, `vsti_rel_v4|None` | 4/18 | 9/18 | 5/18 |
| UD, `vsti_rel_v4|None` | 7/18 | 4/18 | 7/18 |
| Direction, fifteen rebuilt families | 43/270 | 89/270 | 138/270 |
| Direction, three `r1_away_opp|None` families | 9/54 | 18/54 | 27/54 |

Numeric citations occur in **541 of 600** rows; all **2,426 of 2,426** cited values pass. All **600 of 600** rows have timestamps. Spacing min/quartiles/max are **0.83 / 2.54 / 4.00 / 5.84 / 21.86 seconds**. The kept subset contains **495 of 600** rows, including **249 of 495** long videos; kept VSTI contains **41 of 109** long videos.

For comparison, long videos occur in **737 of 1339** dev-S1 items, **1142 of 1781** R0-dev items, **164 of 246** appearance-order items, **76 of 150** in each facing twin set, and **630 of 900** VSTI items. Appearance training therefore includes substantial long-video coverage; the VSTI sample suggests a coverage mismatch requiring a population-weighted check.

**3. What this changes for vehicle N**

1. **Normalize existing frame fields; add no rows.** The sampled non-counting families contain **139,741 retained rows**, according to `STORE_V7_TEMPLATE_COUNTS.json`: both appearance pools, first-seen, six VSTI families, and eighteen direction families. Reword citations wherever present: **“The chair first appears in sampled frame 7 of 32.”** Preserve omitted citations when the source supplies no frame. Apply the same renderer to the additional **30,443 retained relative-distance/object-size rows** for a global convention. **Hypothesis:** this removes ambiguity; no accuracy gain is established. Relevant error ceilings are **34 of 246** appearance items, **162 of 900** VSTI items, and **14 of 150** away items that are wrong and cite >32—not predicted fixes.
2. **Keep frames attached to the sorted appearance sequence.** Reword the **27,587 retained rows** in `obj_appearance_order|w1g|rows_rebuild_d0_v1` and `obj_appearance_order|b12_cntapp_gt_v1|None`: **“First appearances: chair—sampled frame 3 of 32; table—7; lamp—12; door—20. This sequence matches option B.”** Validate the full sequence against the option. This targets **41 of 246** sorting contradictions, including **14 of 93** errors, but only **1 of 93** wrong answers already has truth-consistent frame ordering. **Hypothesis:** stronger training consistency helps; mechanically overriding answers from current traces would lower expected accuracy.
3. **Test queried-frame grounding with controlled training pairs.** **Proposed budget, not an estimated optimum:** add **1,800 rows**, 300 in each VSTI family, pairing the same scene and objects at different k where verified relations change; allocate **1,260 of 1,800** to spacing >4 seconds. Use **“Use the camera viewpoint of sampled frame 29 of 32”**, followed by the verified relation. This addresses a plausible cause of the **375 of 900** VSTI errors, but the fixable count is unknown. Do not assert visibility at k when the row only supports geometry from that viewpoint.

At step 400, repeat the census and timestamp tests, the tie-averaged appearance scores, the **76-of-246** unmatched-order rate, and paired VSTI accuracy by spacing and k. The convention repair fails behaviorally if >32/decimal citations persist; it fails as a grounding repair if valid citations increase while pairwise accuracy and controlled frame-switch accuracy do not. Keep counting runaways separately priced and retain their existing removal.

**4. Refuted**

The evidence contradicts the inference that out-of-range or decimal citations are generally sampled-frame timestamps: appearance and VSTI match their own times less often than shuffled times, and base counting decimals match on only **1 of 313** tested fractional values. The prompt’s **100 of 246**, **373 of 900**, and **121 of 150** out-of-range counts are confirmed. The first-wave appearance report’s **0 of 246** decimal traces is also confirmed at both checkpoints.

**5. Not established**

These tests do not reveal which pixels the model attended, whether arbitrary unsampled times explain some numbers, or whether cited objects are visible at the claimed index. Verified visibility annotations and controlled changes of queried k would settle those questions. Step-100 facing/VSTI returns and a fresh population-weighted training sample would settle the missing trend and coverage comparisons. No benchmark items, images, stores, or returns were changed.

**Appendix — CLASSIFIER**

```python
import sys, re, json, random, sqlite3
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
ROOT = "/scratch/jjyeung/orch_n30/"
RX = re.compile(
    r"\bframes?\s*#?\s*\d+(?:\.\d+)?"
    r"(?:(?:\s*[,;–-]\s*|\s+(?:and|to|through)\s+)"
    r"(?:and\s+)?(?:frames?\s*)?\d+(?:\.\d+)?)*", re.I)
def nums(text):
    return [float(v) for m in RX.finditer(text.split("</think>")[0])
            for v in re.findall(r"\d+(?:\.\d+)?", m.group())]
def agree(a, b):
    return sum(a.index(x) < a.index(y)
               for i, x in enumerate(b) for y in b[i+1:])
rows = K.direct("R1", 200, "R0-dev", types=["obj_appearance_order"])
c = Counter()
for r in rows:
    text = r["text"]
    f = {n.strip().lower(): float(v) for n, v in re.findall(
        r"([^:;\n]+?) frame (\d+(?:\.\d+)?)", text.split("Step 2:")[0])}
    m = re.search(r"order them by first appearance:\s*(.*?)(?:\.?(?:\n|</think>))", text)
    w = [x.strip().lower() for x in m.group(1).rstrip(".").split(",")]
    o = [[x.strip().lower() for x in s[3:].rstrip(".").split(",")]
         for s in r["options"]]
    g, p = ord(r["gt"])-65, ord(r["pred"])-65
    assert set(f) == set(w) == set(o[g]) and len(set(f.values())) == 4
    for name, order in [("frames", sorted(f, key=f.get)), ("written", w)]:
        scores = [agree(order, option) for option in o]
        best = [i for i, v in enumerate(scores) if v == max(scores)]
        c[name] += (g in best) / len(best)
    c["actual"] += p == g
    c["frame_pairs"] += agree(sorted(f, key=f.get), o[g])
    c["answer_pairs"] += agree(o[p], o[g])
    c["unmatched"] += w not in o
    c["unmatched_correct"] += w not in o and p == g
print("Appearance", len(rows), dict(c))
for name, rs in [("appearance", rows), ("vsti", K.vsti("R1", 200)),
                 ("away", K.facing("R1", 200, "away"))]:
    s = "R0-dev" if name == "appearance" else name
    tm = K.timing("R1", 200, s)
    z = Counter()
    for typ in sorted({r["type"] for r in rs}):
        group = sorted([r for r in rs if r["type"] == typ], key=lambda r:r["id"])
        for j, r in enumerate(group):
            own = tm[r["id"]]["timestamps_s"]
            other = tm[group[(j+len(group)//2+1)%len(group)]["id"]]["timestamps_s"]
            z["items_above32"] += any(v > 32 for v in nums(r["text"]))
            for v in set(nums(r["text"])):
                if v <= 32: continue
                z["values"] += 1
                z["own_hits"] += min(abs(v-t) for t in own) <= .6
                z["shuffled_hits"] += min(abs(v-t) for t in other) <= .6
    print(name, len(rs), dict(z))
sam = json.load(open(ROOT+"dist_diag/work/q2/STORE_V7_SAMPLES20.json"))
prefixes = ("obj_appearance_order|", "first_seen_frame|", "object_counting|",
            "camera_obj_rel_dist_", "obj_obj_relative_pos_", "object_rel_direction_")
keys = sorted(k for k in sam if k.startswith(prefixes))
rng, ids = random.Random(200), []
for j, k in enumerate(keys):
    ids.extend(v["i"] for v in rng.sample(sam[k], 600//len(keys)+(j<600%len(keys))))
db = sqlite3.connect("file:"+ROOT+"r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro", uri=True)
z = Counter()
for start in range(0, 600, 200):
    part = ids[start:start+200]
    query = "select i,row from rows where i in ("+",".join("?"*len(part))+")"
    for i, raw in db.execute(query, part):
        r = json.loads(raw)
        vs, ts = nums(r["target"]), r["student_input"]["timestamps"]
        z["rows"] += 1
        z["numeric_rows"] += bool(vs)
        z["values"] += len(vs)
        z["invalid"] += sum(not (1 <= v <= 32 and v.is_integer()) for v in vs)
        z["long"] += (ts[-1]-ts[0])/(len(ts)-1) > 4
print("Training", dict(z))
```