**1. Scope**

Step 200 follows its stated conclusions reliably, but often states the wrong spatial relation. R0-dev improves substantially over step 544 while remaining below dev-S1.

| Set | Step 544 accuracy | Step 200 accuracy |
|---|---:|---:|
| dev-S1 | 134 of 150; 89.33% | 132 of 150; 88.00% |
| R0-dev | 95 of 194; 48.97% | 126 of 194; 64.95% |
| R0-dev toward | 83 of 129; 64.34% | 88 of 129; 68.22% |
| R0-dev away | 12 of 65; 18.46% | 38 of 65; 58.46% |

I recomputed these scores with `san_kit` and read all wrong traces: 18 of 150 dev-S1 items and 68 of 194 R0-dev items. B2048 and ON16k predictions agree on 344 of 344 items; forced closure occurs on 0 of 344.

Files read through the loader:
- Step 200: `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 544 R0-dev: the corresponding `a7` paths under build `adff67f7ae9`.
- Step 544 dev-S1: `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.

**2. Failure modes**

Each wrong item receives exactly one primary mode. Costs are percentage points of the complete type/set.

| Mode | Definition | dev-S1 count; cost | R0-dev count; cost |
|---|---|---:|---:|
| Toward side error | The stated relation and answer swap left/right. | 10 of 150; 6.67 | 26 of 194; 13.40 |
| Toward back-band error | The stated relation and answer confuse back with a side. | 8 of 150; 5.33 | 15 of 194; 7.73 |
| Away forward-relation error | The half-turn correctly transforms a forward relation that implies the wrong answer. | 0 of 150; 0.00 | 22 of 194; 11.34 |
| Away omitted turn | The trace faces the reference object and explicitly keeps that heading despite “away.” | 0 of 150; 0.00 | 5 of 194; 2.58 |
| **Total wrong** | | **18 of 150; 12.00** | **68 of 194; 35.05** |

The conclusion’s direction maps to the chosen option on 344 of 344 items. Usage failures therefore account for 0 of 150 and 0 of 194; missing answers, unparsed conclusions, and runaways also account for 0 of 150 and 0 of 194.

The confusion table uses each truth category as its denominator.

| Set/subtype | Truth | Answer left | Answer right | Answer back |
|---|---|---:|---:|---:|
| dev-S1 | left | 71 of 78 | 6 of 78 | 1 of 78 |
| dev-S1 | right | 4 of 63 | 59 of 63 | 0 of 63 |
| dev-S1 | back | 4 of 9 | 3 of 9 | 2 of 9 |
| R0 toward | left | 40 of 62 | 18 of 62 | 4 of 62 |
| R0 toward | right | 8 of 50 | 42 of 50 | 0 of 50 |
| R0 toward | back | 5 of 17 | 6 of 17 | 6 of 17 |
| R0 away | left | 5 of 7 | 2 of 7 | 0 of 7 |
| R0 away | right | 4 of 19 | 13 of 19 | 2 of 19 |
| R0 away | back | 8 of 39 | 11 of 39 | 20 of 39 |

At the answer-category level, left/right swaps explain 10 of 18 dev-S1 errors and 32 of 68 R0-dev errors. Back-versus-side confusion explains the remaining 8 of 18 and 36 of 68. **The requested geometric “front/back only” versus “both axes” split is not identifiable:** a medium `back` label hides its side, and a `left/right` label hides its front/back component.

For away questions, 5 of 65 traces omit the half-turn. Among the remaining 60 of 65, all produce the correct medium-category transformation of their written forward relation; 22 of 60 nevertheless answer incorrectly. I found one-axis-only violations in 0 of 60. This checks the observable category transformation: a final `back` answer does not expose its left/right component.

Frame citations do not establish a temporal-separation failure. dev-S1 cites frames on 0 of 150 items. R0-dev gives numeric frame triples on 72 of 194, with errors on 22 of 72; all three citations coincide on 0 of 72. Among away triples, a cited span above 16 has errors on 16 of 48, versus 5 of 10 for spans at most 16. The cutoff is an analyst-chosen diagnostic, not a validated threshold.

The traces often name objects without locating them: this occurs on 150 of 150 dev-S1 items and 119 of 194 R0-dev items, with errors on 18 of 150 and 45 of 119 respectively. R0-dev omits an object name from its opening line on 0 of 194 items. Citations exceed 32 on 61 of 194 items; their indexing convention needs verification before interpreting them as input-frame evidence.

R0-dev’s lower accuracy is not explained entirely by “away”: toward accuracy is also lower. Its fixed “If I am standing by…” wording appears on 194 of 194 questions, versus 0 of 150 dev-S1 questions, but that wording is present in training samples. Object vocabulary shifts substantially: at least one object name falls outside the dev-S1 object vocabulary on 191 of 194 R0-dev items. Yet unseen target names do not show a consistent penalty: toward errors occur on 29 of 98 unseen-target items versus 12 of 31 shared-target items; away errors occur on 18 of 42 versus 9 of 23. Repeated physical instances cannot be counted from these texts.

