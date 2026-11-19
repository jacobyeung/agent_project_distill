**1. Scope**

Step 200 improves easy-direction accuracy, but its remaining errors occur inside the stated reasoning. Every chosen answer follows the trace’s final left/right conclusion.

| Set | Step 544 correct | Step 200 correct | Change |
|---|---:|---:|---:|
| dev-S1 | 137 of 150; 91.33% | 140 of 150; 93.33% | +2.00 points |
| R0-dev | 126 of 192; 65.63% | 151 of 192; 78.65% | +13.02 points |
| R0-dev toward | 92 of 126; 73.02% | 98 of 126; 77.78% | +4.76 points |
| R0-dev away | 34 of 66; 51.52% | 53 of 66; 80.30% | +28.79 points |

I recomputed scores with `san_kit` and read all 10 of 10 dev-S1 errors and all 41 of 41 R0-dev errors. No official benchmark items were used.
Source prefix `B` is `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build`.
- Step 200: `B/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`, where `main` means dev-S1 and `a7` means R0-dev.
- Step 544 R0-dev: `B/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 544 dev-S1: `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.

**2. Failure modes at step 200**

Costs use the complete set denominator. Each wrong item receives exactly one primary mode.

| Mode | Definition | dev-S1 count; cost | R0-dev count; cost |
|---|---|---:|---:|
| Wrong toward relation | The trace states the wrong side while facing the reference object. | 10 of 150; 6.67 points | 28 of 192; 14.58 points |
| Omitted half-turn | The away trace explicitly keeps the forward heading and side. | 0 of 150; 0.00 points | 5 of 192; 2.60 points |
| Wrong forward relation after valid turn | The away trace correctly reverses its stated side, but that initial side is wrong relative to the label. | 0 of 150; 0.00 points | 8 of 192; 4.17 points |
| Usage failure | The chosen option disagrees with the trace’s final relation. | 0 of 150; 0.00 points | 0 of 192; 0.00 points |
| Format failure | The answer or conclusion is missing/unparsed, or the trace runs away. | 0 of 150; 0.00 points | 0 of 192; 0.00 points |
| **Total** | | **10 of 150; 6.67 points** | **41 of 192; 21.35 points** |

The conclusion parser succeeds on 150 of 150 dev-S1 items and 192 of 192 R0-dev items. Conclusions agree with chosen options throughout. B2048 and ON16k predictions also agree throughout; forced closure occurs on 0 of 150 and 0 of 192 items.

| Set/subtype and truth | Answer left | Answer right |
|---|---:|---:|
| dev-S1: left | 75 of 81 | 6 of 81 |
| dev-S1: right | 4 of 69 | 65 of 69 |
| R0-dev toward: left | 56 of 72 | 16 of 72 |
| R0-dev toward: right | 12 of 54 | 42 of 54 |
| R0-dev away: left | 22 of 27 | 5 of 27 |
| R0-dev away: right | 8 of 39 | 31 of 39 |

On the scored axes, 10 of 10 dev-S1 errors and 41 of 41 R0-dev errors are left/right errors. Front/back-only versus both-axis errors are **not identifiable**: easy-direction labels contain no front/back component.

For away questions, 14 of 66 traces omit the half-turn; 5 of those 14 are wrong and 9 of those 14 are correct despite internally inconsistent reasoning. The remaining 52 of 66 state both axis swaps, and 52 of those 52 actually reverse left/right. Their forward statements contain no front/back relation, so one-axis-only execution cannot be measured. Among these traces, 8 of 52 start from the wrong forward side.

Frame evidence is limited. All 150 of 150 dev-S1 traces merely instruct “find” or “locate,” without frame citations. R0-dev has no frame citation on 118 of 192 items, including 28 of 41 errors; 117 of those 118 use generic “find” instructions. All 192 of 192 R0-dev opening lines name every requested object, but naming does not establish localization.
Among R0-dev traces citing frames, 12 of 61 with an index span ≥32 are wrong, compared with 1 of 13 with a smaller span. All objects share one cited frame on 0 of 74 cited items. These are claimed locations, not first-seen measurements; 67 of 74 cited traces use indices above 32, making temporal interpretation uncertain.
Away wording does not explain the overall R0-dev gap: away errors are 13 of 66, versus 28 of 126 toward errors. R0-dev uses fixed “standing by … facing …” wording; dev-S1 uses paraphrases, but wording and scenes are confounded.
Exact target names absent from dev-S1’s object vocabulary have 29 of 138 errors, versus 12 of 54 for present names. Multiword targets have 17 of 77 errors, versus 24 of 115 single-word targets. Neither comparison isolates an object-name effect. Repeated physical instances cannot be established from these records.

