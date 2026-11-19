**1. Question and answer**

1. **Which link fails between stated frames, written order, and answer?** At step 200, the stated frames imply a wrong order on **92 of 93 wrong items**. On the remaining **1 of 93**, the frames imply the truth but the written order changes it; **0 of 93** have a correct written order followed by a wrong answer.
2. **Which object pairs fail, and are some classes placed early?** The last two objects are reversed most often: **89 of 246 pairs**, versus **52 of 246** for the first two. Heater has an early bias in this sample—earlier than truth on **7 of 20 occurrences**, later on **0 of 20**—but no evidence establishes an unconditional class rule.
3. **Are errors stable across checkpoints?** **58 of 246 items** are wrong at all three checkpoints; **35 of 246** choose the same wrong option throughout. **106 of 246** change their answer at least once.
4. **Where does an answer that departs from the trace come from?** On **76 of 246 items**, the answer differs from the written order; it is correct on **45 of those 76**, while the written order is correct on **0 of 76**. First-object agreement is common, but these associations do not identify the answer’s causal source.
5. **Does video length explain errors or out-of-range citations?** Correct answers number **55 of 82**, **49 of 82**, and **49 of 82** across increasing spacing terciles. Out-of-range citations occur on **29 of 82**, **38 of 82**, and **33 of 82**: they do not increase monotonically with length.
6. **What do the training targets teach?** All **300 of 300** sampled appearance-order rows state four frames and a consistent order; **0 of 300** contain ties. All **300 of 300** first-seen rows state one frame matching both the answer and stored provenance.
7. **What should vehicle N change?** Prioritize better first-seen evidence and explicit comparisons, especially between later objects; **92 of 93 errors** involve wrong stated chronology. Do not generally force answers to follow existing traces: nearest-option selection from frames reduces accuracy from **62.2% to 54.9% over 246 items**.

**2. Evidence**