**3. Examples**

Questions below are verbatim excerpts, shortened at clause boundaries. Truth and answer include the option’s direction.

**Toward side error**
- `vsi590k_124960`, dev-S1. Q: “If I'm next to the heater, looking towards the paper bag, is the slippers on my left, right, or behind me?” Truth C/right; answer B/left. Trace: “I find the slippers ahead of me, slightly to my left.”
- `vsi590k_125260`, dev-S1. Q: “Standing near the bucket, directing my view towards the microwave, is the toilet located left, right, or behind?” Truth C/left; answer A/right. Trace: “I find the toilet out to my right.”
- `01b59eefa37623984d2ca21a`, R0-dev. Q: “If I am standing by the mattress and facing the kitchen appliance, is the door to my left, right, or back?” Truth A/left; answer B/right. Trace: “I find the door out to my right.”

**Toward back-band error**
- `vsi590k_017390`, dev-S1. Q: “If I am near the counter, turned toward the microwave, is the guitar found on my left, right, or rear?” Truth B/left; answer A/back. Trace: “I find the guitar behind me.”
- `vsi590k_241555`, dev-S1. Q: “From my place by the dishwasher, facing the stove, is the table on my left side, right side, or behind?” Truth C/back; answer B/right. Trace: “I find the table out to my right.”
- `03a29ec19b0d6b9a32ffbf1b`, R0-dev. Q: “If I am standing by the smoke detector and facing the table, is the bookshelf to my left, right, or back?” Truth A/back; answer C/left. Trace: “I find the bookshelf out to my left.”

**Away forward-relation error**
- `07889b044e703f2aafb94f3f`, R0-dev. Q: “If I am standing by the tray and facing away from the bed, is the standing lamp to my left, right, or back?” Truth A/back; answer C/left. Trace: “the standing lamp would be behind me, on my right.” / “So I find the standing lamp to my left.”
- `087cf9e308ea209659af1633`, R0-dev. Q: “If I am standing by the smoke detector and facing away from the lint roller, is the paper bag to my left, right, or back?” Truth A/left; answer C/right. Trace: “the paper bag would be out to my left.” / “So I find the paper bag to my right.”
- `8dd1b1ead0e432cb4db35c04`, R0-dev. Q: “If I am standing by the wardrobe and facing away from the bed, is the extension cord to my left, right, or back?” Truth C/right; answer A/back. Trace: “the extension cord would be ahead of me, slightly to my right.” / “So I find the extension cord at my back.”

**Away omitted turn**
- `12396a66724db9c049323e18`, R0-dev. Q: “If I am standing by the soap dispenser and facing away from the soap, is the door to my left, right, or back?” Truth C/left; answer A/right. Trace: “The question has me face away from the soap, so I keep that heading.”
- `2ccca92044a1d59e5feff625`, R0-dev. Q: “If I am standing by the cabinet and facing away from the subway tunnel, is the window to my left, right, or back?” Truth B/back; answer A/right. Trace: “The question has me face away from the subway tunnel, so I keep that heading.”
- `8b303794ed451186d5960b3f`, R0-dev. Q: “If I am standing by the air purifier and facing away from the cabinet, is the first aid box to my left, right, or back?” Truth C/back; answer A/right. Trace: “I find the first aid box ahead of me, slightly to my right.” / “The question has me face away from the cabinet, so I keep that heading.”

**4. Step 544 against step 200**

| Set | Right→wrong | Wrong→right | Wrong→wrong | Right→right |
|---|---:|---:|---:|---:|
| dev-S1 | 5 of 150 | 3 of 150 | 13 of 150 | 129 of 150 |
| R0-dev | 14 of 194 | 45 of 194 | 54 of 194 | 81 of 194 |

Step 544 states angles on 67 of 67 flipped items; step 200 substitutes qualitative relations. Mean think lengths for dev-S1 regressions remain 66 tokens at both checkpoints; improvements change from 66 to 64.3. R0-dev regressions change from 69 to 79 tokens; improvements change from 69.5 to 90.6.

Away items account for 32 of 45 R0-dev improvements and 6 of 14 regressions. The explicit forward-relation/half-turn form accompanies the gains, but does not guarantee the forward relation. For example, `8dd1b1ead0e432cb4db35c04` changes from the correct away relation “117 degrees right” to an incorrect forward “ahead” relation that correctly rotates into `back`.

**5. Hypotheses**

I read the medium-direction samples in `STORE_V7_SAMPLES20.json` and their counts in `STORE_V7_TEMPLATE_COUNTS.json`, both under `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`. All 120 of 120 sampled rows are marked kept. Family aliases below retain the complete identifiers:
- **W:** `object_rel_direction_medium|w1g|rows_rebuild_d0_v1`.
- **F:** `object_rel_direction_medium|rows_rebuild_d0_T1H2_gen_r2|None`.
- **O:** `object_rel_direction_medium|r1_away_opp|None`.

