**1. Scope**

I analyzed all VSTI relative-dev items for `obj_obj_relative_pos_lr` (LR) and `obj_obj_relative_pos_ud` (UD). No official benchmark items were used.

| Type | Step 544 B2048 | Step 200 B2048 | Change |
|---|---:|---:|---:|
| LR | 81 of 150 correct; 54.00% | 105 of 150 correct; 70.00% | +16.00 points |
| UD | 89 of 150 correct; 59.33% | 124 of 150 correct; 82.67% | +23.33 points |

I recomputed these scores with `san_kit`. The source prefix is `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/build/`. Step 544 uses `acb2faedd41`; step 200 uses `a35f73e87f0`. Under each, the files are `fetched/x/r6/a0/results/budget_2048/0/items_a0.jsonl` for scores and `fetched/x/r6/a0/results/0/items_a0.jsonl` for full traces.

All 150 of 150 questions per type follow: “In frame k of 32, relative to B, is A to the [Left/Right]?” or “[Up/Down]?” Each has two options whose letter order varies. These questions do not ask closest/farthest.

Uniform chance is 50%, or an expected 75 of 150 correct. Both types have A/B truths of 75 of 150 each. The best constant **word** is Right for LR: 79 of 150, 52.67%; Up for UD: 76 of 150, 50.67%. Step 200 exceeds these semantic constants by 17.33 and 32.00 points, respectively; it exceeds either constant letter by 20.00 and 32.67 points.

**2. Failure modes at step 200**

Every wrong item received one primary classification. “Wrong relation” means disagreement with the supplied label; it does not establish whether perception or the label caused that disagreement.

| Mode | Definition | LR count; cost | UD count; cost |
|---|---|---:|---:|
| Wrong horizontal relation | The trace states the incorrect left/right relation, and the answer follows it. | 45 of 150; 30.00 points | 0 of 150; 0.00 points |
| Wrong vertical relation | The trace states the incorrect higher/lower relation, and the answer follows it. | 0 of 150; 0.00 points | 26 of 150; 17.33 points |
| Answer contradicts relation | The answer does not follow the stated relation. | 0 of 150; 0.00 points | 0 of 150; 0.00 points |
| Runaway | Thinking requires forced closure. | 0 of 150; 0.00 points | 0 of 150; 0.00 points |
| Missing/unparsed | The answer or relation cannot be parsed. | 0 of 150; 0.00 points | 0 of 150; 0.00 points |

The relation sentence, concluding sentence, and option agree on 150 of 150 items per type. B2048 and ON16k answers also agree on 150 of 150 per type.

**Frame use.** All 150 of 150 traces per type name the correct k in their viewpoint and relation sentences, but their Locate lines cite first-seen frames. Both Locate citations equal k on only 1 of 150 LR items and 0 of 150 UD items. Neither equals k on 139 of 150 LR items, including 42 of 45 errors, and 144 of 150 UD items, including 24 of 26 errors. Textual references to k do not prove that the model inspected k.

| First-seen evidence | LR | UD |
|---|---:|---:|
| At least one citation later than k | 95 of 150 items; 29 of 45 errors | 91 of 150 items; 11 of 26 errors |
| At least one citation outside 1–32 | 57 of 150 items; 21 of 45 errors | 54 of 150 items; 6 of 26 errors |
| Later than k, but both citations within 1–32 | 38 of 150 items; 8 of 45 errors | 37 of 150 items; 5 of 26 errors |

Under the trace’s literal first-seen claim, a later citation implies that the object was not yet visible at k. This is an internal inconsistency, not verified absence. An earlier citation does **not** imply absence at k.

Errors do not generally concentrate in later-citation cases: LR has 29 of 95 wrong versus 16 of 55 without later citations; UD has 11 of 91 versus 15 of 59. Out-of-range citations show a descriptive association for LR—21 of 57 wrong versus 24 of 93—but the reverse for UD: 6 of 54 versus 20 of 96.

**Answer bias.**

| Type / representation | Truth | Step 544 answers | Step 200 answers |
|---|---|---|---|
| LR letters | A: 75 of 150; B: 75 of 150 | A: 78 of 150; B: 72 of 150 | A: 80 of 150; B: 70 of 150 |
| LR words | Left: 71 of 150; Right: 79 of 150 | Left: 50 of 150; Right: 100 of 150 | Left: 40 of 150; Right: 110 of 150 |
| UD letters | A: 75 of 150; B: 75 of 150 | A: 94 of 150; B: 56 of 150 | A: 71 of 150; B: 79 of 150 |
| UD words | Up: 76 of 150; Down: 74 of 150 | Up: 77 of 150; Down: 73 of 150 | Up: 92 of 150; Down: 58 of 150 |

LR answers Right on 38 of 71 Left-truth items and Left on 7 of 79 Right-truth items. UD answers Up on 21 of 74 Down-truth items and Down on 5 of 76 Up-truth items. These polarity errors occur in the relation sentence itself.