**3. Examples**

Questions below are shortened verbatim. Trace quotations preserve the generated wording.

**Wrong toward relation — examples:**
- `vsi590k_136835`, dev-S1: “Standing next to the keyboard, and facing the telephone, do you see the computer mouse positioned to the left or to the right?” Truth B/left; answer A/right.
  “Step 2: I stand at the keyboard facing the telephone; I find the computer mouse to my right.”
- `vsi590k_251249`, dev-S1: “When I'm at the stool, looking directly toward the stove, is the washer located to the left or right?” Truth A/right; answer B/left.
  “Step 2: I stand at the stool facing the stove; I find the washer to my left.”
- `005f06769343f453a0304a16`, R0-dev: “…standing by the curtain rail and facing the side table, is the wardrobe to the left or the right…” Truth A/left; answer B/right.
  “Step 2: I stand at the curtain rail facing the side table; I find the wardrobe to my right.”

**Omitted half-turn — examples:**
- `05d90f7d09554791b4f0df2f`, R0-dev: “…standing by the book and facing away from the headphones, is the basket to my left or to my right?” Truth A/left; answer B/right.
  “The question has me face away from the headphones, so I keep that heading.” / “So I find the basket to my right.”
- `138dad9a1e4405439c81f484`, R0-dev: “…standing by the shower curtain rod and facing away from the power sockets, is the toilet brush to my left or to my right?” Truth B/left; answer A/right.
  “The question has me face away from the power sockets, so I keep that heading.” / “So I find the toilet brush to my right.”
- `55a3cbf424aada9e27880aad`, R0-dev: “…standing by the oven and facing away from the soap, is the bench to my left or to my right?” Truth A/left; answer B/right.
  “The question has me face away from the soap, so I keep that heading.” / “So I find the bench to my right.”

**Wrong forward relation after valid turn — examples:**
- `0482b66651468047fbcc3b62`, R0-dev: “…standing by the window wiper and facing away from the telephone, is the liquid soap bottle to my left or to my right?” Truth A/left; answer B/right.
  “If I stood at the window wiper facing the telephone, the liquid soap bottle would be to my left.” / “So I find the position of the liquid soap bottle to my right.”
- `11064bd249620f904ad791e9`, R0-dev: “…standing by the table and facing away from the storage box, is the faucet to my left or to my right?” Truth B/right; answer A/left.
  “If I stood at the table facing the storage box, the faucet would be to my right.” / “So I find the faucet to my left.”
- `4505ca80756e9f25d8f6f37b`, R0-dev: “…standing by the heater and facing away from the coat hanger, is the picture to my left or to my right?” Truth B/right; answer A/left.
  “If I stood at the heater facing the coat hanger, the picture would be to my right.” / “So I find the picture to my left.”

Usage and format failures have no examples because none occur.

**4. Step 544 against step 200**

| Set | Right to wrong | Wrong to right | Wrong to wrong | Right to right |
|---|---:|---:|---:|---:|
| dev-S1 | 2 of 150 | 5 of 150 | 8 of 150 | 135 of 150 |
| R0-dev | 15 of 192 | 40 of 192 | 26 of 192 | 111 of 192 |

All 7 of 7 dev-S1 flips replace an asserted angle with a side assertion and heading clause; mean thinking length increases from 58.14 to 63.14 tokens. The stated side changes, so these are not answer-mapping repairs.
All 55 of 55 R0-dev flips likewise remove angle assertions; mean thinking length increases from 61.04 to 82.40 tokens. Toward flips comprise 13 of 126 improvements and 7 of 126 regressions.
Away flips comprise 27 of 66 improvements and 8 of 66 regressions. Explicit half-turn traces account for 23 of those 27 improvements and 6 of those 8 regressions. A valid turn helps only when the conditional forward side is correct.

**5. Hypotheses**

Evidence comes from `STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json` under `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`. All 120 of 120 sampled easy-direction rows are marked kept, and all 120 of 120 conclusions match their answer options.

