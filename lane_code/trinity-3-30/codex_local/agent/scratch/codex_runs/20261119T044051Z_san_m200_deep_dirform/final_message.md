## 1. Question and answer

**1. Does the opening determine the written turn?** All 42 of 202 R0-dev away items that actually omit the turn use a D-style opening. Another 1 of 202 writes “keep that heading” but explicitly reverses both axes; all 159 of 202 “Seen:” items turn correctly.

**2. What do the training rows teach?** In the proportional sample, 1,069 of 1,069 D-style rows are toward questions with keep-heading clauses. Among “Seen:” rows, 557 of 931 ask away/opposite questions; none of those 557 uses D. This supports an opening–operation shortcut, although it does not prove causation.

**3. What accompanies D on R0-dev away items?** Hard questions show the clearest association: D appears on 24 of 71 hard items, versus 14 of 66 easy and 5 of 65 medium items. Vocabulary novelty differs little: at least one name is absent from the training sample on 32 of 43 D items and 112 of 159 “Seen:” items.

**4. Do the rows teach a back prior?** They teach a front-heavy *reference relation*: 455 of 558 toward-hard rows and 111 of 141 away/opposite-hard rows place the target forward. Turning converts the latter into back answers, but R0-dev away-hard truths are even more back-heavy: 61 of 71.

**5. Does dataset, spacing, or vocabulary explain the toward gap?** None of these measured splits eliminates it. Dev-S1 d2 scores 203 of 233, versus R0-dev’s 261 of 376; R0-dev questions with three sampled-training names score 81 of 111, versus dev-S1’s 396 of 450.

**6. What should vehicle N change?** Reword all 93,370 direction rows into one shared skeleton whose explicit question clause selects the turn. This targets 42 of 202 R0-dev away omissions, including 31 wrong answers; fixing the turn alone recovers 21 of those 31.

## 2. Evidence