**Twins.** In each type, 0 of 150 items has a same-room, same-frame counterpart with swapped object roles. Removing the same-frame requirement still finds counterparts for 0 of 150. Twin consistency therefore cannot be measured here.

**3. Examples**

Each question and excerpt below is verbatim. All examples are from VSTI relative dev.

- **Wrong horizontal relation — `04ae6979aee7233e3460dae7`.** Q: “In frame 22 of 32, relative to weight scale, is bookshelf to the [Left/Right]?” Truth: A/Left; answer: B/Right.  
  “Step 3: locate the weight scale, first seen in frame 92.” “Step 4: from the camera viewpoint of frame 22, the bookshelf is to the right of the weight scale.”
- **Wrong horizontal relation — `08d0c6f75c1ef2c3a06d8495`.** Q: “In frame 26 of 32, relative to lectern, is projector to the [Left/Right]?” Truth: B/Left; answer: A/Right.  
  “Step 4: from the camera viewpoint of frame 26, the projector is to the right of the lectern.”
- **Wrong horizontal relation — `0dae86f5e7dbfa2c0af03724`.** Q: “In frame 15 of 32, relative to pedestal fan, is cabinet to the [Left/Right]?” Truth: B/Right; answer: A/Left.  
  “Step 2: locate the cabinet, first seen in frame 17.” “Step 4: from the camera viewpoint of frame 15, the cabinet is to the left of the pedestal fan.”
- **Wrong vertical relation — `02e32b8885975f9205ac627c`.** Q: “In frame 25 of 32, relative to smartboard, is ladder to the [Up/Down]?” Truth: A/Down; answer: B/Up.  
  “Step 4: in frame 25's level horizon, the centre of the ladder is higher than the centre of the smartboard.”
- **Wrong vertical relation — `684ebad7dd6132b8ef84fd38`.** Q: “In frame 19 of 32, relative to table, is cup to the [Up/Down]?” Truth: A/Up; answer: B/Down.  
  “Step 2: locate the cup, first seen in frame 36.” “Step 4: in frame 19's level horizon, the centre of the cup is lower than the centre of the table.”
- **Wrong vertical relation — `839d72076b0e30ea8bac9aa4`.** Q: “In frame 18 of 32, relative to ladder, is sink to the [Up/Down]?” Truth: B/Down; answer: A/Up.  
  “Step 4: in frame 18's level horizon, the centre of the sink is higher than the centre of the ladder.”

The zero-count modes have no examples.

**4. Step 544 against step 200**

| Type | Right → wrong | Wrong → right | Wrong → wrong | Right → right |
|---|---:|---:|---:|---:|
| LR | 9 of 150 | 33 of 150 | 36 of 150 | 72 of 150 |
| UD | 14 of 150 | 49 of 150 | 12 of 150 | 75 of 150 |

Step 544 often uses an inappropriate facing or measurement template. It writes degrees on 132 of 150 LR traces and 99 of 150 UD traces, and “standing at … facing” on 79 of 150 LR traces and 46 of 150 UD traces. It interprets “k of 32” as “find the frames (k, 32)” on 25 of 150 LR traces and 7 of 150 UD traces. Step 200 writes no metric-distance or degree expressions on 150 of 150 traces per type.

Among wrong→right items, the base writes degrees on 31 of 33 LR cases and 33 of 49 UD cases. Median B2048 thinking length changes from 58 to 87 tokens for these LR cases and from 64 to 91 for UD. Among right→wrong items, medians change from 60 to 88 for LR and 63.5 to 89 for UD. Both improvements and regressions adopt the same short, axis-appropriate step-200 template.

For example, the base trace for `02a6f29ba3e442a637a23aef` concludes “So computer tower is to the left.” despite an Up/Down question; step 200 correctly states lower/Down. Conversely, the base gets `02e32b8885975f9205ac627c` right with option A while concluding “So the ladder is to the left.” Its correct letter does not demonstrate correct vertical reasoning.

The base has a runaway on 1 of 150 UD items, `419285d69ea5a66222d6e0b4`, costing 0.67 points; step 200 answers it correctly.

**5. Hypotheses**

I read the supplied `STORE_V7_SAMPLES20.json` and `STORE_V7_TEMPLATE_COUNTS.json` under `/scratch/jjyeung/orch_n30/dist_diag/work/q2/`. The relevant families are **F_LR** = `obj_obj_relative_pos_lr|vsti_rel_v4|None` and **F_UD** = `obj_obj_relative_pos_ud|vsti_rel_v4|None`. The counts file reports 1,978 of 1,998 LR rows and 1,974 of 1,996 UD rows kept.

**HYPOTHESIS—wrong horizontal relation:** F_LR teaches the requested viewpoint as a verbal declaration without requiring target-frame localization. Kept row `i=158333` trains: “Step 1: take the camera viewpoint of frame 4. … Step 2: locate the trash can, first seen in frame 15. … Step 4: from the camera viewpoint of frame 4, the trash can is to the right of the window.” Later-than-k citations occur in 9 of 20 sampled LR targets. This supports a template defect, but the dev error rates do not establish it as the main cause.

