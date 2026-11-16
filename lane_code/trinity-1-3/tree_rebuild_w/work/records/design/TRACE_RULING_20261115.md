# Trace ruling for the repair seal (2026-11-15)

**Status:** proposed ruling, read-only analysis. Nothing was built, launched or admitted. It needs the orchestrator's acceptance and two user defaults (section 2.9). Paths are under `/scratch/jjyeung/orch_cd/` unless absolute. Scripts and their outputs are in `trace_ruling/work/`.

## Question

Which trace should each training row of the repair seal carry, and what should the model do at inference, so that (1) no row is answer-only and no trace states a quantity that the frames, a printed response or an explicit computation does not supply, and (2) the model does not route a type whose program loses to direct answering with deployed perception?

## Answer

1. **Form by type (O1).** Program rows only for absolute distance, room size and the three camera types. Every other type gets a direct row whose trace locates objects by frame, states relations in words, and writes out the question's own steps. No direct trace is empty, and none states a measurement.
2. **Deployed responses for the routed object types only (O3, restricted).** Render absolute-distance and room rows from the pipeline that runs at inference, on training scenes. Keep rows whose response agrees with ground truth, and rows whose response is a real failure and whose trace then answers directly from the frames. No row ends in a refusal.
3. **Direction and counting stay direct.** O2 is rejected for this seal and O4 is rejected outright. O3 for hard direction and a tool-plus-reconcile form for counting are gated experiments, not seal content.
4. **The builder re-renders two families and rebuilds one.** Facing and totals become direct rows; units stay program rows but in the sealed event schema; recovery is rebuilt on routed types with real failure statuses. The integration tree must stop admitting direct rows that contain calls and responses; today it supervises that text.

The sealed leg did train answer-only rows: 15.3 of its 192 language rows per step. It also trained 95.0 rows per step that state a measurement with no derivation. Both forms end with this seal.

---

# Part 1: facts

## 1a. Row families and trace forms

### The sealed leg (job 169097, steps 1 to 544)

A step holds 192 language rows: 128 VQA and 64 routing. The design step is 320 rows (pose 64, VQA 128, MDG 32, routing 64, pointing 32; `leg_s1_tree/out/NO_FLAG_MIX.md:7-13`). The run had no MDG stream and used 288 (`leg_s1_tree/out/PRELAUNCH_CARD.md:37-43`; `leg_s1_review/CONTINUATION_FACTS_20261114.md:32`). The language rows are the same in both.

Counts and expected rows per step are exact for production: the local pass reproduced both production digests (`leg_s1_tree/out/ADMITTED_TYPE_HISTOGRAM_07ca49df.md:3,11-18,31-36`). Expected rows are natural shares under the stream quotas, not per-type quotas. `NO_FLAG_MIX.md:35-43` gives design values within 0.2 rows of these.

| Stream | Type | Trace form | Rows | Expected rows per step |
|---|---|---|---:|---:|
| VQA | direction easy | prose stating an angle, no derivation | 13,586 | 15.13 |
| VQA | direction medium | prose stating an angle, no derivation | 16,527 | 18.41 |
| VQA | direction hard | prose stating an angle, no derivation | 22,607 | 25.18 |
| VQA | relative distance | prose stating a distance in metres per candidate | 22,082 | 24.60 |
| VQA | object size | prose stating a length in centimetres | 10,492 | 11.69 |
| VQA | counting | prose listing frames and first-seen frames | 10,000 | 11.14 |
| VQA | appearance order | prose listing first-seen frames | 15,302 | 17.05 |
| VQA | 3D box | **empty think block**, JSON answer | 4,308 | 4.80 |
| routing | route planning | **empty think block**, letter answer | 9,404 | 10.53 |
| routing | absolute distance | program, printed responses | 11,728 | 13.14 |
| routing | room size | program, printed responses | 581 | 0.65 |
| routing | camera displacement | program, printed responses | 14,020 | 15.70 |
| routing | camera movement direction | program, printed responses | 12,260 | 13.73 |
| routing | camera rotation | program, printed responses | 9,143 | 10.24 |

| Form | Rows | Expected rows per step | Share of 192 |
|---|---:|---:|---:|
| Empty think block (answer-only) | 13,712 | 15.33 | 8.0% |
| Prose stating a measurement | 85,294 | 95.02 | 49.5% |
| Prose listing frames | 25,302 | 28.19 | 14.7% |
| Program with printed responses | 47,732 | 53.47 | 27.8% |
| Qualitative with no numbers | 0 | 0 | 0% |

**The sealed leg trained answer-only rows.** Route planning and 3D boxes have `<think>\n\n</think>` followed by the answer: 15.33 expected rows per step, 4.8% of a 320-row step and 5.3% of the 288-row step (`ADMITTED_TYPE_HISTOGRAM_07ca49df.md:18,24,36,41`; `PRELAUNCH_CARD.md:52`). The histogram pass checked empty against non-empty think content per row (same file, line 48).

**It also trained the form that failed review.** The five stated-measurement families come from `weak_data_canonical_trace_pack`; the 2026-11-07 review found that the weak packs' direction and relative-distance rows "state bare numbers" (`trace-review-20261107.md:14`), and the sampled rows still do (Appendix A). The leg's own read flags all 25 sampled rows (`leg_s1_tree/out/ROWS_FIVE_PER_TYPE_07ca49df.md:3`), and the orchestrator accepted them for that leg only (`leg_s1_tree/STATUS.md:41`).

**It trained no facing-away row and no multi-category total row.** The kit config has no `extra_pool_sets` key (`leg_s1_fourstream_kit/final_b/k/b02e4385.json`), every sealed direction row is a "toward" row, and no sealed counting row names several categories (`rs_rows/out/SEALED_REFERENCE.json`, keys `object_rel_direction_*|toward` and `single_or_unspecified_count`; `rs_rows/out/ROWS_REPORT.md:30`). The empty-think facing and total rows are kits built for the next leg: `back_dir/out/r2/DESIGN_RECORD.md:11` ("Both directions use `<think>`, a blank line, `</think>`, a blank line, and the answer letter") and `pool_r2/out/ROWS_READ_TOTALCOUNT.md:28-38`. The flag tree mixed them in as direct rows (`leg_s2_tree/REVIEW_VERDICT.md:10,26`); the leg that ran did not use that tree.

**Types with no language row at all:** camera-object absolute distance, VSTI's camera-object relative distance and object-object relations, relative count, relative size, absolute direction (`PRELAUNCH_CARD.md:54`; `NO_FLAG_MIX.md:54`).

**Pose and pointing rows are not question-answer traces.** Pose rows (64 per step) carry a readout target (`leg_s1_tree/work/tree_s1/student_pilot/carrier_c1_data.py:431-432`). Pointing rows (32 per step) carry `{"point_2d": [u, v]}` or `null` with no reasoning text (same file, lines 521 and 530). I treat both as perception supervision outside the trace rule.

Three sample rows per family, with question, think block and answer, are in Appendix A (14 families, 42 rows, each cited by line of `ROWS_FIVE_PER_TYPE_07ca49df.md`).

### The builder's four families (`rs_rows/out/rows`, built 05:20Z, all unadmitted)

| Family | Rows | Scenes | Question type | Trace form as built | Rows per step in the sealed leg |
|---|---:|---:|---|---|---:|
| facing | 67,970 (33,985 toward/away pairs) | 1,135 | direction easy, medium, hard | three `<ground>` calls with responses, then cross, dot and atan2 written in text | 0 |
| units | 24,628 | 2,189 | absolute distance (23,456), room size (1,172) | `<ground mode="box">` twice and `<gap>`, or `<ground mode="room">`, then one conversion line | 0 |
| recovery | 4,670 | 673 | counting totals only | one failing call, then either instance enumeration (2,335) or a refusal (2,335) | 0 |
| totals | 2,335 | 673 | counting totals | `<ground mode="instances">` per category, then an explicit sum | 0 |

Sources: `rs_rows/out/ROWS_REPORT.md:5-10,28`; `rs_rows/out/rows/*/MANIFEST.json` (`strata`). Samples are in Appendix B, cited by line of `rs_rows/out/SAMPLES.md` as regenerated at 05:20Z.

Four properties hold for every row I read:

- **The target is a flat direct-schema string that contains calls and responses.** `repair.source_form` is `direct`, `repair.target_form` is `evidence_trace`, `head_program` is null, `route_policy_approved` is false (first two rows of `rows/facing/rows.jsonl.gz`). The builder says so: "These targets contain explicit evidence calls, including on direct-by-default tasks" (`ROWS_REPORT.md:57`).
- **Every response is ground truth.** "The response evidence is GT-derived source supervision" (`ROWS_REPORT.md:55`); the facing row carries `scope: "GT-derived source centres; no fresh mask/depth lifting"`.
- **Recovery teaches refusal on half its rows,** including on `not seen` (116 rows). Its failing call is unrelated to the question: a box ground or a camera gap inside a counting question (`SAMPLES.md:890-907,1096-1100`), and 16 of its 20 refusal statuses are error texts of other tools, six of them room errors (`rows/recovery/MANIFEST.json`, `strata`; `ROWS_REPORT.md:28,59`).
- **Unit rows end in a bare number,** while the sealed rows of the same types end in `<answer>...</answer>` (Appendix A, absolute distance; `tree_s1/student_pilot/ground_rows.py:39-40` enforces that ending).

**The integration tree's first pass admits these targets as direct rows and supervises every token.** It builds a `direct_evidence_trace` row with `events=[]` and `tool_output_spans=[]` (`rs_tree/work/tree_r1/student_pilot/carrier_c1_routing.py:813-834`), passes the builder's row through unchanged (`r1_contract.py:90-92`), and records the choice: "Direct rows retain printed tool responses and explicit computations" (`rs_tree/out/DESIGN_RECORD_rs_tree_20261115.md:14`). The stream builder's docstring in the same file states the opposite intent: "direct rows carry a reasoning trace without tool calls" (line 849). As integrated, the seal would train the model to write `<ground>` calls and their responses as plain text on direction and counting questions.

