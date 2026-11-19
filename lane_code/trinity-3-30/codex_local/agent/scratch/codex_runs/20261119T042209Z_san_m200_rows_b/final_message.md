## 1. Scope

I audited **720 of 53,226 kept Store-v7 rows**, with 60 per assigned family; **20 of 6,636 removed rebuilt-counting rows**; and **60 of 747 packed unit rows**. I read the ruling’s Answer, grammar, assigned-type, and unit sections. Sections 2–5 below are training-row audit tables.

These scores were recomputed through `san_kit`; source files are identified in the appendix. Direct scores use B2048. Routed scores use the loader’s separate G3T arm.

| Set and type | Items evaluated | Step 544 → step 200 |
|---|---:|---:|
| dev-S1 counting | 150 of 150 | 62.80 → 56.33 |
| R0-dev counting | 385 of 385 | 50.78 → 53.74 |
| R0-dev appearance order | 246 of 246 | 56.50 → 62.20 |
| VSTI camera-relative v1 | 150 of 150 | 24.67 → 38.00 |
| VSTI camera-relative v2 | 150 of 150 | 32.00 → 37.33 |
| VSTI camera-relative v3 | 150 of 150 | 55.33 → 59.33 |
| VSTI left/right | 150 of 150 | 54.00 → 70.00 |
| VSTI near/far | 150 of 150 | 51.33 → 62.67 |
| VSTI up/down | 150 of 150 | 59.33 → 82.67 |
| Routed dev-S1 absolute distance | 150 of 150 | 28.27 → 50.27 |
| Routed dev-S1 room size | 36 of 36 | 11.67 → 66.94 |
| Routed room134 | 134 of 134 | 6.57 → 64.40 |

The VSTI aggregate improves from 46.11 to 58.33 across 900 of 900 items. No first-seen-frame or box evaluation was supplied.

## 2. Family counts and trace skeletons

Counts come from `STORE_V7_TEMPLATE_COUNTS.json`; sampling and exclusion checks used SQLite primary keys and `n.json`/`z.json`. `X`, `F`, `N`, and `A` denote object, frame, number, and answer placeholders. Verbatim targets appear in the appendix.

| Alias and family: type × pool × retrace | Kept of family rows | Skeleton shares in sample |
|---|---:|---|
| C: object_counting × r1g × rows_rebuild_d0_v1 | 2,617 of 9,253 | “locate distinct instances of X; count once”: 18 of 60; “find…”: 10 of 60; “locate each distinct X…count once”: 17 of 60; “find…”: 15 of 60 |
| C-removed: same family | 6,636 of 9,253 removed | “list each distinct X…frame F;…”: 9 of 20; “locate each distinct X at its first appearance…”: 11 of 20; then count N |
| AW: obj_appearance_order × w1g × rows_rebuild_d0_v1 | 13,622 of 13,622 | Object/frame table then sorted order: 55 of 60; separate Locate lines then order: 4 of 60; object names then order without frames: 1 of 60 |
| AB: obj_appearance_order × b12_cntapp_gt_v1 × None | 13,965 of 14,169 | Object/frame table then sorted order: 60 of 60 |
| F: first_seen_frame × b12_cntapp_gt_v1 × None | 6,985 of 7,076 | “X is first seen in frame F (region)”: 29 of 60; “X first appears…”: 31 of 60 |
| V1: camera_obj_rel_dist_v1 × vsti_rel_v4 × None | 1,930 of 1,951 | Camera viewpoint F; locate four candidates; rank nearest→farthest; select nearest: 60 of 60 |
| V2: camera_obj_rel_dist_v2 × vsti_rel_v4 × None | 1,957 of 1,983 | Same, with three candidates: 60 of 60 |
| V3: camera_obj_rel_dist_v3 × vsti_rel_v4 × None | 1,978 of 1,998 | Same, with two candidates: 60 of 60 |
| LR: obj_obj_relative_pos_lr × vsti_rel_v4 × None | 1,978 of 1,998 | Viewpoint F; locate X,Y; state left/right relation; select letter: 60 of 60 |
| NF: obj_obj_relative_pos_nf × vsti_rel_v4 × None | 1,982 of 2,000 | Viewpoint F; locate X,Y; state nearer ordering; answer queried object’s near/far relation: 60 of 60 |
| UD: obj_obj_relative_pos_ud × vsti_rel_v4 × None | 1,974 of 1,996 | Viewpoint F; locate X,Y; compare centres against level horizon; select up/down: 60 of 60 |
| R: room_size_estimation × r1_room_traced × None | 425 of 431 | State area task; list landmarks; farthest pair with third landmark between: 23 of 60; third landmark beside: 36 of 60; pair only: 1 of 60 |
| B: box_3d × None × rows_rebuild_d0_v1 | 3,813 of 3,813 | “find X in frame F”, then box JSON: 43 of 60; “locate…”: 17 of 60 |
| U: packed units | 747 of 747 survive n/z exclusions | Two grounds, gap response, explicit conversion, answer: 60 of 60; feet: 59 of 60; inches: 1 of 60 |