**HYPOTHESIS—wrong vertical relation:** F_UD permits a learned object-height prior to replace frame-specific comparison. Kept row `i=162546` trains: “Step 2: locate the tv, first seen in frame 6. … Step 3: locate the sofa, first seen in frame 1. … Step 4: in frame 16's level horizon, the centre of the tv is higher than the centre of the sofa.” Up is the target on 14 of 20 sampled rows, and the model overpredicts Up. This small sample does not establish whole-family imbalance or category-prior causation.

All 20 of 20 sampled rows per family are marked kept. Neither Locate citation equals k in 16 of 20 LR samples and 19 of 20 UD samples; out-of-range citations occur in 0 of 20 samples per family. Thus the sampled targets support the first-seen template explanation, but not the origin of generated indices above 32.

**6. Label or scoring defects**

None found in the text-level checks. At each checkpoint, 300 of 300 scores match predicted-letter equality with the supplied truth, and 300 of 300 truth labels match `gt_released`. The options are valid binary choices on 150 of 150 items per type.

The frame-92 and frame-36 citations above are trace defects, not demonstrated label defects. I could not validate geometric labels without the images and annotation convention.

**7. Three changes for vehicle N**

These row budgets are **proposal guesses**. Affected-error counts are overlapping ceilings, not predicted gains.

1. **Reword F_LR and F_UD Locate lines to cite verified evidence in k.** Revise approximately all retained rows: 1,978 of 1,998 LR and 1,974 of 1,996 UD. Map source indices explicitly to the sampled 1–32 sequence; omit unsupported first-seen claims. This directly targets the internal frame contradictions accompanying 29 of 45 LR errors and 11 of 26 UD errors, including the out-of-range citations.
2. **Add approximately 1,000 training rows per family as swapped-role pairs, balanced by semantic direction and option letter.** Require the reversed question to reverse the relation. This targets the dominant polarity errors: 38 of 45 LR errors and 21 of 26 UD errors. The count identifies the bias to test; absent dev twins prevent attributing those errors to failed reversal.
3. **Add approximately 1,000 difficult, frame-verified comparisons per family with coarse image-region Locate evidence and an explicit relation.** Include cases where familiar object identities do not predict the direction. This targets errors that survive without later-frame contradictions: 16 of 45 LR errors and 15 of 26 UD errors. **I am least sure of this change:** the traces do not distinguish mistaken identity, visual comparison, and annotation convention.

**8. Not established**

The traces do not establish actual visibility at k, use of the requested image, the source of indices above 32, or whether UD’s “level horizon” matches its labels. Sampled RGB frames, source-to-sampled frame mappings, object masks, and the relation annotation rule would settle these questions. Controlled training ablations would be needed to price recoverable gains.

**Appendix — CLASSIFIER**

```python
import sys, re, collections
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K

types = ['obj_obj_relative_pos_lr', 'obj_obj_relative_pos_ud']
rows = K.vsti('R1', 200, types=types)
modes = ['Wrong horizontal relation', 'Wrong vertical relation',
         'Answer contradicts relation', 'Runaway', 'Missing/unparsed']
for typ in types:
    rs = [r for r in rows if r['type'] == typ]
    counts = collections.Counter()
    costs = collections.Counter()
    for r in rs:
        if r['score'] == 1:
            continue
        text = r['text'].split('</think>')[0]
        q = re.fullmatch(
            r'In frame (\d+) of 32, relative to (.*), is (.*)'
            r' to the \[.*\]\?', r['question'])
        opts = dict(x.split('. ', 1) for x in r['options'])
        gt = opts.get(r['gt'], '').lower()
        pred = opts.get(r['pred'], '').lower()
        ref, obj = map(re.escape, q.group(2, 3))
        if typ.endswith('_lr'):
            pat = (r'Step 4:.*?, the ' + obj +
                   r' is to the (left|right) of the ' + ref + r'\.')
        else:
            pat = (r'Step 4:.*?, the centre of the ' + obj +
                   r' is (higher|lower) than the centre of the ' + ref + r'\.')
        m = re.search(pat, text)
        c = re.search(r'So the ' + obj +
                      r' is (left|right|up|down) relative to the ' +
                      ref + r'\.', text)
        rel = {'higher': 'up', 'lower': 'down'}.get(m[1], m[1]) if m else None
        if r['forced_close']:
            mode = 'Runaway'
        elif not m or not c or not pred:
            mode = 'Missing/unparsed'
        elif pred != rel:
            mode = 'Answer contradicts relation'
        else:
            assert rel == c[1] and rel != gt, r['id']
            mode = ('Wrong horizontal relation' if typ.endswith('_lr')
                    else 'Wrong vertical relation')
        counts[mode] += 1
        costs[mode] += 1 - r['score']
    assert sum(counts.values()) == sum(r['score'] < 1 for r in rs)
    for mode in modes:
        print('vsti', typ, mode, f'{counts[mode]} of {len(rs)}',
              f'{100 * costs[mode] / len(rs):.2f} points')
```