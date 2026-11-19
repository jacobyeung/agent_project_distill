## 1. Scope

I classified all **26 of 150** wrong dev-S1 answers and **81 of 192** wrong R0-dev answers. Every answer follows its trace’s final quadrant. The errors arise earlier: the trace states the wrong relation or fails to turn away.

| Set | Step 544 accuracy | Step 200 accuracy |
|---|---:|---:|
| dev-S1 | 126 of 150 — 84.00% | 124 of 150 — 82.67% |
| R0-dev | 88 of 192 — 45.83% | 111 of 192 — 57.81% |
| R0-dev toward | 78 of 121 — 64.46% | 75 of 121 — 61.98% |
| R0-dev away | 10 of 71 — 14.08% | 36 of 71 — 50.70% |

I recomputed these scores through `san_kit`. Source roots are `C=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build` and `E=/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged`.
- Step 200: `C/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 544 dev-S1: `E/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
- Step 544 R0-dev: `C/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.

B2048 and ON16k predictions agree on **342 of 342** step-200 items; force-closing affects **0 of 342**.

## 2. Failure modes

Each wrong item receives exactly one primary mode. Costs are percentage points lost on the entire type within its set.

| Mode | Definition | dev-S1 count; cost | R0-dev count; cost |
|---|---|---:|---:|
| Wrong toward relation | The trace states an incorrect quadrant while facing the reference object. | 26 of 150; 17.33 | 46 of 192; 23.96 |
| Away heading retained | The trace retains its stated forward relation despite the away clause. | 0 of 150; 0.00 | 21 of 192; 10.94 |
| Wrong forward relation before correct turn | The trace correctly swaps both axes, but its starting relation is wrong. | 0 of 150; 0.00 | 14 of 192; 7.29 |
| Usage mismatch | The chosen option contradicts the trace’s final quadrant. | 0 of 150; 0.00 | 0 of 192; 0.00 |
| Runaway | B2048 force-closes the trace. | 0 of 150; 0.00 | 0 of 192; 0.00 |
| Unparsed | The relation or answer cannot be parsed. | 0 of 150; 0.00 | 0 of 192; 0.00 |
| **Total wrong** | | **26 of 150; 17.33** | **81 of 192; 42.19** |

For away items, **23 of 71** write no half-turn or equivalent operation; **48 of 71** write and correctly apply both swaps. **0 of 71** apply only one axis. Among correctly executed turns, **14 of 48** start from a wrong forward relation. The omitted-turn group contains **2 of 23** correct answers through cancellation of errors.

Correcting only the omitted turn fixes **14 of 21** wrong items in that mode. The remaining **7 of 21** also have an incorrect forward relation.

**Truth-to-answer confusion.** FL/FR/BL/BR mean front-left/front-right/back-left/back-right. Each denominator is the number with that truth.

| Set/subtype | Truth | Answer FL | Answer FR | Answer BL | Answer BR |
|---|---|---:|---:|---:|---:|
| dev-S1 | FL | 52 of 57 | 5 of 57 | 0 of 57 | 0 of 57 |
| dev-S1 | FR | 3 of 53 | 48 of 53 | 0 of 53 | 2 of 53 |
| dev-S1 | BL | 7 of 23 | 1 of 23 | 13 of 23 | 2 of 23 |
| dev-S1 | BR | 0 of 17 | 5 of 17 | 1 of 17 | 11 of 17 |
| R0-dev all | FL | 36 of 49 | 8 of 49 | 4 of 49 | 1 of 49 |
| R0-dev all | FR | 13 of 59 | 40 of 59 | 2 of 59 | 4 of 59 |
| R0-dev all | BL | 12 of 43 | 10 of 43 | 16 of 43 | 5 of 43 |
| R0-dev all | BR | 6 of 41 | 7 of 41 | 9 of 41 | 19 of 41 |
| R0-dev toward | FL | 33 of 44 | 8 of 44 | 3 of 44 | 0 of 44 |
| R0-dev toward | FR | 13 of 54 | 38 of 54 | 1 of 54 | 2 of 54 |
| R0-dev toward | BL | 8 of 12 | 2 of 12 | 1 of 12 | 1 of 12 |
| R0-dev toward | BR | 2 of 11 | 3 of 11 | 3 of 11 | 3 of 11 |
| R0-dev away | FL | 3 of 5 | 0 of 5 | 1 of 5 | 1 of 5 |
| R0-dev away | FR | 0 of 5 | 2 of 5 | 1 of 5 | 2 of 5 |
| R0-dev away | BL | 4 of 31 | 8 of 31 | 15 of 31 | 4 of 31 |
| R0-dev away | BR | 4 of 30 | 4 of 30 | 6 of 30 | 16 of 30 |

Among wrong answers, front/back-only, left/right-only, and both-axis errors are respectively: dev-S1 **14 of 26, 11 of 26, 1 of 26**; R0-dev **27 of 81, 35 of 81, 19 of 81**; R0 toward **16 of 46, 25 of 46, 5 of 46**; R0 away **11 of 35, 10 of 35, 14 of 35**.

**Frame evidence.** dev-S1 cites no numeric frames on **150 of 150** items. R0-dev cites none on **138 of 192**, with **66 of 138** wrong; complete citations appear on **53 of 192**, with **14 of 53** wrong. The remaining **1 of 192** says “eraser in hand” and cites frames for the other objects; it is wrong. These are evidence omissions, not proof that the model failed to see an object.

Among complete R0 citations, a maximum-minus-minimum frame span above 32 accompanies **11 of 40** errors, versus **3 of 13** for smaller spans. All objects share one frame on **0 of 53** items. These citations do not establish first-seen times; **46 of 54** traces with numeric citations exceed frame 32, so their numbering needs validation.

**Why R0-dev is harder remains partly unresolved.** Toward-only accuracy is already lower than dev-S1. The Cartesian-plane explanation appears on **192 of 192** R0 questions versus **0 of 150** dev-S1 questions, but wording and scenes are confounded. Targets outside dev-S1’s exact object-name vocabulary fail on **54 of 129**, versus **27 of 63** for familiar names: lexical novelty alone shows no error increase. Repeated physical instances cannot be established from these traces.

## 3. Examples

Questions below retain verbatim excerpts; ellipses omit text. Truth and answer name the option’s quadrant.

**Wrong toward relation — three examples.**
- `vsi590k_000428`, dev-S1. Q: “If located at the chair and looking toward the sofa, in what direction is the closet: …” Truth BL; answer FL. Trace: “I find the closet in front of me, on my left.”
- `vsi590k_103370`, dev-S1. Q: “I'm at the shoe rack, looking toward the table. Is the exhaust fan located at my …” Truth FL; answer FR. Trace: “I find the exhaust fan in front of me, on my right.”
- `2ad8bccf7a49fe5eea135f47`, R0-dev. Q: “If I am standing by the speaker and facing the french window, is the paper towel …” Truth FR; answer BL. Trace: “I find the paper towel behind me, on my left.”

**Away heading retained — three examples.**
- `10bbc3801dff57035968331e`, R0-dev. Q: “If I am standing by the sink and facing away from the door, is the toilet brush …” Truth FL; answer BR. Trace: “I find the toilet brush behind me, on my right.” / “The question has me face away from the door, so I keep that heading.”
- `178f68bda9c0857ee978f543`, R0-dev. Q: “If I am standing by the bin and facing away from the door, is the clothes hanger …” Truth BR; answer BL. Trace: “The question has me face away from the door, so no turn applies.”
- `1cd67c3595ac310edc7aec5e`, R0-dev. Q: “If I am standing by the shelf and facing away from the plant, is the ceilng lamp bar …” Truth BR; answer FR. Trace: “The question has me face away from the plant, so I keep that heading.”

**Wrong forward relation before correct turn — three examples.**
- `0ccc53f251d06a78b9514e78`, R0-dev. Q: “If I am standing by the scarf and facing away from the fireplace, is the plant pot …” Truth BR; answer FR. Trace: “If I stood at the scarf facing the fireplace, the plant pot would be behind me, on my left.” / “So I find the plant pot at my front-right.”
- `13ac805185f5e0504ebf1580`, R0-dev. Q: “If I am standing by the trash can and facing away from the office chair, is the closet …” Truth BR; answer BL. Trace: “If I stood at the trash can facing the office chair, the closet would be in front of me, on my right.” / “So I find the closet at my back-left.”
- `2df1f139973fd5e8ea07abbe`, R0-dev. Q: “If I am standing by the power sockets and facing away from the computer desk, is the laminator …” Truth FR; answer BR. Trace: “If I stood at the power sockets facing the computer desk, the laminator would be in front of me, on my left.” / “So I find the position of the laminator at my back-right.”

There are no examples for the zero-count usage, runaway, or unparsed modes.

## 4. Step 544 against step 200

| Set | Right→wrong | Wrong→right | Wrong→wrong |
|---|---:|---:|---:|
| dev-S1 | 6 of 150 | 4 of 150 | 20 of 150 |
| R0-dev | 20 of 192 | 43 of 192 | 61 of 192 |

Step 544 states degree measurements on **342 of 342** traces; step 200 does so on **0 of 342**. Step 200 replaces these with verbal relations and an explicit facing clause. On dev-S1 regressions, mean thinking length rises from 58.8 to 68.7 tokens; on improvements, from 57.8 to 67.2. Neither group supplies frame evidence.

R0 improvements include **32 of 43** away items; regressions include **6 of 20** away items. Frame-citing `Seen:` traces appear on **33 of 43** improvements versus **3 of 20** regressions. Mean thinking length rises from 62.5 to 94.7 tokens for improvements and from 62.2 to 77.5 for regressions. These associations do not isolate the effects of length, grounding, and turning.

## 5. Hypotheses

I inspected the assigned `STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json`. The relevant samples contain **120 of 120** kept rows. Below, `H` expands to `object_rel_direction_hard`.

- **HYPOTHESIS — wrong toward relation:** `H|w1g|rows_rebuild_d0_v1` teaches a relation assertion without auditable visual evidence. This family supplies **21,385 of 32,589** hard-direction rows; its sample cites frames on **0 of 20**. Target `q631ec0c8d2907796dc382c99` says: “Step 1: find the backpack, the file cabinet and the books.” Then: “I find the books behind me, on my left.” This supports a grounding concern, but does not prove perception rather than spatial reasoning failed.
- **HYPOTHESIS — retained away heading:** the dominant toward template transfers its “keep that heading” clause into away questions. `H|w1g|rows_rebuild_d0_v1` contains that clause, while `H|rows_rebuild_d0_T1H2_gen_r2|None` provides the correct alternative. Target `vsi590k_105570_away` says: “That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.” The erroneous traces visibly combine away wording with the toward operation.
- **HYPOTHESIS — wrong forward relation:** `H|rows_rebuild_d0_T1H1_gen_r2|None` and `H|r1_away_opp|None` teach the swap successfully but insufficiently constrain its visual premise. Target `vsi590k_099547_away` asserts: “If I stood at the cutting board facing the bookshelf, the paper bag would be in front of me, on my right.” A possible additional bias is that **18 of 20** sampled `r1_away_opp` answers are back quadrants; this sample does not establish the population balance.

## 6. Label or scoring defects

None found in the available checks: option equality disagrees with the recorded score on **0 of 342** items. I did not visually validate ground truth. Frame numbers above 32 are an annotation/trace audit question, not an established label defect.

## 7. Three changes for vehicle N

1. **Add about 2,000 paired rows** to `H|r1_away_opp|None`, including literal “facing away from” wording and both axis swaps. Reject targets that retain the heading. The exact trace-level repair would fix **14 of 21** retained-heading errors, or 7.29 R0-dev points; it would not fix the other **7 of 21** without correcting their forward relation.
2. **Reword about 4,000 rows** in `H|w1g|rows_rebuild_d0_v1` to locate each object with a verified sampled-frame index and distinguishing image region, then justify front/back and left/right separately. This targets **26 of 150** dev-S1 and **46 of 192** R0 errors. Those counts are exposure ceilings, not predicted gains; numeric frame evidence is absent on **71 of 72** affected items.
3. **Add about 2,000 visually checked, quadrant-balanced paired rows** across `H|rows_rebuild_d0_T1H1_gen_r2|None` and `H|rows_rebuild_d0_T1H2_gen_r2|None`. Keep the same verified forward relation in both twins. This targets **14 of 192** errors after correctly executed turns, plus **7 of 192** retained-heading errors that also need a corrected premise. **This is the least certain change:** the traces cannot distinguish visual ambiguity from learned relation bias.

## 8. Not established

The traces cannot establish physical instance confusion, actual first-seen separation, correct frame numbering, or whether an incorrect relation originates in perception or reasoning. Sampled RGB frames, their source-index mapping, and instance-level object annotations would settle these questions. Matched wording variants on identical scenes would test the Cartesian-clause effect. Proposed training gains remain hypotheses.

**Appendix — CLASSIFIER**

```python
import sys, re
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
MODES = ["Wrong toward relation", "Away heading retained",
         "Wrong forward relation before correct turn",
         "Usage mismatch", "Runaway", "Unparsed"]
