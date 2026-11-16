NO — POOL_S1 multiple-choice supervision does not fully match the released option text under case/whitespace-only normalization.
Training: direction_easy 3000/3000 (100.00%), direction_medium 3000/3000 (100.00%), direction_hard 3000/3000 (100.00%), rel_distance 2676/3000 (89.20%), relative_count 1413/1413 (100.00%), relative_size_object N/A (no rows).
Dev-S1: direction_easy 150/150 (100.00%), direction_medium 150/150 (100.00%), direction_hard 150/150 (100.00%), rel_distance 150/150 (100.00%), relative_count 139/139 (100.00%), relative_size_object 150/150 (100.00%); route_planning: released text unavailable, 150/150.

The denominators above exclude unavailable released text; zero-row types are N/A. Admitted and packed files are two representations of the same rows, not independent samples. All paired MC answers/options and packed terminal answer tags were checked.

Released authority: `/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl`, joined by `qid`; `question` contains the original `Options:` block and `released_answer_check_only` selects its answer. `common.py:split_question` defines the block format. `source_join.options` in POOL_S1 is the intermediate pool order, not the released order; `source_join.gt_answer` is the intermediate answer. The audit uses the original released prompt, never assumes those fields are released labels.

Sampling: rank final eligible (set, qid) rows per type by SHA256(`devs1-r2|TYPE|SET|QID`), take the first 3,000 or all if fewer. Apply all three manifest exclusion lists first. `TRAIN_SAMPLE.jsonl` records both full questions, both option lists, both answers, scenes, and source lines. `LABEL_SOURCE_PINS.json` pins inputs. No synonym, punctuation, or object-name normalization is applied.

| Type | Dev content | Dev letters | Dev unavailable | Training content | Training letters | Training unavailable | File / final MC rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| object_rel_direction_easy | 150/150 (100.00%) | 69/150 (46.00%) | 0/150 (0.00%) | 3000/3000 (100.00%) | 1503/3000 (50.10%) | 0/3000 (0.00%) | 16192 / 14630 |
| object_rel_direction_medium | 150/150 (100.00%) | 53/150 (35.33%) | 0/150 (0.00%) | 3000/3000 (100.00%) | 961/3000 (32.03%) | 0/3000 (0.00%) | 15620 / 14082 |
| object_rel_direction_hard | 150/150 (100.00%) | 37/150 (24.67%) | 0/150 (0.00%) | 3000/3000 (100.00%) | 755/3000 (25.17%) | 0/3000 (0.00%) | 9715 / 8788 |
| object_rel_distance | 150/150 (100.00%) | 36/150 (24.00%) | 0/150 (0.00%) | 2676/3000 (89.20%) | 768/3000 (25.60%) | 0/3000 (0.00%) | 21433 / 19339 |
| relative_count | 139/139 (100.00%) | 53/139 (38.13%) | 0/139 (0.00%) | 1413/1413 (100.00%) | 440/1413 (31.14%) | 0/1413 (0.00%) | 1555 / 1413 |
| relative_size_object | 150/150 (100.00%) | 62/150 (41.33%) | 0/150 (0.00%) | N/A (no rows) | N/A (no rows) | N/A (no rows) | 0 / 0 |
| route_planning | N/A | N/A | 150/150 (100.00%) | N/A: direct rows excluded from program audit | N/A | N/A | N/A |

The upstream builder already gates released-label agreement: `dose_pool/work/dosepool/build.py:agree` requires `p["letter"] == q["released_answer_check_only"]` in the original option order (lines 28–31); lines 279–283 reject failures. `assign_letters` (188–211) then permutes options and rewrites `answer` and the target suffix while leaving `released_answer` unchanged. These are selection-conditioned agreements, not independent accuracy estimates.

| Type | Candidates reaching upstream release gate | Dropped | Drop share |
|---|---:|---:|---:|
| object_rel_direction_easy | 34412 | 1 | 1/34412 (0.00%) |
| object_rel_direction_medium | 35483 | 4 | 4/35483 (0.01%) |
| object_rel_direction_hard | 23409 | 3 | 3/23409 (0.01%) |
| object_rel_distance | 48842 | 501 | 501/48842 (1.03%) |
| relative_count | 4295 | 96 | 96/4295 (2.24%) |
| relative_size_object | 27839 | 1353 | 1353/27839 (4.86%) |

Denominator: all upstream rows reaching the release gate, before trace rejection/balancing; reconstructed from `pool_v0/ROWS_ALL`, `RESERVE`, and `DROPS` (agreement failures plus passed rows including later trace failures). This gate feeds the POOL_S1 builders and the dev source pool.

