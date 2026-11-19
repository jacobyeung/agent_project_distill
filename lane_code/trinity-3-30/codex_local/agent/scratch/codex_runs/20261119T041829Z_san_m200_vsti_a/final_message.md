## 1. Scope

Step 200 improves both types, but every wrong answer follows an already-wrong nearest-object ordering.

| VSTI relative dev type | Step 544 correct | Step 200 correct | Gain |
|---|---:|---:|---:|
| `camera_obj_rel_dist_v1` | 37 of 150; 24.67% | 57 of 150; 38.00% | 13.33 points |
| `camera_obj_rel_dist_v2` | 48 of 150; 32.00% | 56 of 150; 37.33% | 5.33 points |

I recomputed these B2048 scores through `san_kit`. Under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/build/`, the source prefixes are `acb2faedd41/fetched/x/r6/a0/results/` for step 544 and `a35f73e87f0/fetched/x/r6/a0/results/` for step 200. Each supplies `budget_2048/0/items_a0.jsonl` for scores and `0/items_a0.jsonl` for full traces.
Step-200 B2048 and ON16k predictions agree on 300 of 300 items. I read no official evaluation items.

The question asks “Measuring from the closest point of each object” which candidate is closest to the camera in a specified frame. V1 has four options on 150 of 150 items; v2 has three on 150 of 150. Both ask **closest**, never farthest.

Uniform chance is 25.00% for v1 and 33.33% for v2. The best constant letter scores 38 of 150 for v1, using A or B, and 50 of 150 for v2, using any letter. Step 200 exceeds these baselines by 12.67 and 4.00 points, respectively.

## 2. Failure modes

These are mutually exclusive **wrong-order subgroups**, separated by their frame citations. The partition describes evidence; it does not establish that a citation defect caused an error.

| Primary mode | Definition | V1 count; cost | V2 count; cost |
|---|---|---:|---:|
| Wrong order / invalid frame | The nearest object is wrong, and a first-seen citation falls outside 1–32. | 43 of 150; 28.67 points | 46 of 150; 30.67 points |
| Wrong order / later frame | The nearest object is wrong; all citations are within 1–32, but at least one exceeds queried frame k. | 31 of 150; 20.67 points | 26 of 150; 17.33 points |
| Wrong order / other | The nearest object is wrong; every first-seen citation is within 1–k. | 19 of 150; 12.67 points | 22 of 150; 14.67 points |
| Answer contradicts order | The answer selects something other than the stated nearest object. | 0 of 150; 0 points | 0 of 150; 0 points |
| Format failure | The answer/order is missing or unparsed, or thinking is force-closed. | 0 of 150; 0 points | 0 of 150; 0 points |
| **Total wrong** | Every wrong item receives one primary mode. | **93 of 150; 62.00 points** | **94 of 150; 62.67 points** |

The traces repeat the correct queried frame in both viewpoint statements on 300 of 300 items. They cite another frame for at least one object on 300 of 300 items. No object receives a first-seen citation at k on 142 of 150 v1 items and 138 of 150 v2 items; these groups contain 88 of 93 and 87 of 94 errors.

A first-seen citation **before** k does not establish visibility or absence at k. A valid first-seen citation **after** k implies absence at k if the trace’s claim is true. This latter condition occurs on 42 of 150 v1 items, including 31 of 93 errors, and 41 of 150 v2 items, including 26 of 94 errors.
Error rates are 31 of 42 versus 19 of 29 for valid later citations versus citations entirely within 1–k in v1; they are 26 of 41 versus 22 of 38 in v2. Errors concentrate modestly in the valid-later group, descriptively.
Out-of-range citations show no consistent concentration: v1 errors are 43 of 79 with them versus 50 of 71 without; v2 errors are 46 of 71 versus 48 of 79.

| Answer distribution | Truth | Step-200 prediction |
|---|---|---|
| V1 letters | A: 38 of 150; B: 38 of 150; C: 37 of 150; D: 37 of 150 | A: 27 of 150; B: 37 of 150; C: 32 of 150; D: 54 of 150 |
| V2 letters | A: 50 of 150; B: 50 of 150; C: 50 of 150 | A: 42 of 150; B: 44 of 150; C: 64 of 150 |
| V1 words, selected categories plus remainder | table: 5 of 150; bed: 8 of 150; wardrobe: 6 of 150; other: 131 of 150 | table: 15 of 150; bed: 10 of 150; wardrobe: 6 of 150; other: 119 of 150 |
| V2 words, selected categories plus remainder | whiteboard: 1 of 150; sink: 2 of 150; cabinet: 6 of 150; other: 141 of 150 | whiteboard: 6 of 150; sink: 6 of 150; cabinet: 3 of 150; other: 135 of 150 |

The last option is overselected in both types. V1 selects “table” on 15 of 17 items offering it; 11 of those 15 selections are wrong. This supports investigating category bias, not concluding its cause.
Closest/farthest polarity reversals occur on 0 of 300 items: every answer selects the stated nearest object. Left/right and mirrored-twin consistency are outside these assigned types.

## 3. Examples

All examples are from VSTI relative dev. Questions omit their shared closest-point preamble; quoted trace excerpts are verbatim.

**Wrong order / invalid frame**
- `0585b3cd53b023b46d8b4edf` (v1). Q: “which of these objects (bottle, lanyard, helmet, document holder) is the closest to the camera in frame 8 of 32?” Truth: C, helmet. Answer: D, document holder.
  > Step 3: locate the lanyard, first seen in frame 117.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 8, the objects are document holder, then bottle, then lanyard, then helmet.
- `05c9b3bae0ea15c1314275ae` (v1). Q: “which of these objects (shoes, towel, blinds, trash bin) is the closest to the camera in frame 20 of 32?” Truth: D, trash bin. Answer: C, blinds.
  > Step 2: locate the shoes, first seen in frame 85.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 20, the objects are blinds, then towel, then shoes, then trash bin.
- `01762479e42ee27cae3991a8` (v2). Q: “which of these objects (leaf fan, caution board, brush) is the closest to the camera in frame 25 of 32?” Truth: A, leaf fan. Answer: C, brush.
  > Step 4: locate the brush, first seen in frame 37.
  > Step 5: ordered nearest to farthest from the camera viewpoint of frame 25, the objects are brush, then leaf fan, then caution board.

**Wrong order / later frame**
- `0ba09d4f9de9f6904ead73ac` (v1). Q: “which of these objects (jacket, mug, cloth, plate) is the closest to the camera in frame 23 of 32?” Truth: B, mug. Answer: A, jacket.
  > Step 3: locate the mug, first seen in frame 27.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 23, the objects are jacket, then mug, then plate, then cloth.
- `0f98fb79977cb69da470035f` (v1). Q: “which of these objects (kettle, wardrobe, bookshelf, roomba) is the closest to the camera in frame 6 of 32?” Truth: C, bookshelf. Answer: B, wardrobe.
  > Step 4: locate the bookshelf, first seen in frame 24.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 6, the objects are wardrobe, then bookshelf, then kettle, then roomba.
- `063e52f3963a0c603b986c3b` (v2). Q: “which of these objects (books, heater, trolley) is the closest to the camera in frame 8 of 32?” Truth: A, books. Answer: C, trolley.
  > Step 4: locate the trolley, first seen in frame 23.
  > Step 5: ordered nearest to farthest from the camera viewpoint of frame 8, the objects are trolley, then books, then heater.

**Wrong order / other**
- `0057c3c84ed9f3181396ae1b` (v1). Q: “which of these objects (kitchen counter, umbrella holder, laminator, backsplash) is the closest to the camera in frame 29 of 32?” Truth: D, backsplash. Answer: A, kitchen counter.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 29, the objects are kitchen counter, then backsplash, then umbrella holder, then laminator.
- `030920c8738688c4cdcb6ce2` (v1). Q: “which of these objects (stove hood, cutting board, sling bag, faucet) is the closest to the camera in frame 25 of 32?” Truth: D, faucet. Answer: A, stove hood.
  > Step 6: ordered nearest to farthest from the camera viewpoint of frame 25, the objects are stove hood, then cutting board, then faucet, then sling bag.
- `12e2877fe8041a5073be3c5f` (v2). Q: “which of these objects (bottle, refrigerator, closet) is the closest to the camera in frame 14 of 32?” Truth: A, bottle. Answer: C, closet.
  > Step 5: ordered nearest to farthest from the camera viewpoint of frame 14, the objects are closet, then refrigerator, then bottle.

## 4. Step 544 against step 200

| Type | Right → wrong | Wrong → right | Wrong → wrong | Right → right |
|---|---:|---:|---:|---:|
| V1 | 18 of 150 | 38 of 150 | 75 of 150 | 19 of 150 |
| V2 | 22 of 150 | 30 of 150 | 72 of 150 | 26 of 150 |

Step 544 states candidate distances in meters on 300 of 300 items. Step 200 instead supplies first-seen citations and a verbal order on 300 of 300 items. Thus both improvements and regressions adopt the same trace change; it does not distinguish successful flips.
Across flipped items, mean thinking length rises from 78.2 to 130.8 tokens for v1 and from 69.5 to 110.2 for v2.
The base misstates the camera’s frame on 27 of 150 v1 items and 31 of 150 v2 items. Step 200 names it correctly on 300 of 300 items, although actual use of that viewpoint remains unverified.
For example, `0f98fb79977cb69da470035f` regresses from correctly assigning bookshelf the smallest stated distance, “bookshelf 2.36 m,” to the wrong order quoted above. These files establish a repeated numeric template, not literal copying from a particular training row.

## 5. Hypotheses

Let F1 mean `camera_obj_rel_dist_v1|vsti_rel_v4|None`, and F2 mean `camera_obj_rel_dist_v2|vsti_rel_v4|None`.
I inspected 20 of 20 provided samples for each family in `STORE_V7_SAMPLES20.json`. The samples retain 20 of 20 F1 rows and 19 of 20 F2 rows. `STORE_V7_TEMPLATE_COUNTS.json` reports 1,930 of 1,951 F1 rows and 1,957 of 1,983 F2 rows kept.

- **HYPOTHESIS—invalid frames:** The model generates plausible-looking frame identifiers without binding them to the sampled input. F1/F2 teach the citation syntax, but neither sample contains an out-of-range citation: 0 of 20 for each. F1 row 154009 says, “Step 2: locate the stool, first seen in frame 2.” Source-frame namespace confusion is another unverified explanation.
- **HYPOTHESIS—later frames:** First-seen supervision leaves the target-camera geometry implicit. Valid later citations occur in 10 of 20 kept F1 samples and 11 of 19 kept F2 samples. F2 row 154426 queries frame 14 but says, “Step 3: locate the smoke detector, first seen in frame 22.”
- **HYPOTHESIS—other wrong orders:** F1/F2 teach an order without enough visible evidence for distinguishing close candidates; category or option-position priors can fill that gap. F2 row 154688 says, “the objects are refrigerator, then frying pan, then chair.” Its citations concern frames 18 and 1, although the question concerns frame 29. This hypothesis remains weaker than the observed answer bias.

## 6. Label or scoring defects

None found in the checks available here. Scores disagree with letter equality on 0 of 300 items, and duplicate options occur on 0 of 300 items. Out-of-range citations are trace defects, not demonstrated label defects. RGB evidence and geometric annotations were not inspected, so ground-truth geometry is unverified.

## 7. Three changes for vehicle N

These row quantities are **planning guesses**. The affected-item counts are diagnostic upper bounds, not predicted recoveries.

1. **Reword F1/F2 citations to identify sampled frames explicitly, and validate their range.** Apply this to all kept rows: 1,930 of 1,951 F1 rows and 1,957 of 1,983 F2 rows. Remap source indices when a verified mapping exists; omit unsupported citations. This targets 43 of 93 v1 errors and 46 of 94 v2 errors. **I am least sure this improves accuracy**, because invalid citations do not consistently concentrate errors.
2. **Add approximately 1,000 training rows per family that distinguish object identification from the queried viewpoint.** Use verified target-frame evidence when available; when another frame identifies an object, state how it supports the comparison from k. Include same-scene questions whose nearest object changes with k. This directly targets the valid-later subgroup: 31 of 93 v1 errors and 26 of 94 v2 errors.
3. **Add approximately 500 hard-comparison rows per family, with balanced answer positions and verified closest-point relations.** Favor candidates whose object category or apparent size gives a misleading shortcut; train a short supported comparison before the order. This targets the remaining 19 of 93 v1 errors and 22 of 94 v2 errors. The category-selection bias motivates this proposal, but does not prove those errors share that cause.

## 8. Not established

The traces cannot establish actual visibility at k, whether first-seen citations are true, or whether ordering uses the queried image. Sampled RGB frames, object visibility annotations, and the source-to-sampled-frame mapping would settle those questions.
Only the first ranked object is checked against truth; the remaining order lacks labels here. Controlled training ablations are needed to price recoverable gains. Mirrored lr/nf/ud twins were not examined because they are outside this assignment.

## Appendix: CLASSIFIER

```python
import sys, re
from collections import Counter
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
types = ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2']
rows = K.vsti('R1', 200, types=types)
modes = ['Wrong order / invalid frame', 'Wrong order / later frame',
         'Wrong order / other', 'Answer contradicts order', 'Format failure']