## 1b. Where printed responses come from

| Program family | Response source at training time | Evidence | What the same call returns at inference |
|---|---|---|---|
| Camera displacement, movement direction, rotation (`<move>`, `<turn>`) | The row's recorded ground-truth pose values | `tree_s1/student_pilot/carrier_c1_routing.py:304-305` ("Replays the row's own GT printed values"); own-value probability 0.0 (kit `b02e4385.json`, `scheduled_sampling.max_own_probability`; `CONTINUATION_FACTS_20261114.md:18`) | G3T tower pose, converted to the native camera convention and scaled by the checkpoint's own pose and depth heads (`legs1_routed/out/ROUTED_READ_SPEC_NOMDG.md:23,27`) |
| Absolute distance (`<ground mode="box">`, `<gap>`) | Ground-truth masks and geometry; boxes from annotations (`annotation_full_box_v1`, 112,770 response events) or a fused fit (`fit_gbox_fused_full_v1`, 6,546) in rows whose mask and geometry sources are both `gt` | Bounded read of `dose_pool/out/POOL_S1/*_admitted.jsonl.gz`, 73,088 rows: `mask_source` gt 72,005 and none 1,083; `geometry_source` gt on all; `not_seen` false on all; `simulated_misses` empty on all (`work/pool_sources.txt`). `tree_s1/generator/dose_t0.py:1` ("GT.npz") | SAM 3 proposals at the frozen `dense_aliases` setting, the frozen candidate policy, G3T depth lifting and the frozen box-fit policy; no ground-truth mask, no direct-answer fallback (`ROUTED_READ_SPEC_NOMDG.md:31,35,48`). Real failures occur: 13.7% of 791 dev-S1 distance items return no answer, all "No linked candidate for a required operand" (`work/peritem_stats.txt`) |
| Room size (`<ground mode="room">`) | Ground-truth geometry, no masks (`mask_source` none) | Same read; `dose_pool/STATUS.md:4` | Floor-cell voting on predicted geometry, no masks (`ROUTED_READ_SPEC_NOMDG.md:49`) |
| Deferred pool programs (direction, relative distance, counting, never trained in the sealed leg) | Ground truth; counting takes "GT identity at training time" | `dose_pool/out/RENDERER_GAPS.md:26`; same read | Deployed masks; counting uses a 3D merge of proposals (same line) |

Three further facts bear on the ruling.

- **The model never writes a response.** The routing encoder masks response spans from the loss (`carrier_c1_routing.py:467-468`, "tool outputs masked"). The VQA path supervises its whole target (`ROWS_FIVE_PER_TYPE_07ca49df.md:11`). A flat direct row that contains response text would therefore train the model to write responses, if it entered the VQA stream as built.
- **Training never showed a failed call.** `not_seen` is false and `simulated_misses` is empty on all 73,088 pool rows read, none of 165 sampled training distance rows shows a failure, and after a refused ground the model issued 198 repeated gap calls (`next_queue/out/NEXT_QUEUE_20261115.md`, section 1.6, row "Failed-ground behavior").
- **"The model's own heads" do not ground objects in this lineage.** The four-stream config has neither `mdg` nor `geometry_online` (`ROUTED_READ_SPEC_NOMDG.md:15`). The own heads supply scale and gravity; masks come from the external segmenter. The 58.7 score "with the model's own heads" belongs to an earlier model's head programs (`toolprog-results-20261107.md:13`). Own-value sampling exists in code (`carrier_c1_routing.py:533-541`) and was off; a grounded row cannot take own values without a live grounding session (line 348).

## 1c. Why programs lose on direction and counting with deployed masks

The route table on dev-S1 (deployed masks, parent CP1 m200 as the direct arm, room bootstrap): `devs1_masks/cache_r1/ROUTE_PREDICTED.md:9-16`. The fallback column is recorded in `ROUTE_PREDICTED.json` (`fallback_program_pct`, "direct fallback descriptive only"); the last three columns are my arithmetic on `ROUTE_PREDICTED.pairs.jsonl` (`work/pairs_stats.txt`, `work/pairs_fallback.json`).

| Type (150 items; room 36) | Direct | Program | Program minus direct | Program, direct when no answer | No answer | On answered items: program / direct | Per-item best of the two |
|---|---:|---:|---|---:|---:|---|---:|
| Absolute distance | 38.9 | 46.9 | +8.1 [+0.9, +16.9] | 54.5 | 28 | 57.7 / 38.4 | 62.9 |
| Room size | 55.6 | 62.2 | +6.7 [-14.4, +25.0] | 62.2 | 0 | 62.2 / 55.6 | 75.8 |
| Direction hard | 78.7 | 68.7 | -10.0 [-19.8, -1.4] | 82.7 | 33 | 88.0 / 82.9 | 89.3 |
| Direction easy | 91.3 | 70.7 | -20.7 [-34.7, -8.7] | 84.0 | 23 | 83.5 / 92.1 | 95.3 |
| Direction medium | 88.7 | 61.3 | -27.3 [-41.9, -14.3] | 82.7 | 35 | 80.0 / 87.8 | 94.7 |
| Relative distance | 72.0 | 44.0 | -28.0 [-40.3, -16.4] | 62.7 | 43 | 61.7 / 74.8 | 78.7 |
| Counting | 58.4 | 44.2 | -14.2 [-24.6, -4.9] | 44.9 | 2 | 44.8 / 58.5 | 71.1 |
| Object size | 68.1 | 60.5 | -7.6 [-14.5, -0.9] | 64.1 | 9 | 64.4 / 68.7 | 82.1 |

The records give five causes.

1. **Missing operands end the program.** 224 of 1,056 operand instances are never proposed; ever-recall is 78.8% (`mask_recall/out/NEVER_PROPOSED.md:1,41`). A direction program needs three operands, so 15 to 23% of direction items and 29% of relative-distance items return no answer. That loss is visible in the response, and a direct fallback recovers most of it (column 5).
2. **Wrong objects are accepted silently.** Wrong accepts cost 12.0 relative-distance and 6.8 to 9.5 direction task points; 20 of 30 hand-read cases are visually fixable (`NEXT_QUEUE_20261115.md`, section 1.6, row "Wrong object accepted"). After fallback, easy, medium and relative distance still trail direct by 7.3, 6.0 and 9.3 points, because on answered items the program is less accurate than direct (column 7). The response shows no sign of the error.
3. **Ground-truth masks do not make direction programs beat direct.** With ground-truth masks the programs score -12.5 [-27.6, 0.0], -5.1 and +2.6 against direct on easy, medium and hard (`devs1_masks/out/ROUTE_GT_UPPER_BOUND.md:11-13`). "Direct beats even the GT program on some types: direction easy, ..." (`toolprog-results-20261107.md:22`). Direct direction is already 80 to 90 on official VSI-Bench (`NEXT_QUEUE_20261115.md`, section 1.1, relative direction row).
4. **Counting fails without a visible cue.** The program answers 148 of 150 items and is exact on 52. The losses are objects never proposed (+23.2 if granted) and identity and mask residual (+17.5): split instances and wrong accepts (`ROUTE_PREDICTED.json`, `decomposition`; `NEVER_PROPOSED.md:35`). Denser proposals lower counting by a further 8.3 (`result-devs1-route-table-predicted-masks-20261112.md:27`). With ground-truth masks the same program scores 85.7 against 56.7 direct, +29.0 [+17.1, +41.1] (`ROUTE_GT_UPPER_BOUND.md:10`). Counting is the type with the largest routed ceiling and the least visible failure.
5. **Arithmetic written in text is unreliable.** Text atan2 errs on 13 to 30% of items; the rule is that an operation stays in text only at 2% error or less (`toolprog-results-20261107.md:21`).

Two cautions about the direct arm. It is the parent's prose with self-asserted quantities, not a trace-free answer (`result-devs1-route-table-predicted-masks-20261112.md:22`), and its failures are those asserted quantities: 62 wrong bearings and 120 wrong counts on dev-S1 (`trace_diag/out/TRACE_DIAG.md:11,16`). Direct counting sits below the constant-2 answer, 58.40 against 60.9 to 61.87 (`TRACE_DIAG.md:119,121`). And the parent saw dev-S1 scenes before the split existed (`NEXT_QUEUE_20261115.md`, section 1.5), so its direct numbers there may be inflated. The official direct cells (direction 80 to 90, counting 67.31; section 1.1 of the same report) show that the direct level does not come from that exposure. No official program-against-direct pair exists for these types.

The older records agree on the principle. Traces that assert unseen numbers cost about 12 points against bare answers, and camera motion and room size are never visible, so they need a tool (`trace-failure-analysis-20261020.md:11,21,32`). Sampled prose rows passed review 0 of 85; tool programs with printed values are the template (`trace-review-20261107.md:10,15`). Prose traces may be converted by program (`user-ruling-trace-rewrite-gemini-20261111.md:8`). The product routes inside one forward pass with no harness (`no-harness-end-to-end.md:8,15`).

---

# Part 2: ruling

## 2.1 Trace grammar

A trace is built from four kinds of line and nothing else.

| Line | Content | Example |
|---|---|---|
| Locate | An object and one frame where it is clearly visible (first-seen or best view); optionally a coarse image region | "the stove is seen in frame 17" |
| Relate | A relation in words among located things: side, front or behind, order, nearest to farthest, which dimension is longest | "the pillow is nearest, then the bed" |
| Step | The question's own logic: restating its clause, a half turn, the threshold the question defines, listing instances, a sum, a unit conversion of a printed value | "I face away, a half turn: left and right swap" |
| Call | A call and its printed response; values copied from a response (program types only) | `<gap ...>` and `distance 2.55 m` |