Sources: all dev results below come from `san_kit`, restricted to `obj_appearance_order` on R0-dev. Under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/`, checkpoint directories are `adff67f7ae9` for 544, `a5d2d909067` for 100, and `a8102c3207b` for 200. Each supplies `fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`. Timing comes through `K.timing` from the step-200 return.

Training evidence comes from the supplied `rows.sqlite`, `FAMILY_INDEX_RANGES.json`, `STORE_V7_TEMPLATE_COUNTS.json`, and removal records `n.json` and `z.json`. I sampled 300 primary keys per type without replacement using seed 200. Every SQLite query contained at most 150 primary keys.

**Parsing and failure links.** All **738 of 738 traces** parse completely. B2048 and ON16k answers agree on **738 of 738**; **0 of 738** have tied frames or forced closes. “Frames correct” below means their complete sorted order equals the labeled order, not that their frame citations have been visually verified.

| Checkpoint | Answer correct | Frames’ complete order correct | Written order correct | Written order contradicts frames | Citation above 32 |
|---|---:|---:|---:|---:|---:|
| 544 | 139 of 246 | 77 of 246 | 89 of 246 | 32 of 246 | 100 of 246 |
| 100 | 146 of 246 | 87 of 246 | 107 of 246 | 51 of 246 | 105 of 246 |
| 200 | 153 of 246 | 86 of 246 | 108 of 246 | 41 of 246 | 100 of 246 |

The exhaustive step-200 error partition is **92 of 246** with wrong frame-implied chronology, costing **37.40 type points**, and **1 of 246** with correct frame chronology but wrong sorting, costing **0.41 points**. Answer-letter failure after a correct written order costs **0 points: 0 of 246**. Sorting contradictions overlap chronology errors on **13 of 93 wrong items**.

**Pair accuracy.** Each item contributes six object pairs. The gap is the absolute difference between the trace’s stated frame numbers.

| Checkpoint | All pairs correct | Equal-frame pairs | Correct with gap 1–2 | Correct with gap >2 |
|---|---:|---:|---:|---:|
| 544 | 1,148 of 1,476 | 0 of 1,476 | 111 of 183 | 1,037 of 1,293 |
| 100 | 1,153 of 1,476 | 0 of 1,476 | 101 of 157 | 1,052 of 1,319 |
| 200 | 1,155 of 1,476 | 0 of 1,476 | 99 of 152 | 1,056 of 1,324 |

| Positions in the true order | Frame pair correct, step 200 | Frame pair reversed |
|---|---:|---:|
| First, second | 194 of 246 | 52 of 246 |
| First, third | 208 of 246 | 38 of 246 |
| First, fourth | 218 of 246 | 28 of 246 |
| Second, third | 185 of 246 | 61 of 246 |
| Second, fourth | 193 of 246 | 53 of 246 |
| Third, fourth | 157 of 246 | 89 of 246 |

The frame-sorted sequence identifies the true first object on **183 of 246**, versus the last on **136 of 246**. Written-order endpoints score **183 of 246** and **153 of 246**; answer endpoints score **192 of 246** and **185 of 246**. Answers preserve **1,240 of 1,476 true pairs**, exceeding the frames’ **1,155 of 1,476**.

**Class pairs.** Errors occur in **296 of 1,314 observed unordered class combinations**; only **22 of 1,314 combinations** occur at least three times. The following table includes every repeated combination with an error.

| Class pair | Reversed / observed | Class pair | Reversed / observed |
|---|---:|---|---:|
| Fire extinguisher, stool | 3 of 3 | Fire extinguisher, screen | 3 of 3 |
| Announcement speaker, projector | 3 of 3 | Board, structure | 3 of 3 |
| Board, pedestal fan | 3 of 3 | Door, sink | 2 of 6 |
| Cardboard, door | 2 of 3 | Cardboard, sink | 2 of 3 |
| Picture, windowsill | 2 of 3 | Clothes rail, door | 2 of 3 |
| Door, poster | 2 of 3 | Door, table | 1 of 5 |
| Heater, picture | 1 of 4 | Door, heater | 1 of 4 |
| Bookshelf, windowsill | 1 of 3 | | |

**Class ranks.** The table includes every class with at least five occurrences, covering **487 of 984 object occurrences**. Each cell reports occurrence count, then mean frame-implied rank and mean true rank; rank 1 means earliest.

| Class | Count; frame rank, true rank | Class | Count; frame rank, true rank |
|---|---|---|---|
| Backpack | 8/984; 2.75, 3.00 | Basket | 5/984; 2.60, 2.40 |
| Bed | 11/984; 1.91, 1.82 | Blanket | 8/984; 1.88, 1.50 |
| Book | 5/984; 2.80, 3.00 | Books | 8/984; 3.38, 3.50 |
| Bookshelf | 6/984; 2.17, 1.83 | Box | 5/984; 2.60, 2.40 |
| Bucket | 5/984; 3.20, 3.20 | Cabinet | 10/984; 1.90, 2.20 |
| Cardboard | 5/984; 2.60, 2.80 | Chair | 7/984; 2.71, 2.00 |
| Clock | 6/984; 2.83, 3.67 | Curtain | 5/984; 2.60, 2.80 |
| Desk | 5/984; 2.00, 1.80 | Door | 38/984; 2.47, 2.53 |
| Door frame | 5/984; 2.60, 2.40 | Extension cord | 6/984; 3.00, 3.33 |
| Faucet | 8/984; 3.00, 2.88 | Fire extinguisher | 11/984; 2.00, 2.55 |
| Hanger | 5/984; 2.40, 3.00 | Heater | 20/984; 2.15, 2.70 |
| Intercom | 5/984; 1.20, 1.20 | Jacket | 8/984; 2.25, 2.13 |
| Keyboard | 5/984; 2.80, 2.60 | Laptop | 5/984; 1.80, 2.20 |
| Machine | 5/984; 1.20, 1.20 | Mattress | 6/984; 2.33, 2.00 |
| Microwave | 5/984; 2.40, 2.40 | Mirror | 5/984; 2.20, 2.40 |
| Monitor | 5/984; 2.20, 2.40 | Mouse | 9/984; 3.33, 3.22 |
| Office chair | 7/984; 2.57, 2.14 | Oven | 7/984; 2.71, 2.71 |
| Paper towel dispenser | 5/984; 3.00, 3.00 | Pedestal fan | 10/984; 2.30, 2.80 |
| Picture | 8/984; 2.50, 2.50 | Pillow | 6/984; 1.67, 1.33 |
| Power strip | 10/984; 3.10, 3.10 | Projector | 5/984; 3.20, 2.20 |
| Refrigerator | 6/984; 2.50, 2.50 | Shelf | 6/984; 2.17, 2.33 |
| Sink | 17/984; 2.06, 2.29 | Smoke detector | 15/984; 3.20, 3.20 |
| Stool | 5/984; 2.00, 1.40 | Structure | 6/984; 1.50, 2.33 |
| Table | 21/984; 1.71, 1.76 | Telephone | 13/984; 2.62, 2.62 |
| Toilet | 12/984; 2.75, 3.17 | Toilet paper | 7/984; 3.00, 2.71 |
| Towel | 10/984; 3.10, 3.20 | Trash can | 14/984; 2.36, 2.21 |
| TV stand | 6/984; 1.50, 1.33 | Wardrobe | 7/984; 1.57, 1.71 |
| Water filter | 5/984; 3.40, 3.00 | Whiteboard | 5/984; 1.60, 1.80 |
| Window | 13/984; 1.92, 2.15 | Windowsill | 11/984; 1.82, 1.82 |

Heater is placed earlier on **7 of 20 occurrences**, equally on **13 of 20**, and later on **0 of 20**. Structure is earlier on **4 of 6**, clock on **2 of 6**, and hanger on **3 of 5**, with no later errors for those classes. These are descriptive biases; heater still receives each of the four possible stated ranks.

**Stability and trace changes.**

| Transition | Answer changes | Wrong becomes correct | Correct becomes wrong | Wrong becomes different wrong | Changed frame order / changed written order |
|---|---:|---:|---:|---:|---:|
| 544 to 100 | 79 of 246 | 32 of 79 | 25 of 79 | 22 of 79 | 75 of 79 / 77 of 79 |
| 100 to 200 | 66 of 246 | 28 of 66 | 21 of 66 | 17 of 66 | 62 of 66 / 65 of 66 |
| 544 to 200 | 82 of 246 | 37 of 82 | 23 of 82 | 22 of 82 | 80 of 82 / 80 of 82 |

For `064af11d6223e654ce758796`, the correct base sequence “scarf, box, mouse, toilet” becomes “scarf, toilet, box, mouse”; the toilet citation changes from 76 to 11 and the answer becomes wrong. Conversely, `0f580a9ef2615899f72a9e2f` becomes correct despite retaining a wrong written order. On **1 of 82 base-to-200 answer changes**, `8558e1f33af69b45c520df73`, both frames and written order stay identical while the answer changes between two wrong options.

**Answer departures.** All **76 of 76 departures** have a written order absent from the options. There are **0 of 246** cases where the written order exactly matches an offered option but the answer selects another.

| Check on the 76 departures | Result |
|---|---:|
| Answer correct / complete written order correct | 45 of 76 / 0 of 76 |
| Answer shares written order’s first object | 61 of 76 |
| Answer shares frame-sorted first object | 62 of 76 |
| Exactly one option shares written first object; answer chooses it | 30 of 32 eligible |
| Answer is among options best matching written pairwise order | 64 of 76 |
| Answer exactly copies question’s object-list order | 1 of 76 |
| Answer’s first object matches question’s first-listed object | 17 of 76 |

Departure predictions are A/B/C/D on **18/20/16/22 of 76** items; their truths are A/B/C/D on **23/19/16/18 of 76**. Across the full set, predictions are **62/59/61/64 of 246**. These counts do not support a dominant-letter explanation. Averaging tied nearest options gives **54.9% from frames**, **56.0% from written order**, and **62.2% from answers**, each over **246 items**.

**Video length.** All **246 of 246 videos** have 60 fps, so total-frame and spacing ranks coincide. Terciles contain 82 items each, sorted by value then item ID; a boundary tie crosses the middle/long split.

| Tercile | Sample spacing, seconds | Total source frames | Answer correct | Any citation >32 |
|---|---|---|---:|---:|
| Short | 2.009–3.890 | 3,737–7,237 | 55 of 82 | 29 of 82 |
| Middle | 4.252–6.124 | 7,910–11,392 | 49 of 82 | 38 of 82 |
| Long | 6.124–22.733 | 11,392–42,285 | 49 of 82 | 33 of 82 |

Items with out-of-range citations score **66 of 100 correct**, versus **87 of 146** without them. This does not establish a benefit or harm from invalid numbering.

**Training rows.**

| Family: question_type\|pool\|retrace | Sample kept | Population kept |
|---|---:|---:|
| obj_appearance_order\|w1g\|rows_rebuild_d0_v1 | 145 of 145 | 13,622 of 13,622 |
| obj_appearance_order\|b12_cntapp_gt_v1\|None | 153 of 155 | 13,965 of 14,169 |
| first_seen_frame\|b12_cntapp_gt_v1\|None | 293 of 300 | 6,985 of 7,076 |

Appearance targets use a frame-list step followed by an order on **292 of 300 rows**, and four Locate steps followed by an order on **8 of 300**. All **1,200 of 1,200 citations** lie within 1–32; **0 of 300 rows** have ties, sorting contradictions, or answer mismatches. At least one pair differs by 1–2 frames on **172 of 300 rows**, so nearby-frame supervision is already present. First-seen targets contain one frame on **300 of 300 rows** and match provenance and answer on **300 of 300**; they cannot teach inter-object tie handling.

**3. What this changes for vehicle N, ranked**

1. **Reword appearance targets to retain frames beside objects and explicitly compare adjacent appearances.** Apply to the **27,587 of 27,791 kept appearance rows** across the two named families. Example using sampled row 173485: “First appearances: mirror, sampled frame 1 of 32; shelf, sampled frame 8 of 32; bottle, sampled frame 13 of 32; bar, sampled frame 20 of 32. Mirror precedes shelf; shelf precedes bottle; bottle precedes bar. The complete sequence matches option D.” **Hypothesis:** this makes pair errors easier to learn and audit. The affected error pool is **92 of 93 wrong items**; last-pair errors occur on **45 of 93**. These are ceilings, not predicted recoveries. It fails if pair accuracy stays near **1,155 of 1,476**, especially the last pair’s **157 of 246**, despite cleaner prose.
2. **Use “sampled frame k of 32” in both appearance families and all 6,985 kept first-seen rows.** This addresses invalid numbering on **100 of 246 dev items**, including **34 of 93 wrong answers**. **Hypothesis:** consistent numbering helps grounding; no positive answer gain is established. It fails as an accuracy repair if citations become valid without improving chronology or answers. Do not drop rows for citation defects: the audit found **0 of 600 sampled rows** with an invalid cited index.
3. **Gate sorting correction on an exact offered sequence; do not force the nearest option.** A frame-sorted sequence exactly matches an option on **135 of 246 items**. Using it on that subset fixes **1 of 93 errors** and breaks **0 of 153 correct answers**, yielding **154 of 246** correct retrospectively. Train the explicit option-match line in the same **27,587 kept appearance rows**; add **0 new rows** for this change. Generalization remains a hypothesis. Unrestricted nearest-option selection loses **18 net correct answers of 246** for frames and an expected **15⅓ of 246** for written order.
4. **Do not invent a tie-breaking rule from this audit.** There are ties on **0 of 738 dev traces** and **0 of 300 sampled appearance targets**, so the observed repair opportunity is **0 demonstrated items**. Add **0 tie-specific rows** until source annotations establish whether simultaneous sampled appearances have a recoverable order.

**4. Refuted**

The reported **54.9%, 56.0%, and 62.2% over 246 items** reproduce; no numerical correction is needed. However, “the answer is not derived from the trace at all” is too strong: answers exactly follow the written order on **170 of 246 items** and choose a nearest written-order option on **64 of 76 departures**. The evidence establishes incomplete trace faithfulness, not absence of trace influence.

A general sorting fix is refuted by the **18-of-246 net loss** from nearest frame-order selection. A narrowly gated exact-option correction survives this test, fixing **1 of 246**.

**5. Not established**

The videos were not visually inspected. Thus, **92 of 93 chronology errors** establish disagreement with labeled order, not which individual first-seen citation is visually wrong. Frame-level onset annotations for these dev items would settle that distinction.

Class effects and video-length effects are observational and may share rooms or object contexts. Room-stratified evaluation and controlled option/question permutations would test whether first-object agreement or class priors actually drive the answers.

No training intervention was run. All proposed accuracy benefits are hypotheses; only the stated retrospective answer substitutions have measured gains or losses.

**Appendix — CLASSIFIER**

```python
import sys, re, itertools, collections, json, random, sqlite3
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