def option(r, key):
    return next((s.split(". ", 1)[1] for s in r["options"]
                 if s.startswith(str(r[key]) + ". ")), None)
def relations(r):
    t = r["text"].split("</think>")[0]
    c = re.findall(r"(?:front|back)[ -](?:left|right)", t)
    final = c[-1].replace(" ", "-") if c else None
    initial = None
    for line in t.splitlines():
        side = re.search(r"(?:on|to) my (left|right)", line)
        axis = ("front" if re.search(r"in front|ahead", line) else
                "back" if re.search(r"behind|back", line) else None)
        if side and axis:
            initial = axis + "-" + side[1]
            break
    return initial, final
opposite = dict(zip(
    ["front-left", "front-right", "back-left", "back-right"],
    ["back-right", "back-left", "front-right", "front-left"]))
for dataset in ["dev-S1", "R0-dev"]:
    rows = K.direct("R1", 200, dataset,
                    types=["object_rel_direction_hard"])
    counts, costs = Counter(), Counter()
    for r in rows:
        if r["score"] == 1:
            continue
        initial, final = relations(r)
        if r["forced_close"]:
            mode = "Runaway"
        elif not initial or not final or not option(r, "pred"):
            mode = "Unparsed"
        elif final != option(r, "pred"):
            mode = "Usage mismatch"
        elif r["subtype"] != "away":
            assert initial == final
            mode = "Wrong toward relation"
        elif initial == final:
            assert "left and right swap" not in r["text"]
            mode = "Away heading retained"
        else:
            assert final == opposite[initial]
            mode = "Wrong forward relation before correct turn"
        counts[mode] += 1
        costs[mode] += 1 - r["score"]
    assert sum(counts.values()) == sum(r["score"] < 1 for r in rows)
    for mode in MODES:
        print(dataset, mode, f"{counts[mode]} of {len(rows)}",
              f"cost={100*costs[mode]/len(rows):.2f} points")
```