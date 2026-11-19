**1. Question and answer**

1. **Which shortcuts predict camera-object answers, and which do training rows reward?** No tested rule explains all answers. Earliest first-seen predicts 216 of 450 model answers and earns 652 of 1,500 training answers; the last candidate predicts 218 of 450 model answers but earns only 539 of 1,500 training answers.
2. **What polarity biases remain, and does UD follow class-height priors?** Step 200 selects Right on 110 of 150 LR items versus 79 of 150 truths, and Up on 92 of 150 UD items versus 76 of 150 truths. The requested UD class-pair test is inconclusive: its training majority covers only 2 of 150 dev items and matches both model and truth on 1 of 2.
3. **Do training rows carry evidence for an honest frame-k trace?** They carry more than first-seen frames: 30 of 30 audited rows contain target-frame visibility shares and geometry values. However, all candidates have zero recorded visible area at k in 15 of 30 rows; none supplies a complete per-frame localization and camera-pose record.
4. **Does the model change its ordering with k when truth changes?** Across camera types, the highest-ranked shared object changes on 18 of 59 comparable pairs whose true winner changes. With identical candidate sets, the model changes on 2 of 8 truth-changing pairs.
5. **What trace should vehicle N teach, and how many errors could it address?** Teach verified localization at k followed by the type’s specific comparison, with separate evidence requirements for objects located through other frames. This addresses the relation-form failure shared by 375 of 900 items, but 375 is a ceiling, not a recovery estimate.

**2. Evidence**

All dev results use B2048 answers. First-seen predictors use the generated ON16k trace; the first-wave reports established answer agreement between these arms on all 900 of 900 items.

