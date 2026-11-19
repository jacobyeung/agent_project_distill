**1. Question and answer**

1. **Can the removed lists become tallies?** All **3,000 of 3,000** sampled rows convert, and every sum equals the stored answer. Region tags occur in **1,646 of 3,000** rows.
2. **How many rows could vehicle N recover?** Family-weighted extrapolation estimates **17,879 convertible rows**: approximately **8,769 single-category** and **9,110 multiple-category** rows. These are estimates from the sample, not a conversion census.
3. **Does the tally invent information or violate the frame convention?** It groups supplied instance citations and computes their counts; **3,000 of 3,000** sampled rows cite only integer frames 1–32 and contain 32 sampled frames. The ruling nevertheless needs an explicit amendment because it currently requires one Locate line per instance.
4. **Can these sources supply relative-count rows?** Yes: **955 of 1,153** sampled scenes contain at least two counted categories with different totals. Their rows use matching sampled clips, with no conflicting category totals.
5. **Would tallies repair the dev traces?** Literal tally sums already match the answer on **352 of 354** completed, fully framed numeric inventories. Truncating runaways before the first repeated frame gives the true count on only **3 of 77** eligible numeric items.
6. **Can this form guarantee termination, and what should N gate on?** A valid tally is bounded, but training wording cannot constrain an unconstrained decoder. Gate on forced closes, increasing integer frame indices, complete category coverage, arithmetic, and answer agreement; current forced-close baselines are **28 of 150**, **83 of 385**, and **65 of 139** items.

**2. Evidence**

I shuffled the 20,669 counting primary keys with seed 200, fetched batches of at most 200 keys, and retained the first 3,000 qids carrying `count_diag_first_seen_list_form` in `z.json`. This fetched 3,600 rows; **0 of 3,000** sampled qids also occur in `n.json`. All analysis ran read-only on `trinity-3-30`.

Training sources were [rows.sqlite](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite), [FAMILY_INDEX_RANGES.json](/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json), [z.json](/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json), [n.json](/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json), and [STORE_V7_TEMPLATE_COUNTS.json](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json). Below, `n/N` means “n of N.”

| Bin | Category–frame entries per row | Largest multiplicity within one category/frame | Sum, equal to stored truth |
|---|---:|---:|---:|
| 1 | 358/3,000 | 1,351/3,000 | 1/3,000 |
| 2 | 849/3,000 | 1,076/3,000 | 890/3,000 |
| 3 | 551/3,000 | 327/3,000 | 429/3,000 |
| 4 | 531/3,000 | 128/3,000 | 594/3,000 |
| 5–8 | 637/3,000 | 99/3,000 | 776/3,000 |
| 9+ | 74/3,000 | 19/3,000 | 310/3,000 |

The largest observed row has 15 category–frame entries; the largest per-frame multiplicity is 17. **1,649 of 3,000** original rows repeat a frame consecutively within a category. Conversion preserves multiplicity rather than treating repeated frames as duplicate objects.

All families below have question type `object_counting`. Removed population counts come from `kept_n − kept_nz`; their sum matches the **17,879 of 17,879** relevant `z.json` qids.

| Pool | Existing retrace rule | Removed / family rows | Converted / sampled |
|---|---|---:|---:|
| `b12_cntapp_gt_v1` | `None` | 10,004/10,177 | 1,646/1,646 |
| `r1g` | `rows_rebuild_d0_v1` | 6,636/9,253 | 1,164/1,164 |
| `rows_rebuild_d0_ARKIT_gaps` | `None` | 363/363 | 60/60 |
| `rows_rebuild_d0_T0_gaps` | `None` | 290/290 | 42/42 |
| `rows_rebuild_d0_T1H1_gaps` | `None` | 307/307 | 47/47 |
| `rows_rebuild_d0_T1H2_gaps` | `None` | 279/279 | 41/41 |

Each sampled row receives its family’s removed-population/sample weight. Estimated stocks below are rounded; the truth-1 estimate rests on only **1 of 1,515** single-category samples and is particularly uncertain.

