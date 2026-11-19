"""Write one prompt per analyst under B/events/swarm_an/prompts/. Rerun with --tag m400 --new-run R1 --new-step 400 after
adding the step-400 roots to san_kit.py; the analyst list and report format stay the same."""
import argparse, os
B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'
OUT = B + '/events/swarm_an/prompts'
ap = argparse.ArgumentParser(); ap.add_argument('--tag', default='m200'); ap.add_argument('--new-step', type=int, default=200)
ap.add_argument('--only', default=''); a = ap.parse_args()
NEW = a.new_step

RULES = """## Rules (binding, verbatim from the lane brief)
read-only; no ssh, network, Git or deletion; no recursive search under /home or /data*; under /scratch/jjyeung/orch_n30 list and read only the named folders, any find limited to depth 4; python from /usr/bin/python3 or /scratch/jjyeung/envs/planner_local_v1/bin/python, CPU only, under 4 GB RAM, scratch files only under /tmp; never load a whole sqlite file; quote counts from files, label guesses.

More rules of this cluster, equally binding:
- You run on trinity-3-30, a shared node. Search for files only with specific patterns inside the bounded directories named here; sweeping searches have crashed nodes. Do not list or read the repository on /home.
- No official VSI-Bench, VSTI or ReVSI item is read or used for any choice. Use only the dev sets named below.
- Change nothing: the returns and stores belong to another lane. Your sandbox is read-only; run python inline (`python3 - <<'EOF' ... EOF`). Keep every command's printed output under about 150 lines: print counts and short excerpts, never whole files or token lists.
- One python process at a time, no parallel workers, no GPU.
- Your final message is the report. Nothing else you write is kept.
"""

CONTEXT = """## What this is
We train a ~9B spatial VLM that answers from RGB video (32 frames). Its chain of thought (the text before `</think>`) either reasons directly from the frames ("direct" types) or calls heads inside its own checkpoint (`<ground ...>`, `<gap ...>`, `<move ...>` and similar) and answers from the `<tool_response>` they print ("routed" types: absolute distance and the three camera types). For every question type we need to know what goes wrong in the model's traces, how many points each failure costs, and which training-row or trace change would fix it in the next training run (called vehicle N).

Checkpoints:
- **step 544** = the base: the sealed leg (run 469ddece) at its last step, trained on the older trace forms.
- **step %(NEW)d** = leg R1 (run 673bc60f), %(NEW)d steps into a continuation from that base, trained on the rebuilt rows (store v7, trace ruling of 2026-11-15) plus routed rows and feet/inch unit rows.
Dev sets (never official benchmark items): **dev-S1** (VSI-Bench-style questions on training-distribution rooms) and **R0-dev** (ReVSI-style questions; subtype field gives e.g. toward/away, closest/farthest, single/multiple). VSTI relative dev set (900 items, six types). Facing twins (150 "away" and 150 "forward" items).

Scored arm: **B2048** = the think block is force-closed at 2,048 tokens and the answer is then generated; that score is `score`. The full generation without the forced close (ON16k) is `text`/`score_on`.

Already known; do not redo, build on it:
- Routed absolute distance at step 200: no tool call on 62 of 150 items; those traces copy the relative-distance direct template; coverage rows are being built.
- Counting: the first-seen list form ("list each distinct X once, by the frame where it first appears: frame a; frame b; ...") can loop until the token budget (a "runaway", `forced_close` true); those rows are removed from the continuation. Report runaways as one priced mode and spend your reading on the other modes.
- Routed room size at step 200 makes no call and scores far better than step 544, which called and hit the call cap.
"""