for typ in types:
    items = [r for r in rows if r['type'] == typ]
    counts, losses = Counter(), Counter()
    for r in items:
        if r['score'] == 1:
            continue
        text = r['text'] or ''
        opts = [s[3:] for s in r['options']]
        match = re.search(r'the objects are (.*?)\.', text)
        order = match[1].split(', then ') if match else []
        frames = list(map(int, re.findall(r'first seen in frame (\d+)', text)))
        k = int(re.search(r'frame (\d+) of 32', r['question'])[1])
        if (r['forced_close'] or r['pred'] not in list('ABCD'[:len(opts)])
                or sorted(order) != sorted(opts) or len(frames) != len(opts)):
            mode = modes[4]
        elif opts[ord(r['pred']) - 65] != order[0]:
            mode = modes[3]
        else:
            assert order[0] != opts[ord(r['gt']) - 65]
            assert list(map(int, re.findall(
                r'camera viewpoint of frame (\d+)', text))) == [k, k]
            mode = modes[0] if any(f < 1 or f > 32 for f in frames) else (
                modes[1] if any(f > k for f in frames) else modes[2])
        counts[mode] += 1
        losses[mode] += 1 - r['score']
    print(typ, 'vsti')
    for mode in modes:
        print(mode, f'{counts[mode]} of {len(items)}',
              f'{100 * losses[mode] / len(items):.2f} points')
    assert sum(counts.values()) == sum(r['score'] < 1 for r in items)
```