| Truth | Single-category sample | Estimated single stock, of ≈8,769 | Multiple-category sample | Estimated multiple stock, of ≈9,110 |
|---|---:|---:|---:|---:|
| 1 | 1/1,515 | ≈6 | 0/1,485 | ≈0 |
| 2 | 890/1,515 | ≈5,156 | 0/1,485 | ≈0 |
| 3 | 273/1,515 | ≈1,575 | 156/1,485 | ≈948 |
| 4 | 140/1,515 | ≈808 | 454/1,485 | ≈2,759 |
| 5–8 | 157/1,515 | ≈912 | 619/1,485 | ≈3,802 |
| 9+ | 54/1,515 | ≈312 | 256/1,485 | ≈1,601 |

These are training-row counts, including paraphrases: **2,881 of 3,000** samples have distinct scene/category/frame-list content.

The [trace ruling](/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md), Answer and counting sections, allows frame indices, instance counts, and explicit arithmetic. Structured provenance independently matches the converted lists on **1,836 of 1,836** rows: 1,485 category-list rows and 351 individual-instance rows. The other **1,164 of 3,000** rows supply the inventory through their existing trace, with provenance naming the frame-number conversion; their upstream annotations were not opened. All **14,112 of 14,112** instance citations fall within 1–32. This establishes the convention in the sample, not throughout the unsampled population.