def parse(x):
    opts = {o[0]: tuple(z.strip() for z in o[3:].split(","))
            for o in x["options"]}
    text = x["text"].split("</think>")[0]
    frames = {a.strip(): int(b) for a, b in re.findall(
        r"(?:each object:|;)\s*(.*?) frame (\d+)", text)}
    line = re.search(r"order them by first appearance:\s*([^\n]+)", text)[1]
    written = tuple(z.strip() for z in line.rstrip(".").split(","))
    truth = opts[x["gt"]]
    assert set(frames) == set(written) == set(truth)
    return dict(x=x, o=opts, f=frames, w=written, t=truth,
                a=opts[x["pred"]], s=tuple(sorted(frames, key=frames.get)))

P = {}
for run, step in [("S1", 544), ("R1", 100), ("R1", 200)]:
    P[step] = [parse(x) for x in K.direct(
        run, step, "R0-dev", types=["obj_appearance_order"])]
p = P[200]
wrong = [z for z in p if not z["x"]["score"]]
labels = {z["x"]["id"]: ("a" if z["s"] == z["t"] else
          "b" if z["w"] == z["t"] else "c") for z in wrong}
print("Wrong-item links:", collections.Counter(labels.values()), "/", len(wrong))
depart = [z for z in p if z["a"] != z["w"]]
print("Departures / answer correct / written correct:",
      len(depart), sum(z["a"] == z["t"] for z in depart),
      sum(z["w"] == z["t"] for z in depart))
