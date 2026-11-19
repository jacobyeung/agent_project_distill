## 1. Scope

Step 200 improves accuracy, but every remaining wrong answer has a wrong ordering endpoint.

| Set | Evaluated | Step 544 correct | Step 200 correct | Change |
|---|---:|---:|---:|---:|
| dev-S1 | 150 of 150 | 106 of 150; 70.67% | 110 of 150; 73.33% | +2.67 points |
| R0-dev | 279 of 279 | 181 of 279; 64.87% | 188 of 279; 67.38% | +2.51 points |

R0-dev closest improves from 120 of 186 to 127 of 186. Farthest stays at 61 of 93.

I recomputed these scores using `san_kit`. With `H=/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build`, the files were:

- Step 200: `H/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 544, R0-dev: `H/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step 544, dev-S1: `/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.

All reported scores use B2048. Step-200 B2048 and ON16k predictions agree on 429 of 429 items.

## 2. Failure modes

I classified all 40 of 150 wrong dev-S1 items and all 91 of 279 wrong R0-dev items. “Adjacent” means truth is second for closest or third for farthest. Answer contradiction takes precedence when both the order and answer mapping fail.

| Primary mode | Definition | dev-S1 count | Cost | R0-dev count | Cost |
|---|---|---:|---:|---:|---:|
| Adjacent order error | The answer follows the wrong endpoint; truth occupies the adjacent rank. | 22 of 150 | 14.67 points | 39 of 279 | 13.98 points |
| Displaced order error | The answer follows the wrong endpoint; truth lies at least two ranks away. | 18 of 150 | 12.00 points | 51 of 279 | 18.28 points |
| Answer contradiction | The emitted letter names a different object from the trace’s selected endpoint. | 0 of 150 | 0.00 points | 1 of 279 | 0.36 points |
| **Total** | Each wrong item appears once. | **40 of 150** | **26.67 points** | **91 of 279** | **32.62 points** |

The contradiction also has a wrong order. Its attributed cost is not recoverable by fixing its letter alone.

**Requested order checks.** The selected ordering endpoint is wrong on 40 of 40 dev-S1 errors and 91 of 91 R0-dev errors. A correct endpoint followed by a wrong answer occurs on 0 of 150 and 0 of 279 items. Explicit closest/farthest reversal occurs on 0 of 150 and 0 of 279 items.

**Truth ranks among wrong items.** For dev-S1 closest, truth ranks second on 22 of 40, third on 12 of 40, and fourth on 6 of 40. For R0-dev closest, those counts are 26 of 59, 20 of 59, and 13 of 59. For R0-dev farthest, truth ranks first on 9 of 32, second on 9 of 32, and third on 14 of 32; the last group includes the contradiction.

**Coverage and format.** Missing order candidates, forced closes, and unparsed answers each occur on 0 of 150 dev-S1 and 0 of 279 R0-dev items. However, 150 of 150 and 279 of 279 traces give a Locate statement only for the reference; no candidate receives its own location. This omission also affects correct answers, so it is a shared weakness rather than a separately priced cause.

**Position distributions at step 200.** Question position means position inside the question’s parenthesized candidate list.

| Set and representation | Predictions | Truth |
|---|---|---|
| dev-S1 letters A/B/C/D | 39 of 150 / 42 of 150 / 30 of 150 / 39 of 150 | 46 of 150 / 34 of 150 / 36 of 150 / 34 of 150 |
| dev-S1 question positions 1/2/3/4 | 45 of 150 / 37 of 150 / 29 of 150 / 39 of 150 | 41 of 150 / 38 of 150 / 32 of 150 / 39 of 150 |
| R0-dev letters A/B/C/D | 85 of 279 / 60 of 279 / 75 of 279 / 59 of 279 | 81 of 279 / 59 of 279 / 72 of 279 / 67 of 279 |
| R0-dev question positions 1/2/3/4 | 68 of 279 / 57 of 279 / 72 of 279 / 82 of 279 | 82 of 279 / 60 of 279 / 68 of 279 / 69 of 279 |

R0-dev predictions shift toward the fourth question position. These marginal distributions do not establish causal position bias.

**Repeated objects.** Actual room multiplicity is unknown. A wording proxy—an object name ending in “s,” excluding “mattress” and “thermos”—has errors on 5 of 26 versus 35 of 124 dev-S1 items, and 27 of 73 versus 64 of 206 R0-dev items. Questions mentioning chair/chairs have errors on 16 of 62 versus 24 of 88 dev-S1 items, and 5 of 18 versus 86 of 261 R0-dev items. These proxies show no consistent concentration. Conditional duplicate instructions occur on 150 of 150 dev-S1 items and 0 of 279 R0-dev items; they do not establish that duplicates exist.

## 3. Examples

Questions below are shortened verbatim excerpts. Trace quotations are verbatim.

**Adjacent order error**

- `vsi590k_069864`, dev-S1. Q: “which one of (table, desk, refrigerator, window) is closest to the closet?” Truth: B, desk. Answer: A, refrigerator.
  > Step 2: the nearest-to-farthest order from the closet is: refrigerator, then desk, then table, then window.
- `12b3606d8b8f52d1f0a49e15`, R0-dev. Q: “which of these objects (door, office table, sofa chair, wardrobe) is the closest to the clothes rail?” Truth: D, wardrobe. Answer: C, door.
  > Step 2: the nearest-to-farthest order from the clothes rail is: door, then wardrobe, then sofa chair, then office table.
- `2c5b2b9f4806d7dcbc0ce847`, R0-dev. Q: “which of these objects (paper, photoframe, postcard, stovetop) is the farthest from the faucet?” Truth: D, paper. Answer: B, photoframe.
  > Step 2: the nearest-to-farthest order from the faucet is: stovetop, then postcard, then paper, then photoframe.

**Displaced order error**

- `vsi590k_282416`, dev-S1. Q: “identify the object from (dishwasher, table, stool, chair) that's closest to the refrigerator.” Truth: A, dishwasher. Answer: D, chair.
  > Step 2: the nearest-to-farthest order from the refrigerator is: chair, then stool, then table, then dishwasher.
- `873ef453f65d671b455ba7db`, R0-dev. Q: “which of these objects (cup, laptop stand, monitor, shelf) is the farthest from the pedestal fan?” Truth: D, shelf. Answer: A, laptop stand.
  > Step 2: the nearest-to-farthest order from the pedestal fan is: shelf, then cup, then monitor, then laptop stand.
- `4ddf6b15d8d833c819cc6770`, R0-dev. Q: “which of these objects (blackboard frame, cardboard, stand, stool) is the closest to the eraser?” Truth: C, blackboard frame. Answer: A, stand.
  > Step 1: find the eraser, first seen in the question.
  > Step 2: the nearest-to-farthest order from the eraser is: stand, then cardboard, then stool, then blackboard frame.

**Answer contradiction**

Only 1 of 429 items exhibits this mode; additional distinct examples do not exist.
- `d6eea8cb010f2e223a6eb0a0`, R0-dev. Q: “which of these objects (panel, picture, router, stool) is the farthest from the whiteboard?” Truth: A, picture. Answer: D, router; panel is option B.
  > Step 2: the nearest-to-farthest order from the whiteboard is: stool, then router, then picture, then panel.
  > The question asks for the farthest: the panel.

## 4. Step 544 against step 200

| Set | Right to wrong | Wrong to right | Wrong to wrong | Right to right |
|---|---:|---:|---:|---:|
| dev-S1 | 9 of 150 | 13 of 150 | 31 of 150 | 97 of 150 |
| R0-dev | 19 of 279 | 26 of 279 | 72 of 279 | 162 of 279 |

Step 544 states a metre value for every candidate on 22 of 22 flipped dev-S1 items and 45 of 45 flipped R0-dev items. Step 200 instead states a complete verbal order, with metre values on 0 of 22 and 0 of 45 flipped items.

For dev-S1 regressions, mean think length falls from 77.9 to 59.2 tokens; for improvements, from 76.5 to 58.3. R0-dev means fall from 79.5 to 61.2 for regressions and from 80.5 to 61.5 for improvements.

The values and orders change in both directions. On `vsi590k_204876`, step 544 writes “plant 0.63 m” and “heater 0.36 m”; step 200 puts plant before heater and becomes wrong. On `vsi590k_073232`, step 544 writes “chair 0.66 m” and “window 0.25 m”; step 200 puts chair first and becomes correct. These are model-generated values, not verified measurements.

Step 544 explicitly concludes “The closest is” on 14 of 93 farthest items. Step 200 does so on 0 of 93. This reversal disappears on 5 of 26 R0-dev improvements, but farthest accuracy remains 61 of 93. Removing metres alone therefore does not explain the net gain.

## 5. Hypotheses

The relevant family is **`object_rel_distance|w1g|rows_rebuild_d0_v1`**. `STORE_V7_TEMPLATE_COUNTS.json` reports 20,665 of 20,665 rows kept. I inspected the supplied samples and a primary-key sample from `rows.sqlite`, covering 119 of 20,665 distinct rows. Farthest questions occur on 0 of 119 sampled rows; this is not a census.

- **HYPOTHESIS—adjacent errors:** The target teaches an asserted ranking without evidence distinguishing the leading alternatives. Row `qe9607f3d46dcc20440d27cf0` says: “the nearest-to-farthest order from the backpack is: thermos, then box, then air vent, then broom.” It supplies no thermos-versus-box comparison.
- **HYPOTHESIS—displaced errors:** Missing candidate locations permit object or instance confusion before ordering. Row `q6f56ae8900c6f764c1359515` says: “find the bag, first seen in frame 8,” then “bookshelf, then boxes, then flipchart, then electrical duct.” It never locates those candidates.
- **HYPOTHESIS—answer contradiction:** The target leaves object-to-letter binding implicit. Row `q08a09b71a1867879cb2dd1e2` ends: “The question asks me to choose the closest, which is the glasses holder.” Its answer is `C`, but the trace never states that glasses holder is option C.

## 6. Label or scoring defects

No confirmed scoring defect was found: score disagrees with exact predicted-letter correctness on 0 of 429 items.

**Possible label ambiguity, not a confirmed defect:** `ba14ba2ac2a20cfb282711e3` asks what is farthest from “the adapter,” with “power adapter” as the truth. Those names may denote distinct instances or an overlapping referent. Instance annotations and geometry are needed before changing the label. The contradiction example is a model error, not a scorer error.

## 7. Three changes

All proposed quantities are **guesses**, and all changes target the family named above. The item counts describe affected errors, not predicted gains.

1. **Reword about 2,000 of 20,665 kept rows to compare the competing endpoint candidates explicitly.** Locate both, then describe why one is nearer or farther using visible spatial evidence. This targets adjacent truth on 22 of 150 dev-S1 and 40 of 279 R0-dev items, including the contradiction. Their score ceilings are 14.67 and 14.34 points; actual recovery is unknown.
2. **Reword about 3,000 of 20,665 kept rows to locate every candidate and distinguish instances before ordering.** Use source-supported frames and regions, and explain closest-point comparisons without invented metres. Prioritize difficult identities and separated views. This targets the displaced-order group: 18 of 150 and 51 of 279 items, with ceilings of 12.00 and 18.28 points.
3. **Reword about 400 of 20,665 kept rows with explicit endpoint-to-option binding and permuted options.** End with, for example, “The farthest is panel, option B.” Include closest and farthest variants where labels support them. This addresses the contradiction on 1 of 279 R0-dev items, but fixes 0 of 279 scored answers by itself because that item’s order is also wrong. **I am least sure this merits substantial training weight.**

## 8. Not established

I did not inspect RGB frames or instance geometry, so I cannot separate visual localization errors, instance confusion, and incorrect distance comparisons. Those data would also settle the adapter ambiguity and actual room multiplicity.

Candidate locations are absent in the written traces; that does not establish that the model never located candidates internally. Likewise, frame references beyond the supplied frame count need the source-to-sampled-frame mapping before they can be called invalid.

The training sample does not establish full-family farthest coverage. Neither paired checkpoints nor these trace counts isolate the causal effect of removing metres. A controlled row-form ablation would settle that question.

## Appendix: CLASSIFIER

```python
import sys, re, resource
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K