**Twelve converted examples.** Each JSON line preserves the question and complete old target verbatim after decoding `\n`; `new` is the exact proposed replacement. The examples cover every observed truth bin and both question forms.
```json
{"i":142693,"question":"How many office chair(s) do we have in this room?","old":"<think>\nStep 1: list each distinct office chair once, by the frame where it first appears: frame 1.\nSo there are 1 in all.\n</think>\n\n1","new":"<think>\nStep 1: new office chair by first-seen frame: frame 1: 1.\nStep 2: 1 = 1.\n</think>\n\n1"}
{"i":86893,"question":"How many cup(s) are there in the room shown in the video?","old":"<think>\nStep 1: locate each distinct cup at its first appearance: frame 6; frame 6.\nSo the count is 2.\n</think>\n\n2","new":"<think>\nStep 1: new cup by first-seen frame: frame 6: 2.\nStep 2: 2 = 2.\n</think>\n\n2"}
{"i":91968,"question":"How many pc(s) are there in the room shown in the video?","old":"<think>\nStep 1: locate each distinct pc at its first appearance: frame 1; frame 3; frame 7.\nSo the count is 3.\n</think>\n\n3","new":"<think>\nStep 1: new pc by first-seen frame: frame 1: 1; frame 3: 1; frame 7: 1.\nStep 2: 1 + 1 + 1 = 3.\n</think>\n\n3"}
{"i":51395,"question":"How many box(s) do we have in this room?","old":"<think>\nStep 1: locate each distinct box at its first appearance: frame 1; frame 1; frame 5; frame 12.\nSo the count is 4.\n</think>\n\n4","new":"<think>\nStep 1: new box by first-seen frame: frame 1: 2; frame 5: 1; frame 12: 1.\nStep 2: 2 + 1 + 1 = 4.\n</think>\n\n4"}
{"i":40477,"question":"How many bottle(s) do we have in this room?","old":"<think>\nStep 1: locate each distinct bottle at its first appearance: frame 3; frame 5; frame 8; frame 9; frame 11.\nSo the count is 5.\n</think>\n\n5","new":"<think>\nStep 1: new bottle by first-seen frame: frame 3: 1; frame 5: 1; frame 8: 1; frame 9: 1; frame 11: 1.\nStep 2: 1 + 1 + 1 + 1 + 1 = 5.\n</think>\n\n5"}
{"i":48030,"question":"How many towel(s) do we have in this room?","old":"<think>\nStep 1: locate each distinct towel at its first appearance: frame 1; frame 1; frame 2; frame 2; frame 3; frame 3; frame 3; frame 3; frame 12.\nSo there are 9 in all.\n</think>\n\n9","new":"<think>\nStep 1: new towel by first-seen frame: frame 1: 2; frame 2: 2; frame 3: 4; frame 12: 1.\nStep 2: 2 + 2 + 4 + 1 = 9.\n</think>\n\n9"}
{"i":172580,"question":"Count the sofa(s) and tv(s) in this room together. How many are there in total?","old":"<think>\nStep 1: locate each distinct sofa at its first appearance: frame 1 (right); frame 1 (right).\nStep 2: locate each distinct tv at its first appearance: frame 5 (left).\nStep 3: add them: 2 + 1 = 3.\nSo there are 3 in total.\n</think>\n\n3","new":"<think>\nStep 1: new sofa by first-seen frame: frame 1: 2.\nStep 2: new tv by first-seen frame: frame 5: 1.\nStep 3: category counts: sofa: 2 = 2; tv: 1 = 1.\nStep 4: total: 2 + 1 = 3.\n</think>\n\n3"}
{"i":171713,"question":"Count the chair(s) and tv(s) in this room together. How many are there in total?","old":"<think>\nStep 1: locate each distinct chair at its first appearance: frame 1 (right).\nStep 2: locate each distinct tv at its first appearance: frame 1 (middle); frame 1 (right); frame 6 (left).\nStep 3: add them: 1 + 3 = 4.\nSo there are 4 in total.\n</think>\n\n4","new":"<think>\nStep 1: new chair by first-seen frame: frame 1: 1.\nStep 2: new tv by first-seen frame: frame 1: 2; frame 6: 1.\nStep 3: category counts: chair: 1 = 1; tv: 2 + 1 = 3.\nStep 4: total: 1 + 3 = 4.\n</think>\n\n4"}
{"i":141533,"question":"What is the total number of door(s) and heater(s) in this room?","old":"<think>\nStep 1: locate each distinct door at its first appearance: frame 4; frame 6; frame 22.\nStep 2: find each distinct heater, using its first-seen frame: frame 2; frame 3; frame 17.\nStep 3: add them: 3 + 3 = 6.\nSo there are 6 in total.\n</think>\n\n6","new":"<think>\nStep 1: new door by first-seen frame: frame 4: 1; frame 6: 1; frame 22: 1.\nStep 2: new heater by first-seen frame: frame 2: 1; frame 3: 1; frame 17: 1.\nStep 3: category counts: door: 1 + 1 + 1 = 3; heater: 1 + 1 + 1 = 3.\nStep 4: total: 3 + 3 = 6.\n</think>\n\n6"}
{"i":141911,"question":"Count the chair(s) and table(s) in this room together. How many are there in total?","old":"<think>\nStep 1: locate each distinct chair at its first appearance: frame 1; frame 1; frame 1; frame 8; frame 9; frame 9.\nStep 2: locate each distinct table at its first appearance: frame 1; frame 3; frame 12.\nStep 3: add them: 6 + 3 = 9.\nSo there are 9 in total.\n</think>\n\n9","new":"<think>\nStep 1: new chair by first-seen frame: frame 1: 3; frame 8: 1; frame 9: 2.\nStep 2: new table by first-seen frame: frame 1: 1; frame 3: 1; frame 12: 1.\nStep 3: category counts: chair: 3 + 1 + 2 = 6; table: 1 + 1 + 1 = 3.\nStep 4: total: 6 + 3 = 9.\n</think>\n\n9"}
{"i":164502,"question":"How many table(s) are there in this room?","old":"<think>\nStep 1: list the distinct table instances by first appearance: frame 2 (left); frame 12 (left); frame 17 (left); frame 25 (left); frame 25 (left).\nSo the count is 5.\n</think>\n\n5","new":"<think>\nStep 1: new table by first-seen frame: frame 2: 1; frame 12: 1; frame 17: 1; frame 25: 2.\nStep 2: 1 + 1 + 1 + 2 = 5.\n</think>\n\n5"}
{"i":172334,"question":"What is the total number of stool(s) and table(s) in this room?","old":"<think>\nStep 1: locate each distinct stool at its first appearance: frame 4 (middle); frame 9 (left).\nStep 2: locate each distinct table at its first appearance: frame 1 (left); frame 4 (left); frame 8 (left).\nStep 3: add them: 2 + 3 = 5.\nSo there are 5 in total.\n</think>\n\n5","new":"<think>\nStep 1: new stool by first-seen frame: frame 4: 1; frame 9: 1.\nStep 2: new table by first-seen frame: frame 1: 1; frame 4: 1; frame 8: 1.\nStep 3: category counts: stool: 1 + 1 = 2; table: 1 + 1 + 1 = 3.\nStep 4: total: 2 + 3 = 5.\n</think>\n\n5"}
```

