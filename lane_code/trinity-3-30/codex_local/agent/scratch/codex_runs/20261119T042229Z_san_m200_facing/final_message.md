## 1. Scope

The remaining twin-away errors begin in the stated forward relation. R0-dev also retains an explicit failure to turn. I classified every wrong item, using B2048 scores.

| Set | Easy: step 544 → step 200 | Medium: step 544 → step 200 | Hard: step 544 → step 200 |
|---|---|---|---|
| Away twins | 19 of 50 (38%) → 47 of 50 (94%) | 10 of 50 (20%) → 45 of 50 (90%) | 3 of 50 (6%) → 41 of 50 (82%) |
| Forward twins | 49 of 50 (98%) → 49 of 50 (98%) | 47 of 50 (94%) → 48 of 50 (96%) | 46 of 50 (92%) → 43 of 50 (86%) |
| R0-dev away | 34 of 66 (51.52%) → 53 of 66 (80.30%) | 12 of 65 (18.46%) → 38 of 65 (58.46%) | 10 of 71 (14.08%) → 36 of 71 (50.70%) |

Overall, away twins improve from 32 of 150 (21.33%) to 133 of 150 (88.67%); forward twins change from 142 of 150 (94.67%) to 140 of 150 (93.33%); R0-dev away improves from 56 of 202 (27.72%) to 127 of 202 (62.87%).

