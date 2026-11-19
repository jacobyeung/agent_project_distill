## 1. Scope

On dev-S1 route planning, step 200 scores **80.67% (121 of 150 correct)**; step 544 scores **78.67% (118 of 150 correct)**. The gain is **2.00 points**.

I recomputed these scores from:
- Step 544: `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
- Step 200 B2048: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl`.
- Step 200 ON16k traces: the same step-200 root, ending in `main/a0/results/0/items_a0.jsonl`.

B2048 and ON16k choose the same answer on 150 of 150 items. All analysis below covers these dev items.

## 2. Failure modes

Every wrong answer follows the trace’s stated turns. The failures occur in the written spatial relations.

| Primary mode | Definition | Wrong items, dev-S1 | Cost |
|---|---|---:|---:|
| One wrong turn | Exactly one written turn differs from the truth sequence. | 16 of 150 | 10.67 points |
| Multiple wrong turns | At least two written turns differ from the truth sequence. | 13 of 150 | 8.67 points |
| **Total** | All wrong items receive exactly one primary mode. | **29 of 150** | **19.33 points** |

Among wrong items, 16 of 29 have one wrong turn, 10 of 29 have two, and 3 of 29 have three. Correct trace followed by another option: **0 of 29**. Trace matching no option: **0 of 29**. Any trace-to-answer mismatch: **0 of 150**. Runaway, missing-answer, and unparsed failures: **0 of 150**.

| Turn position | Wrong turns / opportunities |
|---|---:|
| First fill-in turn | 26 of 150 |
| Middle turn, in three-turn routes | 6 of 43 |
| Last turn, excluding single-turn routes | 13 of 89 |

The first turn fails most often, both by count and rate. In 8 of 150 questions, prescribed forward movement precedes the first fill-in; 2 of those 8 have a wrong first turn. Thus, first-turn errors made at the actual starting location occur in 24 of 142 items.

Of 45 erroneous turns across 282 turn opportunities, **25 of 45** swap left and right; **20 of 45** confuse back with a side. All back confusions occur at the first fill-in. Later errors are left/right swaps in 19 of 19 cases. Back is both the true and predicted first turn on 47 of 150 items, so aggregate back frequency hides the errors.

**Heading continuity:** I found explicit contradictions in **0 of 89 multi-turn traces**. Each later step names the preceding destination correctly, across 132 of 132 transitions. However, “keep that heading” never independently specifies the incoming heading; this does **not** establish that the model updates orientation correctly.

## 3. Examples

Questions below retain verbatim excerpts; omitted route instructions are represented by “…”.

**One wrong turn**

- `q02e8b23ae73dbd77cdfbfc03`, dev-S1. Q: “You are a robot beginning at the counter and facing the sink. You want to navigate to the step stool.”
  Truth: A, back. Answer: C, right.
  > Step 1: I stand at the counter facing the sink. I find the step stool to my right: turn right.

- `q941eed817ccdd8f46383b354`, dev-S1. Q: “You are a robot beginning at the letter tray and facing the cardboard box. …”
  Truth: C, right/left/right. Answer: A, right/right/right.
  > Step 2: I go forward to the desk and keep that heading. I find the chair(s) to my right: turn right.

- `qfef7557a8e0db841a69c54c1`, dev-S1. Q: “You are a robot beginning at the toilet facing the toilet brush. You want to navigate to the radiator.”
  Truth: D, left/right/left. Answer: A, left/right/right.
  > Step 3: I go forward to the trash can and keep that heading. I find the radiator to my right: turn right.

**Multiple wrong turns**

- `q05b8d41ebf0c9b76799923b2`, dev-S1. Q: “You are a robot beginning at the tables and facing the bookshelf. …”
  Truth: C, left/right. Answer: D, back/left.
  > Step 1: I stand at the tables facing the bookshelf. I find the chairs behind me: turn back.
  > Step 2: I go forward to the chairs and keep that heading. I find the table to my left: turn left.

- `q3969a8e77eea1ac295521110`, dev-S1. Q: “You are a robot beginning at the trash can and facing the curtain rail. …”
  Truth: B, left/right/right. Answer: A, right/left/left.
  > The turns are: right, left, left.

- `q3242e9ee4baaef027cd82b52`, dev-S1. Q: “You are a robot beginning at the wardrobe facing the coffee table. …”
  Truth: C, back/left/left. Answer: B, right/left/right.
  > Step 1: I stand at the wardrobe facing the coffee table. I find the bed to my right: turn right.
  > Step 3: I go forward to the mattress and keep that heading. I find the laundry basket to my right: turn right.

## 4. Step 544 against step 200

Right-to-wrong flips occur in **12 of 150** items; wrong-to-right flips in **15 of 150**; wrong-to-wrong outcomes in **17 of 150**; and right-to-right outcomes in **106 of 150**.

| Fill-in turns | Step 544 correct | Step 200 correct | Wrong-to-right | Right-to-wrong |
|---|---:|---:|---:|---:|
| One | 48 of 61, 78.69% | 54 of 61, 88.52% | 8 of 61 | 2 of 61 |
| Two | 36 of 46, 78.26% | 35 of 46, 76.09% | 3 of 46 | 4 of 46 |
| Three | 34 of 43, 79.07% | 32 of 43, 74.42% | 4 of 43 | 6 of 43 |