Sources: `D200` and `D544` are the `a35f73e87f0` and `acb2faedd41` directories under `/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1vsti/kit/build/`, respectively. `san_kit` read each directory’s `fetched/x/r6/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
Training sources are `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/{FAMILY_INDEX_RANGES.json,vqa/rows.sqlite}`. Family totals come from `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json`; exclusions come from `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/{n,z}.json`.

I sampled primary keys without replacement, using `random.Random(200)` separately for each family: 500 rows per camera type, 1,500 UD rows, and 2,000 size rows. Queries contained at most 200 primary keys. All 1,500 of 1,500 camera targets agree with their answer and provenance first-seen map.

**Camera shortcut predictions.** “Closest k” minimizes the absolute difference between stated first-seen frame and k. Ties select the first candidate in question order. “Largest” selects the greatest class median longest dimension; it abstains unless every candidate has a sampled median.

| Type | Rule | Matches model | Matches dev truth | Matches training truth | Matches kept training truth |
|---|---|---:|---:|---:|---:|
| v1 | Closest k | 50 of 150 | 37 of 150 | 132 of 500 | 132 of 496 |
| v1 | Latest first-seen | 17 of 150 | 38 of 150 | 105 of 500 | 105 of 496 |
| v1 | Earliest first-seen | 56 of 150 | 43 of 150 | 153 of 500 | 152 of 496 |
| v1 | Last candidate | 54 of 150 | 37 of 150 | 134 of 500 | 132 of 496 |
| v1 | Largest class median | 14 of 21 | 7 of 21 | 31 of 87 | 31 of 86 |
| v2 | Closest k | 67 of 150 | 57 of 150 | 165 of 500 | 160 of 494 |
| v2 | Latest first-seen | 40 of 150 | 47 of 150 | 135 of 500 | 131 of 494 |
| v2 | Earliest first-seen | 67 of 150 | 58 of 150 | 214 of 500 | 214 of 494 |
| v2 | Last candidate | 64 of 150 | 50 of 150 | 150 of 500 | 148 of 494 |
| v2 | Largest class median | 11 of 24 | 9 of 24 | 50 of 108 | 50 of 107 |
| v3 | Closest k | 87 of 150 | 72 of 150 | 249 of 500 | 246 of 497 |
| v3 | Latest first-seen | 51 of 150 | 74 of 150 | 209 of 500 | 207 of 497 |
| v3 | Earliest first-seen | 93 of 150 | 72 of 150 | 285 of 500 | 284 of 497 |
| v3 | Last candidate | 100 of 150 | 75 of 150 | 255 of 500 | 252 of 497 |
| v3 | Largest class median | 40 of 52 | 35 of 52 | 109 of 187 | 108 of 185 |

Temporal ties are substantial. For closest-k/latest/earliest respectively, they occur on 37/31/49 of 150 v1 items, 37/27/46 of 150 v2 items, and 28/26/26 of 150 v3 items. Excluding earliest-frame ties, that rule matches model/truth on 44/30 of 101 v1 items, 51/43 of 104 v2 items, and 83/61 of 124 v3 items. The preference therefore survives removal of ties.

All 2,000 of 2,000 size questions parsed. Exact lowercase class names yielded medians for 634 classes; no synonym merging or missing-class imputation was used. Coverage is only 97 of 450 dev items. The largest-class rule matches the model on 65 of 97 and truth on 51 of 97; this supports a limited association, not a general explanation.

**Polarity distributions and errors.** Each distribution cell gives counts for the two words in the first column.

| Type; word order | Truth | Step 544 | Step 200 | Step-544 directional errors | Step-200 directional errors |
|---|---|---|---|---|---|
| LR; Left / Right | 71 / 79 of 150 | 50 / 100 of 150 | 40 / 110 of 150 | Left→Right: 45 of 71; Right→Left: 24 of 79 | Left→Right: 38 of 71; Right→Left: 7 of 79 |
| NF; Near / Far | 64 / 86 of 150 | 85 / 65 of 150 | 56 / 94 of 150 | Near→Far: 26 of 64; Far→Near: 47 of 86 | Near→Far: 32 of 64; Far→Near: 24 of 86 |
| UD; Up / Down | 76 / 74 of 150 | 77 / 73 of 150 | 92 / 58 of 150 | Up→Down: 30 of 76; Down→Up: 31 of 74 | Up→Down: 5 of 76; Down→Up: 21 of 74 |

The UD sample contains Up on 745 of 1,500 rows and Down on 755 of 1,500. Its 759 ordered class pairs include 622 of 759 singletons and 4 of 759 tied majorities. Majority lookup fits 1,479 of 1,500 sampled training answers, but that is an in-sample statistic dominated by sparse pairs.
Only `(telephone, trash can)` and `(microwave, heater)` cover dev items; each has one training example. At both checkpoints, majority agreement is 1 of 2 for model and 1 of 2 for truth. Using the kept sample gives the same result. Pooling reversed pairs with inverted labels expands coverage to 7 of 150, with model and truth each matching on 6 of 7.

**Training-row contents.** The audit covers five rows per type, all 30 of 30 kept. Camera and UD audit rows are the lowest five sampled primary keys; LR and NF use separate five-key samples.

| Metadata check | Result |
|---|---|
| `camera_frame`, `first_seen`, `frame_n_share`, `geometry_values`, `instances`, `geometry_audit` | Present in 30 of 30 rows |
| Label-keyed target-frame horizontal bearing | Present in 5 of 5 LR rows |
| Every candidate has zero target-frame visible share | 15 of 30 rows |
| At least one candidate has zero target-frame visible share | 24 of 30 rows |
| Every candidate meets the stored visibility floor | 5 of 30 rows |
| Complete visibility sequence, target-frame boxes/masks, depth map, numeric camera-pose matrix | Present in 0 of 30 rows |

The fields are:
- **Top level:** `answer`, `benchmark_improvement_claim`, `benchmark_trained_diagnostic`, `category`, `dataset`, `generation_commit`, `infrastructure_only`, `license`, `pool`, `provenance`, `provisional_diagnostic`, `qid`, `question_type`, `result_status`, `scene`, `score_nomination_allowed`, `student_input`, `target`, `validation_commit`. No `retrace` field appears in these audited rows.
- **Student input:** `fps`, `frame_indices`, `frames` with hashes, `options`, `question`, `timestamps`, `total_num_frames`. Frame paths were not followed.
- **Provenance:** `camera_frame`, `canonical`, `distance_definition`, `first_seen`, `frame_map_sha256`, `frame_n_share`, `frame_store`, `generator_sha256`, `geometry_audit`, `geometry_values`, `instances`, `raster`, `raster_sha256`, `scene_type_cap`, `source`, `view_labels`, `visibility_floor`; LR also has `frame_n_bearing_deg`.
- **Instances:** `frame`, `id`, `label`, `share`. **Geometry audit:** `axes_layout`, `box_containment`, `box_half_factor`, `camera_height_median`, `camera_height_min`, `floor_height`, `floor_horizontal_spread`, `floor_normal`, `floor_normal_alignment`, `floor_rms`, `horizontal_normal_fraction`, `passed`, `pose`, `reason`, `relative_extent_p98_median`, `up`, `valid_pins`.

`geometry_values` carries closest-box distances for camera/NF rows, horizontal bearings for LR, and vertical scalars for UD. These are label-generation evidence, not a complete visual explanation. The `pose` field states a coordinate convention rather than a numeric pose.
The larger camera sample reinforces the visibility issue: all candidates meet the stored floor in only 51 of 1,500 rows, including 51 of 1,487 kept rows.

**Changes across k.** All 68 of 68 rooms contain different queried k somewhere in the six-type set. Pair counts below require the same room and different k; pairs are dependent observations.

| Type | Rooms represented | ≥1 shared object | ≥2 shared objects | Truth-comparable pairs | Truth changes | Model changes | Model changes when truth changes |
|---|---|---|---|---|---|---|---|
| v1 | 65 of 68 | 78 of 107 pairs | 43 of 107 | 23 of 43 | 8 of 23 | 0 of 23 | 0 of 8 |
| v2 | 67 of 68 | 61 of 99 pairs | 24 of 99 | 18 of 24 | 8 of 18 | 6 of 18 | 4 of 8 |
| v3 | 68 of 68 | 31 of 96 pairs | 5 of 96 | 5 of 5 | 1 of 5 | 0 of 5 | 0 of 1 |
| Camera types pooled | 68 of 68 | 629 of 1,084 pairs | 263 of 1,084 | 138 of 263 | 59 of 138 | 30 of 138 | 18 of 59 |
| LR | 68 of 68 | 10 of 14 pairs | 3 of 14 | 3 of 3 | 0 of 3 | 0 of 3 | No truth-changing pair |
| NF | 68 of 68 | 7 of 7 pairs | 4 of 7 | 4 of 4 | 2 of 4 | 1 of 4 | 1 of 2 |
| UD | 67 of 68 | 3 of 3 pairs | 1 of 3 | 1 of 1 | 0 of 1 | 0 of 1 | No truth-changing pair |

For camera pairs, truth is comparable only when both labeled winners belong to the shared candidates. “Model changes” compares the highest-ranked shared object, not answer letters. The full shared order changes on 76 of 263 overlapping pairs; labels do not establish the full true order.
Among truth-changing pairs, the model gets both shared winners right on 9 of 59. Its winner stays fixed on 41 of 59; these pairs contain 34 distinct wrong items. Identical candidate sets provide 19 of 263 pairs: truth changes on 8 of 19, model on 3 of 19, and both on 2 of 19. Different options remain a confound outside this stricter subset.

**3. What this changes for vehicle N**

The following are ranked proposals, not edits. Every family below has suffix `|vsti_rel_v4|None`.

| Family | Kept rows to review | Step-200 errors potentially addressed |
|---|---:|---:|
| `camera_obj_rel_dist_v1` | 1,930 of 1,951 | 93 of 150 |
| `camera_obj_rel_dist_v2` | 1,957 of 1,983 | 94 of 150 |
| `camera_obj_rel_dist_v3` | 1,978 of 1,998 | 61 of 150 |
| `obj_obj_relative_pos_lr` | 1,978 of 1,998 | 45 of 150 |
| `obj_obj_relative_pos_nf` | 1,982 of 2,000 | 56 of 150 |
| `obj_obj_relative_pos_ud` | 1,974 of 1,996 | 26 of 150 |

**1. Add evidence and gate the trace before rewording all 11,799 of 11,926 kept rows.** Add instance-keyed target-frame regions, visibility status, explicit geometry units and object mapping, and the exact LR/UD coordinate convention. For objects located through other frames, add verified correspondence and viewpoint-transfer evidence, including camera transforms where needed. Keep these annotations builder-side; render qualitative evidence in the direct trace.
Drop unsupported *“visible in frame k” claims* from targets. Do not blanket-drop multi-view questions: the number eligible for a purely frame-k visual trace is not established for the full store.
This targets 354 of 375 wrong items whose Locate lines never cite k; the complete relation repair has a ceiling of 375 of 900 errors, or 41.67 percentage points on 900 items. Neither count predicts recovery. Failure would be continued unsupported k-localization or unchanged relation accuracy despite valid evidence.

The following are **synthetic wording examples**, not verified descriptions of an existing item. The builder must fill their visual claims from annotations. For v1, suppose the options are A chair, B cabinet, C plant, D table:
> `<think>`  
> `In sampled frame 12, locate the chair at lower left, the cabinet at upper right, the plant at centre, and the table at lower right.`  
> `Comparing the closest surfaces to the frame-12 camera, the order is chair, table, plant, cabinet.`  
> `The chair is closest, so choose A.`  
> `</think>`  
> `A`

For LR, suppose the options are A Left and B Right:
> `<think>`  
> `In sampled frame 12, locate the chair at lower left and the cabinet at upper right.`  
> `Along frame 12's horizontal camera axis, the chair is left of the cabinet.`  
> `The requested relation is Left, so choose A.`  
> `</think>`  
> `A`