**The kept counting form supplies an instruction, not an instance inventory.** None of 60 kept samples states how the answer was counted. All 20 removed samples supply first-seen lists, but their list length is not announced before generation.

## 3. Ruling violations and audit flags

| Check | Result |
|---|---|
| Unsupported metric quantity before the answer | 0 of 60 in every sampled family. Direct traces contain only step/frame numbers; unit measurements come from responses and explicit multiplication. Visual grounding remains unverified. |
| Answer-only target | 0 of 60 in every family. Counting’s generic instruction is nonempty, although evidentially weak. |
| Stated relation contradicts answer; wrong option letter | 0 of 60 in every family where applicable. These are internal-consistency checks, not checks against the video. |
| Wrong arithmetic | 0 of 60 unit rows; 0 of 20 removed counting rows. Other sampled families contain no arithmetic requiring correction. |
| Names absent from the question | Room: 60 of 60; every other family: 0 of 60. Room landmarks are supporting references, so this flag alone does **not** establish hallucination. |
| Missing counting evidence | 60 of 60 kept counting rows lack instance Locate lines and a stated count. Source annotations are needed to rebuild them honestly. |
| Missing frame/region detail | AW: 1 of 60 omits frames, which the ruling permits when the source lacks them. Box: 60 of 60 omit the image region requested by its type-specific recommendation. |
| Unit response provenance | 60 of 60 use `geometry_source=gt` and `mask_source=gt`, rather than demonstrating deployed-head responses. All 747 of 747 packed rows have `training_admitted=false`; consumption by R1 is not established by this artifact. |

## 4. Full-row recomputation

I read 10 of 60 rows per family in full, at sample positions 0, 6, …, 54. I also checked the available symbolic relationships across all sampled targets.

| Family | Recomputed result |
|---|---|
| C | 10 of 10 full reads contain no inventory from which to recompute the count. The answer matches the row’s answer field in 60 of 60. |
| C-removed | Listed-instance counts equal both the stated count and answer in 20 of 20. Longest list: five entries. Repeated frames are retained as distinct-instance entries. |
| AW / AB | Stated order maps to the answer option in 60 of 60 each. Frame sorting agrees in 59 of 59 frame-bearing AW rows and 60 of 60 AB rows. |
| F | Stated first frame equals the answer in 60 of 60. |
| V1 / V2 / V3 | First ranked candidate equals the conclusion and selected option in 60 of 60 each. |
| LR / NF / UD | Relation, queried-object orientation, conclusion, and option agree in 60 of 60 each. NF correctly reverses the nearer ordering when answering “far.” |
| R | Task unit and final-answer field agree in 60 of 60. Landmark relations cannot numerically determine the area from these rows alone. |
| B | Frame and object match the question; JSON contains the matching label and nine coordinates in 60 of 60. Geometry cannot be recomputed without annotations. |
| U | Printed gap × printed factor, decimal half-up rounding, conversion result, answer, and question unit agree in 60 of 60. Event concatenation equals `target` in 60 of 60. |

For example, unit row 0 computes `2.55 × 3.28084 = 8.366142 → 8.37 feet`; row 518 computes `1.10 × 39.3701 = 43.30711 → 43.31 inches`.

## 5. Copy risk, loop risk, and step-200 matches

Matches below concern opening lines in the full `text`, not necessarily the force-closed B2048 text. A shared opening establishes resemblance, not which family caused it.