**Relative-count construction.** The 955 eligible scenes supply **8,213 unequal and 3,027 equal pairs out of 11,240 unordered category pairs**. These are available constructions from sampled annotations, not independent scenes or a prescribed training dose. Scene and ordered frame-hash joins agree on **1,153 of 1,153** sampled scene groups; category totals conflict in **0 of 1,153**.

The following four proposed rows all derive from sampled primary key `169738`, qid `b12ct_8c095456591a6e7cff4d3f53`, scene `d2/v95b193bc646a`, canonical scene `scannetppv2/b119249da7`. Its source supplies cloth `[17]`, door `[11,14]`, and rug `[4]`.
```text
Q: Are there more doors, fewer doors, or the same number as cloths? Options: A. fewer; B. equal number; C. more.
Target: <think>Step 1: new door by first-seen frame: frame 11: 1; frame 14: 1. Step 2: new cloth by first-seen frame: frame 17: 1. Step 3: door: 1 + 1 = 2; cloth: 1 = 1. Step 4: 2 > 1, so there are more doors. The option is C.</think> C
Q: Are there more cloths, fewer cloths, or the same number as doors? Options: A. fewer; B. more; C. equal number.
Target: <think>Step 1: new cloth by first-seen frame: frame 17: 1. Step 2: new door by first-seen frame: frame 11: 1; frame 14: 1. Step 3: cloth: 1 = 1; door: 1 + 1 = 2. Step 4: 1 < 2, so there are fewer cloths. The option is A.</think> A
Q: Are there more cloths, fewer cloths, or the same number as rugs? Options: A. more; B. equal number; C. fewer.
Target: <think>Step 1: new cloth by first-seen frame: frame 17: 1. Step 2: new rug by first-seen frame: frame 4: 1. Step 3: cloth: 1 = 1; rug: 1 = 1. Step 4: 1 = 1, so the counts are equal. The option is B.</think> B
Q: Are there more doors, fewer doors, or the same number as rugs? Options: A. equal number; B. more; C. fewer.
Target: <think>Step 1: new door by first-seen frame: frame 11: 1; frame 14: 1. Step 2: new rug by first-seen frame: frame 4: 1. Step 3: door: 1 + 1 = 2; rug: 1 = 1. Step 4: 2 > 1, so there are more doors. The option is B.</think> B
```

**Dev behavior.** `san_kit` read step-200 files under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Text is ON16k; scores and forced-close flags are B2048. Answers agree across arms on **354 of 354** completed, fully framed numeric inventories. The [first-wave counting report](/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T041129Z_san_m200_count/final_message.md) supplies the prior diagnosis; the following counts were checked in memory.

| Set/type | Fully framed / non-runaway | Literal tally agrees with answer | Valid integer frames 1–32 | Forced closes / all items | Runaway loss, type points |
|---|---:|---:|---:|---:|---:|
| dev-S1 counting | 107/122 | 107/107 | 73/107 | 28/150 | 17.87, 150 items |
| R0-dev counting | 247/302 | 245/247 | 168/247 | 83/385 | 19.53, 385 items |
| dev-S1 relative count | 33/74 | 32/33 comparisons | 27/33 | 65/139 | 11.51, 139 items |

Numeric lists omit frames on **64 of 418** inventory-bearing non-runaways; another **6 of 424** non-runaways provide no inventory. A frame tally cannot reconstruct those missing citations without adding information.

The two numeric exceptions require care. In `ef56c8255e82c98f1be043c0`, treating “2 in frame 23” as multiplicity makes the sum agree. In `4f6900b92e1ccf0eeb5b9db8`, “2 in frame 26; 2 in frame 26” plus “2 in frame 8” yields 6 under that interpretation, while the model adds `2 + 2 = 4`; truth is 6. Thus multiplicity interpretation gives agreement on **353 of 354**, leaving **1 of 354** ambiguous or inconsistent.