POOL_S1 then rerenders the pool rows: `work/v314r2/dose_t0.py` lines 121–168 copies the pool answer/options into `source_join`, may rename object categories, and rewrites question templates. Its `prefilter` (175–195) drops native MC labels unequal to the pool label. `work/v314r3/ground_rows_out/render_full.py:check_row` checks the next shuffle mapping against `source_join`. These native checks do not guarantee literal original released-text equality after object renaming. Native gate receipts are retained in `LABEL_AGREEMENT.json`.

Route provenance: `work/v314r3/route_rows.py` reads `weak_data/out/b2/PACK_route_planning.jsonl.gz` and `PLANS_route_planning.jsonl.gz`; `row = dict(r, ...)` preserves the generated pack answer and verifies it against geometric turns. This does not show that the answer was copied from a released dataset row. Route items therefore remain in the unavailable view. Relative-size program rows are absent from POOL_S1.

All 324 sampled text disagreements already appear in the intermediate `source_join`: the training answer selects that same intermediate content. All 13,413 sampled training answers match their intermediate source by content. The changed names explain the literal mismatches; this audit does not establish that each renamed object is semantically identical. The requested strict release-text gate therefore remains NO.

| Released option | Training option | Sampled mismatches |
|---|---|---:|
| chair | office chair | 137 |
| ceiling light | ceiling lamp | 67 |
| trash bin | trash can | 37 |
| computer mouse | mouse | 29 |
| sofa | couch | 29 |
| counter | kitchen counter | 17 |
| refrigerator | mini fridge | 5 |
| chair | armchair | 3 |

Builder source hashes are recorded in `LABEL_BUILDER_PINS.json`.

Disagreeing training examples (up to 10 per type):

### object_rel_direction_easy
0 disagreements in the hash-selected sample.

### object_rel_direction_medium
0 disagreements in the hash-selected sample.

### object_rel_direction_hard
0 disagreements in the hash-selected sample.

### object_rel_distance
324 disagreements in the hash-selected sample.