Bound each trace to one localization per queried object, one type-specific relation, and one option mapping. Enforce four/three/two candidates for v1/v2/v3; LR requires a horizontal relation, NF a camera-distance comparison, and UD the verified vertical convention. A validator should reject cross-type reuse. Wording alone cannot prevent copying or hallucination.

**2. Add verified same-room, same-candidate pairs across k.** **Budget guess:** add 200 rows per camera family, arranged as 100 pairs per family, with changed and unchanged true winners. This directly tests the failure represented by the 34 distinct wrong items in the 41 stale pairs; it does not establish that all 34 are recoverable. Failure would be unchanged conditional order when geometry changes, or arbitrary switching on unchanged controls.

**3. Add controlled candidate permutations and role reversals.** **Budget guess:** add 200 rows per camera family and 200 per object-object family, keeping images and geometry fixed within each control. Balance semantic polarity as well as letters. Last-candidate selections accompany 120 of 248 camera errors; dominant-polarity mistakes account for 38 of 45 LR, 32 of 56 NF, and 21 of 26 UD errors. These are overlapping diagnostic ceilings with proposal 1, not measured shortcut costs. Failure would be changed object choices after option permutation or failure to invert a relation after swapping object roles.

**4. Refuted**

The “only first-seen information” interpretation is false: target-frame shares and geometry exist in 30 of 30 audited rows. The existing textual targets omit much of that evidence.
A later first-seen frame does not necessarily mean zero visible pixels at k. In 3 of 30 audited rows, an object has a later first-seen frame but positive target-frame share below the stored visibility floor.
The first-wave dev scores and answer-bias counts remain consistent with this analysis. The larger UD sample does not support extrapolating its small-sample Up imbalance: Up occurs on 745 of 1,500 sampled rows.