| Skeleton | Copy risk and calls | Loop risk; longest sampled list | Observed step-200 opening matches |
|---|---|---|---|
| C kept, both instruction structures | Single, total, and relative counting can share it. No call. | None; no emitted list. | Counting: 0 of 150 dev-S1, 6 of 385 R0-dev. Cross-type relative_count: 1 of 139 dev-S1. |
| C-removed, both list structures | Total/relative counting can copy the instance-list opening. No call. | **Unbounded**; five entries in 20 samples. | Counting: 150 of 150 dev-S1, 285 of 385 R0-dev. Cross-type relative_count: 66 of 139 dev-S1. |
| Appearance table | First-seen and multi-category counting questions share temporal/object language. No call. | Bounded by four named categories; four. | Appearance: 246 of 246 R0-dev; no cross-type match in the searched direct sets. |
| Appearance separate Locate lines | **High risk:** relative distance, size, and absolute distance share “find X, first seen in frame F.” No call. | Bounded by four categories; four. | Relative distance: 50 of 150 dev-S1, 125 of 279 R0-dev. Size: 43 of 150, 105 of 293. Routed absolute distance: 49 of 150. |
| Appearance without frames | Generic object finding also fits direction and candidate-ranking questions. No call. | Bounded by four categories; four. | Exact four-object opening: 0 of 1,339 dev-S1 and 0 of 1,781 R0-dev direct traces. |
| F, either wording | Appearance, counting, and size can reuse a first-seen fact. No call. | None; one Locate statement. | Exact opening: 0 of 1,339 dev-S1 and 0 of 1,781 R0-dev. |
| V1/V2/V3/LR/NF/UD | All six share the same opening; fixed-frame camera absolute-distance and motion questions also resemble it. No call. | Question-bounded; respectively four, three, two, two, two, two objects. | Respectively 143 of 150, 149 of 150, 147 of 150, 142 of 150, 148 of 150, 142 of 150 VSTI traces. Sharing within these six is expected. |
| R, all landmark variants | Task-specific area opening lowers cross-type risk. No call. | **Unbounded:** the question does not bound selected landmarks; maximum three. | Room: 33 of 36 routed dev-S1 and 130 of 134 room134. |
| B, find/locate variants | “Find X in frame F” also fits first-seen, size, and fixed-frame distance questions. No call. | None in think block; one requested box. | Exact opening: 0 of 1,339 dev-S1 and 0 of 1,781 R0-dev. |
| U | Box-distance opening can spill into closest-object or camera-distance questions. Contains two `<ground>` calls and one `<gap>`. | No model-written variable list; response frame lists reach 27 entries and belong to the tool. | Absolute distance: 87 of 150 routed dev-S1; no other routed-A type matched this opening. |

The known counting runaway mode affects **27 of 150 dev-S1 items**, costing **17.87 counting points**, and **78 of 385 R0-dev items**, costing **19.53 points**. These are wrong, force-closed items only.

## 6. Label or scoring defects

None found in the recomputable row labels, option mappings, or conversions. VSTI sometimes locates an object in a frame later than the queried viewpoint; that is not itself a contradiction when the model may reconstruct the scene across the video.

The packed units’ admission flag is a provenance limitation, not a scoring defect.

## 7. Three changes for vehicle N

1. **Rebuild approximately 2,600 kept counting rows with verifiable, bounded inventories.** Announce the inventory length, identify instances from annotations, and add an explicit terminator before the count. **HYPOTHESIS:** this could address the 27 of 80 wrong dev-S1 counting items and 78 of 211 wrong R0-dev counting items that run away—an upper bound, not a predicted recovery. Row 107’s “count each once across the frames” supplies no evidence to verify its answer.
2. **Make direct openings name the operation before locating objects.** Reword approximately 571 appearance rows with separate first-seen Locate wording and approximately 11,800 kept VSTI rows: temporal ordering, camera-distance ranking, or the requested axis should appear first. **HYPOTHESIS:** the generic Locate opening exposes 43 of 124 wrong routed absolute-distance items, costing 16.87 distance points. This is the **least certain change**: relative-distance training also supplies that opening, so this audit cannot attribute those failures to appearance rows.
3. **Re-render the 747 unit candidates with deployed-head responses while preserving their conversion checks.** The sampled arithmetic needs no repair: 0 of 60 conversions fail. **HYPOTHESIS:** response realism could help some of the 68 of 124 wrong absolute-distance items using the unit opening, whose total exposure is 26.20 points. No recoverable subset is established; admission and response provenance must first be confirmed.

## 8. Not established

This audit does not verify pixels, instance identity, first-seen annotations, room geometry, or box geometry. Those require the sampled rows’ source frames and annotations. It also does not establish which packed unit rows R1 consumed; the admission manifest and encoded training records would settle that.