```json
{
  "answer": "C",
  "answer_content": "trash can",
  "options": [
    "A. nightstand",
    "B. radiator",
    "C. trash can",
    "D. tv"
  ],
  "qid": "vsi590k_080466",
  "question": "Measuring from the closest point of each object, which of these objects (nightstand, radiator, trash can, tv) is the closest to the table?",
  "question_type": "object_rel_distance",
  "released_answer": "C",
  "released_options": [
    "A. nightstand",
    "B. radiator",
    "C. trash bin",
    "D. tv"
  ],
  "released_question": "These are frames of a video.\nConsidering the nearest points, which of these (nightstand, radiator, trash bin, tv) is closest to the table? If there are multiple, identify the closest instance.\nOptions:\nA. nightstand\nB. radiator\nC. trash bin\nD. tv\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "scene0385_00",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 80467,
  "scene": "scannet/scene0385_00",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "A",
  "source_join": {
    "gt_answer": "A",
    "options": [
      "A. trash can",
      "B. tv",
      "C. radiator",
      "D. nightstand"
    ]
  },
  "source_line": 11071,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "D",
  "answer_content": "ceiling lamp",
  "options": [
    "A. stapler",
    "B. monitor",
    "C. plant",
    "D. ceiling lamp"
  ],
  "qid": "vsi590k_203352",
  "question": "Measuring from the closest point of each object, which of these objects (stapler, monitor, plant, ceiling lamp) is the closest to the whiteboard?",
  "question_type": "object_rel_distance",
  "released_answer": "B",
  "released_options": [
    "A. stapler",
    "B. ceiling light",
    "C. monitor",
    "D. plant"
  ],
  "released_question": "These are frames of a video.\nConsidering the nearest point of each object, identify the object from (stapler, ceiling light, monitor, plant) that's closest to the whiteboard. If multiple objects exist, choose the nearest instance.\nOptions:\nA. stapler\nB. ceiling light\nC. monitor\nD. plant\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "fdf7f5cd5d",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 203353,
  "scene": "scannetppv2/fdf7f5cd5d",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "D",
  "source_join": {
    "gt_answer": "D",
    "options": [
      "A. stapler",
      "B. plant",
      "C. monitor",
      "D. ceiling lamp"
    ]
  },
  "source_line": 18795,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "B",
  "answer_content": "mini fridge",
  "options": [
    "A. bed",
    "B. mini fridge",
    "C. backpack",
    "D. door"
  ],
  "qid": "vsi590k_082207",
  "question": "Measuring from the closest point of each object, which of these objects (bed, mini fridge, backpack, door) is the closest to the tv?",
  "question_type": "object_rel_distance",
  "released_answer": "B",
  "released_options": [
    "A. door",
    "B. refrigerator",
    "C. bed",
    "D. backpack"
  ],
  "released_question": "These are frames of a video.\nBased on measuring from their closest points, which among (door, refrigerator, bed, backpack) lies nearest to the tv? If several exist, measure to the closest one.\nOptions:\nA. door\nB. refrigerator\nC. bed\nD. backpack\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "scene0677_02",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 82208,
  "scene": "scannet/scene0677_02",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "D",
  "source_join": {
    "gt_answer": "D",
    "options": [
      "A. backpack",
      "B. door",
      "C. bed",
      "D. mini fridge"
    ]
  },
  "source_line": 522,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "C",
  "answer_content": "office chair",
  "options": [
    "A. bookshelf",
    "B. whiteboard",
    "C. office chair",
    "D. kettle"
  ],
  "qid": "vsi590k_219574",
  "question": "Measuring from the closest point of each object, which of these objects (bookshelf, whiteboard, office chair, kettle) is the closest to the sofa?",
  "question_type": "object_rel_distance",
  "released_answer": "B",
  "released_options": [
    "A. whiteboard",
    "B. chair",
    "C. bookshelf",
    "D. kettle"
  ],
  "released_question": "These are frames of a video.\nConsidering the nearest point of each object, identify the object from (whiteboard, chair, bookshelf, kettle) that's closest to the sofa. If multiple objects exist, choose the nearest instance.\nOptions:\nA. whiteboard\nB. chair\nC. bookshelf\nD. kettle\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "e050c15a8d",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 219575,
  "scene": "scannetppv2/e050c15a8d",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "A",
  "source_join": {
    "gt_answer": "A",
    "options": [
      "A. office chair",
      "B. whiteboard",
      "C. bookshelf",
      "D. kettle"
    ]
  },
  "source_line": 10278,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "D",
  "answer_content": "office chair",
  "options": [
    "A. window",
    "B. door",
    "C. trash can",
    "D. office chair"
  ],
  "qid": "vsi590k_076294",
  "question": "Measuring from the closest point of each object, which of these objects (window, door, trash can, office chair) is the closest to the radiator?",
  "question_type": "object_rel_distance",
  "released_answer": "A",
  "released_options": [
    "A. chair",
    "B. trash bin",
    "C. window",
    "D. door"
  ],
  "released_question": "These are frames of a video.\nUsing proximity from their closest points, determine the closest object from (chair, trash bin, window, door) to the radiator. For multiples, measure the nearest one.\nOptions:\nA. chair\nB. trash bin\nC. window\nD. door\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "scene0241_00",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 76295,
  "scene": "scannet/scene0241_00",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "C",
  "source_join": {
    "gt_answer": "C",
    "options": [
      "A. trash can",
      "B. door",
      "C. office chair",
      "D. window"
    ]
  },
  "source_line": 8307,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "A",
  "answer_content": "trash can",
  "options": [
    "A. trash can",
    "B. monitor",
    "C. clock",
    "D. window"
  ],
  "qid": "vsi590k_079604",
  "question": "Measuring from the closest point of each object, which of these objects (trash can, monitor, clock, window) is the closest to the door?",
  "question_type": "object_rel_distance",
  "released_answer": "A",
  "released_options": [
    "A. trash bin",
    "B. clock",
    "C. monitor",
    "D. window"
  ],
  "released_question": "These are frames of a video.\nWhich one of these items (trash bin, clock, monitor, window) lies closest to the door when measured from their nearest points? Use the nearest instance if multiple exist.\nOptions:\nA. trash bin\nB. clock\nC. monitor\nD. window\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "scene0211_01",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 79605,
  "scene": "scannet/scene0211_01",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "A",
  "source_join": {
    "gt_answer": "A",
    "options": [
      "A. trash can",
      "B. window",
      "C. clock",
      "D. monitor"
    ]
  },
  "source_line": 4239,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "B",
  "answer_content": "armchair",
  "options": [
    "A. window",
    "B. armchair",
    "C. door",
    "D. lamp"
  ],
  "qid": "vsi590k_083710",
  "question": "Measuring from the closest point of each object, which of these objects (window, armchair, door, lamp) is the closest to the microwave?",
  "question_type": "object_rel_distance",
  "released_answer": "B",
  "released_options": [
    "A. window",
    "B. chair",
    "C. door",
    "D. lamp"
  ],
  "released_question": "These are frames of a video.\nFrom their nearest points, which object (window, chair, door, lamp) is closest to the microwave? If multiple instances appear, pick the nearest one.\nOptions:\nA. window\nB. chair\nC. door\nD. lamp\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "scene0487_01",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 83711,
  "scene": "scannet/scene0487_01",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T0_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "B",
  "source_join": {
    "gt_answer": "B",
    "options": [
      "A. door",
      "B. armchair",
      "C. lamp",
      "D. window"
    ]
  },
  "source_line": 7531,
  "source_set": "T0_gen_r2"
}
```