I recomputed these from the following files. Paths below share `/scratch/jjyeung/orch_n30/`; braces enumerate files actually read.
- Step-200 twins: `cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched/x/{away,forward}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step-544 twins: `evalx27/work/pull/x27/res/e193/merged/{away,forward}/results/budget_2048/0/items_leg_m544_{away,forward}.jsonl`, matching each set name.
- Step-200 R0-dev: `cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step-544 R0-dev: `cont_ops16/work/c15/h1read/kit/build/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.

## 2. Failure modes at step 200

Each cell gives the mode’s item count, followed by its **easy / medium / hard percentage-point cost**, using each level’s denominator from Scope. “Turn omitted” takes precedence when an item also has a wrong initial relation.

| Mode | Definition | Away twins | Forward twins | R0-dev away |
|---|---|---|---|---|
| Side/quadrant | An easy/hard trace states a wrong forward side or quadrant, then consistently derives its answer. | 12 of 150; **6 / 0 / 18 pp** | 8 of 150; **2 / 0 / 14 pp** | 22 of 202; **12.12 / 0 / 19.72 pp** |
| Medium band/side | A medium trace states a wrong forward band or side, then consistently maps it to an option. | 5 of 150; **0 / 10 / 0 pp** | 2 of 150; **0 / 4 / 0 pp** | 22 of 202; **0 / 33.85 / 0 pp** |
| Turn omitted | An away trace explicitly keeps the forward heading or says no turn applies. | 0 of 150; **0 / 0 / 0 pp** | 0 of 150; **0 / 0 / 0 pp** | 31 of 202; **7.58 / 7.69 / 29.58 pp** |

These account for 17 of 150 away errors, 10 of 150 forward errors, and 75 of 202 R0-dev-away errors. Answer–conclusion mismatches, runaways, missing answers, and unparsed answers each occur on 0 of 502 items. B2048 and ON16k predictions agree on 502 of 502 items.

**Twin pairing.** I matched the suffix after `backdir_` and `forwardtwin_`, such as `vsi590k_010414`. All 150 of 150 pairs have matching rooms and option orders.

| Level | Both right | Forward right, away wrong | Forward wrong, away right | Both wrong |
|---|---|---|---|---|
| Easy | 47 of 50 | 2 of 50 | 0 of 50 | 1 of 50 |
| Medium | 44 of 50 | 4 of 50 | 1 of 50 | 1 of 50 |
| Hard | 41 of 50 | 2 of 50 | 0 of 50 | 7 of 50 |

The premise that forward-right/away-wrong necessarily identifies a failed half-turn does **not** hold here. Among those 8 of 150 pairs, the away trace changes or adds forward-relation detail on 6 of 8. On the other 2 of 8 (`116311`, `128783`), both traces state the same wrong medium band; the forward answer remains correct because its option hides that band error.

Relative to the relation actually written, failed front/back swaps occur on 0 of 8, failed left/right swaps on 0 of 8, and failures of both swaps on 0 of 8. At the answer level, discrepancies comprise a hard front/back error on 1 of 8, an easy/hard side error on 3 of 8, a medium band error on 3 of 8, and a medium side error on 1 of 8.

Away twins write a conditional forward relation and explicit half-turn on 150 of 150 items. R0-dev away writes a forward relation on 202 of 202, the conditional-plus-“half turn” form on 159 of 202, another explicit reversal on 1 of 202, and an explicit no-turn instruction on 42 of 202. Among wrong away twins, the stated relations match their forward twins on 11 of 17 and differ in detail on 6 of 17.

**Hard confusion tables.** Columns within each cell are answers **front-left, front-right, back-left, back-right**, respectively; denominators are truth-row totals.

| Truth | Away twins | Forward twins | R0-dev away |
|---|---|---|---|
| Front-left | 5 of 8; 1 of 8; 2 of 8; 0 of 8 | 18 of 18; 0 of 18; 0 of 18; 0 of 18 | 3 of 5; 0 of 5; 1 of 5; 1 of 5 |
| Front-right | 0 of 9; 4 of 9; 2 of 9; 3 of 9 | 0 of 15; 15 of 15; 0 of 15; 0 of 15 | 0 of 5; 2 of 5; 1 of 5; 2 of 5 |
| Back-left | 0 of 15; 0 of 15; 15 of 15; 0 of 15 | 2 of 9; 2 of 9; 5 of 9; 0 of 9 | 4 of 31; 8 of 31; 15 of 31; 4 of 31 |
| Back-right | 0 of 18; 0 of 18; 1 of 18; 17 of 18 | 0 of 8; 2 of 8; 1 of 8; 5 of 8 | 4 of 30; 4 of 30; 6 of 30; 16 of 30 |

Away-hard twins answer “back” on 40 of 50 (80%) against truths on 33 of 50 (66%). Forward-hard answers contain “back” on 11 of 50 (22%) against truths on 17 of 50 (34%). R0-dev away-hard answers contain “back” on 46 of 71 (64.79%) against truths on 61 of 71 (85.92%): it **underuses** back overall. Among wrong away-hard twins, 7 of 9 replace a front truth with a back answer.

**Wording variants.** Only object names are replaced in this verbatim template: “If I am standing by the {X} and {heading} the {Y}, is the {Z} {ending}”. Away-easy ends “to my left or to my right?”; forward-easy ends “to the left or the right of the {Y}?”; medium ends “to my left, right, or back?”; hard ends “to my front-left, front-right, back-left, or back-right?”

Every medium question appends: “An object is to my back if I would have to turn at least 135 degrees in order to face it.” Every hard question appends: “The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).”

| Set and exact heading | Easy accuracy | Medium accuracy | Hard accuracy |
|---|---|---|---|
| Away: “facing away from” | 21 of 22 (95.45%) | 11 of 14 (78.57%) | 15 of 18 (83.33%) |
| Away: “facing directly away from” | 6 of 8 (75%) | 19 of 20 (95%) | 16 of 19 (84.21%) |
| Away: “facing in the opposite direction of” | 20 of 20 (100%) | 15 of 16 (93.75%) | 10 of 13 (76.92%) |
| Forward: “facing” | 49 of 50 (98%) | 48 of 50 (96%) | 43 of 50 (86%) |
| R0-dev away: “facing away from” | 53 of 66 (80.30%) | 38 of 65 (58.46%) | 36 of 71 (50.70%) |

These enumerate every structural wording variant observed. R0-dev uses exactly the plain twin-away wording. Its hard variant performs worst overall; twin easy “directly away” performs worst within twins. These comparisons confound wording with scene and object selection.

## 3. Examples

Questions below omit only long endings or explanatory footers. Trace quotations are verbatim excerpts.
- **Side/quadrant — away, `backdir_vsi590k_010414`.** Q: “If I am standing by the towel and facing away from the window, is the washing machine …?” Truth: front-right; answer: back-right. Trace: “the washing machine would be in front of me, on my left.” / “So I find the washing machine at my back-right.”
- **Side/quadrant — forward, `forwardtwin_vsi590k_093926`.** Q: “If I am standing by the trash can and facing the telephone, is the keyboard …?” Truth: back-left; answer: front-left. Trace: “I find the keyboard in front of me, on my left.” / “So I find the keyboard at my front-left.”
- **Side/quadrant — R0-dev away, `0482b66651468047fbcc3b62`.** Q: “If I am standing by the window wiper and facing away from the telephone, is the liquid soap bottle …?” Truth: left; answer: right. Trace: “the liquid soap bottle would be to my left.” / “So I find the position of the liquid soap bottle to my right.”
- **Medium band/side — away, `backdir_vsi590k_116311`.** Q: “If I am standing by the blanket and facing away from the whiteboard, is the plant to my left, right, or back?” Truth: right; answer: back. Trace: “the plant would be ahead of me, slightly to my left.” / “So I find the plant at my back.”
- **Medium band/side — forward, `forwardtwin_vsi590k_127822`.** Q: “If I am standing by the headphones and facing the plant, is the mouse to my left, right, or back?” Truth: back; answer: left. Trace: “Standing at the headphones facing the plant, I find the mouse out to my left.” / “So I find the mouse to my left.”
- **Medium band/side — R0-dev away, `ae318897fcb2976db57d3c2c`.** Q: “If I am standing by the monitor and facing away from the kettle, is the jacket to my left, right, or back?” Truth: right; answer: back. Trace: “the jacket would be ahead of me, slightly to my left.” / “So I find the jacket at my back.”
- **Turn omitted — R0-dev away, `05d90f7d09554791b4f0df2f`.** Q: “If I am standing by the book and facing away from the headphones, is the basket to my left or to my right?” Truth: left; answer: right. Trace: “I find the basket to my right.” / “The question has me face away from the headphones, so I keep that heading.”
- **Turn omitted — R0-dev away, `12396a66724db9c049323e18`.** Q: “If I am standing by the soap dispenser and facing away from the soap, is the door to my left, right, or back?” Truth: left; answer: right. Trace: “I find the door out to my right.” / “The question has me face away from the soap, so I keep that heading.”
- **Turn omitted — R0-dev away, `81a23caf9995607ca60fd8e6`.** Q: “If I am standing by the air purifier and facing away from the cabinet, is the door frame …?” Truth: back-left; answer: front-right. Trace: “I find the door frame in front of me, on my right.” / “The question has me face away from the cabinet, so I keep that heading.”

## 4. Step 544 against step 200

| Set | Right → wrong | Wrong → right | Wrong → wrong |
|---|---|---|---|
| Away twins | 6 of 150 | 107 of 150 | 11 of 150 |
| Forward twins | 4 of 150 | 2 of 150 | 6 of 150 |
| R0-dev away | 20 of 202 | 91 of 202 | 55 of 202 |

Every flipped item’s step-544 trace states a degree measurement. Among improvements, step 200 writes an explicit “half turn” on 107 of 107 away twins and 87 of 91 R0-dev-away items. Median think lengths for those improvements change from 61 to 97 tokens and from 65 to 99 tokens, respectively. Forward improvements change from a wrong measured relation to a correct verbal relation; their median length changes from 61.5 to 71.5 tokens.

All 6 of 6 away-twin regressions still execute the written half-turn correctly. Their initial relation changes adversely, as `010414` illustrates. R0-dev regressions include 15 of 20 with the half-turn form and 5 of 20 with omitted turns. The remaining twin-away errors share short, internally consistent traces whose initial spatial claims disagree with the labels.

## 5. Hypotheses

Training evidence comes from the supplied `dist_diag/work/q2/STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json`, plus the ruling’s Answer and §2.3.
- **HYPOTHESIS — Side/quadrant:** weak spatial reconstruction combines with a forward-front prior. In the sampled hard generated families, away answers contain back on 34 of 40 away rows. Family `object_rel_direction_hard|rows_rebuild_d0_T1H2_gen_r2|None`, kept row `i=125565`, teaches: “the door would be in front of me, on my left.” / “So I find the door at my back-right.” This supports a prior hypothesis, not proof that the target is defective.
- **HYPOTHESIS — Medium band/side:** the model learns the band-to-answer mapping more reliably than the visual band itself. Family `object_rel_direction_medium|rows_rebuild_d0_T1H2_gen_r2|None`, kept row `i=140823`, teaches: “the door would be ahead of me, slightly to my left.” / “So I find the door at my back.” The same mapping is applied correctly to wrong bands in the cited errors.
- **HYPOTHESIS — Turn omitted:** the toward trace template generalizes into away questions, particularly on R0-dev objects/scenes. Family `object_rel_direction_hard|w1g|rows_rebuild_d0_v1`, kept row `i=0`, teaches: “The question has me facing the file cabinet; I keep that heading.” Its sampled questions are toward on 20 of 20 rows. The failing away traces reuse this legitimate toward instruction.

## 6. Label or scoring defects

None found in the text, options, or scoring checks. Easy/hard twin labels are exact half-turn counterparts on 100 of 100 pairs; medium label transitions are geometrically feasible on 50 of 50 pairs. Labels and options remain unchanged between checkpoints on 502 of 502 items. This does not verify the labels against RGB or source geometry.

## 7. Three changes for vehicle N

Proposed row quantities are guesses. The affected-item counts below are diagnostic ceilings, not predicted gains.
1. **Add clause-matched toward/away pairs to `object_rel_direction_{easy,medium,hard}|w1g|rows_rebuild_d0_v1`; approximately 2,400 rows.** Require the heading clause to select “keep” versus “half turn,” with identical forward evidence. Correcting only the turn fixes 21 of 31 turn-omission errors; the other 10 of 31 also require a relation correction. Do not blanket-flip outputs.
2. **Rebalance and reword easy/hard generated pairs; approximately 2,400 rows.** Use `object_rel_direction_easy|rows_rebuild_d0_{T0,T1H1,T1H2,ARKIT}_gaps|None` and the corresponding hard `..._gen_r2|None` families. Balance forward front/back sectors and sides, preserve the same relation across twins, and ground that relation in visible evidence. This targets 12 of 150 away, 8 of 150 forward, and 22 of 202 R0-dev-away errors.
3. **Add medium pairs that distinguish “ahead,” “out to,” and “behind” while preserving side; approximately 1,600 rows.** Use `object_rel_direction_medium|rows_rebuild_d0_{T0,T1H1,T1H2,ARKIT}_gen_r2|None`. These target 5 of 150 away, 2 of 150 forward, and 22 of 202 R0-dev-away errors. I am least sure of this change: extra verbal supervision may not improve the underlying visual band estimate.

## 8. Not established

I did not inspect RGB or source geometry, so I cannot separate object-identification failures, viewpoint reconstruction errors, boundary errors, and incorrect geometric labels. Matched frame/geometry audits would settle that distinction. Controlled paraphrases of identical scenes would isolate wording effects; training ablations would establish whether the proposed row changes improve accuracy.

## Appendix — CLASSIFIER

```python
import sys, re
from collections import Counter
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