**Sources.** Paths below share `/scratch/jjyeung/orch_n30/`. Scores and traces come through `san_kit` from `cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl` and `cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched/x/{away,forward}/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Timing comes from `K.timing`. B2048 and ON16k predictions agree on 1,328 of 1,328 direction items; forced closure affects 0 of 1,328.

**Training sources.** I sampled primary keys from `r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite`, using `FAMILY_INDEX_RANGES.json`, family sizes from `dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json`, and exclusions from `r1_ops6/cp/out/records/{n,z}.json`. The census uses 2,000 kept rows; vocabulary uses 3,000 kept rows. Both allocate samples proportionally by family with largest-remainder rounding and seed 200. Population cell counts below are sample-based estimates, not full-store classifications.

**Opening × operation.** “Half turn” includes an explicit equivalent reversal. Each cell uses its set/subtype denominator.

| Set and question clause | D: half turn | D: keep/no turn | Seen: half turn | Seen: keep/no turn |
|---|---:|---:|---:|---:|
| R0-dev away | 1 of 202 | 42 of 202 | 159 of 202 | 0 of 202 |
| Away twins | 0 of 150 | 0 of 150 | 150 of 150 | 0 of 150 |
| R0-dev toward | 0 of 376 | 331 of 376 | 0 of 376 | 45 of 376 |
| Dev-S1 toward | 0 of 450 | 450 of 450 | 0 of 450 | 0 of 450 |
| Forward twins | 0 of 150 | 66 of 150 | 0 of 150 | 84 of 150 |

The exceptional D item, `9a6a1be636043e0590aefd7e`, says “keep that heading but flip forward to backward,” explicitly swaps both axes, and answers correctly. Thus keep-phrase presence is 43 of 202, but actual omission is 42 of 202. Toward questions execute an unwanted half turn on 0 of 976 items.

**Family census.** Each family is `object_rel_direction_{level}|pool|retrace`. Below, `w1g` has retrace `rows_rebuild_d0_v1`; every other pool has retrace `None`. `ARKIT/T0/T1H1/T1H2` expand to `rows_rebuild_d0_{name}_gaps` for easy and `rows_rebuild_d0_{name}_gen_r2` otherwise. “Opp” means `r1_away_opp`. Every sampled toward row writes keep/no turn; every sampled away/opposite row writes a half turn.

| Level / pool | Kept population | Toward sample | Away/opposite sample | Opening |
|---|---:|---:|---:|---|
| Easy / w1g | 12,969 of 93,370 | 278 of 278 | 0 of 278 | D |
| Easy / ARKIT | 2,842 of 93,370 | 30 of 61 | 31 of 61 away | Seen |
| Easy / T0 | 6,428 of 93,370 | 61 of 138 | 77 of 138 away | Seen |
| Easy / T1H1 | 3,012 of 93,370 | 38 of 64 | 26 of 64 away | Seen |
| Easy / T1H2 | 2,742 of 93,370 | 23 of 59 | 36 of 59 away | Seen |
| Easy / Opp | 3,664 of 93,370 | 0 of 78 | 78 of 78 opposite | Seen |
| Medium / w1g | 15,547 of 93,370 | 333 of 333 | 0 of 333 | D |
| Medium / ARKIT | 2,074 of 93,370 | 20 of 44 | 24 of 44 away | Seen |
| Medium / T0 | 4,582 of 93,370 | 52 of 98 | 46 of 98 away | Seen |
| Medium / T1H1 | 2,258 of 93,370 | 27 of 48 | 21 of 48 away | Seen |
| Medium / T1H2 | 1,998 of 93,370 | 23 of 43 | 20 of 43 away | Seen |
| Medium / Opp | 2,665 of 93,370 | 0 of 57 | 57 of 57 opposite | Seen |
| Hard / w1g | 21,385 of 93,370 | 458 of 458 | 0 of 458 | D |
| Hard / ARKIT | 2,320 of 93,370 | 24 of 50 | 26 of 50 away | Seen |
| Hard / T0 | 3,294 of 93,370 | 39 of 71 | 32 of 71 away | Seen |
| Hard / T1H1 | 1,774 of 93,370 | 19 of 38 | 19 of 38 away | Seen |
| Hard / T1H2 | 1,634 of 93,370 | 18 of 35 | 17 of 35 away | Seen |
| Hard / Opp | 2,182 of 93,370 | 0 of 47 | 47 of 47 opposite | Seen |

Therefore, **P(keep | D) = 1,069 of 1,069**. **P(away/opposite | Seen) = 557 of 931**; excluding opposite wording, plain away questions account for 375 of 931. Away/opposite questions with D occur on 0 of 2,000 sampled rows.

| Estimated population cell | Toward question | Away question | Opposite question |
|---|---:|---:|---:|
| D opening | 49,901 of 93,370 | 0 of 93,370 | 0 of 93,370 |
| Seen opening | ≈17,459 of 93,370 | ≈17,499 of 93,370 | 8,511 of 93,370 |

**What distinguishes the 43 D items from the 159 Seen items?** D scores 12 of 43; Seen scores 115 of 159. Their objects include familiar and unfamiliar names: all three names occur in the vocabulary sample on 11 of 43 D items and 47 of 159 Seen items. Names such as “toilet brush” and “door frame” occur in both groups.

Question wording is identical within level on 202 of 202 R0-dev away items. D and Seen also coexist in 25 of 92 rooms: those shared rooms contain 35 of 43 D items and 49 of 159 Seen items. Thus neither wording nor room identity deterministically selects D. Hardness is associated with D, but scene appearance, object difficulty, and template selection remain confounded.

**Training relation and answer distributions.** Hard vectors are ordered **front-left, front-right, behind/back-left, behind/back-right**. Medium reference vectors are **ahead, out, behind**; medium answer vectors are **left, right, back**.

| Level / question | Stated reference relation | Resulting answer |
|---|---|---|
| Hard / toward | 227 of 558; 228 of 558; 50 of 558; 53 of 558 | 227 of 558; 228 of 558; 50 of 558; 53 of 558 |
| Hard / away | 48 of 94; 28 of 94; 6 of 94; 12 of 94 | 12 of 94; 6 of 94; 28 of 94; 48 of 94 |
| Hard / opposite | 16 of 47; 19 of 47; 4 of 47; 8 of 47 | 8 of 47; 4 of 47; 19 of 47; 16 of 47 |
| Medium / toward | 192 of 455; 240 of 455; 23 of 455 | 230 of 455; 202 of 455; 23 of 455 |
| Medium / away | 49 of 111; 60 of 111; 2 of 111 | 34 of 111; 28 of 111; 49 of 111 |
| Medium / opposite | 24 of 57; 31 of 57; 2 of 57 | 13 of 57; 20 of 57; 24 of 57 |

Easy reference-left counts are 248 of 430 toward, 92 of 170 away, and 34 of 78 opposite; reference-right counts are 182 of 430, 78 of 170, and 44 of 78. Answer-left counts are respectively 248 of 430, 78 of 170, and 44 of 78; answer-right counts are 182 of 430, 92 of 170, and 34 of 78.

R0-dev hard truths, in the hard order above, are **44 of 121; 54 of 121; 12 of 121; 11 of 121** toward and **5 of 71; 5 of 71; 31 of 71; 30 of 71** away. Medium truths, in left/right/back order, are **62 of 129; 50 of 129; 17 of 129** toward and **7 of 65; 19 of 65; 39 of 65** away.

Away-hard twins predict back on 40 of 50 against 33 of 50 truths, consistent with the training sample’s 111 of 141 back answers. However, R0-dev away-hard predicts back on only 46 of 71 against 61 of 71 truths. A universal excess-back explanation is therefore wrong.

**Toward accuracy by dataset.** R0-dev room identifiers lack dataset prefixes. Its timing metadata reports 60 fps on 376 of 376 toward items, matching dev-S1 d2’s signature; this is evidence of resemblance, not verified dataset identity.

| Set / dataset | Easy | Medium | Hard | All |
|---|---:|---:|---:|---:|
| Dev-S1 / d1 | 35 of 37 | 21 of 23 | 26 of 28 | 82 of 88 |
| Dev-S1 / d2 | 67 of 72 | 76 of 87 | 60 of 74 | 203 of 233 |
| Dev-S1 / d3 | 38 of 41 | 35 of 40 | 38 of 48 | 111 of 129 |
| R0-dev / unresolved | 98 of 126 | 88 of 129 | 75 of 121 | 261 of 376 |

**Toward accuracy by `K.timing.spacing_s`.** Intervals include the lower bound and exclude the upper bound. Each three-part cell gives easy; medium; hard.

| Sampled-frame spacing | Dev-S1 | R0-dev | Dev-S1 d2, all levels |
|---|---|---|---:|
| 1–2 seconds | 19 of 21; 12 of 15; 12 of 17 | 2 of 2; 2 of 2; 1 of 1 | 0 of 0 |
| 2–4 seconds | 50 of 51; 35 of 39; 43 of 48 | 31 of 42; 28 of 45; 29 of 44 | 25 of 27 |
| 4–8 seconds | 54 of 61; 70 of 79; 61 of 76 | 54 of 69; 48 of 64; 39 of 63 | 142 of 167 |
| At least 8 seconds | 17 of 17; 15 of 17; 8 of 9 | 11 of 13; 10 of 18; 6 of 13 | 36 of 39 |

**Toward accuracy by vocabulary coverage.** The training sample contains 389 distinct object names. Matching ignores case but preserves the complete name; all extracted names were checked against their questions. “Absent” means absent from this sample, not necessarily from all training.

| Level | Dev-S1: all three present | R0-dev: all three present | R0-dev: at least one absent |
|---|---:|---:|---:|
| Easy | 140 of 150 | 28 of 37 | 70 of 89 |
| Medium | 132 of 150 | 30 of 36 | 58 of 93 |
| Hard | 124 of 150 | 23 of 38 | 52 of 83 |
| All | 396 of 450 | 81 of 111 | 180 of 265 |

The hard gap also survives truth-sector conditioning: front truths score 100 of 110 on dev-S1 versus 71 of 98 on R0-dev; back truths score 24 of 40 versus 4 of 23. Different answer proportions alone cannot explain it.

## 3. What this changes for vehicle N

1. **Reword all 93,370 direction rows across the 18 listed families.** Give toward, away, and opposite questions identical opening and reference-relation syntax; quote the question’s heading clause before selecting the operation. This changes the 49,901 `w1g` rows and the 43,469 remaining rows together. It targets 42 of 202 omitted turns, costing 31 of 202 answers, or 15.35 percentage points. A turn-only counterfactual fixes 21 of 31 errors—5 of 5 easy, 2 of 5 medium, and 14 of 21 hard—but breaks 11 currently correct omission items. Consequently, 21 recoverable errors are not a predicted training gain. The change fails if omissions persist on R0-dev or unwanted turns appear on toward items.
2. **Add a proposed 2,400 hard rows: 600 to each hard ARKIT/T0/T1H1/T1H2 family.** This budget is a guess. Use 300 matched toward/away pairs per family, balanced over verified reference quadrants, with identical evidence across each pair. This targets relation errors beyond turning, including 26 of 150 dev-S1 hard errors and 46 of 121 R0-dev toward-hard errors. The change fails if clause compliance improves while those relation errors remain.
3. **Add a proposed 1,600 medium rows: 400 to each medium ARKIT/T0/T1H1/T1H2 family.** This budget and its benefit are guesses. Use matched pairs covering ahead/out/behind and both sides, preserving the same reference band across twins. Relevant failures include 18 of 150 dev-S1 medium items and 41 of 129 R0-dev toward-medium items. The change fails if correct band-to-answer transformations continue to operate on incorrect visual bands.

The following hard examples specify the shared skeleton. They are illustrative, not claims about inspected frames. Options are A: front-left, B: front-right, C: back-left, D: back-right; production frame citations and relations must come from verified row evidence.

```text
Toward:
<think>
Seen: chair in frame 4; table in frame 12; lamp in frame 20.
Reference heading: standing at the chair and facing the table, the lamp is in front of me, on my left.
Question clause: “facing the table.” This keeps the reference heading, so front-left stays front-left.
The lamp is at my front-left.
</think>
A