MODES = (
    "Adjacent order error",
    "Displaced order error",
    "Answer contradiction",
)

def parsed(r):
    options = {x[0]: x[3:].lower().strip() for x in r["options"]}
    match = re.search(r"order[^\n]*?is: ([^\n]+)", r["text"])
    assert match, r["id"]
    order = [
        re.sub(r"^(?:then |the )", "", x.strip().rstrip("."))
        for x in match[1].lower().split(",")
    ]
    assert len(order) == 4, r["id"]
    assert set(order) == set(options.values()), r["id"]
    return options, order

for name in ("dev-S1", "R0-dev"):
    rows = K.direct("R1", 200, name, types=["object_rel_distance"])
    counts, losses = Counter(), defaultdict(float)
    for r in rows:
        options, order = parsed(r)
        assert not r["forced_close"], r["id"]
        assert r["pred"] == r["pred_on"], r["id"]
        assert r["score"] == float(r["pred"] == r["gt"]), r["id"]
        if r["score"] == 1:
            continue
        endpoint = 3 if r["subtype"] == "farthest" else 0
        truth, answer = options[r["gt"]], options[r["pred"]]
        assert truth != order[endpoint], r["id"]
        if answer != order[endpoint]:
            mode = MODES[2]
        elif abs(order.index(truth) - endpoint) == 1:
            mode = MODES[0]
        else:
            mode = MODES[1]
        counts[mode] += 1
        losses[mode] += 1 - r["score"]
    assert sum(counts.values()) == sum(r["score"] < 1 for r in rows)
    for mode in MODES:
        print("{} | {} | {} of {} | {:.2f} points".format(
            name, mode, counts[mode], len(rows),
            100 * losses[mode] / len(rows)))
```