```json
{
  "answer": "C",
  "answer_content": "office chair",
  "options": [
    "A. whiteboard",
    "B. telephone",
    "C. office chair",
    "D. laptop"
  ],
  "qid": "vsi590k_193500",
  "question": "Measuring from the closest point of each object, which of these objects (whiteboard, telephone, office chair, laptop) is the closest to the keyboard?",
  "question_type": "object_rel_distance",
  "released_answer": "C",
  "released_options": [
    "A. telephone",
    "B. laptop",
    "C. chair",
    "D. whiteboard"
  ],
  "released_question": "These are frames of a video.\nWhen measuring from their nearest points, which of these objects (telephone, laptop, chair, whiteboard) is closest to the keyboard? If multiple instances exist, select the closest.\nOptions:\nA. telephone\nB. laptop\nC. chair\nD. whiteboard\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "94ee15e8ba",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 193501,
  "scene": "scannetpp/94ee15e8ba",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T1H2_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "A",
  "source_join": {
    "gt_answer": "A",
    "options": [
      "A. office chair",
      "B. telephone",
      "C. whiteboard",
      "D. laptop"
    ]
  },
  "source_line": 867,
  "source_set": "T1H2_gen_r2"
}
```

```json
{
  "answer": "A",
  "answer_content": "ceiling lamp",
  "options": [
    "A. ceiling lamp",
    "B. heater",
    "C. keyboard",
    "D. monitor"
  ],
  "qid": "vsi590k_219471",
  "question": "Measuring from the closest point of each object, which of these objects (ceiling lamp, heater, keyboard, monitor) is the closest to the door?",
  "question_type": "object_rel_distance",
  "released_answer": "D",
  "released_options": [
    "A. monitor",
    "B. heater",
    "C. keyboard",
    "D. ceiling light"
  ],
  "released_question": "These are frames of a video.\nConsidering distances from each object's nearest point, which object (monitor, heater, keyboard, ceiling light) is nearest to the door? If multiple instances exist, select the closest one.\nOptions:\nA. monitor\nB. heater\nC. keyboard\nD. ceiling light\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "b08a908f0f",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 219472,
  "scene": "scannetpp/b08a908f0f",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T1H2_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "C",
  "source_join": {
    "gt_answer": "C",
    "options": [
      "A. heater",
      "B. keyboard",
      "C. ceiling lamp",
      "D. monitor"
    ]
  },
  "source_line": 476,
  "source_set": "T1H2_gen_r2"
}
```

```json
{
  "answer": "B",
  "answer_content": "mouse",
  "options": [
    "A. heater",
    "B. mouse",
    "C. table lamp",
    "D. door"
  ],
  "qid": "vsi590k_193756",
  "question": "Measuring from the closest point of each object, which of these objects (heater, mouse, table lamp, door) is the closest to the telephone?",
  "question_type": "object_rel_distance",
  "released_answer": "A",
  "released_options": [
    "A. computer mouse",
    "B. heater",
    "C. table lamp",
    "D. door"
  ],
  "released_question": "These are frames of a video.\nIdentify which of these items (computer mouse, heater, table lamp, door) is nearest to the telephone, measured from their closest points. Select the nearest if multiple instances are present.\nOptions:\nA. computer mouse\nB. heater\nC. table lamp\nD. door\nAnswer with the option's letter from the given choices directly.",
  "released_scene": "1366d5ae89",
  "released_source": "/scratch/jjyeung/orch_cd/weak_data/in/v590kgt/inv/QUESTIONS.jsonl",
  "released_source_line": 193757,
  "scene": "scannetpp/1366d5ae89",
  "source_file": "/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/T1H1_gen_r2_admitted.jsonl.gz",
  "source_gt_answer": "C",
  "source_join": {
    "gt_answer": "C",
    "options": [
      "A. door",
      "B. table lamp",
      "C. mouse",
      "D. heater"
    ]
  },
  "source_line": 3261,
  "source_set": "T1H1_gen_r2"
}
```

### relative_count
0 disagreements in the hash-selected sample.

### relative_size_object
0 disagreements in the hash-selected sample.

