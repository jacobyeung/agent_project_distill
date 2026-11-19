**1. Scope**

R0-dev contains **246 of 246** assigned `obj_appearance_order` items, all subtype `first_seen`. I classified every wrong item. Dev-S1 is outside this assignment.

| Set | Step 544 B2048 | Step 200 B2048 | Change |
|---|---:|---:|---:|
| R0-dev | 139 of 246 correct; 56.50% | 153 of 246 correct; 62.20% | +5.69 points |

I recomputed these results using `san_kit`. The source directory is `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/`.
The step-544 and step-200 subdirectories are respectively `adff67f7ae9` and `a8102c3207b`. Under each, the files are `fetched/x/a7/a0/results/0/items_a0.jsonl` and `fetched/x/a7/a0/results/budget_2048/0/items_a0.jsonl`.
ON16k and B2048 predictions agree on **246 of 246** items at each checkpoint.

**2. Failure modes at step 200**

The primary classifier checks answer–order disagreement first, sorting disagreement second, and wrong chronology last. These modes partition **93 of 246** errors.

| Primary mode | Definition | R0-dev count | Cost |
|---|---|---:|---:|
| Wrong first-seen order | The frames sort into a wrong option; the written order and answer follow them. | 49 of 246 | 19.92 points |
| Unmatched order / option | The written order matches no option, but the model selects an option anyway. | 31 of 246 | 12.60 points |
| Sorting inconsistency | The written order contradicts the stated frames, and the answer follows that written order. | 13 of 246 | 5.28 points |
| **Total** | | **93 of 246** | **37.80 points** |

The requested frame-based checks overlap these primary modes:
- **92 of 93** wrong items have frame-implied orders inconsistent with truth: **49 of 93** match a wrong option; **43 of 93** match no option. This establishes an ordinal contradiction, not visually verified frame error.
- **1 of 93** has frames ordered consistently with truth but writes and chooses the wrong order: `d572b3b6c7e1bd35f9084ed6`.
- **0 of 246** have tied frame assignments; **0 of 246** omit an object’s frame; **0 of 246** have runaways, missing answers, or unparsed traces.
- Sorting contradictions occur in **14 of 93** wrong traces. The primary sorting mode contains **13 of 93**; the remaining **1 of 93** also selects an option inconsistent with its written order.

Among wrong answers, **19 of 93** written orders differ from truth by one adjacent swap; **74 of 93** require more. The swapped objects’ stated gaps range from 2–44, with median 5. Only **6 of 93** satisfy the ≤2-frame *trace-proxy* near-miss criterion.
Across all answers, **138 of 246** written orders differ from truth: **47 of 138** involve one adjacent swap, including **13 of 47** with stated gaps ≤2. Actual temporal proximity remains unverified.

Neither checkpoint uses decimals: **0 of 246** at each step. Both keep every citation within 1–32 on **146 of 246** items and exceed 32 on **100 of 246**. Maximum citations are 635 at step 544 and 221 at step 200.
At step 200, sorting contradictions occur on **24 of 100** items exceeding 32 versus **17 of 146** confined to 1–32. At step 544, those counts are **18 of 100** and **14 of 146**. This is association, not evidence that numbering causes sorting errors.

**3. Examples**

All examples are R0-dev. Questions are shortened to their category lists; trace excerpts are verbatim.

**Wrong first-seen order**

`008113524364ec0bd653c491` — Q: “…jacket, power strip, shoes, trash bin?”
Truth C: jacket, power strip, trash bin, shoes. Answer B.
> Step 1: find the first frame showing each object: jacket frame 5; power strip frame 13; shoes frame 11; trash bin frame 8.
> Step 2: order them by first appearance: jacket, trash bin, shoes, power strip.

`033e3fac986f863d837263d7` — Q: “…book, books, door, pedestal fan?”
Truth D: book, door, pedestal fan, books. Answer A.
> Step 1: find the first frame showing each object: book frame 7; books frame 10; door frame 3; pedestal fan frame 5.
> Step 2: order them by first appearance: door, pedestal fan, book, books.

`043e10b6f4d19ab7ca3be98f` — Q: “…bookshelf, door frame, whiteboard, windowsill?”
Truth B: windowsill, bookshelf, door frame, whiteboard. Answer A.
> Step 1: find the first frame showing each object: bookshelf frame 15; door frame frame 37; whiteboard frame 31; windowsill frame 2.
> Step 2: order them by first appearance: windowsill, bookshelf, whiteboard, door frame.