Opening matches cannot establish training-family causation or expected score gains. Controlled row-form ablations would settle those hypotheses. The unit sample contains only 1 of 60 inch rows, so its clean arithmetic result gives limited coverage of inches.

---

## Appendix

### Sample indices

All indices are zero-based primary keys, except U, whose indices are zero-based JSONL line numbers. The following specifies every selected index exactly; the classifier also prints the expanded SQLite lists.

Define `E(a,b) = [a + floor(j*(b-a)/59) for j in range(60)]`. Replacements below apply to values, not positions.

- **C:** `[107,12943,19632,24510,29159,32950,35497,38015,40162,41738,43246,44334,45323,46061,46735,47343,48088,48642,49089,49476,49782,50121,50418,50791,51061,51328,51592,51854,52112,52407,61076,69357,74430,78212,81868,84592,86723,88981,90738,92209,93577,94537,95299,95943,96553,97191,97774,98223,98634,98942,99256,99587,99917,100223,100483,100766,101020,101274,101545,321]`.
- **C-removed:** `[454,25067,35995,42191,45616,47749,49346,50341,51280,52087,69817,82268,89452,93872,96218,98053,99139,100164,100978,101830]`.
- **AW:** `[2,1336,2690,3840,4988,6162,7550,8863,10041,11136,12321,13501,14465,15318,16130,16999,19573,23418,27184,30421,33185,35386,37193,39020,40442,41492,42640,43689,46067,49781,56843,57945,58910,59809,60719,61711,62774,63744,64629,65509,66406,67258,68009,68758,69525,70469,73766,77008,79951,82317,84501,86346,88147,89659,90848,91849,92928,94515,97770,100086]`.
- **AB:** `E(173352,187520)`.
- **F:** `E(187521,194596)`.
- **V1:** `E(152123,154073)`, replacing `152651` with `152652`.
- **V2:** `E(154074,156056)`, replacing `154376` with `154377`.
- **V3:** `E(156057,158054)`, replacing `156903` with `156904`.
- **LR:** concatenate inclusive ranges `[158055,159178]` and `[194597,195470]`; select positions `floor(j*1997/59)` for `j=0…59`; replace `158325` with `158326`.
- **NF:** `E(159179,161178)`.
- **UD:** `E(161179,163174)`, replacing `161483` with `161484` and `163140` with `163141`.
- **R:** `E(195471,195901)`.
- **B:** `E(52529,56341)`.
- **U:** `E(0,746)`.

Sampling advances from evenly spaced positions to the next eligible, unused primary key, wrapping at the endpoint. It is deterministic coverage sampling, not random sampling. The full-read subset uses positions `0,6,12,18,24,30,36,42,48,54` in each list; all removed samples were read in full.

### Verbatim target examples

These are lossless JSON-string representations: `\n` denotes the target’s actual newline. Names and numbers remain unchanged.

**C, locate instances, i=107**
```text
"<think>\nStep 1: locate the distinct instances of box; count each once across the frames.\n</think>\n\n8"
```

**C, find instances, i=41738**
```text
"<think>\nStep 1: find the distinct instances of blind; count each once across the frames.\n</think>\n\n2"
```

**C, locate each, i=24510**
```text
"<think>\nStep 1: locate each distinct tea box, across the frames, and count it once.\n</think>\n\n3"
```

**C, find each, i=32950**
```text
"<think>\nStep 1: find each distinct shower wall, across the frames, and count it once.\n</think>\n\n3"
```

**C-removed, list each, i=454**
```text
"<think>\nStep 1: list each distinct dish soap bottle once, by the frame where it first appears: frame 7; frame 17.\nSo the count is 2.\n</think>\n\n2"
```

**C-removed, locate each, i=25067**
```text
"<think>\nStep 1: locate each distinct kitchen cabinet at its first appearance: frame 3; frame 3.\nSo the count is 2.\n</think>\n\n2"
```

**AW, frame table, i=2**
```text
"<think>\nStep 1: find the first frame showing each object: bedside cabinet frame 8; blanket frame 3; picture frame 18; wardrobe frame 14.\nStep 2: order them by first appearance: blanket, bedside cabinet, wardrobe, picture.\n</think>\n\nA"
```