KIT = """## How to read the traces (read in place; never copy)
A loader is provided. Use it instead of parsing the raw files (they are 6 to 26 MB each, mostly token ids):
```
python3 - <<'EOF'
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
new = K.direct('R1', %(NEW)d, 'dev-S1', types=['object_rel_direction_hard'])   # step %(NEW)d
old = K.direct('S1', 544, 'dev-S1', types=['object_rel_direction_hard'])   # step 544 base
for o, n in K.paired(old, new)[:2]:
    print(n['id'], n['question'], n['options'], 'gt', n['gt'], '| 544:', o['pred'], o['score'], '| %(NEW)d:', n['pred'], n['score'])
    print(n['text'])
print(K.SOURCES)   # the files that were read
EOF
```
- `K.direct(run, step, set, types=None)`: set is 'dev-S1' or 'R0-dev'. Runs/steps with traces: ('R1', %(NEW)d), ('R1', 100), ('S1', 544).
- `K.facing(run, step, twin)`: twin 'away' or 'forward'; ('R1', 200) and ('S1', 544).
- `K.vsti(run, step)`: ('R1', 200) and ('S1', 544).
- `K.routed(step, types=None, part='A')`: step 200 or 544; needs `/scratch/jjyeung/envs/planner_local_v1/bin/python`. part 'A' = 636 dev-S1 routed items (camera_displacement, camera_rotation, camera_movement_direction, object_abs_distance, room_size_estimation); part 'B' = 134 room items.
- Row fields: id, set, step, type, question, options, gt, pred, score (B2048 arm), pred_on, score_on (ON16k), text (full generated trace), forced_close, think_tokens, out_tokens, hit_cap, finish, room, subtype, unit. Routed rows: text (with `<tool_response>` blocks), calls (list of call/family/served/response), ncalls, answer, score (MRA for numeric types, accuracy for choice), finish, scale. Read the docstring at the top of `/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py` first.
- For ('S1', 544, 'dev-S1') and the step-544 facing twins only the B2048 arm exists, so `text` is the B2048 text there.
- Numeric types score by mean relative accuracy (MRA: the share of thresholds 0.50, 0.55, ..., 0.95 that the relative error passes), so `score` is fractional; a "wrong item" there is one with score < 1, and its cost is 1 - score.

Training rows (to link a failure mode to the row family that could teach it):
- Store v7: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite`, 1.7 GB, table `rows(i INTEGER PRIMARY KEY, row TEXT, target TEXT)`; `row` is JSON with `question_type`, `pool`, `qid`, `retrace`, `student_input.question`, `student_input.options`, `target` (the trained text: `<think>...</think>` then the answer), `answer`. Open it read-only (`sqlite3.connect('file:...rows.sqlite?mode=ro', uri=True)`) and fetch rows by primary key only: `select i,row from rows where i in (...)` with at most 200 ids per query. Index ranges per question type: `/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json` (key `families`, zero-based inclusive ranges). Never run a query without a primary-key condition; never `select *` over the table.
- A family = question_type x pool x retrace rule. Rows removed from training: qids listed as `row_key` in `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json` and `z.json` (one JSON object per line, with a `reason`); a row is "kept" when its qid is in neither.
- Ready-made: 20 rows per family in `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_SAMPLES20.json` (dict family -> list of {i, qid, kept_nz, question, options, target, answer}) and per-family row counts in `/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json` (`families[name].rows / kept_nz`).
- Feet and inch unit rows (routed distance): `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl` (13 MB; one JSON per line with `question`, `target`, `answer`, `provenance.details`); read it line by line.
- Trace ruling (which trace form each type should carry): `/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md` (83 KB; read the Answer section and the parts on your type only, with one bounded read).
""" % dict(NEW=NEW)