Numbers allowed in a trace: frame indices, counts of listed items, values a response printed, results of explicit arithmetic on those, and constants the question states. A length, area, angle or coordinate that no response printed never appears in a trace. For a direct numeric type the estimate appears only as the answer after `</think>`.

Frames are cited one per object, from the row's own source (first-seen frame or the ground-truth best view), never as an exhaustive visibility list and never as "absent in". The 2026-11-07 review rejected exhaustive ground-truth visibility lists (`trace-review-20261107.md:30,35`) and passed first-seen frames in appearance-order rows (line 14). A row whose source has no frame for an object omits that Locate line.

## 2.2 Recommendation per type

"Route" means the model writes the calls and copies the printed value; after a failed call it answers directly from the frames. "Direct" means no call. The model chooses by question type with no prompt flag, as it already does: in the step-544 direct read, which serves no tool, 164 of 168 budget hits fall on distance and room, where the model calls the tool, and the other types hit the budget on 7 of 1,339 items (`NEXT_QUEUE_20261115.md`, sections 1.5 and 1.7). That choice is untested on types that have no row; the report names camera-object absolute distance as a possible unexpected-call family (section 1.7), so that type needs direct rows before its direct behaviour can be assumed.

| Benchmark type | Training trace in the repair seal | Inference | Main evidence |
|---|---|---|---|
| **VSI-Bench** counting; **ReVSI** count single | Direct. One Locate line per distinct instance (first-seen frame, image region where a mask supplies it), then the count. No exhaustive frame list | Direct | Program -14.2 with deployed masks; errors carry no cue (1c, cause 4) |
| **ReVSI** count total | Direct. Per category the same instance list, then the explicit sum and one scalar | Direct | Same; the sum is an explicit computation |
| **VSI-Bench**, **ReVSI** absolute distance | Program: two box grounds, `<gap>`, one conversion line. Responses rendered from the deployed pipeline. Rows with a failed call end in a direct answer with Locate lines | Route; direct after a failed call | +8.1 routed, 54.5 with fallback against 38.9 direct |
| **VSI-Bench** room size; **ReVSI** combined room, main room | Program: `<ground mode="room">`, conversion line. Responses from predicted geometry | Route | +6.7 on dev-S1 (undecided), +3.09 [-1.88, +8.12] official; room size is never visible in frames (`trace-failure-analysis-20261020.md:21`). The main-room scope needs a tool-side rule (`TRACE_DIAG.md:19`), not a trace change |
| **VSI-Bench**, **ReVSI** object size | Direct. Locate line, then the Step "the longest of its three dimensions". The number is the answer only | Direct | Program -7.6; -1.6 even with ground-truth masks (`ROUTE_GT_UPPER_BOUND.md:15`) |
| **VSI-Bench** relative distance; **ReVSI** closest, farthest | Direct. Locate the anchor, order the candidates in words, restate "closest" or "farthest" | Direct | Program -28.0; +2.1 with ground-truth masks (same file, line 14) |
| **VSI-Bench** relative direction easy, medium, hard; **ReVSI** forward easy and hard | Direct. Locate lines, the relation in sector words, the facing-clause Step (2.3) | Direct | Program -10.0 to -27.3; no gain with ground-truth masks |
| **ReVSI** backward easy and hard | Direct, as the away twin of a toward row (2.3) | Direct | Step 544 leaves 74 of 150 away answers equal to the forward answer (`evalx/work/milestone/reports/step544_e193c2a3c/SUMMARY.md:33`) |
| **VSI-Bench**, **ReVSI** route planning | Direct. One Step per waypoint: current position and heading, where the next waypoint lies, the turn. Then the turn list | Direct | Parent traces omit waypoints on 52 of 63 items (`TRACE_DIAG.md:15,115`); the fix class named there is one state update per waypoint |
| **VSI-Bench** appearance order | Direct, unchanged: first-seen frame per object, then the order | Direct | Passed review |
| **VSTI** camera displacement, camera movement direction; camera rotation | Program, unchanged: `<move>` or `<turn>`, the printed value, the option mapping. Ground-truth responses stay for this seal | Route | Native tower calls score 83.9 and 98.0 (`NEXT_QUEUE_20261115.md`, section 1.3); the call needs no mask, so the only train-to-inference gap is pose noise |
| **VSTI** camera-object absolute distance | Direct. Locate line; the number is the answer only. No row exists yet; the coverage lane should supply some, because the wording resembles a routed type | Direct | Direct beats the ground-truth program on this type (`toolprog-results-20261107.md:22`) |
| **VSTI** camera-object relative distance v1 to v3; object-object left/right, near/far, up/down | Direct. Locate lines and one Relate line. No row exists yet | Direct | Direct cells are 82 to 96 (`NEXT_QUEUE_20261115.md`, section 1.3) |
| 3D box (auxiliary) | One Locate line (frame and image region), then the JSON. Or leave the family out; see 2.9 | Direct | Its nine metric numbers are the answer, like a pointing target |

Per step, this changes the form of 121.5 of the sealed leg's 192 language rows (95.0 stated-measurement, 15.3 empty, 11.1 counting), re-renders 13.8 (distance and room) from deployed responses, and leaves 56.7 as they are (camera 39.7, appearance order 17.0). Quotas for the new pairs and families belong to the integration and coverage lanes.

Types with no benchmark weight (relative count, relative size, absolute direction) take the direct form if a lane supplies rows: two instance lists and a comparison for relative count, two Locate lines and a Relate line for relative size, and Locate lines with the angle as the answer only for absolute direction.

### Proposed renderings

Each rewrites a sampled sealed row using only values the row already holds (Appendix A). They show the form; the builder owns the wording and a paraphrase bank.

```text
Direction easy, toward (row qe70d0c1..., stated "41 degrees right ... in front")
<think>
Step 1: find the sink, the sofa and the stove.
Step 2: standing at the sink and facing the sofa, the stove is ahead of me to the right.
The question has me face the sofa, so no turn applies.
So the stove is to the right.
</think>

A

Relative distance (row q1381e0e..., stated "bag 2.23 m; pillow 0.64 m; badge 3.15 m; bed 1.25 m")
<think>
Step 1: the backpack is first seen in frame 9.
Step 2: order the candidates from nearest to the backpack: pillow, bed, bag, badge.
The question asks for the closest: the pillow.
</think>

B

Object size (row q6d75862..., stated "the longest edge is 101 cm")
<think>
Step 1: the kitchen counter is first seen in frame 11.
Step 2: the question asks for the longest of its three dimensions, in centimeters. I estimate that edge from the frames.
</think>

101

Counting (row q4c257aa..., three instances first seen in frames 1, 9, 15)
<think>
Step 1: list each distinct notebook once, by the frame where it first appears: frame 1; frame 9; frame 15.
So there are 3 notebooks.
</think>

3

Route planning (row q71b11cb..., answer "Turn Left, Turn Left")
<think>
Step 1: I stand at the toilet facing the shower curtain. The bathroom vanity is to my left: turn left.
Step 2: I go forward to the bathroom vanity and keep that heading. The tissue box is to my left: turn left.
The turns are: left, left.
</think>

B

Absolute distance after a failed call (row vsi590k_162632; the status line is the runtime's own text)
<think>
I will ground the boxes and ask the tool to measure their box distance.
<ground obj="ceiling lamp" mode="box">
<tool_response>
ceiling lamp: not seen
</tool_response>
The tool did not find the ceiling lamp, so it gives no measurement and I do not call it again. I answer from the frames: the ceiling lamp is seen in frame 16 and the heater in frame 13.
</think>
<answer>2.55</answer>
```

For a direct numeric type the trace is short by design: the measurement cannot appear before the answer. The only honest way to lengthen it is a tool, and object size loses 7.6 points routed.

## 2.3 Facing-direction rows without tools

The defect: the model answers the away question as if it faced the object. Step 544 gives the forward answer on 74 of 150 away twins, and the parent's ReVSI backward leaves score 15.4 and 0.0 (`TRACE_DIAG.md:66-68`). The sealed leg held no away row at all.

The rows are direct pairs. A pair shares its scene, objects, frames and option order; the two rows differ in the facing clause and the answer.