**HYPOTHESIS — wrong toward relation:** The dominant generic template teaches a side assertion without observable localization evidence. The family `object_rel_direction_easy|w1g|rows_rebuild_d0_v1` retains 12,969 of 12,969 rows; 20 of 20 sampled targets omit frames. Row `qf11f7d65d5bc1a08adadf56f-p1` says: “Step 1: find the desk, the window and the mirror.” Then: “I find the mirror to my right.” This resembles every dev-S1 error, but does not distinguish perception from spatial reasoning.
**HYPOTHESIS — omitted half-turn:** The model sometimes extends that family’s “keep that heading” clause to away wording. Correct supervision exists in `object_rel_direction_easy|rows_rebuild_d0_T1H1_gaps|None`: row `vsi590k_041500_away` states “the printer would be to my left,” then “That is a half turn,” and concludes “So I find the printer to my right.” The failure suggests inconsistent template selection, not missing instruction alone.
**HYPOTHESIS — wrong forward relation after valid turn:** Frame citations and a correct reversal do not ensure a correct observer-relative relation. In `object_rel_direction_easy|rows_rebuild_d0_T0_gaps|None`, row `vsi590k_035483_away` says “Seen: bookshelf in frame 11; lamp in frame 17; desk in frame 4,” then “the desk would be to my right.” That jump still lacks an auditable spatial connection between the cited views.

**6. Label or scoring defects**

None found in the inspected text: stored scores agree with option-letter equality on 150 of 150 dev-S1 items and 192 of 192 R0-dev items. This does not validate scene geometry.
A separate trace defect needs investigation: `11064bd249620f904ad791e9` cites frame 101, `4505ca80756e9f25d8f6f37b` cites frame 212, and `1aefd2f19de4b011cad95002` cites frame 367. These exceed the stated input size. Original-video indexing could explain them; the frame mapping is unavailable.

**7. Three changes for vehicle N**

The row budgets below are **guesses**. Addressable error counts are diagnostic ceilings, not predicted gains. Build rows from training scenes rather than these dev items.
1. **Reword about 3,000 of 12,969 `object_rel_direction_easy|w1g|rows_rebuild_d0_v1` rows.** Replace generic “find” instructions with verified object-instance localization and a concise observer-relative relation. This targets 10 of 150 dev-S1 errors and 23 of 192 R0-dev errors whose toward traces provide no frame evidence.
2. **Add about 1,000 matched toward/away rows to `object_rel_direction_easy|rows_rebuild_d0_T1H1_gaps|None`.** Share the verified forward relation, vary away paraphrases, and require an explicit side reversal. This targets 5 of 192 R0-dev errors. Do not blindly flip existing outputs: that would damage the 9 of 14 omitted-turn traces whose final answers are already correct.
3. **Reword about 1,000 of 6,428 `object_rel_direction_easy|rows_rebuild_d0_T0_gaps|None` rows with verified frame mappings and object-instance descriptions.** This targets the remaining 13 of 192 R0-dev errors with frame citations: 5 of 126 toward and 8 of 66 away. **I am least sure of this change:** citations may be cosmetic, and the underlying failure may require better visual representations.

**8. Not established**

The traces cannot separate incorrect object recognition, instance selection, scene reconstruction, and observer-frame reasoning. Sampled RGB frames, object-instance annotations, and verified geometry would settle that distinction.
First-seen separation, repeated observer/target instances, and front/back execution remain unmeasured. They require frame-index mappings, instance identities, and labels or traces containing both axes.
The proposed training changes have no measured causal benefit. A controlled continuation with matched training-row budgets would test them.

**Appendix — CLASSIFIER**

```python
import sys, re
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

MODES = [
    "Wrong toward relation",
    "Omitted half-turn",
    "Wrong forward relation after valid turn",
    "Usage failure",
    "Format failure",
]

def option_word(r, key):
    return next((o[3:].strip().lower() for o in r["options"]
                 if o.startswith(str(r[key]) + ".")), None)

def conclusion(r):
    text = (r["text"] or "").split("</think>")[0]
    words = re.findall(r"(?m)^So .*?\b(left|right)\b", text)
    return words[-1] if words else None

def classify(r):
    if r["score"] == 1:
        return None
    c = conclusion(r)
    if r["forced_close"] or not r["pred"] or c is None:
        return "Format failure"
    if c != option_word(r, "pred"):
        return "Usage failure"
    if r["subtype"] != "away":
        return "Wrong toward relation"
    if "half turn" not in r["text"]:
        assert "so I keep that heading" in r["text"]
        return "Omitted half-turn"
    f = re.search(r"would be to my (left|right)", r["text"])
    assert f and f.group(1) != c
    return "Wrong forward relation after valid turn"

for name in ("dev-S1", "R0-dev"):
    rows = K.direct("R1", 200, name,
                    types=["object_rel_direction_easy"])
    assigned = [(r, classify(r)) for r in rows]
    assert sum(m is not None for _, m in assigned) == sum(
        r["score"] < 1 for r in rows)
    for mode in MODES:
        selected = [r for r, m in assigned if m == mode]
        cost = 100 * sum(1 - r["score"] for r in selected) / len(rows)
        print(f"{name}: {mode}: {len(selected)} of {len(rows)}; "
              f"{cost:.2f} points")
```