| Runaway group | Complete framed prefixes / runaways | Prefix equals truth | Prefix has valid sampled-frame indices |
|---|---:|---:|---:|
| dev-S1 counting | 19/28 | 1/19 | 15/19 |
| R0-dev counting | 58/83 | 2/58 | 51/58 |
| dev-S1 relative count | 7/65 | 1/7 comparisons | 3/7 |

A prefix stops before the first repeated frame separately within each requested category. Numeric prefixes undercount on **74 of 77** eligible items; **0 of 77** overcount. Requiring valid sampled-frame indices leaves only **2 of 66** exact numeric prefixes. Relative-count prefix substitution would reduce correct answers from **5 of 7** to **1 of 7** eligible items.

Tally consistency cannot repair an incomplete inventory. Among non-runaways with truth ≥3, answers undercount on **26 of 46** dev-S1 items and **70 of 113** R0-dev items, costing respectively **11.00 points over 150 items** and **12.36 points over 385 items**. Across both sets, B2048 MRA is **73.98 with 289 truth-2 items**, **45.14 with 105 truth-3 items**, **33.75 with 48 truth-4 items**, and **15.05 with 93 truth-≥5 items**.

**3. What this changes for vehicle N, ranked**

1. **Replace the removed list targets with tallies in the six source families above**, recording a proposed retrace rule `count_tally_v1`. There are **3,000 of 3,000 audited replacements**, with an estimated full stock of 17,879. Use the exact wording illustrated above; preserve optional region information as per-frame region counts where supplied. This targets **176 of 674 force-closed dev items**, of which **121 of 176** lose credit. **Hypothesis:** removing repeated training entries reduces runaways; those counts are exposure, not predicted recovery.
2. **Add `relative_count|vehicle_N_train|count_tally_compare_v1`**, using the 11,240 sampled category pairs, subject to training-split and duplicate checks. Balance comparisons and option letters. Literal comparison would correct **1 of 33** fully framed completed comparisons, worth **0.72 points over 139 items**; broader inventory improvements remain a hypothesis. Fail the consistency gate if either category is missing or the comparison/letter contradicts the sums.
3. **Give larger inventories explicit supervision.** The convertible sample contains **2,109 of 3,000** rows with truth ≥3. **Hypothesis:** increasing their training share could address the **96 of 159** non-runaway high-truth undercounts. Reformatting alone preserves those erroneous model inventories, so judge this change by truth-stratified MRA and undercount rates, not shorter traces. The retained 2,617 counting rows need source inventories before they can receive the same treatment.

At N’s first read, require zero malformed tallies and separately report forced closes, missing categories, repeated/decreasing/out-of-range frames, sum/answer mismatches, and truth-stratified scores. A loop could repeat a frame, cycle through frames, exceed frame 32, or restart a category; B2048 would expose long versions through `forced_close=true` and `think_tokens=2048`, but a completed wrong tally requires the structural checks.

**Hypothesis—transfer risk:** appearance order and relative distance are the closest neighboring forms because they already locate categories by frame; size, room-size, and direction traces could also copy the opening. Inspect non-counting uses of “new … by first-seen frame,” and protect routed-call coverage. No tally-transfer effect was measured here.

**4. Refuted**

“Cannot loop” is not established by a training template. Strict frame order bounds a valid tally to 32 entries **per category**; **1,485 of 3,000** sampled questions require multiple categories, so the whole-row bound is larger unless all categories share one frame ledger. A hard termination guarantee requires enforced generation structure.

“The sum should match” is not universally true: literal sums disagree on **2 of 354** completed numeric frame inventories. The first-wave report already identified both exceptions; this analysis narrows one to a clear multiplicity reading and leaves the other ambiguous.

**5. Not established**

The sample does not establish conversion success for every unsampled row, correctness of the upstream first-seen annotations, or improved model accuracy after tally training. A full bounded conversion pass, source-annotation checks, and a controlled N dev read would settle those questions. Frame grouping also removes region cues unless they are retained; those cues occur in **1,646 of 3,000** source rows. No files were changed.