1. **Locate.** One line: each of the three objects with its best-view frame (the builder's source prints it as `(best k)`).
2. **Forward relation, in words.** Where the query object lies when I stand at S and face F. The away row words it as a condition ("If I faced ..., it would be ..."); the toward row words it as a fact. The wording carries exactly what the level needs:
   - easy: the side (left or right);
   - hard: front or behind, and the side;
   - medium: one of three bands and the side: "ahead of me, slightly to the left" (within 45 degrees of straight ahead), "out to my left" (45 to 135), "behind me, on my left" (135 or more). The trace uses the words, never the angle.
3. **The facing clause.** Toward: "The question has me face F, so no turn applies." Away: "The question has me face away from F. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap."
4. **Conclusion.** The relation after the turn, mapped to the option. For medium: ahead becomes back; out to one side becomes the other side; behind on one side becomes the other side.

```text
Away twin (rs_facing_1f6148d3...: forward bearing -22 degrees, answer C. back)
<think>
Seen: toilet in frame 27; keyboard in frame 6; sofa in frame 16.
If I stood at the toilet facing the keyboard, the sofa would be ahead of me, slightly to my right.
The question has me face away from the keyboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So the sofa is at my back.
</think>

C

Toward twin of the same question (answer: right)
<think>
Seen: toilet in frame 27; keyboard in frame 6; sofa in frame 16.
Standing at the toilet facing the keyboard, the sofa is ahead of me, slightly to my right.
The question has me face the keyboard, so no turn applies.
So the sofa is to my right.
</think>
```

Why this form. The half turn is an explicit computation on a stated relation, so the trace needs no coordinate. It reverses per item and not by a blanket flip, which would break two correct answers (`TRACE_DIAG.md:147`). Medium cannot be reversed by swapping strings (`back_dir/out/r2/DESIGN_RECORD.md:7`); the three bands make its reversal exact, because the 45 and 135 boundaries map onto each other under a half turn. The twelve transitions in `rs_rows/out/FLIP_STRATA.json` are exactly the ones this rule produces. Because both twins share lines 1 and 2, the only token that predicts the answer change is the clause.

Requirements on the rows: labels recomputed from the same geometry as now; both twins or neither; the existing 5-degree and 10-degree margins applied at every boundary the row's words depend on (0, 45, 90, 135, 180 as the level requires); band words derived from the stored forward bearing; no digit in the trace other than frame indices.

One prior to watch: 85.5% of away-hard answers are a "back" quadrant and 43% of away-medium answers are "back" (`rs_rows/out/rows/facing/MANIFEST.json`, `strata`). The paired read in 2.7 separates the half turn from that prior.

## 2.4 Changes for the builder lane

| Family | Keep | Change |
|---|---|---|
| **facing** (67,970) | Pairs, geometry recompute, margins, exclusions, `FLIP_STRATA.json` | Render as direct rows per 2.3. Take out every call, response, coordinate and the cross, dot and atan2 lines. The sealed calculator already has an `<angle ... rule=easy\|medium\|hard>` call (`tree_s1/trace_format/calculator.py:32`), so even a program rendering would not compute atan2 in text. Hold the program rendering as an unadmitted kit for the experiment in 2.6 |
| **totals** (2,335) | Disjoint identity checks, one scalar answer | Render as direct rows: per category the instance list with first-seen frame (the source prints `first k`) and an image region where a mask supplies it, then the explicit sum. No `<ground mode="instances">` call |
| **units** (24,628) | Program form, metric response, metric twin for every quantity, round-trip tests | (a) Deliver as ground-form event rows (`ground_trace_start`, `canonical_text`, `ground_call`, `ground_response`) so the sealed encoder masks responses and enforces the `<answer>` ending; a flat target would supervise response text. (b) Re-render responses from the deployed pipeline when the cache of 2.6 exists, and keep only rows that pass the filter there. (c) Report the text-arithmetic error of the conversion line at the first read; multiplication by 100 erred on at most 1.5% of items in earlier models (`toolprog-results-20261107.md:21`), multiplication by 3.28084 or 39.3701 is unmeasured, and the calculator has no conversion call (`calculator.py:28-35`) |
| **recovery** (4,670) | The finite-trace and no-repeat tests; the runtime's own response formatter | Rebuild. (a) Put failures in routed types (absolute distance, room, camera), at the call the question really makes. (b) Use real statuses from the deployed pipeline on training scenes; until that cache exists, simulate a miss by withholding an operand's masks so the runtime prints its own status (the pool schema already has `simulated_misses`), at the measured rate of 14 to 19% of distance rows. (c) End every row in a direct answer with Locate lines. No row refuses: a refusal scores zero on every benchmark, and the runtime's own text says "answer directly from the video". (d) Leave out operator faults ("Routed policy requires a fixed named candidate universe", `form_requires_v3.13`, `frozen_fusion_requires_depth_cut_receipt`, `mask_source_unavailable_for_type`): a correct deployment never prints them, and a model that absorbs them hides a broken kit. (e) No call after a failed ground except one retry with a different operand name that the candidate list holds |

Two tests to add to the builder's proof: a direct row that contains `<tool_response>` must fail, and a trace that contains a number outside the allowed set of 2.1 must fail.

The integration lane needs the matching change. Its direct contract must refuse a call tag or a `<tool_response>` in a direct target, and program rows must enter through the event path whose response spans are masked (`tree_s1/student_pilot/carrier_c1_routing.py:467-468`). Today it does the reverse (1a).

## 2.5 Options argued

**O1, allowlist with qualitative direct rows: adopted for the forms.** It satisfies the user's rule on every row, keeps every type on the side of the route table that wins, and needs no GPU: each direct trace is a deterministic rewrite of a row that already holds the needed values, as the user allowed. Its weakness is that no record compares a qualitative trace with a stated-number trace on this model. The direction rows that state an angle score 79 to 91, and route planning gained 42 points with an empty think block (`NEXT_QUEUE_20261115.md`, section 1.5). The rule forbids both forms, so the test in 2.7 guards the change.

**O2, more program types as built: rejected for this seal.** For direction and counting not to lose 8 to 28 points, four things would have to hold together.

1. A failed call falls back to a direct answer. That alone moves easy from 70.7 to 84.0, medium from 61.3 to 82.7, hard from 68.7 to 82.7 and relative distance from 44.0 to 62.7. Counting does not move (44.9).
2. On the items the program answers, it is at least as accurate as direct. Today it is 83.5 against 92.1 (easy), 80.0 against 87.8 (medium), 61.7 against 74.8 (relative distance) and 44.8 against 58.5 (counting). Only hard meets it, 88.0 against 82.9. The gap is wrong accepts. The report's bar for a visual verifier is to fix at least half of them and break at most 5%; the existing CPU features fix 1 to 3 of 30 (`NEXT_QUEUE_20261115.md`, section 1.6, row 1). Better masks alone are not enough for direction (1c, cause 3).
3. Training responses show the failures and noise of deployment. The builder's are ground truth.
4. Angles come from the calculator call, not text atan2.

None of 2 to 4 holds now. And O2 is what the seal would train as integrated today: the integration tree supervises the calls and the responses of these rows as plain text (1a). At inference a served call then returns deployed responses, with the measured loss; an unserved call either ends the read or leaves the model to write the response itself, which is a coordinate nobody saw.

**O3, train on deployed responses: adopted for absolute distance and room; an experiment elsewhere.** For the routed object types it repairs two measured defects at once: the model has never seen a failed call, and the fallback is worth 7.6 points in scripted form (46.9 to 54.5). For the other types its ceiling is real but small and unproven: a perfect per-item choice between program and direct would add 4.0 (easy), 6.0 (medium), 10.7 (hard), 6.7 (relative distance) and 12.7 (counting) to direct. The visible cue reaches only part of that. Status text is a cue; whether frame counts or spread separate right from wrong answers is not measured in any record I read. Price in 2.6.

**O4, a prompt flag: rejected.** The flag tree works mechanically (`leg_s2_tree/REVIEW_VERDICT.md:4,11`), but it solves a problem this model does not have and creates three.
- The model already picks the form by type with no flag.
- Someone must set the flag at inference. That is an external router, which the user ruled out (`no-harness-end-to-end.md:8`).
- The flag mix cuts unflagged routed-default programs from 53.47 to 11.58 rows per step and all unflagged language rows from 192 to 72.8 (`REVIEW_VERDICT.md:19`).
- As built it admits programs of every type, including the ones the route table keeps out (`REVIEW_VERDICT.md:18`), and its direct rows are empty.

A flag stays useful only as a measurement device for forced-path reads.

**O5, counting by tool list plus reconcile (my addition): an experiment.** The deployed instance list is the starting point; the trace adds instances the list missed (each with a Locate line) and merges duplicates, then sums. Ground truth on training scenes supplies the corrections, the responses are real, and the two largest counting losses (never proposed, identity residual) are exactly what the corrections address. It is worth a census before any build: if the median deployed list needs more than two edits to match ground truth, the form is as hard as direct counting.

## 2.6 O3 priced

**Caches that exist.** None covers training scenes.

| Lane | What it holds | Usable for training rows |
|---|---|---|
| `devs1_masks` | SAM 3 candidates, selected masks and priced programs for 152 dev-S1 captures, 6,161 questions (`devs1_masks/out/DESIGN_RECORD.md:15`; `cache_r1/predicted_price/PER_ITEM.jsonl`) | No: dev-S1 is the test set |
| `mask_recall` | The same 152 captures with denser variants and ground-truth grants (`mask_recall/out/NEVER_PROPOSED.md:1`) | No |
| `grd_selector` | Candidates for 84 selector-training scans (785 names) and for VSI-Bench scenes (486 names) (`grd_selector/out/RUN_CARD_DENSE.md:55-57`) | The 84 scans are disjoint from dev-S1 (`devs1_masks/out/DESIGN_RECORD.md:19`) and suit a cue study; whether they are training scenes of the leg is not recorded. The VSI-Bench cache can never train |
| `own_ground` | Two sealed kits; "No GPU inference ran here" (`own_ground/out/STATUS.md:1`) | No |
| `dose_pool` | Ground-truth rows only (1b) | No |

**GPU passes for absolute distance and room** (2,189 scenes, the builder's unit family; estimates on A6000-class cards):

| Pass | Basis | Estimate |
|---|---|---:|
| Geometry: G3T tower plus own-head export, per capture | about 24.6 s per capture (`devs1_tower/out/DEVS1_TOWER.md:12`, an estimate there) | 15 GPU-h |
| SAM 3 proposals, per (capture, object name) | 1.9 to 2.1 s per call measured at default density (`devs1_masks/out/RUNCARD.md:59`); 6,790 unique operands counted on 8,926 of 11,728 distance rows (`work/pool_sources.txt`), so about 8,900 in all (guess) | 4.5 to 5.2 GPU-h |
| The same at the frozen `dense_aliases` setting | twice the calls, 1.2 to 1.6 times per call (`grd_selector/out/RUN_CARD_DENSE.md:57`); alias prompts may add calls | 11 to 17 GPU-h |
| Total | | 20 to 32 GPU-h; 2.5 to 4 hours on eight cards |

It also needs about 70,000 PNGs (20 GB at the dev-S1 size of 290 KB each) on the GPU node, and CPU selection and rendering whose duration is unmeasured. Where those frames sit on Trinity is not in the records I read, so staging is a heavy-IO question for the user.

**Rows that survive the filter.** A row is a trust row when the deployed answer is within 15% of ground truth (exact for counts and options) and the accepted masks match the ground-truth instance; its answer is the printed value. It is a fallback row when the response is a failure status. Other rows are left out. Rates are from all dev-S1 priced items at default density (`work/peritem_stats.txt`); applying them to training scenes is a guess.

| Type | Pool rows | Failure status | Consistent | Silent wrong (left out) | Estimated rows kept |
|---|---:|---:|---:|---:|---:|
| Absolute distance | 11,728 | 13.7% | 44.9% | 41.5% | 6,860 |
| Room size | 581 | 0% | 50.0% (36 items) | 50.0% | 290 |
| Direction easy | 14,630 | 19.0% | 69.9% | 11.1% | 13,000 |
| Direction medium | 14,082 | 19.8% | 66.2% | 14.0% | 12,100 |
| Direction hard | 8,788 | 19.5% | 66.4% | 14.0% | 7,560 |
| Relative distance | 19,339 | 34.5% | 41.5% | 23.9% | 14,700 |
| Counting | 3,099 | 1.9% | 34.0% | 64.1% | 1,110 |

The sealed leg drew 13.1 distance rows per step, so 6,860 rows last about 520 steps before repeating; each row's unit twin doubles that. Room is scarce either way. The mask-match requirement will lower the consistent share by an amount no record gives.

**The smallest experiment before a full leg**, in three stages with a stop after each:

1. **Cue study, CPU only.** On the 84-scan cache, test whether anything printed in a response (status, number of frames, spread, missing size) separates right from wrong program answers. If nothing beyond the status does (AUROC below 0.65), O3 equals "fall back on a status", whose value column 5 of the 1c table already gives.
2. **One direct read, no training** (about 975 generations; my guess is 1 to 2 GPU-h). Read step 544 directly on every dev-S1 item of hard direction (769) and counting (206). The scripted program arm already exists for all 6,161 items, so this yields the paired difference "program with fallback minus direct" on five times the present denominator for hard direction. A type proceeds only if its room-bootstrap interval is above zero. Today's 150 items give hard direction +4.0, too few to decide. Absolute distance needs no such read: step 544 calls the tool on that type, and it is already routed.
3. **A 100-step branch, about 15 H100-h plus 3 to 6 GPU-h of cache**, only for a type that passes stage 2. Render that type's rows from deployed responses on about 300 training captures, branch from the seal's first export, replace the type's direct rows, and read natively on dev-S1 with tools served. It passes if the native score is within 5 points of the scripted arm and above the direct arm with the interval above zero, the model falls back on at least 90% of failed responses, and it repeats no call. Step time is 131 s on four GPUs (`CONTINUATION_FACTS_20261114.md:24`).

## 2.7 The test on dev-S1 that would falsify this ruling

Arms: A is the accepted step-544 export; B is the repair seal at steps 100 and 200. Same reader, same items, paired differences with the 10,000-draw room bootstrap of the route table. Direct types use the direct reader at the frozen budget; routed types use the native routed read with deployed tools (150 distance, 36 room, 450 camera items).

The ruling is wrong, in the part named, if any of these holds at step 200:

| Test | Falsifies | Condition |
|---|---|---|
| F1 | Qualitative direct traces (O1) | For route planning, counting, direction easy, medium or hard, relative distance or object size, B minus A has its 95% interval wholly below zero |
| F2 | The facing fix without tools (2.3) | On the 150 toward/away twins: away accuracy at any level has an interval that does not clear the constants 54, 40 and 36 (`back_dir/out/r2/DESIGN_RECORD.md:19`); or more than 20% of pairs give the same answer to both twins (step 544: 49%; a correct model: 0%); or toward accuracy falls with its interval below zero |
| F3 | Deployed responses and fallback on routed types | On distance items the scripted program answers, the native score is more than 5 points below the scripted score on the same geometry; or, on items where a call fails, fewer than 95% end in a parsed numeric answer; or the call rate is below 95%; or a call is repeated after a failed response on more than 2% of items; or any final answer is a refusal |
| F4 | The allowlist itself | On the full dev-S1 denominator of a direct type, the scripted program with fallback beats B's direct answers with the interval above zero. That type then takes the O3 form in the following seal |

Guards against answer priors: totals must beat the train-fitted constant 7 (46.30% on the kit's set, `rs_rows/out/ROWS_REPORT.md:30`) and single counts must not fall against the constant 2 (61.87).

## 2.8 What might not work, and how we would notice

| Risk | Sign | Response |
|---|---|---|
| A qualitative trace carries less than the stated number did, and direct accuracy falls | F1 on that type | Change that type's template; the stated-number form stays out |
| Route planning loses its gain once the think block is non-empty | F1 on route planning; turn-position errors rise | Fall back to the shortest non-empty form: the Step lines without positions, then the turn list |
| The away rows teach "away means back" instead of the half turn | F2 by level and by the twelve transitions in `FLIP_STRATA.json` | Rebalance pairs by forward band |
| The model writes frames it did not see | Share of cited frames in which ground truth shows the object, on the 93 dev-S1 captures with ground truth | Restrict Locate lines to first-seen frames above the size floor |
| Fallback rows teach the model to skip calls | Call rate below 95% in F3 | Lower the fallback share to the measured failure rate |
| The deployed cache is late | No cache at seal time | Launch with ground-truth trust rows and simulated-miss fallback rows, record that in the run identity, and switch at an epoch boundary |
| Trust rows are too few for room | Fewer than about 300 rows after the filter | More room scenes from the coverage lane; do not loosen the tolerance |
| The conversion line is wrong in text | Conversion error above 2% at the first read | Move the conversion into the response or a calculator call |
| The model's heads drift from the checkpoint that rendered the responses | Scripted and native scores diverge in F3 | Re-render at the next epoch boundary |
| The seal also trains a grounding head, so the pipeline behind a call changes inside the leg (`NEXT_QUEUE_20261115.md`, section 3.3, brief B6) | Scripted and native scores diverge as the head trains | Render the cache with the pipeline fixed at seal time. Once the head passes its gate, use the code's own-value path, which trains no text after an own-value response (`tree_s1/student_pilot/carrier_c1_routing.py:444`) |
| The model calls a tool on a direct type that has no row (camera-object absolute distance) | Call records on that type in any read | Supply direct rows for the type; never widen the route table from a benchmark read |

## 2.9 Open points and defaults

Known and not known:

- **Not measured:** a qualitative trace against a stated-number trace on this model; the deployed pipeline on any training scene; whether printed frame counts or spread predict a wrong response; pointing quality of the current checkpoint (`own_ground/out/FEASIBILITY.md`, row "Held-out pointing quality"); text-arithmetic error for unit factors; ReVSI's unit mix.
- **Measured on 150 items only:** every "program with fallback" number. Hard direction's +4.0 may be noise.
- **Moving target:** the builder regenerated its rows and samples while I read them (05:08Z and 05:20Z). Counts and forms above match the 05:20Z files.

Two points are the user's to rule. Each has a default that the build can proceed on.

1. **May a direct trace cite one frame per object taken from ground-truth visibility?** Default: yes, one first-seen or best-view frame per object, never an exhaustive list. If no, direct traces carry Relate and Step lines only, and counting rows list instances without frames.
2. **Is a 3D-box row perception supervision, like pointing, or a question-answer row under the trace rule?** Default: keep it with one Locate line before the JSON. The alternative is to leave the family out of the seal (4.8 rows per step).

## 2.10 Tests that would settle the open points

| Open point | Test | Cost |
|---|---|---|
| Does the form change cost accuracy? | F1 at steps 100 and 200 | Inside the seal's registered reads |
| Is the facing defect fixed without tools? | F2 | Same |
| Should hard direction or counting route? | Stages 1 and 2 of 2.6, then F4 | CPU, then 1 to 2 GPU-h |
| Does a response reveal its own unreliability? | Stage 1 of 2.6 | CPU |
| Would counting gain from tool plus reconcile? | Census of edits between the deployed instance list and ground truth on the 84-scan cache | CPU |
| Can traces cite points instead of regions? | Kit B of `own_ground` (parse rate and in-mask rate of the checkpoint's pointing) | One GPU pass, already built |

## Status

Proposed. No tree, row file or run was changed. The builder lane has not been told; the orchestrator relays section 2.4 if it accepts the ruling. Evidence was read between 05:13Z and 05:45Z on 2026-11-15; `NEXT_QUEUE_20261115.md` and the builder's files changed during that time, and the citations match their 05:31Z and 05:20Z states.

---

# Appendix A: three rows per family consumed by the sealed leg

Source: `leg_s1_tree/out/ROWS_FIVE_PER_TYPE_07ca49df.md` (70 real admitted rows, seed 20261113, read through the sealed tree's own renderer; line 11 of that file). Each sample cites the lines of its full target text. The first row of a program family is complete; rows 2 and 3 show each call, the first and last line of its response, and the closing line.

**vqa / `object_rel_direction_easy`**

```text
[1] lines 45-51
Q: If I am standing by the sink and facing the sofa, is the stove to the left or the right of the sofa?  (A. right | B. left)
think:
  Step 1: locate the centres of the sink, the sofa and the stove.
  Step 2: standing at the sink and facing the sofa, the stove lies 41 degrees right of straight ahead, in front.
  So the stove is to the right.
A: A

[2] lines 86-92
Q: If I am standing by the fireplace and facing the shelf, is the tv to the left or the right of the shelf?  (A. right | B. left)
think:
  Step 1: locate the centres of the fireplace, the shelf and the tv.
  Step 2: standing at the fireplace and facing the shelf, the tv lies 61 degrees left of straight ahead, in front.
  So the tv is to the left.
A: B

[3] lines 127-133
Q: If I am standing by the refrigerator and facing the table, is the oven to the left or the right of the table?  (A. left | B. right)
think:
  Step 1: locate the centres of the refrigerator, the table and the oven.
  Step 2: standing at the refrigerator and facing the table, the oven lies 92 degrees left of straight ahead, behind.
  So the oven is to the left.
A: A
```

**vqa / `object_rel_direction_medium`**

```text
[1] lines 471-477
Q: If I am standing beside the cabinet and facing the chair, which direction describes the tv relative to me: left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.  (A. left | B. back | C. right)
think:
  Step 1: locate the centres of the cabinet, the chair and the tv.
  Step 2: standing at the cabinet and facing the chair, the tv lies 106 degrees left of straight ahead, a turn of less than 135 degrees.
  So the tv is on my left.
A: A

[2] lines 514-520
Q: If I am standing by the bathtub and facing the toilet, is the cabinet to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it.  (A. back | B. left | C. right)
think:
  Step 1: locate the centres of the bathtub, the toilet and the cabinet.
  Step 2: standing at the bathtub and facing the toilet, the cabinet lies 22 degrees left of straight ahead, a turn of less than 135 degrees.
  So the cabinet is on my left.
A: B

[3] lines 556-562
Q: From my place by the plant, facing the sofa, is the backpack on my left side, right side, or behind? 'Behind' indicates needing to rotate at least 135 degrees.  (A. right | B. back | C. left)
think:
  Step 1: locate the centres of the plant, the sofa and the backpack.
  Step 2: standing at the plant and facing the sofa, the backpack lies 41 degrees left of straight ahead, a turn of less than 135 degrees.
  So the backpack is on my left.
A: C
```

**vqa / `object_rel_direction_hard`**

```text
[1] lines 252-258
Q: When standing at the door and oriented toward the counter, where does the microwave appear: front-left, front-right, back-left, or back-right?  (A. front-left | B. front-right | C. back-left | D. back-right)
think:
  Step 1: locate the centres of the door, the counter and the microwave.
  Step 2: standing at the door and facing the counter, the microwave lies 48 degrees right of straight ahead, in front.
  So the microwave is at my front-right.
A: B

[2] lines 296-302
Q: With the bed ahead of me as I stand by the nightstand, which direction describes the picture: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the o [...]  (A. back-right | B. front-right | C. back-left | D. front-left)
think:
  Step 1: locate the centres of the nightstand, the bed and the picture.
  Step 2: standing at the nightstand and facing the bed, the picture lies 41 degrees right of straight ahead, in front.
  So the picture is at my front-right.
A: B

[3] lines 340-346
Q: With the projector screen ahead of me as I stand by the table, which direction describes the cabinet: front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing [...]  (A. front-left | B. back-left | C. front-right | D. back-right)
think:
  Step 1: locate the centres of the table, the projector screen and the cabinet.
  Step 2: standing at the table and facing the projector screen, the cabinet lies 112 degrees right of straight ahead, behind.
  So the cabinet is at my back-right.
A: D
```

**vqa / `object_rel_distance`**

```text
[1] lines 685-691
Q: Measuring from the closest point of each object, which of these objects (badge, bag, bed, pillow) is the closest to the backpack?  (A. bag | B. pillow | C. badge | D. bed)
think:
  Step 1: find the backpack (first seen in frame 9) and each candidate.
  Step 2: measure the closest-point distance from the backpack to each: bag 2.23 m; pillow 0.64 m; badge 3.15 m; bed 1.25 m.
  The closest is the pillow.
A: B

[2] lines 728-734
Q: From the closest point of each object, determine which among (stove, dishwasher, tv, sofa) is nearest the fireplace. If multiple exist, use the nearest instance.  (A. dishwasher | B. tv | C. sofa | D. stove)
think:
  Step 1: find the fireplace (first seen in frame 8) and each candidate.
  Step 2: measure the closest-point distance from the fireplace to each: dishwasher 2.75 m; tv 0.61 m; sofa 0.16 m; stove 1.36 m.
  The closest is the sofa.
A: C

[3] lines 771-777
Q: Measuring from the closest point of each object, which of these objects (chair, plant, radiator, table) is the closest to the kitchen cabinets?  (A. plant | B. chair | C. radiator | D. table)
think:
  Step 1: find the kitchen cabinets (first seen in frame 6) and each candidate.
  Step 2: measure the closest-point distance from the kitchen cabinets to each: plant 2.12 m; chair 1.23 m; radiator 2.45 m; table 1.73 m.
  The closest is the chair.
A: B
```

**vqa / `object_size_estimation`**

```text
[1] lines 897-902
Q: Measure the kitchen counter along its longest dimension and give that length in centimeters.
think:
  Step 1: find the kitchen counter (first seen in frame 11).
  Step 2: measure its 3D box; the longest edge is 101 cm.
A: 101

[2] lines 936-941
Q: Of the length, width, and height of the cable raceway, what is the largest measurement in centimeters?
think:
  Step 1: find the cable raceway (first seen in frame 7).
  Step 2: measure its 3D box; the longest edge is 201 cm.
A: 201

[3] lines 975-980
Q: What is the length of the longest edge of the baby bassinet, in centimeters?
think:
  Step 1: find the baby bassinet (first seen in frame 5).
  Step 2: measure its 3D box; the longest edge is 85 cm.
A: 85
```

**vqa / `object_counting`**

```text
[1] lines 1511-1517
Q: Based on the video, give the number of notebook(s) in this room.
think:
  Step 1: find the frames that show a notebook: frame 1, frame 3, frame 5, frame 7, frame 9, frame 15, frame 21, frame 23, frame 25, frame 27, frame 31.
  Step 2: match the notebook detections across those frames into distinct instances: 3, first seen in frame 1, frame 9, frame 15.
  So there are 3 notebook.
A: 3

[2] lines 1551-1557
Q: How many curtain(s) do we have in this room?
think:
  Step 1: find the frames that show a curtain: frame 1, frame 5, frame 7, frame 9, frame 11, frame 13, frame 15, frame 17, frame 21, frame 23, frame 29, frame 31.
  Step 2: match the curtain detections across those frames into distinct instances: 5, first seen in frame 1, frame 1, frame 1, frame 5, frame 13.
  So there are 5 curtain.
A: 5

[3] lines 1591-1597
Q: How many vase(s) do we have in this room?
think:
  Step 1: find the frames that show a vase: frame 1, frame 3, frame 9, frame 15, frame 25, frame 27, frame 29.
  Step 2: match the vase detections across those frames into distinct instances: 2, first seen in frame 1, frame 3.
  So there are 2 vase.
A: 2
```

**vqa / `obj_appearance_order`**

```text
[1] lines 1304-1309
Q: What will be the first-time appearance order of the following categories in the video: backpack, bookshelf, clock, trash bag?
think:
  Step 1: find the first frame showing each object: backpack frame 13; bookshelf frame 11; clock frame 8; trash bag frame 2.
  Step 2: order them by first appearance: trash bag, clock, bookshelf, backpack.
A: C

[2] lines 1346-1351
Q: In what order do these object categories first appear in the video: cloth, coffee machine, dustpan, paper bag?
think:
  Step 1: find the first frame showing each object: cloth frame 23; coffee machine frame 5; dustpan frame 1; paper bag frame 19.
  Step 2: order them by first appearance: dustpan, coffee machine, paper bag, cloth.
A: B

[3] lines 1388-1393
Q: In what order do these object categories first appear in the video: backpack, dining table, door, stair rail?
think:
  Step 1: find the first frame showing each object: backpack frame 8; dining table frame 1; door frame 4; stair rail frame 6.
  Step 2: order them by first appearance: dining table, door, stair rail, backpack.
A: D
```

**vqa / `box_3d`**

```text
[1] lines 1093-1099
Q: Detect the bedside lamp in frame 21 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
think: (empty)
A: ```json [{"bbox_3d":[-0.55, -0.39, 1.26, 0.23, 0.38, 0.18, 0.67, 0.20, 0.78],"label":"bedside lamp"}] ```

[2] lines 1134-1140
Q: Detect the couch in frame 16 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
think: (empty)
A: ```json [{"bbox_3d":[-0.64, -0.96, 3.58, 0.82, 1.07, 2.37, 0.81, 0.22, 0.85],"label":"couch"}] ```

[3] lines 1175-1181
Q: Detect the cabinet in frame 16 and predict the 3D box in the camera coordinates of that frame. Output JSON: [{"bbox_3d":[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw],"label":"category"}].
think: (empty)
A: ```json [{"bbox_3d":[0.64, 0.60, 3.13, 0.57, 0.79, 1.37, 0.24, 0.43, 0.25],"label":"cabinet"}] ```
```

**routing / `route_planning`**

```text
[1] lines 2231-2235
Q: You are a robot beginning at the toilet facing the shower curtain. You want to navigate to the tissue box. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn r [...]  (A. Turn Back, Turn Right | B. Turn Left, Turn Left | C. Turn Right, Turn Left | D. Turn Right, Turn Right)
think: (empty)
A: B

[2] lines 2272-2276
Q: You are a robot beginning at the copier facing the light switch. You want to navigate to the file cabinet. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' or 'turn r [...]
think: (empty)
A: C

[3] lines 2312-2316
Q: You are a robot beginning at the shower curtain facing the toilet paper holder. You want to navigate to the bathtub. You will perform the following actions (Note: for each [please fill in], choose either 'turn back,' 'turn left,' [...]  (A. Turn Back | B. Turn Right | C. Turn Left)
think: (empty)
A: B
```

**routing / `object_abs_distance`**

```text
[1] lines 1713-1736
Q: Measuring from the closest point of each object, what is the distance between the ceiling lamp and the heater (in meters)?
think:
  I will ground the boxes and ask the tool to measure their box distance.
  <ground obj="ceiling lamp" mode="box">
  <tool_response>
  ceiling lamp: frames 5,12,16,17,32 (best 16)
  B1: f1 centre (1.44, 1.10, 0.80) m
  size 0.43 x 0.43 x 0.04 m
  yaw 64 deg (0 = +x; positive +x toward -z about +y)
  </tool_response>
  <ground obj="heater" mode="box">
  <tool_response>
  heater: frames 4,5,8,10,11,13,22 (best 13)
  B2: f1 centre (3.37, -1.08, 1.74) m
  size 0.90 x 0.25 x 0.75 m
  yaw 64 deg (0 = +x; positive +x toward -z about +y)
  </tool_response>
  <gap a="ceiling lamp" b="heater" rule="box_grid_5cm">
  <tool_response>
  distance 2.55 m
  </tool_response>
  The box gap is the smallest distance between points on a 5 cm grid over the two objects' full boxes, taken over every pair of instances.
  The box distance is 2.55 m.
A: <answer>2.55</answer>

[2] lines 1770-1793
Q: Measuring from the closest point of each object, what is the distance between the cup and the bed (in meters)?
think: <ground obj="cup" mode="box"> -> cup: frames 21,26 (best 21) ... yaw 65 deg (0 = +x; positive +x toward -z about +y) / <ground obj="bed" mode="box"> -> bed: frames 2,4,5,6,7,8,9,10,11,12,28,31 (best 11) ... yaw 6 deg (0 = +x; positive +x toward -z about +y) / <gap a="cup" b="bed" rule="box_grid_5cm"> -> distance 2.06 m / closing: The box distance is 2.06 m.
A: <answer>2.06</answer>

[3] lines 1827-1850
Q: Measuring from the closest point of each object, what is the distance between the kitchen counter and the bookshelf (in meters)?
think: <ground obj="kitchen counter" mode="box"> -> kitchen counter: frames 14,15,16,19,20,21,22,23,24,25,26,28,29 (best 21) ... yaw -138 deg (0 = +x; positive +x toward -z about +y) / <ground obj="bookshelf" mode="box"> -> bookshelf: frames 5,7,8,9,10,11,12,21,29 (best 12) ... yaw -138 deg (0 = +x; positive +x toward -z about +y) / <gap a="kitchen counter" b="bookshelf" rule="box_grid_5cm"> -> distance 1.59 m / closing: The box distance is 1.59 m.
A: <answer>1.59</answer>
```

**routing / `room_size_estimation`**

```text
[1] lines 1999-2010
Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
think:
  I will project the depth points onto the floor and measure their covered area.
  <ground mode="room">
  <tool_response>
  room: frames 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
  floor height -0.08 m
  floor cells 7378; supported cells 5658; cell size 0.05 m; min frames 1
  area 18.45 m^2
  </tool_response>
  The covered floor area is 18.45 square meters.
A: <answer>18.45</answer>

[2] lines 2045-2056
Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
think: <ground mode="room"> -> room: frames 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32 ... area 19.44 m^2 / closing: The covered floor area is 19.44 square meters.
A: <answer>19.44</answer>

[3] lines 2091-2102
Q: What is the size of this room (in square meters)? If multiple rooms are shown, estimate the size of the combined space.
think: <ground mode="room"> -> room: frames 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32 ... area 12.18 m^2 / closing: The covered floor area is 12.18 square meters.
A: <answer>12.18</answer>
```

**routing / `camera_displacement`**

```text
[1] lines 2429-2437
Q: Approximately how far (in meters) did the camera move between frame 1 and frame 25 of 32?
think:
  Okay, I need to measure how the camera moved between frame 1 and frame 25. The pose head with the scale head gives the metric camera motion, which the move tool prints in the starting frame's level coordinates.
  
  The move tool gives the camera displacement from frame 1 to frame 25 in frame 1's level frame (x right, y up, z forward). <move from=1 to=25><tool_response>dx = -0.21 m, dy = +0.28 m, dz = -0.07 m, distance = 0.35 m</tool_response>
  
  The printed distance is 0.35 m, so the camera moved about 0.35 m.
A: 0.35

[2] lines 2470-2478
Q: Approximately how far (in meters) did the camera move between frame 6 and frame 9 of 32?
think: <move from=6 to=9> -> dx = +0.80 m, dy = +0.06 m, dz = -0.84 m, distance = 1.16 m / closing: The printed distance is 1.16 m, so the camera moved about 1.16 m.
A: 1.16

[3] lines 2511-2519
Q: Approximately how far (in meters) did the camera move between frame 13 and frame 31 of 32?
think: <move from=13 to=31> -> dx = -3.11 m, dy = +0.08 m, dz = +1.07 m, distance = 3.29 m / closing: The printed distance is 3.29 m, so the camera moved about 3.29 m.
A: 3.29
```

**routing / `camera_movement_direction`**

```text
[1] lines 2637-2647
Q: During the sequence between frame 2 and frame 27 of 32, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are Left, Forward, Backward and Right.  (A. left | B. forward | C. backward | D. right)
think:
  Okay, I need to measure how the camera moved between frame 2 and frame 27. The pose head with the scale head gives the metric camera motion, which the move tool prints in the starting frame's level coordinates.
  
  The move tool gives the camera displacement from frame 2 to frame 27 in frame 2's level frame (x right, y up, z forward). <move from=2 to=27><tool_response>dx = +1.73 m, dy = +0.18 m, dz = +6.41 m, distance = 6.64 m</tool_response>
  
  Scoring each option by the matching component: left = -dx = -1.73 m; forward = dz = 6.41 m; backward = -dz = -6.41 m; right = dx = 1.73 m.
  
  The largest is forward. That matches option B.
A: B

[2] lines 2683-2693
Q: During the sequence between frame 18 and frame 19 of 32, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are Backward, Left, Right and Forward.  (A. backward | B. left | C. right | D. forward)
think: <move from=18 to=19> -> dx = -0.10 m, dy = -0.05 m, dz = +0.32 m, distance = 0.34 m / closing: The largest is forward. That matches option D.
A: D

[3] lines 2729-2739
Q: During the sequence between frame 21 and frame 23 of 32, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are Right, Forward, Left and Backward.  (A. right | B. forward | C. left | D. backward)
think: <move from=21 to=23> -> dx = +0.07 m, dy = -0.05 m, dz = -0.19 m, distance = 0.21 m / closing: The largest is backward. That matches option D.
A: D
```

**routing / `camera_rotation`**

```text
[1] lines 2862-2870
Q: What is the signed camera rotation in degrees between frame 2 and frame 21 of 32? Positive means left; use (-180, 180].
think:
  I will use the pose head's turn from frame 2 to frame 21, wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees.
  
  <turn from=2 to=21><tool_response>turn = +136 deg</tool_response>
  
  The camera rotation is 136 degrees; positive yaw means left.
A: 136

[2] lines 2903-2911
Q: What is the signed camera rotation in degrees between frame 20 and frame 24 of 32? Positive means left; use (-180, 180].
think: <turn from=20 to=24> -> turn = +20 deg / closing: The camera rotation is 20 degrees; positive yaw means left.
A: 20

[3] lines 2944-2952
Q: What is the signed camera rotation in degrees between frame 17 and frame 23 of 32? Positive means left; use (-180, 180].
think: <turn from=17 to=23> -> turn = -59 deg / closing: The camera rotation is -59 degrees; positive yaw means left.
A: -59
```

# Appendix B: three rows per new family in `rs_rows/out/rows`

Source: `rs_rows/out/SAMPLES.md` as regenerated at 05:20Z (fixed-seed samples, twelve per family). The first row of each family is complete; rows 2 and 3 are shortened as in Appendix A. None of these rows is admitted.

**`facing`**

```text
[1] rs_facing_1f6148d3d0de15ed18d857c7, lines 7-45
Q: If I am standing by the toilet and facing directly away from the keyboard, is the sofa to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it. A. left B. right C. back
think:
  I locate the standing object S, the facing object F, and the query object Q. Each cam coordinate is in its named camera frame; f1 is the shared level reference.
  <ground obj="toilet">
  <tool_response>
  toilet: frames 20,27,30 (best 27)
  P1: cam27 (-0.69, -0.28, 1.26) m; f1 (2.81, -0.91, 0.18) m; spread 0.01
  size 0.35 x 0.30 x 0.58 m
  </tool_response>
  <ground obj="keyboard">
  <tool_response>
  keyboard: frames 6,9,10 (best 6)
  P2: cam6 (-0.38, -0.06, 0.94) m; f1 (-1.38, -0.64, 0.92) m; spread 0.02
  size 0.30 x 0.09 x 0.02 m
  </tool_response>
  <ground obj="sofa">
  <tool_response>
  sofa: frames 1,2,6,16,17,31 (best 16)
  P3: cam16 (-0.52, -0.39, 1.78) m; f1 (-0.70, -1.05, 2.41) m; spread 0.01
  size 1.30 x 0.60 x 0.48 m
  </tool_response>
  I face away, so I negate the vector toward F. On the floor, u = S - F = (4.19, -0.74); v = Q - S = (-3.51, 2.23).
  cross = u_x x v_z - u_z x v_x = 6.7463; dot = u_x x v_x + u_z x v_z = -16.3571.
  atan2(cross, dot) = 158 degrees, rounded to a whole degree. An absolute bearing of at least 135 degrees means back; otherwise its sign gives left or right. The query object is back, so I choose C.
A: C

[2] rs_facing_11377d2270bf6542c3c0b67b, lines 47-85
Q: If I am standing by the stove and facing the dishwasher, is the refrigerator to my left, right, or back? An object is to my back if I would have to turn at least 135 degrees in order to face it. A. left B. right C. back
think: <ground obj="stove"> -> stove: frames 4,5,6,12,31 (best 6) ... size 0.86 x 0.49 x 0.16 m / <ground obj="dishwasher"> -> dishwasher: frames 3,14 (best 14) ... size 0.49 x 0.07 x 0.77 m / <ground obj="refrigerator"> -> refrigerator: frames 5,7,8,9,17,31 (best 7) ... size 0.66 x 0.08 x 0.78 m / closing: atan2(cross, dot) = -77 degrees, rounded to a whole degree. An absolute bearing of at least 135 degrees means back; otherwise its sign gives left or right. The query object is right, so I choose B.
A: B

[3] rs_facing_81a6ec14da21cccbcb4383f7, lines 165-204
Q: If I am standing by the door and facing directly away from the whiteboard, is the monitor to my front-left, front-right, back-left, or back-right? The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the p [...]
think: <ground obj="door"> -> door: frames 5,13,14,21,22,24,31 (best 24) ... size 0.91 x 0.00 x 0.84 m / <ground obj="whiteboard"> -> whiteboard: frames 2,4,9,12,14,16,21,23,25,26 (best 2) ... size 1.11 x 0.01 x 0.60 m / <ground obj="monitor"> -> monitor: frames 1,3,6,8,9,12,14,15,16,25,27,30 (best 3) ... size 0.58 x 0.20 x 0.52 m / closing: atan2(cross, dot) = 156 degrees, rounded to a whole degree. An absolute bearing below 90 degrees means front; otherwise it means back. A positive sign means left and a negative sign means right. The query object is back-left, so I choose B.
A: B
```

**`units`**

```text
[1] rs_units_2f0c76ed57ca80e8999c024e, lines 490-522
Q: Measuring from the closest point of each object, what is the distance between the heater and the chair (in feet)?
think:
  I use the printed metric measurement and convert it to the unit in the question.
  <ground obj="heater" mode="box">
  <tool_response>
  heater: frames 1,2,11,32 (best 1)
  B1: f1 centre (0.35, -0.48, 1.74) m
  size 0.59 x 0.09 x 0.80 m
  yaw -154 deg (0 = +x; positive +x toward -z about +y)
  </tool_response>
  <ground obj="chair" mode="box">
  <tool_response>
  chair: frames 5,6,7,10,28,29 (best 7)
  B2: f1 centre (-0.39, -1.02, 0.09) m
  size 0.36 x 0.21 x 0.42 m
  yaw -99 deg (0 = +x; positive +x toward -z about +y)
  </tool_response>
  <gap a="heater" b="chair" rule="box_grid_5cm">
  <tool_response>
  distance 1.55 m
  </tool_response>
  1.55 m x (10000 / 3048) = 5.09 feet (rounded to two decimals).
A: 5.09

[2] rs_units_015b2fd283f3ed71e31d64e7, lines 524-546
Q: What is the size of this room (in square feet)? If multiple rooms are shown, estimate the size of the combined space.
think: <ground mode="room"> -> room: frames 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32 ... area 11.42 m^2 / closing: 11.42 m^2 x (10000 / 3048)^2 = 122.92 square feet (rounded to two decimals).
A: 122.92

[3] rs_units_53ea574e41b3f293d500bf1a, lines 548-580
Q: Measuring from the closest point of each object, what is the distance between the whiteboard and the laptop (in meters)?
think: <ground obj="whiteboard" mode="box"> -> whiteboard: frames 1,2,7,9,10,11,18,19,22,23,29 (best 7) ... yaw -97 deg (0 = +x; positive +x toward -z about +y) / <ground obj="laptop" mode="box"> -> laptop: frames 16,19,24 (best 16) ... yaw -113 deg (0 = +x; positive +x toward -z about +y) / <gap a="whiteboard" b="laptop" rule="box_grid_5cm"> -> distance 2.25 m / closing: 2.25 m x 1 = 2.25 meters (rounded to two decimals).
A: 2.25
```

**`recovery`**

```text
[1] rs_recovery_144ab6beff8d748f073ad070, lines 890-907
Q: How many desk(s), keyboard(s), and window(s) are there in total in this room?
think:
  <ground obj="window" mode="box">
  <tool_response>
  error: Routed query lies outside the fixed candidate universe; answer directly from the video
  </tool_response>
  The call did not provide the requested evidence. Repeating it would not supply a measurement. I cannot establish a reliable answer from the available frames, so I decline to guess.
A: I cannot determine this reliably from the available evidence.

[2] rs_recovery_f1189d96ebd76293b701d7b2, lines 909-939
Q: How many monitor(s) and mouse(s) are there in total in this room?
think: <ground obj="mouse" mode="box"> -> mouse: box unavailable / <ground obj="monitor" mode="instances"> -> monitor: 2 found ... P2: monitor instance 2 cam21 (0.43, -0.18, 0.86) m; f1 (-2.38, -0.32, -1.54) m; first 5 / <ground obj="mouse" mode="instances"> -> mouse: 2 found ... P4: mouse instance 2 cam21 (0.26, -0.43, 0.93) m; f1 (-2.34, -0.59, -1.37) m; first 21 / closing: The instance responses supply distinct identities P1, P2, P3, P4. The total is 2 + 2 = 4.
A: 4

[3] rs_recovery_b649c25e18cd38ec4a248043, lines 941-984
Q: How many headphones, monitor(s), and plant(s) are there in total in this room?
think: <ground obj="plant" mode="box"> -> plant: box unavailable / <ground obj="headphones" mode="instances"> -> headphones: 2 found ... P2: headphones instance 2 cam27 (-0.46, -0.36, 0.83) m; f1 (0.99, -0.50, 1.69) m; first 27 / <ground obj="monitor" mode="instances"> -> monitor: 9 found ... P11: monitor instance 9 cam23 (0.62, -0.02, 1.35) m; f1 (4.66, -0.20, -0.48) m; first 23 / <ground obj="plant" mode="instances"> -> plant: 2 found ... P13: plant instance 2 cam13 (0.35, 0.55, 1.37) m; f1 (5.55, 0.59, -1.96) m; first 9 / closing: The instance responses supply distinct identities P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13. The total is 2 + 9 + 2 = 13.
A: 13
```

**`totals`**

```text
[1] rs_totals_446868aab63326d6f5c85aad, lines 1204-1244
Q: How many keyboard(s), office chair(s), and whiteboard(s) are there in total in this room?
think:
  I enumerate each category and count each reported instance once across frames.
  <ground obj="keyboard" mode="instances">
  <tool_response>
  keyboard: 3 found
  P1: keyboard instance 1 cam24 (-0.08, -0.26, 1.11) m; f1 (-0.04, -0.59, 3.01) m; first 7
  P2: keyboard instance 2 cam22 (0.43, -0.17, 0.90) m; f1 (2.51, -0.63, 3.43) m; first 9
  P3: keyboard instance 3 cam15 (0.51, -0.35, 1.25) m; f1 (2.39, -0.58, 2.39) m; first 9
  </tool_response>
  <ground obj="office chair" mode="instances">
  <tool_response>
  office chair: 8 found
  P4: office chair instance 1 cam11 (-0.50, -0.12, 0.94) m; f1 (2.62, -0.52, 1.71) m; first 2
  P5: office chair instance 2 cam11 (0.11, 0.03, 1.57) m; f1 (3.44, -0.69, 1.42) m; first 2
  P6: office chair instance 3 cam14 (0.14, 0.55, 1.48) m; f1 (3.21, -0.76, 0.14) m; first 3
  P7: office chair instance 4 cam14 (0.59, 0.71, 1.72) m; f1 (3.24, -0.79, -0.39) m; first 3
  P8: office chair instance 5 cam29 (0.31, -0.20, 0.55) m; f1 (0.01, -0.31, 3.75) m; first 7
  P9: office chair instance 6 cam22 (-0.82, -0.04, 1.32) m; f1 (3.05, -0.75, 4.63) m; first 9
  P10: office chair instance 7 cam17 (-0.26, -0.09, 0.86) m; f1 (2.48, -0.70, 4.01) m; first 16
  P11: office chair instance 8 cam21 (1.58, -0.15, 2.93) m; f1 (-0.88, -0.80, 4.17) m; first 19
  </tool_response>
  <ground obj="whiteboard" mode="instances">
  <tool_response>
  whiteboard: 2 found
  P12: whiteboard instance 1 cam8 (1.49, 1.23, 3.07) m; f1 (2.43, 0.13, 4.97) m; first 2
  P13: whiteboard instance 2 cam4 (-0.53, 0.39, 2.60) m; f1 (3.92, 0.20, 1.01) m; first 3
  </tool_response>
  The distinct reported identities are P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13.
  The total is 3 + 8 + 2 = 13. I return one scalar total.
A: 13

[2] rs_totals_040cbe1fa53790e5333fe0f4, lines 1246-1273
Q: How many tv(s) and whiteboard(s) are there in total in this room?
think: <ground obj="tv" mode="instances"> -> tv: 2 found ... P2: tv instance 2 cam18 (0.39, 0.20, 0.94) m; f1 (3.58, -0.16, 1.97) m; first 3 / <ground obj="whiteboard" mode="instances"> -> whiteboard: 2 found ... P4: whiteboard instance 2 cam22 (-0.07, 0.11, 2.16) m; f1 (0.59, 0.11, -2.04) m; first 3 / closing: The total is 2 + 2 = 4. I return one scalar total.
A: 4

[3] rs_totals_a686b0945873a308b86ade77, lines 1275-1311
Q: How many chair(s) and table(s) are there in total in this room?
think: <ground obj="chair" mode="instances"> -> chair: 6 found ... P6: chair instance 6 cam24 (-0.18, -0.08, 0.71) m; f1 (-4.69, -0.30, 2.66) m; first 19 / <ground obj="table" mode="instances"> -> table: 7 found ... P13: table instance 7 cam23 (-0.08, -0.29, 0.79) m; f1 (-5.24, -0.26, 2.90) m; first 21 / closing: The total is 6 + 7 = 13. I return one scalar total.
A: 13
```