Step 544 has empty think blocks on 150 of 150 items. Step 200 writes stepwise relations and a turn summary on 150 of 150, using 31–108 think tokens, with median 61.

The corrected items explicitly state the truth sequence in 15 of 15 cases; the regressions explicitly state a wrong sequence in 12 of 12. For example, `q300764cc6bb54549f087a4a8` changes from back to the correct right; `q3969a8e77eea1ac295521110` changes from the correct sequence to its complete left/right reversal.

The continuation improves single-turn accuracy but reduces multi-turn accuracy. Writing steps makes errors inspectable; these checkpoints do not isolate its causal effect from the other training changes.

## 5. Hypotheses

The observed family is **`route_planning|dose_route_direct|None`**. The supplied `STORE_V7_TEMPLATE_COUNTS.json` reports 8,894 of 8,894 rows kept. I read 20 of 8,894 cached samples in `STORE_V7_SAMPLES20.json`; 20 of 20 are marked kept, and 0 of 20 cite visual frames.

- **HYPOTHESIS — one wrong turn:** The template teaches an unsupported relation assertion more directly than it teaches visual verification. Row `104014`, qid `q77b4f8ce1fc4635fdc6150d4`, trains: “I stand at the chair facing the table. I find the sofa to my right: turn right.” The generated errors reproduce this fluent assertion form. This supports a grounding hypothesis, not proof of its cause.
- **HYPOTHESIS — multiple wrong turns:** The template permits a coherent-looking sequence without making heading updates checkable. Row `150233`, qid `q926cb2f9c5b46a2b9a59546f`, trains: “I go forward to the bed and keep that heading. I find the carpet to my right: turn right.” All 8 of 8 multi-turn samples use this phrase. An initial spatial misinterpretation or repeated independent relation errors could explain the failures; the traces cannot distinguish them.

## 6. Label or scoring defects

**None found in the text and scoring audit.** Option sequences are unique on 150 of 150 items, recorded labels agree on 150 of 150, and scores agree with answer correctness on 150 of 150. Visual ground-truth correctness remains unverified.

## 7. Three changes for vehicle N

All changes target `route_planning|dose_route_direct|None`. Volumes below are proposed allocations, not measured optima; candidate fixes are ceilings, not predicted gains.

1. **Reword approximately 1,000 of 8,894 rows to verify the first-turn reference pose and distinguish back from a side.** Include frame-grounded evidence for the start, facing anchor, and next destination. This targets 20 of 29 wrong items containing back confusion. Correcting that turn alone would fully fix 12 of 29 wrong items; the other 8 of 29 also need later corrections.
2. **Reword approximately 1,000 of 8,894 rows to state the incoming travel direction at each waypoint.** Replace the bare heading phrase with, for example, “At B, still facing along A-to-B, …”, supported by scene evidence. Later-turn errors affect 16 of 29 wrong items; correcting only later turns would fully fix 3 of 29. **This is the least certain change:** no explicit heading contradiction establishes heading loss as the cause.
3. **Rebuild approximately 1,000 of 8,894 rows as visually verified left/right contrast cases covering complete routes.** Match start poses and waypoint identities carefully, and require each relation before the final sequence. Pure left/right errors account for 9 of 29 wrong items: 4 of those 9 have one error and 5 of 9 have multiple errors. These are the candidate full-item fixes if the contrasts improve spatial discrimination. This overlaps change 2.

## 8. Not established

The traces cannot establish whether errors arise from object identity, visual geometry, viewpoint conversion, heading updates, or answer-conditioned narration. Frame-level object evidence and verified waypoint poses would distinguish these explanations.

The sampled targets do not establish their geometry’s correctness or population-wide coverage. A controlled training ablation would determine whether the proposed wording helps and whether explicit reasoning causes the observed accuracy changes.

## Appendix: CLASSIFIER

```python
import sys, re
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

rows = K.direct("R1", 200, "dev-S1", types=["route_planning"])

def turns(text):
    return re.findall(r"\b(left|right|back)\b", text.lower())

names = [
    "One wrong turn", "Multiple wrong turns",
    "Trace-answer mismatch", "No option match", "Format failure",
]
counts, costs = Counter(), Counter()
for r in rows:
    if r["score"] == 1:
        continue
    body = (r["text"] or "").split("</think>")[0]
    match = re.search(r"The turns are:\s*([^\n]+)", body)
    opts = {x.split(".", 1)[0]: turns(x) for x in r["options"]}
    seq = turns(match.group(1)) if match else []
    steps = re.findall(r": turn (left|right|back)\.", body)
    if r["forced_close"] or not seq or r["pred"] not in opts:
        mode = "Format failure"
    elif seq not in opts.values():
        mode = "No option match"
    elif seq != opts[r["pred"]]:
        mode = "Trace-answer mismatch"
    else:
        assert steps == seq
        assert len(seq) == len(opts[r["gt"]])
        differences = sum(a != b for a, b in zip(seq, opts[r["gt"]]))
        assert differences > 0
        mode = "One wrong turn" if differences == 1 else "Multiple wrong turns"
    counts[mode] += 1
    costs[mode] += 1 - r["score"]

for mode in names:
    print(
        "dev-S1", mode, f"{counts[mode]} of {len(rows)}",
        f"cost={100 * costs[mode] / len(rows):.2f} points"
    )
assert sum(counts.values()) == sum(r["score"] < 1 for r in rows)
print(f"All wrong items: {sum(counts.values())} of {len(rows)}")
```