REPORT = """## Required report (your final message; at most 120 lines, then the appendix)
Write for a reader who has not seen the traces. Use full sentences in the prose parts. Sections, in this order:
1. **Scope**: sets, item counts, score at step 544 and step %(NEW)d per set, recomputed by you from the files (say which files).
2. **Failure modes** at step %(NEW)d: a table with one row per mode: name, one-line definition, count per set, cost in points on the type per set (100 x summed (1 - score) of the mode's items / items of the type in that set). Classify ALL wrong items of the type, not a sample (a sample of at least 150 wrong items is allowed only when a type has 400 or more items in a set; say so). Each wrong item gets exactly one primary mode; the counts must add up to the number of wrong items. Separate where the trace itself goes wrong (a wrong relation, order, count or number is written) from where the answer does not follow the trace (the trace states X, the answer is Y), and from format failures (no answer, runaway, unparsed).
3. **Examples**: three verbatim examples per mode: item id, set, question (shortened if long), truth, answer, and the trace excerpt that shows the failure (at most 4 lines each).
4. **Step 544 against step %(NEW)d**: counts right->wrong, wrong->right, wrong->wrong per set, and what changed in the trace for the flipped items (trace form, length, what is stated).
5. **Hypotheses**: for each mode, the cause you think most likely, labelled HYPOTHESIS, with the training-row family it points to (question_type|pool|retrace) and the evidence from rows you read (quote one row target, shortened).
6. **Label or scoring defects**: items whose ground truth, options or scoring look wrong, with ids and the reason; "none found" if none.
7. **Three changes** you would make to the rows or traces of the next training run (add, reword or drop; which family; about how many rows), each with the number of wrong items it could fix and the reasoning for that number. Say which of them you are least sure of.
8. **Not established**: what you could not determine and what data would settle it.

**Appendix (not counted in the 120 lines)**: `CLASSIFIER`: one python code block of at most 60 lines, runnable as is, that loads the items with san_kit and prints your section-2 counts per mode and set. Where a mode rests on your reading rather than on a rule, list its item ids in the code as a set. The coordinator reruns this block and opens items you cite; a report whose two largest counts cannot be reproduced is sent back.
State every count as "n of N". Label every guess as a guess. Do not pad.
""" % dict(NEW=NEW)

def direct_block(types, sets_note, extra):
    return """## Your assignment
Types: %s.
Sets: %s
%s
""" % (types, sets_note, extra)