print("Correct frame pairs:", sum(z["f"][a] < z["f"][b]
      for z in p for a, b in itertools.combinations(z["t"], 2)), "/ 1476")
for field in ["s", "w"]:
    expected = 0
    for z in p:
        pairs = list(itertools.combinations(z[field], 2))
        scores = {k: sum(o.index(a) < o.index(b) for a, b in pairs)
                  for k, o in z["o"].items()}
        winners = [k for k, v in scores.items() if v == max(scores.values())]
        expected += (z["x"]["gt"] in winners) / len(winners)
    print("Nearest-option accuracy:", field, 100 * expected / len(p), len(p))
exact = [z for z in p if z["s"] in z["o"].values()]
print("Exact-option eligible / fixes / breaks:", len(exact),
      sum(not z["x"]["score"] and z["s"] == z["t"] for z in exact),
      sum(bool(z["x"]["score"]) and z["s"] != z["t"] for z in exact))

base = "/scratch/jjyeung/orch_n30/"
with open(base + "r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json") as f:
    index = json.load(f)["families"]
db = sqlite3.connect("file:" + base +
    "r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro", uri=True)
ids = [i for a, b in index["obj_appearance_order"] for i in range(a, b + 1)]
ids = sorted(random.Random(200).sample(ids, 300))
ties = contradictions = count = 0
for start in range(0, 300, 150):
    batch = ids[start:start + 150]
    sql = "select i,row from rows where i in (" + ",".join("?" * len(batch)) + ")"
    for i, raw in db.execute(sql, batch):
        target = json.loads(raw)["target"]
        frames = {a.strip(): int(b) for a, b in re.findall(
            r"(?:each object:|;)\s*(.*?) frame (\d+)", target)}
        if len(frames) != 4:
            frames = {a: int(b) for a, b in re.findall(
                r"find the (.*?), first seen in frame (\d+)", target)}
        pattern = r"(?:order them by first appearance:|the order is:|the order of first appearance is:)\s*([^\n]+)"
        order = re.search(pattern, target)[1].rstrip(".").split(",")
        order = [a.strip() for a in order]
        assert len(frames) == 4 and set(order) == set(frames)
        count += 1
        ties += len(set(frames.values())) < 4
        contradictions += any(frames[a] > frames[b]
                              for a, b in itertools.combinations(order, 2))
db.close()
print("Sampled appearance rows / ties / contradictions:", count, ties, contradictions)
```