**5. Not established**

These associations do not identify which shortcut causally drives an answer. Generated first-seen claims may themselves follow the chosen answer. Controlled image, k, candidate-order, and role interventions would separate these possibilities.
UD class-height dependence remains unmeasured for 148 of 150 dev items under exact ordered-pair lookup. Broader training coverage or a prespecified, independently validated class mapping would settle it.
No RGB, raster, or independent geometry audit was performed. Visibility shares may require validation; depth ordering cannot be certified from coarse image regions alone. Full truth orders, instance correspondence across questions, and controlled vehicle-N ablations are needed to establish recoverable points.

**Appendix — CLASSIFIER**

```python
import sys, json, re, random, sqlite3, itertools
from collections import defaultdict, Counter
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
base = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
idx = json.load(open(base + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + base + '/vqa/rows.sqlite?mode=ro', uri=True)
def sample(t, n):
    keys = [i for a, b in idx[t] for i in range(a, b + 1)]
    keys = sorted(random.Random(200).sample(keys, n))
    out = []
    for start in range(0, n, 200):
        batch = keys[start:start + 200]
        sql = 'select i,row from rows where i in (' + ','.join('?' * len(batch)) + ')'
        out.extend(json.loads(s) for i, s in db.execute(sql, batch))
    assert len(out) == n and all(r['question_type'] == t for r in out)
    return out
def q(r):
    return r.get('question', r.get('student_input', {}).get('question'))
def options(r):
    return [o.split('. ', 1)[1].lower() for o in
            (r['options'] if 'options' in r else r['student_input']['options'])]
def word(r, field):
    return options(r)[ord(r[field].strip()) - 65]
def frame(r):
    return int(re.search(r'frame (\d+) of 32', q(r), re.I)[1])
def pair(r):
    m = re.search(r'relative to (.*?), is (.*?) to the', q(r).lower())
    return m[2], m[1]
def order(r):
    m = re.search(r'the objects are (.*?)\.\s*So ', r['text'])
    return m[1].lower().split(', then ')
dev = K.vsti('R1', 200)
cams = ['camera_obj_rel_dist_v' + str(i) for i in (1, 2, 3)]
ud = 'obj_obj_relative_pos_ud'
tr = {t: sample(t, 500) for t in cams}
tr[ud] = sample(ud, 1500)
audit = [r for t in cams + [ud] for r in tr[t][:5]]
audit += sample('obj_obj_relative_pos_lr', 5) + sample('obj_obj_relative_pos_nf', 5)
print('Errors:', sum(r['score'] == 0 for r in dev), 'of', len(dev))
print('Audit geometry:', sum('geometry_values' in r['provenance'] for r in audit), 'of', len(audit))
print('Audit all-zero visibility:', sum(all(v == 0 for v in r['provenance']['frame_n_share'].values()) for r in audit), 'of', len(audit))
pc = defaultdict(Counter)
for r in tr[ud]:
    pc[pair(r)][word(r, 'answer')] += 1
major = {p: max(c, key=c.get) for p, c in pc.items()
         if len(c) == 1 or len(set(c.values())) > 1}
covered = [r for r in dev if r['type'] == ud and pair(r) in major]
print('UD coverage:', len(covered), 'of', 150)
print('UD prior model/truth:', [sum(word(r, f) == major[pair(r)] for r in covered) for f in ['pred', 'gt']], 'of', len(covered))
groups = defaultdict(list)
for r in dev:
    if r['type'] in cams:
        groups[r['room']].append(r)
overlap, comparable, changed, tracked = 0, 0, 0, 0
for rows in groups.values():
    for a, b in itertools.combinations(rows, 2):
        common = set(options(a)) & set(options(b))
        if frame(a) == frame(b) or len(common) < 2:
            continue
        overlap += 1
        if word(a, 'gt') not in common or word(b, 'gt') not in common:
            continue
        comparable += 1
        if word(a, 'gt') != word(b, 'gt'):
            changed += 1
            tracked += next(o for o in order(a) if o in common) != next(o for o in order(b) if o in common)
print('Camera overlap/comparable/truth-change:', overlap, comparable, changed)
print('Model changes with truth:', tracked, 'of', changed)
db.close()
```