**AW, separate Locate lines, i=37193**
```text
"<think>\nStep 1: find the mirror, first seen in frame 3.\nStep 2: find the shower, first seen in frame 1.\nStep 3: find the toilet, first seen in frame 17.\nStep 4: find the toilet paper, first seen in frame 19.\nStep 5: their first-appearance order is: shower, mirror, toilet, toilet paper.\n</think>\n\nC"
```

**AW, no frames, i=46067**
```text
"<think>\nStep 1: find the counter, the sofa, the door, the nightstand.\nStep 2: order them by first appearance: nightstand, sofa, door, counter.\n</think>\n\nD"
```

**AB, frame table, i=173352**
```text
"<think>\nStep 1: find the first frame showing each object: clock frame 27; couch frame 1; cup frame 12; whiteboard frame 20.\nStep 2: order them by first appearance: couch, cup, whiteboard, clock.\n</think>\n\nC"
```

**F, “is first seen”, i=187521**
```text
"<think>\nStep 1: the couch is first seen in frame 1 (left).\n</think>\n\n1"
```

**F, “first appears”, i=187760**
```text
"<think>\nStep 1: the tv first appears in frame 14 (left).\n</think>\n\n14"
```

**V1, i=152123**
```text
"<think>\nStep 1: take the camera viewpoint of frame 4.\nStep 2: locate the bathtub, first seen in frame 2.\nStep 3: locate the sofa, first seen in frame 2.\nStep 4: locate the table, first seen in frame 2.\nStep 5: locate the toilet, first seen in frame 6.\nStep 6: ordered nearest to farthest from the camera viewpoint of frame 4, the objects are bathtub, then toilet, then sofa, then table.\nSo the bathtub is closest to that camera viewpoint.\n</think>\n\nA"
```

**V2, i=154074**
```text
"<think>\nStep 1: take the camera viewpoint of frame 1.\nStep 2: locate the couch, first seen in frame 4.\nStep 3: locate the computer tower, first seen in frame 14.\nStep 4: locate the file cabinet, first seen in frame 1.\nStep 5: ordered nearest to farthest from the camera viewpoint of frame 1, the objects are couch, then file cabinet, then computer tower.\nSo the couch is closest to that camera viewpoint.\n</think>\n\nA"
```

**V3, i=156057**
```text
"<think>\nStep 1: take the camera viewpoint of frame 20.\nStep 2: locate the table, first seen in frame 12.\nStep 3: locate the cabinet, first seen in frame 1.\nStep 4: ordered nearest to farthest from the camera viewpoint of frame 20, the objects are table, then cabinet.\nSo the table is closest to that camera viewpoint.\n</think>\n\nA"
```

**LR, i=158055**
```text
"<think>\nStep 1: take the camera viewpoint of frame 28.\nStep 2: locate the windowsill, first seen in frame 7.\nStep 3: locate the telephone, first seen in frame 16.\nStep 4: from the camera viewpoint of frame 28, the windowsill is to the left of the telephone.\nSo the windowsill is left relative to the telephone.\n</think>\n\nB"
```

**NF, i=159179**
```text
"<think>\nStep 1: take the camera viewpoint of frame 22.\nStep 2: locate the dishwasher, first seen in frame 1.\nStep 3: locate the table, first seen in frame 1.\nStep 4: from the camera viewpoint of frame 22, the table is nearer than the dishwasher.\nSo the dishwasher is farther than the table relative to that camera viewpoint.\n</think>\n\nA"
```

**UD, i=161179**
```text
"<think>\nStep 1: take the camera viewpoint of frame 31.\nStep 2: locate the bed, first seen in frame 4.\nStep 3: locate the tv, first seen in frame 27.\nStep 4: in frame 31's level horizon, the centre of the bed is lower than the centre of the tv.\nSo the bed is down relative to the tv.\n</think>\n\nA"
```

**R, between, i=195471**
```text
"<think>\nThe question asks for the combined floor area in square meters.\nSeen: shelf in frame 11; whiteboard in frame 1; table in frame 1.\nThe shelf and the whiteboard are the farthest apart among these landmarks, with the table between them.\n</think>\n\n17.51"
```

**R, beside, i=195478**
```text
"<think>\nThe question asks for the combined floor area in square meters.\nSeen: door first seen in frame 9; doorframe first seen in frame 2; shelf first seen in frame 5.\nOf these, the doorframe and the shelf are farthest apart, with the door off to the side.\n</think>\n\n7.94"
```