**HYPOTHESIS—toward side error:** W encourages an unsupported relation assertion after an instruction to find objects. W contains 15,547 of 29,124 medium rows; frame citations occur in 0 of 20 sampled W targets. Row `i=13` says, “Step 1: find the binding machine and the paper stack, then the paper,” followed by “ahead of me, slightly to my right.” This supplies no observable instance selection or view alignment.

**HYPOTHESIS—toward back-band error:** W insufficiently distinguishes lateral placement from the rear band through visual evidence. Row `i=5` jumps from locating names to “I find the wall clock behind me.” The dev traces similarly assert `out to my left/right` on rear-labelled items. This is evidence of missing justification, not proof that the training labels are wrong.

**HYPOTHESIS—away forward-relation error:** F teaches the transformation successfully, but its forward relation does not generalize reliably to R0-dev scenes or objects. Row `i=140823` states, “the door would be ahead of me, slightly to my left,” then concludes, “So I find the door at my back.” The failed dev traces preserve this valid mapping while supplying a wrong premise.

**HYPOTHESIS—away omitted turn:** The dominant W continuation “I keep that heading” sometimes overrides the away clause. O already supplies the counterexample: row `i=197084` says, “That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.” More turn prose alone may therefore be less useful than paired clause contrasts.

**6. Label or scoring defects**

None found in option mapping or answer scoring. Visual ground-truth validity was not established. Large frame indices and the “in question” citations in `27c9d69893799df46bfbce92` and `cea19b1517614b8ab63dae14` are trace-evidence defects or indexing ambiguities, not demonstrated label defects.

**7. Three changes**

1. **Add about 400 paired clause-contrast rows to O; this budget is a guess.** Include “facing away from” alongside “opposite direction,” with identical objects and verified forward relations. This targets 5 of 68 R0-dev errors. Correcting only the turn would fix 2 of 5—`12396a66724db9c049323e18` and `8b303794ed451186d5960b3f`—worth 1.03 R0-dev points. The other 3 of 5 also require a different forward band.
2. **Reword about 2,000 of 15,547 W rows; this budget is a guess.** Replace “find X” with verified frame/instance evidence and include matched observer-heading contrasts. This targets the toward side errors: 10 of 18 dev-S1 errors and 26 of 68 R0-dev errors. Those are addressable cases, not predicted recoveries.
3. **Reword about 600 of 15,547 W rows and 600 of 1,998 F rows around verified band contrasts; these budgets are guesses.** Balance ahead, lateral, and behind cases, preserve the side, and show the post-turn relation before choosing an option. This targets 23 of 86 toward back-band errors plus 22 of 86 away forward-relation errors. **I am least sure of this change:** the texts cannot distinguish mistaken object perception from mistaken spatial reasoning, and band supervision may not repair perception.

**8. Not established**

The traces cannot establish actual first-seen frame gaps, repeated physical instances, or correct object localization. The cited frames are model outputs, not verified observations. Video frames, sampling-index maps, instance annotations, and signed relative bearings would settle those questions and permit the exact two-axis error split. Training changes need controlled validation; the priced modes are recovery ceilings, not expected gains.

**Appendix — CLASSIFIER**

```python
import sys, re
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

TYPE = "object_rel_direction_medium"
MODES = (
    "toward_side",
    "toward_back_band",
    "away_wrong_forward",
    "away_no_turn",
)

def direction(row, key):
    letter = row[key]
    return next(o[3:].strip() for o in row["options"]
                if o.startswith(letter + "."))

for dataset in ("dev-S1", "R0-dev"):
    rows = K.direct("R1", 200, dataset, types=[TYPE])
    counts = Counter()
    costs = Counter()
    for row in rows:
        text = row["text"].split("</think>")[0].strip()
        conclusion = text.splitlines()[-1]
        pred = direction(row, "pred")
        stated = re.findall(r"\b(left|right|back)\b", conclusion)
        assert stated == [pred], (row["id"], "usage/unparsed")
        assert not row["forced_close"], (row["id"], "runaway")
        assert row["pred"] == row["pred_on"]
        if row["score"] == 1:
            continue
        if row["subtype"] == "away":
            if "half turn" not in text:
                assert "keep that heading" in text
                mode = "away_no_turn"
            else:
                forward = text.splitlines()[1]
                assert any(p in forward for p in
                           ("ahead of me", "out to my", "behind me"))
                expected = ("back" if "ahead of me" in forward else
                            "left" if "right" in forward else "right")
                assert expected == pred, (row["id"], "turn mismatch")
                mode = "away_wrong_forward"
        else:
            mode = ("toward_back_band"
                    if "back" in (direction(row, "gt"), pred)
                    else "toward_side")
        counts[mode] += 1
        costs[mode] += 1 - row["score"]
    assert sum(counts.values()) == sum(r["score"] < 1 for r in rows)
    for mode in MODES:
        print(dataset, mode, f"{counts[mode]} of {len(rows)}",
              f"{100 * costs[mode] / len(rows):.2f} points")
    print(dataset, "usage/format failures", f"0 of {len(rows)}")
```