**Appendix — CLASSIFIER**
```python
import sys, json, sqlite3, random, re, collections
sys.dont_write_bytecode = True
B = "/scratch/jjyeung/orch_n30"
sys.path.insert(0, B + "/swarm_an/kit")
import san_kit as K
R = B + "/r1_ops6/store/a2_vqa_v7"
ranges = json.load(open(R + "/FAMILY_INDEX_RANGES.json"))["families"]
ids = [i for a,b in ranges["object_counting"] for i in range(a,b+1)]
z = set()
for line in open(B + "/r1_ops6/cp/out/records/z.json"):
    r = json.loads(line)
    if r["reason"] == "count_diag_first_seen_list_form": z.add(r["row_key"])
random.Random(200).shuffle(ids)
db = sqlite3.connect("file:" + R + "/vqa/rows.sqlite?mode=ro", uri=True)
sample = []
for j in range(0, len(ids), 200):
    batch = ids[j:j+200]
    sql = "select i,row from rows where i in (" + ",".join("?"*len(batch)) + ")"
    got = {i:json.loads(s) for i,s in db.execute(sql,batch)}
    for i in batch:
        if got[i]["qid"] in z: sample.append((i,got[i]))
        if len(sample) == 3000: break
    if len(sample) == 3000: break
pat = r"(?:list each distinct (.*?) once,|find each distinct (.*?), using|locate each distinct (.*?) at its|list the distinct (.*?) instances by)"
good = []; scenes = collections.defaultdict(lambda: collections.defaultdict(set))
for i,r in sample:
    inv = []; ok = True
    for line in r["target"].splitlines():
        if not line.startswith("Step ") or "add them:" in line: continue
        _, desc, body = line.split(":",2)
        m = re.search(pat,desc); name = next(x for x in m.groups() if x is not None)
        entries = [x.strip().rstrip(".") for x in body.strip().split(";")]
        ms = [re.fullmatch(r"frame (\d+)(?: \([^()]+\))?",x) for x in entries]
        if not all(ms): ok = False; break
        inv.append((name,[int(m.group(1)) for m in ms]))
    if not ok or sum(len(fs) for _,fs in inv) != int(r["answer"]): continue
    good.append((i,r,inv))
    key = (r["dataset"],r["scene"],tuple(f.get("sha256",f.get("path")) for f in r["student_input"]["frames"]))
    for name,fs in inv: scenes[key][name].add(len(fs))
eligible = sum(len(d)>=2 and all(len(v)==1 for v in d.values()) and len(set.union(*d.values()))>=2 for d in scenes.values())
print("converted",len(good),"of",len(sample),"eligible scenes",eligible,"of",len(scenes))
print("valid32 rows",sum(all(1<=f<=32 for _,fs in inv for f in fs) for _,r,inv in good),"of",len(good))
print("region rows",sum(bool(re.search(r"frame \d+ \([^)]+\)",r["target"])) for _,r,inv in good),"of",len(good))
def lists(r):
    out = []
    for line in r["text"].split("</think>")[0].splitlines():
        if re.match(r"Step \d+: (?:list|locate|find) ",line) and line.count(":")>=2:
            out.append([e.strip().rstrip(".") for e in line.split(":",2)[2].strip().split(";") if e.strip().rstrip(".")])
    return out
def frame(e):
    m = re.search(r"\bframe\s+(\d+(?:\.\d+)?)",e)
    return float(m.group(1)) if m else None
for name in ["dev-S1","R0-dev"]:
    rows = K.direct("R1",200,name,types=["object_counting"])
    framed = []; prefixes = []
    for r in rows:
        ls = lists(r)
        if not r["forced_close"]:
            if ls and all(frame(e) is not None for es in ls for e in es): framed.append((r,ls))
            continue
        if len(ls) != (2 if r.get("subtype")=="multiple" else 1): continue
        total = 0; valid = True
        for es in ls:
            seen = set()
            for e in es:
                f = frame(e)
                if f is None: valid = False; break
                if f in seen: break
                seen.add(f)
            total += len(seen)
        if valid: prefixes.append((r,total))
    matches = sum(sum(map(len,ls))==float(r["pred"]) for r,ls in framed)
    exact = sum(n==float(r["gt"]) for r,n in prefixes)
    print(name,"literal sum matches",matches,"of",len(framed),"prefix exact",exact,"of",len(prefixes))
db.close()
```