Away:
<think>
Seen: chair in frame 4; table in frame 12; lamp in frame 20.
Reference heading: standing at the chair and facing the table, the lamp is in front of me, on my left.
Question clause: “facing away from the table.” This requires a half turn: front becomes back and left becomes right.
The lamp is at my back-right.
</think>
D
```

For opposite wording, quote that clause and use the same half-turn operation. Easy rows retain only side; medium rows retain band and side before applying the clause.

## 4. Refuted

- **“43 items omit the turn” is incorrect.** The keep phrase appears on 43 of 202, but 1 of those 43 explicitly reverses both axes correctly. Actual omissions number 42 of 202; their wrong answers still number 31 of 202.
- **“Away errors generally reflect excessive back answers” is incorrect.** It describes the away-hard twins’ 40 of 50 predictions against 33 of 50 truths, but reverses on R0-dev: 46 of 71 predictions against 61 of 71 truths.

## 5. Not established

The opening association does not establish why the model chooses D on a particular image. Matched-scene paraphrases and a controlled shared-skeleton training comparison would isolate wording and template effects. RGB/geometry audits would distinguish recognition, spatial reconstruction, and label errors. A room-to-source mapping would establish R0-dev’s dataset identity; a complete training-name inventory would establish true vocabulary novelty. None of these analyses predicts the gain from the proposed row budgets.

## Appendix — CLASSIFIER

```python
import sys, json, re, random, sqlite3
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
R = "/scratch/jjyeung/orch_n30/"
T = ["object_rel_direction_" + x for x in ("easy", "medium", "hard")]
def opening(t):
    t = re.sub(r"^\s*<think>\s*", "", t).lstrip()
    return "D" if t.startswith("Step 1") else "Seen" if t.startswith("Seen:") else "other"