**R, pair only, i=195726**
```text
"<think>\nThe question asks for the combined floor area in square meters.\nSeen: coffee table in frame 1; tv in frame 4.\nThe coffee table and the tv are the farthest apart among these landmarks.\n</think>\n\n16.82"
```

**B, find, i=52529**
```text
"<think>\nStep 1: find the box in frame 14.\n</think>\n\n```json\n[{\"bbox_3d\":[0.60, -0.36, 2.25, 0.44, 0.46, 0.63, 0.18, 0.08, 0.07],\"label\":\"box\"}]\n```"
```

**B, locate, i=52852**
```text
"<think>\nStep 1: locate the table in frame 28.\n</think>\n\n```json\n[{\"bbox_3d\":[-0.22, 0.25, 1.18, 0.40, 0.42, 0.40, 0.34, 0.19, 0.29],\"label\":\"table\"}]\n```"
```

**U, line 0, qid=a0_units_vsi590k_047478**
```text
"<think>\nI will ground the boxes and ask the tool to measure their box distance.\n<ground obj=\"door\" mode=\"box\">\n<tool_response>\ndoor: frames 1,2,3,31,32 (best 2)\nB1: f1 centre (-0.40, -0.72, 0.20) m\nsize 0.87 x 0.50 x 1.26 m\nyaw -70 deg (0 = +x; positive +x toward -z about +y)\n</tool_response>\n<ground obj=\"desk\" mode=\"box\">\n<tool_response>\ndesk: frames 1,11,12,14,15,16,17,18,19,20 (best 17)\nB2: f1 centre (1.22, -1.03, 3.68) m\nsize 1.67 x 1.56 x 0.72 m\nyaw -70 deg (0 = +x; positive +x toward -z about +y)\n</tool_response>\n<gap a=\"door\" b=\"desk\" rule=\"box_grid_5cm\">\n<tool_response>\ndistance 2.55 m\n</tool_response>\nThe box gap is the smallest distance between points on a grid over both objects' full boxes, taken over every pair of instances.\nConverting to feet: 2.55 x 3.28084 = 8.37.\n</think>\n<answer>8.37</answer>"
```

### Score source files

All paths below start with `/scratch/jjyeung/orch_n30/`.

- Step-544 dev-S1: `evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
- Direct R1: `cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- Step-544 R0-dev: `cont_ops16/work/c15/h1read/kit/build/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- VSTI: `cont_ops16/work/c15/h1vsti/kit/build/{acb2faedd41,a35f73e87f0}/fetched/x/r6/a0/results/{0,budget_2048/0}/items_a0.jsonl`, respectively step 544 and step 200.
- Routed step 544: `cont_ops16/work/c15/r1route/out3s/bases/b1/work/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`, plus read `1`, journal `3`, for distance.
- Routed step-544 room134: `cont_ops16/work/c15/r1route/out3s/bases/b2/work/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`.
- Routed step 200: `cont_ops16/work/c15/r1route/out3/A4/ret/metadata/reads/0/metadata/journals/{0,1,2,3,4}/0/items.jsonl`.
- Routed step-200 room134: `cont_ops16/work/c15/r1route/out3/B5/ret/metadata/reads/0/metadata/journals/4/0/items.jsonl`.

### CLASSIFIER

This reproduces the family samples, skeleton counts, unit arithmetic, principal opening matches, and priced counting runaways. It performs only primary-key SQLite reads.

```python
import sys,json,sqlite3,re,collections,decimal
sys.dont_write_bytecode=True
B="/scratch/jjyeung/orch_n30/"
R=json.load(open(B+"r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json"))["families"]
C=json.load(open(B+"dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json"))["families"]
bad={json.loads(l)["row_key"] for p in ("n","z") for l in open(B+"r1_ops6/cp/out/records/"+p+".json")}
db=sqlite3.connect("file:"+B+"r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro",uri=True)
V=["camera_obj_rel_dist_v"+str(j) for j in (1,2,3)]+["obj_obj_relative_pos_"+x for x in ("lr","nf","ud")]
F=["object_counting|r1g|rows_rebuild_d0_v1","obj_appearance_order|w1g|rows_rebuild_d0_v1","obj_appearance_order|b12_cntapp_gt_v1|None","first_seen_frame|b12_cntapp_gt_v1|None"]+[t+"|vsti_rel_v4|None" for t in V]+["room_size_estimation|r1_room_traced|None","box_3d|None|rows_rebuild_d0_v1"]
def fetch(ids):
 return {i:json.loads(s) for i,s in db.execute("select i,row from rows where i in ("+",".join("?"*len(ids))+")",ids)}
def sk(f,t):
 if f.startswith("object_counting"):return re.search(r"Step 1: (find|locate)",t)[1]+(" instances" if "instances of" in t else " each")
 if f.startswith("obj_appearance"):return "table" if "first frame showing" in t else "per-object" if "first seen in frame" in t else "no-frame"
 if f.startswith("first_seen"):return "seen" if "is first seen" in t else "appears"
 if f.startswith("room_size"):return "between" if "between" in t else "side" if "side" in t else "two"
 if f.startswith("box_3d"):return "find" if "Step 1: find" in t else "locate"
 return "main"
for fam in F:
 typ,pool,_=fam.split("|"); ids=[i for a,b in R[typ] for i in range(a,b+1)]
 if typ=="object_counting":ids=[i for i in ids if i<141000]; countids=ids
 if typ=="obj_appearance_order":ids=[i for i in ids if (i>=173352)==(pool=="b12_cntapp_gt_v1")]
 pos=[j*(len(ids)-1)//59 for j in range(60)]; got={}; seen=set()
 for off in range(500):
  req={j:ids[(p+off)%len(ids)] for j,p in enumerate(pos) if j not in got}
  if not req:break
  rows=fetch(list(set(req.values())))
  for j,i in req.items():
   r=rows[i]; key="|".join([r["question_type"],str(r.get("pool")),str((r.get("retrace") or {}).get("rule"))])
   if key==fam and r["qid"] not in bad and i not in seen:got[j]=(i,r);seen.add(i)
 assert len(got)==60
 print(fam,C[fam]["kept_nz"],"of",C[fam]["rows"],dict(collections.Counter(sk(fam,r["target"]) for i,r in got.values())))
 print("i:",[got[j][0] for j in range(60)])
removed=[]
for j in range(20):
 for off in range(500):
  i=countids[min(j*(len(countids)-1)//19+off,len(countids)-1)];r=fetch([i])[i]
  if r.get("pool")=="r1g" and r["qid"] in bad and i not in removed:removed.append(i);break
print("removed i:",removed,collections.Counter("list" if "list each" in r["target"] else "locate" for r in fetch(removed).values()))
U=[];D=decimal.Decimal
for i,l in enumerate(open(B+"r1_ops6/cp/out/units/packed.jsonl")):
 if i not in {j*746//59 for j in range(60)}:continue
 r=json.loads(l);t=r["target"];u,x,f,y=re.search(r"Converting to (\w+): ([\d.]+) x ([\d.]+) = ([\d.]+)",t).groups();y=y.rstrip(".")
 ok=D(y)==D(r["answer"])==(D(x)*D(f)).quantize(D(".01"),rounding=decimal.ROUND_HALF_UP)
 ok=ok and re.findall(r"distance ([\d.]+) m",t)==[x] and u in r["question"] and f=={"feet":"3.28084","inches":"39.3701"}[u]
 U.append((i,u,ok))
print("units:",collections.Counter(u for i,u,k in U),"conversion failures",sum(not k for i,u,k in U),"of",len(U))
sys.path.insert(0,B+"swarm_an/kit");import san_kit as K
P={"C-list":r"^Step 1: (?:list each distinct|locate each distinct .+ at its first appearance|find each distinct .+using its first-seen frame)","A-table":r"^Step 1: find the first frame showing each object:","A-locate":r"^Step 1: find the .+, first seen in frame \d+\.","V":r"^Step 1: take the camera viewpoint of frame \d+\."}
for s in ("dev-S1","R0-dev","vsti"):
 rows=K.vsti("R1",200) if s=="vsti" else K.direct("R1",200,s)
 for k,p in P.items():
  for typ in sorted({r["type"] for r in rows}):
   allr=[r for r in rows if r["type"]==typ]; m=[r for r in allr if re.search(p,(r["text"] or "").replace("<think>","").strip())]
   if m:print(s,k,typ,len(m),"of",len(allr))
 for typ in ("object_counting",):
  allr=[r for r in rows if r["type"]==typ];m=[r for r in allr if r["forced_close"] and r["score"]<1]
  if allr:print(s,"runaway wrong",len(m),"of",len(allr),"cost",100*sum(1-r["score"] for r in m)/len(allr))
```