**Unmatched order / option**

`04cead03c436f4edca556995` — Q: “…bathroom vent, faucet, shower sponge, toothbrushes?”
Truth B: shower sponge, bathroom vent, toothbrushes, faucet. Answer A: shower sponge, toothbrushes, faucet, bathroom vent.
> Step 1: find the first frame showing each object: bathroom vent frame 8; faucet frame 32; shower sponge frame 1; toothbrushes frame 6.
> Step 2: order them by first appearance: shower sponge, toothbrushes, bathroom vent, faucet.

`064af11d6223e654ce758796` — Q: “…box, mouse, scarf, toilet?”
Truth C: scarf, box, mouse, toilet. Answer A: scarf, toilet, mouse, box.
> Step 1: find the first frame showing each object: box frame 16; mouse frame 24; scarf frame 2; toilet frame 11.
> Step 2: order them by first appearance: scarf, toilet, box, mouse.

`072349cf2766955bdbe82e5a` — Q: “…boiler, cardboard, door, sink?”
Truth B: door, cardboard, sink, boiler. Answer D: door, sink, cardboard, boiler.
> Step 1: find the first frame showing each object: boiler frame 11; cardboard frame 18; door frame 1; sink frame 7.
> Step 2: order them by first appearance: door, sink, boiler, cardboard.

**Sorting inconsistency**

`d572b3b6c7e1bd35f9084ed6` — Q: “…blanket, mini oven, shoe box, storage shelf?”
Truth A: blanket, mini oven, shoe box, storage shelf. Answer C.
> Step 1: find the first frame showing each object: blanket frame 5; mini oven frame 29; shoe box frame 73; storage shelf frame 90.
> Step 2: order them by first appearance: blanket, shoe box, mini oven, storage shelf.

`166bcbfccbb16fb7f2aa70bd` — Q: “…bottles, curtain rod, teapot, water pot?”
Truth C: bottles, curtain rod, teapot, water pot. Answer B.
> Step 1: find the first frame showing each object: bottles frame 16; curtain rod frame 7; teapot frame 18; water pot frame 21.
> Step 2: order them by first appearance: curtain rod, teapot, water pot, bottles.

`28634b402e5a1cfc4be4ee6e` — Q: “…ironing board, mop, umbrella holder, vase?”
Truth D: umbrella holder, vase, mop, ironing board. Answer B.
> Step 1: find the first frame showing each object: ironing board frame 36; mop frame 40; umbrella holder frame 38; vase frame 13.
> Step 2: order them by first appearance: vase, ironing board, mop, umbrella holder.

**4. Step 544 against step 200**

R0-dev transitions are **23 of 246** right-to-wrong, **37 of 246** wrong-to-right, **70 of 246** wrong-to-wrong, and **116 of 246** right-to-right.
Among gains, **20 of 37** acquire correct frame-derived and written orders; **8 of 37** acquire the correct written order despite contradictory frames; **9 of 37** choose the correct letter despite a wrong written order. Thus, the gain only partly reflects coherent temporal reasoning.
Among regressions, **23 of 23** end with frame-implied and written orders inconsistent with truth. Previously, **9 of 23** had coherent correct traces, **4 of 23** had correct written orders despite contradictory frames, and **10 of 23** had correct letters despite wrong written orders.
The template stays unchanged on **60 of 60** flips. Mean think length changes from 59.78 to 60.14 tokens for gains and 59.09 to 59.22 for regressions.
For example, `18de456b6cf181eb1855e58d` changes table frame 18 to frame 1 and correctly writes “table, container, paper towel, backpack.” Conversely, `064af11d6223e654ce758796` moves box from 2 to 16 and toilet from 76 to 11, breaking its previously correct chronology.

**5. Hypotheses**