def clause(t):
    h = bool(re.search(r"half.turn|flip forward to backward|180", t, re.I))
    k = bool(re.search(r"keep that heading|no turn applies", t, re.I))
    return "both" if h and k else "half" if h else "keep" if k else "other"
def heading(q):
    return "O" if "opposite" in q.lower() else "A" if re.search(r"away from|back to", q, re.I) else "T"
dev = {s: K.direct("R1", 200, s, types=T) for s in ("dev-S1", "R0-dev")}
dev.update({s: K.facing("R1", 200, s) for s in ("away", "forward")})
for s, rows in dev.items():
    for h in ("T", "A"):
        rr = [r for r in rows if ("T" if heading(r["question"]) == "T" else "A") == h]
        if rr: print(s, h, len(rr), Counter((opening(r["text"]), clause(r["text"])) for r in rr))
C = json.load(open(R + "dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json"))["families"]
C = {f: v["kept_nz"] for f, v in C.items() if f.split("|")[0] in T}
G = json.load(open(R + "r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json"))["families"]
excluded = set()
for tag in ("n", "z"):
    for line in open(R + "r1_ops6/cp/out/records/" + tag + ".json"):
        if line.strip(): excluded.add(json.loads(line)["row_key"])
def quota(n):
    a = {f: n * v / sum(C.values()) for f, v in C.items()}
    b = {f: int(v) for f, v in a.items()}
    for f in sorted(a, key=lambda f: (-(a[f] - b[f]), f))[:n - sum(b.values())]: b[f] += 1
    return b
q2, q3 = quota(2000), quota(3000)
ids = [i for t in T for a, b in G[t] for i in range(a, b + 1)]
random.Random(200).shuffle(ids)
db = sqlite3.connect("file:" + R + "r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro", uri=True)
sample = defaultdict(list)
for p in range(0, 6000, 200):
    batch = ids[p:p + 200]
    got = dict(db.execute("select i,row from rows where i in (" + ",".join("?" * len(batch)) + ")", batch))
    for i in batch:
        r = json.loads(got[i]); rt = r.get("retrace")
        rule = rt.get("rule") if isinstance(rt, dict) else rt
        f = "|".join((r["question_type"], r["pool"], str(rule)))
        if r["qid"] not in excluded and f in q3 and len(sample[f]) < q3[f]: sample[f].append(r)
    if all(len(sample[f]) == q3[f] for f in C): break
assert sum(map(len, sample.values())) == 3000
small = [r for f in C for r in sample[f][:q2[f]]]
D = [r for r in small if opening(r["target"]) == "D"]
S = [r for r in small if opening(r["target"]) == "Seen"]
print("D keep", sum(clause(r["target"]) == "keep" for r in D), "of", len(D))
print("Seen questions", Counter(heading(r["student_input"]["question"]) for r in S), "of", len(S))
print("Away D", sum(heading(r["student_input"]["question"]) != "T" for r in D), "of", len(D))
for h in ("T", "A", "O"):
    rr = [r for r in small if r["question_type"].endswith("hard") and heading(r["student_input"]["question"]) == h]
    front = sum("in front of me" in r["target"].split("The question")[0] for r in rr)
    print("Hard forward-front", h, front, "of", len(rr))
```