A = {}
DIRQ = """Direction questions ask where a target object lies for an observer standing at one object and facing (or facing away from) another; easy = left/right, medium = left/right/back, hard = front-left/front-right/back-left/back-right. R0-dev carries `subtype` toward or away ("facing away from" wording).
Questions to answer besides the required report:
- Confusion table truth -> answer by direction word (and by subtype on R0-dev). Split the wrong items into: only the front/back part wrong, only the left/right part wrong, both wrong.
- Does the answer follow the trace? Parse the relation the trace states in words (e.g. "behind me, on my left", "at my back-left") and compare it with the option chosen. Count the items where the trace's own conclusion maps to a different option than the answer (usage failure) against those where the trace's stated relation is itself wrong (perception or reasoning failure).
- For "facing away" items: does the trace write the half-turn step, and does it apply it correctly (front<->back and left<->right both swap)? Count: no half-turn written; half-turn written but applied to one axis only; applied correctly but the forward relation was wrong.
- Does the wrong answer correlate with the frames cited (objects first seen far apart in the video, the same frame for all three objects, an object the trace never locates)?
- dev-S1 against R0-dev: R0-dev scores far lower. Which wording or object property of R0-dev items goes with the failures (wording differences, "away", object classes, repeated instances of the observer or target object)?"""
A['dir_easy'] = direct_block('object_rel_direction_easy', "dev-S1 (150 items) and R0-dev (192 items; subtype toward 126, away 66).", DIRQ)
A['dir_med'] = direct_block('object_rel_direction_medium', "dev-S1 (150 items) and R0-dev (194 items; subtype toward 129, away 65).", DIRQ)
A['dir_hard'] = direct_block('object_rel_direction_hard', "dev-S1 (150 items) and R0-dev (192 items; subtype toward 121, away 71).", DIRQ)
A['rel_dist'] = direct_block('object_rel_distance', "dev-S1 (150 items) and R0-dev (279 items; subtype closest 186, farthest 93).", """Relative distance asks which of four candidates is closest to (or, on R0-dev, also farthest from) a reference object.
Questions to answer besides the required report:
- The step-%(NEW)d trace orders the candidates ("ordered nearest to farthest ..."). Parse that order. Count wrong items where (a) the order's first (or last, for farthest) element is not the truth: the order itself is wrong; (b) the order is right for the question but the answer picks another candidate; (c) the question asks farthest and the trace answers the nearest (or the reverse); (d) a candidate is missing from the order or an object is never located.
- When the order is wrong: at which rank does the truth sit in the model's order (2nd, 3rd, 4th)? A truth at rank 2 is a near miss.
- Step 544 wrote a metre value per candidate; step %(NEW)d writes no metres. Compare the two on the flipped items.
- Position bias: distribution of the answer letter and of the answer's position in the question's candidate list, against the truth's.
- Is the reference object or a candidate present several times in the room (plural wording, "the chair")? Do failures concentrate there?""" % dict(NEW=NEW))
A['app_order'] = direct_block('obj_appearance_order', "R0-dev only (246 items; subtype first_seen). dev-S1 has none.", """Appearance order asks in which order four object categories first appear in the video; the options are four orderings.
Questions to answer besides the required report:
- The trace lists a first-seen frame per object and then an order. Parse both. Count wrong items where (a) the stated first-seen frames give an order that matches no option or a wrong option (perception: frames wrong); (b) the stated frames are consistent with the truth but the order written or the option chosen differs (usage or sorting failure); (c) ties: two objects given the same frame; (d) an object is not given a frame.
- How far off are the stated frames? When the trace's order differs from the truth, is it a single adjacent swap or more? An adjacent swap between objects that appear within about 2 frames of each other is a near miss.
- Frame numbering: does the trace use frame indices 1 to 32 or decimal values such as 118.9 (step 544 did)? Does the numbering form change between steps, and do sorting mistakes go with one form?
- Step 544 against step %(NEW)d: the score rose about 6 points; what changed in the flipped items?""" % dict(NEW=NEW))
A['route'] = direct_block('route_planning', "dev-S1 only (150 items).", """Route planning asks for the turns (left, right, back) that fill a route between named objects.
Questions to answer besides the required report:
- The trace writes one line per step ("I find the bed to my left: turn left") and then "The turns are: ...". Parse the turns in the trace and compare with the truth sequence and with the option chosen. Count wrong items where (a) one turn is wrong, (b) two or more turns are wrong, (c) the trace's turns match the truth but another option is chosen, (d) the trace's turns match no option.
- Which turn is wrong most often: the first (from the start pose), a middle one, the last? Left/right swaps against back confusions?
- Does the trace keep the heading correctly from step to step ("keep that heading")? Give the count of traces whose later turn is inconsistent with their own earlier statement.
- Step 544 had an empty think block for this type (answer only). Compare right/wrong flips: what does writing the steps buy and where does it hurt?
- Number of fill-in turns per item (1, 2, 3) against accuracy at both steps.""")
A['size'] = direct_block('object_size_estimation (numeric, centimetres) and relative_size_object', "object_size_estimation: dev-S1 (150) and R0-dev (293; subtype longest_dimension). relative_size_object: dev-S1 only (150).", """Object size asks for the longest dimension of an object in centimetres (MRA score). Relative size asks which of several objects is larger or smaller.
Questions to answer besides the required report:
- Size: distribution of the signed relative error (answer/truth) at both steps: bias (under or over), spread, share of items within 10%%, 25%%, 50%%. Per object class with at least 5 items: mean ratio. Is the answer a round or class-typical number regardless of the instance (same answer for the same class across rooms)? Count the distinct answers per class.
- Does the trace state anything that determines the number (a comparison object, a frame), or is the number asserted? Does the answer equal the number in the trace (usage)?
- Unit failures: answers that look like metres or inches when centimetres are asked; R0-dev wording differences ("unit" field).
- Which truth ranges fail most (small objects under 30 cm, large over 200 cm)?
- Relative size: for wrong items, does the trace state sizes or just an order? Is the trace's order wrong, or does the answer not follow it? Does a "smaller/smallest" question get the largest (polarity error)?""")
A['count'] = direct_block('object_counting (numeric, MRA) and relative_count', "object_counting: dev-S1 (150) and R0-dev (385; subtype single 287, multiple 98). relative_count: dev-S1 only (139).", """Counting asks how many instances of a category are in the room ("multiple" asks for the total over two categories). Relative count asks which category has more or fewer instances.
Runaways are known (see "Already known"): count them (forced_close true) as one mode with its cost, and read at most 5. Spend the reading on the rest.
Questions to answer besides the required report:
- Non-runaway wrong items: signed error distribution (answer - truth) per set and subtype; undercount against overcount; error against truth size (truth 1, 2, 3, 4, 5+). What share of the lost MRA sits at truth >= 5?
- Does the answer equal the number of first-seen frames listed in the trace (usage)? Count items where the list length differs from the stated count.
- Do listed frames repeat (the same frame given for two instances) or cluster in adjacent frames (the same instance counted twice)? Count.
- "Multiple" items: is each category counted and are the two counts added correctly? Count arithmetic failures against per-category miscounts.
- Runaway against truth size and category: which categories and truth sizes run away? In the ON16k text of runaways, at what list length does the repetition start, and would cutting the list at that point give the right count?
- For force-closed items the B2048 answer is generated after a forced close: is it a huge number (e.g. 38)? What would the score be if such items answered with the count of distinct frames listed before the repetition began? Report that score as an upper bound, labelled as computed by you.
- relative_count: 65 of 139 items are force-closed at step 200 (5 at step 544). Describe that trace form, where it loops, and what the non-runaway wrong items get wrong (each category's count against the comparison).
- Step 544 against step %(NEW)d on the paired items: counting fell on dev-S1 (62.8 to 56.3) and rose on R0-dev (50.8 to 53.7): attribute each change to runaways against the rest.""" % dict(NEW=NEW))
VSTIQ = """VSTI relative questions: camera_obj_rel_dist_v1 (which of four objects is closest to the camera in frame k), v2 (three objects?), v3 (two?), obj_obj_relative_pos_lr / nf / ud (is object A left or right of / nearer or farther than / above or below object B, from the camera viewpoint of a frame). Verify the exact question forms from the items; do not trust this summary.
Load with `K.vsti('R1', 200, types=[...])` and `K.vsti('S1', 544, types=[...])`.
Questions to answer besides the required report:
- Chance level per type (from the option count and the truth distribution) and the score of the best constant answer; how far above it is step 200?
- The step-200 trace takes "the camera viewpoint of frame k", locates each object by its first-seen frame, then orders or relates them. Parse the stated order or relation. Count wrong items where the stated relation is wrong against those where the answer does not follow it.
- Is the named frame k used? Does the trace locate the objects in frame k, or in other frames (first seen elsewhere)? Count wrong items where an object is not visible in frame k according to the trace's own first-seen frames; say whether failures concentrate there.
- Answer bias: distribution of answers against truths (letters and words); polarity errors (asks farthest, answers closest; asks left, answers right for the mirrored pair).
- For lr/nf/ud: are the items pairs or mirrored twins (same objects, swapped roles)? If so, how often are both twins answered consistently?
- Step 544 against step 200: the base copied a template on some types; what changed?"""
A['vsti_a'] = direct_block('camera_obj_rel_dist_v1 and camera_obj_rel_dist_v2 (VSTI relative dev set)', "150 items each.", VSTIQ)
A['vsti_b'] = direct_block('camera_obj_rel_dist_v3 and obj_obj_relative_pos_nf (VSTI relative dev set)', "150 items each.", VSTIQ)
A['vsti_c'] = direct_block('obj_obj_relative_pos_lr and obj_obj_relative_pos_ud (VSTI relative dev set)', "150 items each.", VSTIQ)
A['facing'] = direct_block('facing twins: the same direction question asked "facing away from" (away) and "facing" (forward)', "`K.facing('R1', 200, 'away')` and `K.facing('R1', 200, 'forward')`: 150 items each (50 easy, 50 medium, 50 hard); step 544 through `K.facing('S1', 544, ...)`. Also the R0-dev direction items with subtype away (66 easy, 65 medium, 71 hard) through `K.direct('R1', 200, 'R0-dev', types=[...])`, whose wording is the ReVSI wording.", """Questions to answer besides the required report:
- Pair each away item with its forward twin (same scene and objects; find the pairing key from the ids or the question text and say how you paired). Four cells per level: both right, forward right and away wrong, forward wrong and away right, both wrong. When the forward twin is right and the away item wrong, the half-turn is the failure; count which part failed (front/back not swapped, left/right not swapped, both).
- away-hard: the model is suspected of over-using "back". Give the confusion table truth -> answer for away-hard (twins and R0-dev away), the share of answers containing "back" against the share of truths containing "back", and the same for forward-hard.
- The away trace form: "If I stood at X facing Y, the Z would be ...; The question has me face away ... half turn ...; So ...". Count traces that write the forward relation and the half-turn step; among wrong items, is the forward relation as written the same as the forward twin's trace states? (If the twin's forward relation is right and the away trace writes a different forward relation, the failure is in the first step, not the turn.)
- Wording: compare the twin wording with the R0-dev (ReVSI) away wording verbatim; list every wording variant with its item count and accuracy at step 200. Which variants does the model handle worst?
- Step 544 scored 6 to 38 on away; step 200 scores 82 to 94. What do the remaining wrong away items have in common?""")
ROUTEDQ = """Load with `/scratch/jjyeung/envs/planner_local_v1/bin/python` and `K.routed(200, types=[...])`, `K.routed(544, types=[...])`.
For every routed type report a three-part table per step (placement, head accuracy, usage), with counts:
- **Placement**: items with a call; the call's arguments against the question (the frames or objects named in the question: are they the ones in the call?); unserved or malformed calls; extra calls.
- **Head accuracy**: the value the tool printed against the ground truth: MRA (or accuracy) of the printed value itself, ignoring what the model then answered.
- **Usage**: does the final answer equal the printed value (after any unit conversion or mapping the question requires)? Count answers that depart from the response and whether departing helped or hurt.
Then classify every item with score < 1 by which of the three lost it (head wrong but used faithfully; head right but answer departs; call misplaced; no call)."""
A['routed_disp'] = direct_block('camera_displacement (routed; numeric, MRA)', "150 dev-S1 routed items.", ROUTEDQ + """
Extra questions:
- Error of the printed distance against truth as a function of the frame gap (to - from), of the truth size, and of `scale` (the scale head's value for the item): is the loss a scale error (ratio answer/truth constant within an item's room) or a pose error?
- If each room's answers were rescaled by the room's median ratio truth/printed, what would MRA be (upper bound for a scale fix; label it as computed by you)?
- Units and wording: every unit asked (m, cm, feet), every question template, with counts and MRA. Does any template lose the call or the conversion?
- Step 544 against step 200: are the calls and responses identical on paired items? Where they differ, why?""")
A['routed_rot'] = direct_block('camera_rotation (numeric, MRA) and camera_movement_direction (choice, accuracy), both routed', "150 dev-S1 routed items each.", ROUTEDQ + """
Extra questions:
- Rotation: which quantity does the tool print (yaw, total angle, signed or unsigned) and which does the question ask? Error against the truth angle size (small angles under 15 degrees, large over 90), sign or wrap-around errors (e.g. 350 against 10), answers in the wrong unit. MRA punishes small truths hardest: what share of the lost MRA sits at truths under 20 degrees?
- Movement direction: the tool prints dx, dy, dz; the answer is a direction word or letter. For each wrong item: is the printed displacement itself pointing the wrong way (head), or is the mapping from dx/dz to the word wrong (usage)? State the mapping rule the traces use and test it on all 150 items.
- Every question template and unit with counts and score. Step 544 against step 200 on paired items.""")
A['routed_dist'] = direct_block('object_abs_distance (routed; numeric, MRA), the items that DO call', "150 dev-S1 routed items; at step 200 88 of them call the tool (the 62 that do not are already diagnosed: report them only as one line). Step 544: 149 call.", ROUTEDQ + """
Extra questions (on the calling items):
- Grounding: for each `<ground obj=...>` call, does the response find the object (frames listed, a box) or report it not seen? Are the two grounded names the two objects of the question (same words)? Count items where an object has several instances and which instance pair the gap uses ("taken over every pair of instances").
- Head accuracy: MRA of the printed gap in metres against the truth converted to metres, per unit asked (m, ft, in, cm). Error against truth size (under 0.5 m, 0.5 to 2 m, over 2 m). Is the printed gap biased low (box-to-box gaps of overlapping boxes print 0.00)? Count printed gaps of 0.00 and their truths.
- Usage: answer against printed gap x unit factor; conversions with a wrong factor, a missing conversion (metres answered for a feet question), arithmetic slips. Centimetre questions: 12 of 13 calling items answer metres; list them.
- Which selector rule does each gap call use (`rule=` attribute) and does the rule differ between right and wrong items?
- What would MRA be on the 88 items if (a) every answer equalled printed gap x correct factor, (b) the gap were perfect? Label both as computed by you. This prices usage against head accuracy.
- Step 544 against step 200 on the items that call at both steps: are call strings and responses identical? Where they differ, which is closer to truth?""")
A['cot_cost'] = direct_block('chain-of-thought cost, all types', "All sets: direct dev-S1 and R0-dev at step 544 and step %(NEW)d (and R1 step 100), facing twins, VSTI, routed (parts A and B)." % dict(NEW=NEW), """This is a measurement task; your report replaces sections 2 to 7 of the required report with the tables below (keep sections 1, 6, 8 and the appendix).
- Per set and type, at step 544 and step %(NEW)d (and R1 step 100 where it exists): median, mean, 90th percentile and maximum of think tokens (B2048 `think_tokens`) and of ON16k `out_tokens`; number force-closed at 2,048 (`forced_close`); number that hit the 16,384 cap (`hit_cap`); for routed types the tokens and calls per item and the finish reasons.
- Loops: define a loop detector (e.g. the same line or the same 8-token phrase repeated 10 or more times) and count looping traces per type and step, also below the 2,048 budget. For each looping type show two excerpts (first 3 lines of the loop) and name the trace line that repeats.
- Score against length: per type, accuracy of the shortest third against the longest third of traces at step %(NEW)d. Does longer thinking go with wrong answers once runaways are excluded?
- Cost of the forced close: per type, B2048 score against ON16k score (`score` against `score_on`) on the same items; the number of items where they differ and in which direction.
- Trace-form census: per type and step, the three most common trace skeletons (replace object names and numbers by placeholders, then count identical skeletons), with their share and accuracy. A type whose step-%(NEW)d traces are all one skeleton has learned one template; say which types have a second skeleton and whether it is copied from another type's rows.
- Tokens per point: total think tokens per type against the type's score change from step 544 to step %(NEW)d.
- Three changes that would cut tokens without losing accuracy, each with the tokens saved per item and the evidence.""" % dict(NEW=NEW))
ROWQ = """This is a training-row audit, not a trace read. Sections 2 to 5 of the required report become the audit tables below (keep sections 1, 6, 7, 8; the appendix lists the row indices `i` you read per family and the code that drew them).
For each family assigned to you, draw 60 kept rows spread evenly over the family's index ranges (by primary key; see "Training rows"), read their `target` against the trace ruling (`TRACE_RULING_20261115.md`: read the Answer section and the sections on these types), and report:
- rows in the family, kept rows, and the trace skeletons present (replace names and numbers by placeholders): each skeleton with its share of the 60 and one verbatim target.
- Ruling violations, counted over the 60: a trace that states a quantity that the frames, a printed response or an explicit computation does not supply; an answer-only row; a trace whose stated relation contradicts its answer; a trace that names an object the question does not; a wrong letter for the stated conclusion (check the options); arithmetic that is wrong.
- **Copy risk**: could this form be copied onto another question type? A form is risky when its opening lines do not depend on the question type (e.g. "Step 1: find the X, first seen in frame N" opens relative-distance rows and is copied onto absolute-distance questions, which then skip their tool call). For each skeleton say which other question types have questions similar enough to trigger it, and whether the skeleton contains a call (`<ground`, `<gap`, `<move`, ...) or not.
- **Loop risk**: does the form contain a list whose length the model must decide (frames, instances, candidates) with no stated stop (no count announced before the list, no terminator)? Rate each skeleton: none, bounded by the question (e.g. four candidates), unbounded. Give the longest list in the 60 rows.
- Check 10 rows per family in full: recompute what can be recomputed from the row itself (option letter against the stated conclusion; sums; sorted order against stated frames).
- Which step-200 model traces look like this family's skeleton? You may call `K.direct('R1', 200, ...)` and count, per question type, the traces that match each skeleton's opening line; report cross-type matches (a skeleton of family X appearing on questions of type Y)."""
A['rows_a'] = direct_block('training-row audit A', "Store v7 families (question_type|pool|retrace): object_rel_direction_easy, _medium and _hard in every pool (w1g|rows_rebuild_d0_v1; rows_rebuild_d0_*_gaps or *_gen_r2; r1_away_opp), object_rel_distance|w1g|rows_rebuild_d0_v1, object_size_estimation|r1g|rows_rebuild_d0_v1, route_planning|dose_route_direct. Treat the four rows_rebuild_d0_* pools of one type as one family (60 rows over the four).", ROWQ)
A['rows_b'] = direct_block('training-row audit B', "Store v7 families: object_counting (kept rows only: r1g|rows_rebuild_d0_v1 keeps 2,617 of 9,253; say what form the kept rows have and what form the removed ones had, 20 removed rows are enough), obj_appearance_order (b12_cntapp_gt_v1 and w1g|rows_rebuild_d0_v1), first_seen_frame|b12_cntapp_gt_v1, the six VSTI families (camera_obj_rel_dist_v1/v2/v3, obj_obj_relative_pos_lr/nf/ud; pool vsti_rel_v4; 30 rows each are enough), room_size_estimation|r1_room_traced, box_3d|rows_rebuild_d0_v1 (30 rows), and the feet/inch unit rows in `/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl` (60 rows spread over the file; check each conversion by recomputation: printed gap x factor = answer, rounding, unit word).", ROWQ)

os.makedirs(OUT, exist_ok=True)
only = set(x for x in a.only.split(',') if x)
for k, v in A.items():
    if only and k not in only: continue
    txt = "# Trace analyst san_%s (%s): read-only analysis on trinity-3-30\n\n" % (k, a.tag) + RULES + "\n" + CONTEXT % dict(NEW=NEW) + "\n" + v + "\n" + KIT + "\n" + REPORT
    p = '%s/%s_%s.md' % (OUT, a.tag, k)
    open(p, 'w').write(txt); print(p, len(txt.splitlines()), 'lines', len(txt), 'bytes')