types = ["object_rel_direction_" + x for x in ("easy", "medium", "hard")]
sets = {s: K.facing("R1", 200, s) for s in ("away", "forward")}
sets["R0-away"] = [
    r for r in K.direct("R1", 200, "R0-dev", types=types)
    if r["subtype"] == "away"
]
names = ("Side/quadrant", "Medium band/side", "Turn omitted")

def classify(r, name):
    text = r["text"]
    skipped = ("so I keep that heading" in text or "so no turn applies" in text)
    skipped = skipped and "flip forward to backward" not in text
    if name != "forward" and skipped:
        return "Turn omitted"
    return "Medium band/side" if r["type"].endswith("medium") else "Side/quadrant"

for name, rows in sets.items():
    wrong = [r for r in rows if r["score"] < 1]
    assert all(not r["forced_close"] and r["pred"] is not None for r in rows)
    for r in rows:
        line = next(x for x in r["text"].splitlines() if x.startswith("So "))
        relation = re.search(
            r"(front-left|front-right|back-left|back-right|left|right|back)\.$",
            line,
        )
        answer = next(o[3:] for o in r["options"]
                      if o.startswith(r["pred"] + ". "))
        assert relation and relation.group(1) == answer
    counts = Counter(classify(r, name) for r in wrong)
    assert sum(counts.values()) == len(wrong)
    for mode in names:
        print(name, mode, f"{counts[mode]} of {len(rows)}")
        for level in ("easy", "medium", "hard"):
            group = [r for r in rows if r["type"].endswith(level)]
            errors = [r for r in group
                      if r["score"] < 1 and classify(r, name) == mode]
            cost = 100 * sum(1 - r["score"] for r in errors) / len(group)
            print(" ", level, f"{len(errors)} of {len(group)}; {cost:.2f} pp")
```