I read both appearance families in `STORE_V7_SAMPLES20.json` and their counts in `STORE_V7_TEMPLATE_COUNTS.json`, under `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`. Family F1 is `obj_appearance_order|w1g|rows_rebuild_d0_v1`; F2 is `obj_appearance_order|b12_cntapp_gt_v1|None`.
F1 retains **13,622 of 13,622** rows; F2 retains **13,965 of 14,169**. The inspected **40 of 40** samples are kept, use indices within 1–32, sort correctly, and match their answer options. These samples do not establish store-wide consistency.
- **HYPOTHESIS — wrong first-seen order:** The model produces plausible frame assignments without reliably grounding earliest visibility. F1 and F2 supervise the resulting assignments but provide little visible justification. F1 row `qade6d0b02a55107cdcee753e` says “bedside cabinet frame 8; blanket frame 3; picture frame 18; wardrobe frame 14.”
- **HYPOTHESIS — unmatched order / option:** The model learns the order template and letter prediction without reliably enforcing their agreement. F2 row `b12ao_73d6d4eed0ab2ad1dd3b453c` correctly says “Step 2: order them by first appearance: projector, standing lamp, jacket, towel.” Its answer is C; the inspected targets do not demonstrate recovery when no option matches.
- **HYPOTHESIS — sorting inconsistency:** The model predicts an ordering without consistently using its own numbers. F1 row `qaede4f47af042c7586f977af` supplies “book frame 2; computer mouse frame 17; headphones frame 9; windowsill frame 4” followed by “book, windowsill, headphones, computer mouse.” Training examples demonstrate sorting, but do not guarantee execution at inference.

**6. Label or scoring defects**

None found. At each checkpoint, **246 of 246** scores agree with prediction-versus-label equality, and **246 of 246** option lists contain distinct permutations of the requested categories. Visual label correctness was not checked. Out-of-range model citations are trace defects, not evidence of bad labels.

**7. Three changes for vehicle N**

These row budgets are proposals, and affected-item counts are opportunities rather than predicted gains.
1. **Reword approximately 2,000 of 27,587 retained F1/F2 rows** around verified earliest visibility in the actual sampled frames, explicitly naming the sampled-frame index and a short identifying cue. This targets the frame-order conflict on **92 of 93** errors, including **34 of 93** with citations above 32.
2. **Reword approximately 1,000 of 13,965 retained F2 rows** to teach recovery from an order absent from the options: revisit the disputed first appearances, then print an exactly matching option. This targets **31 of 93** errors. **This is the least certain change:** none has a correct written order already, so letter matching alone would fix **0 of 31**.
3. **Reword and validate 27,587 of 27,587 retained F1/F2 rows** so the sorted output retains each object’s frame number and the final letter matches that sequence. This targets sorting contradictions on **14 of 93** errors, overlapping the unmatched mode on **1 of 93**. Sorting alone has a demonstrated answer-fixing opportunity on only **1 of 93**; the others also need corrected frame evidence.

**8. Not established**

Absolute frame error, genuine ≤2-frame near misses, and visual label correctness require verified first-visibility annotations plus the mapping between source frames and the sampled 32 frames. The traces cannot supply those measurements.
The decimal-numbering claim is unsupported by these files. Whether the proposed rows improve accuracy requires a controlled training comparison; enforcing existing frame assignments blindly could damage currently correct answers.

**Appendix — CLASSIFIER**

```python
import sys, re
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

rows = K.direct("R1", 200, "R0-dev",
                types=["obj_appearance_order"])
counts = Counter()
costs = Counter()

for r in rows:
    text = r["text"]
    first = text.split("Step 2:")[0]
    frames = {
        name.strip().lower(): float(value)
        for name, value in re.findall(
            r"([^:;\n]+?) frame (\d+(?:\.\d+)?)", first)
    }
    match = re.search(
        r"order them by first appearance:\s*(.*?)(?:\.?(?:\n|</think>))",
        text)
    assert match is not None
    order = [x.strip().lower()
             for x in match.group(1).rstrip(".").split(",")]
    options = [
        [x.strip().lower() for x in option[3:].rstrip(".").split(",")]
        for option in r["options"]
    ]
    truth = options[ord(r["gt"]) - ord("A")]
    assert set(frames) == set(order) == set(truth)
    assert len(frames) == len(set(frames.values())) == 4
    assert not r["forced_close"] and r["pred"] in "ABCD"
    assert r["pred"] == r["pred_on"]
    assert r["score"] == float(r["pred"] == r["gt"])
    if r["score"] == 1:
        continue
    chosen = options[ord(r["pred"]) - ord("A")]
    if order != chosen:
        assert order not in options
        mode = "Unmatched order / option"
    elif order != sorted(frames, key=frames.get):
        mode = "Sorting inconsistency"
    else:
        mode = "Wrong first-seen order"
    counts[mode] += 1
    costs[mode] += 1 - r["score"]

assert len(rows) == 246 and sum(counts.values()) == 93
for mode in ("Wrong first-seen order", "Unmatched order / option",
             "Sorting inconsistency"):
    print("R0-dev", mode, f"{counts[mode]} of {len(rows)}",
          f"{100 * costs[mode] / len(rows):.2f} points")
```