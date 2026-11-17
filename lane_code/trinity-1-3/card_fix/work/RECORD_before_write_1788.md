# Next 4-H100 leg: which module serves each call, what the leg trains, and what must start now (2026-11-17)

Lane next_leg (Devin, trinity-1-3), design only: no GPU, no Orchard call, no Git, no dispatch. `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, `W` = trinity-1-3 `/scratch/jjyeung/orch_n30/tree_rebuild_w`, `C` = trinity-1-3 `/scratch/jjyeung/orch_n30/cont_ops/work`, `L` = trinity-1-3 `/scratch/jjyeung/orch_n30/next_leg`. "Own arm" = every call served by heads the student trained. "Tower arm" = camera pose and depth from frozen G3T inside the checkpoint, metric scale from the own depth head, level frame from the own gravity head. "Guess" marks a number with no measurement behind it. Times are UTC; PT is UTC-8.

## Question
1. In the claimed artifact, which module inside the checkpoint prints each field of each call, and what do the training rows print, so that training and inference strings match?
2. Which leg takes the four H100 when Orchard advanced returns, and what does H1-1's m100 read change?
3. What is ready, what is not, and what must start now for a submit at the slot?
4. What should the single Orchard job place run until then?
5. Does the leg pass the pre-launch checklist?

## Answer
1. **Camera calls are served by frozen G3T inside the checkpoint, scaled by the own depth head; the own pose head keeps training and serves no call.** The scale is fixed math, median(own depth / G3T depth), the layer behind job 170056's 82.3 / 94.7 / 75.7 on dev-S1. The learned scale head lost 9.3 points of displacement to it, so it stays a parallel build that starts from the rule and must beat it. Lifting uses G3T depth times that scale. Room has no call.
2. **Leg R1 takes the four H100: step 544 plus the repair rows, GT-valued responses, 1,000 steps with its decisive read at step 200.** Rows: recovery after a failed ground, model-written unit conversion, direct room, the six VSTI relative types, facing twins that include ReVSI's away wording, and the verified first-seen repairs (store v6 plus two additions). No GF-1, no own-valued rows, no H1-1 continuation, no H1-2. Expected: VSTI primary 73.9 to 79-83, ReVSI about +3.5 to +5 from facing, and a room and distance path that terminates in a claimed read.
3. **Two vehicles are built in parallel, and the first to pass a production proof launches.** Vehicle P is the deployment that runs H1-1 today (Orchard 170710), with the VQA store swapped and own-valued rows off. Vehicle N is the new tree at build 9, which has never run on Orchard and carries 15 named blockers (7 bind a launch without GF-1, by my reading of their names) and 14 missing evidence records. P carries what the sealed tree admits; the rest joins at R1's step-200 boundary on N. The orchestrator's ruling in force makes recovery and unit rows hard requirements of the next leg, so P may launch without them only if that ruling is amended to bind the leg from step 200 on. I recommend the amendment: the alternative is four idle H100 while N is proven.
4. **H1-1's m100 read decides one switch, S2, and nothing else.** The stop rule has already fired (0.367 against 0.35), which ends H1-1 at step 100 and removes own-valued camera rows from R1.
5. **The production proof of R1 goes first in the Orchard job place,** ahead of every read except the two H1-1 m100 reads; the tower-arm read of step 544 is next.
6. **Four points need the user's word** (section 1.4); each has a default in force.

## 1. Head-serving table for the claimed artifact

### 1.1 Table
Every printed string comes from the tree's v3.14 formatters (`trace_format/box_v313.py`, `ground_v313.py`; the checkpoint was trained on that format, `DD/E2E_READER_B04_20261116.md`, "Operational definition"). Training rows and the reader call the same formatter, so the strings match when the reader prints only statuses the rows contain (1.3).

| Call | Field printed | Module inside the checkpoint at inference | Training rows print |
|---|---|---|---|
| `<move from=i to=j>` | `dx, dy, dz, distance` in metres, 2 decimals, in frame i's level frame | direction and relative rotation: G3T camera head (frozen tower) on the row's 32 frames; metric scale: `tower_scale`, fixed math on the own depth head and G3T depth; level frame: own gravity head | GT trajectory of the row's 32 frames (`gt_pose9`, `gt_up`), same formatter; `max_own_probability 0` |
| `<turn from=i to=j>` | `turn = +-N deg` | G3T camera head rotations and the own gravity head, through the `heading` fixed-math module (build 10, group G2) | GT |
| `<ground obj=A mode="box">` | frame list with best frame; box centre, size, yaw; or `A: not seen` | SAM 3 tower on the raw name; selector head (b04 `run_iso`, 6d97c524, trained on K1); lifting `bestspread` (fixed math) on G3T depth x `tower_scale`; G3T pose x scale into frame 1; own gravity for level and yaw | GT instance masks, GT depth, GT poses (sealed v3.14 rows); recovery rows print `A: not seen` on one operand |
| `<gap a=A b=B>` | `distance X.XX m` | fixed math (`box_grid_5cm` over the two printed boxes) | the same math on GT boxes |
| room | no call; a `<ground mode="room">` from the model is unserved and its rate is printed | none | direct rows (476 in square metres, 95 in square feet) |

### 1.2 The three choices, with evidence
- **Own pose head or G3T for camera calls: G3T.** With the own pose head, step 544 scores 47.2 / 42.7 / 75.3 on dev-S1 displacement, rotation and movement direction (0.605 m, 17.9 deg, 75.3% per call; Orchard 170631, `DD/H1_GT_HEAD_ROUTING_SFT_20261116.md` Status). With G3T in the call the same checkpoint scores 82.3 / 94.7 / 75.7 on the same types (job 170056, `DD/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md` as cited in the H1 record). The own head trails by 35 and 52 points on two types (point differences, unpaired), far outside the registered M2 bar (own minus tower lower bound above -5). SFT will not close that gap: the Qwen ViT gives chance-level pose to a probe (58-77 deg), the LM carrier stops at 15-25 deg, and rooms, resolution, loss and partner frames did not move it, while G3T's decoded pose is 3.0-6.3 deg on the same rows (`DD/POSE_PLATEAU_DIAGNOSIS_20261109.md`, Test 2). H1-1 confirms it on training scenes: own-valued faithful camera rows carry an answer that differs from GT beyond tolerance on 36.7% of rows over steps 1-50, and on 25-30% per step after step 30 (`EV/cont_ops/20261117T1345Z_RESULT_h1_1_step50_stop_rule_TRIGGERED.md`).
- **Scale: fixed math on the own depth head now; the learned head must beat it.** The rule is `tower_scale_rule.json` in the sealed tree: median(own depth / G3T depth) over a 51 x 51 grid on the 32 anchors, on points whose G3T confidence exceeds the clip median and whose own depth lies in 0.1-10 m. It is the scale in force behind job 170056 (`DD/ARCHITECTURE_CURRENT.md` section 2; `EV/b04_e2ehook/STATUS.md` line 24) and, on an earlier checkpoint, gave 14.0% centre error against 45.5% for the own pose head and 8.9% for an oracle scale (`DD/SOTA_PLAN_20261109.md` section 1). b04's learned head is a ridge with 31 parameters on 29 tower features fitted on 233 K1 captures; it misses on K1 distance (61.3 against 62.9, -1.6 [-4.1, +1.1]) and loses 9.3 [-14.1, -5.0] on dev-S1 displacement (`DD/E2E_READER_B04_20261116.md`; `EV/b04_e2ehook/STATUS.md` lines 9-12).
  **What the scale head needs:** (a) fit and serving on the same tower layout (it never saw G3T run on the 32 viewpoints); (b) a trajectory-scale target, the least-squares ratio of GT to G3T translations per clip, because displacement is where it lost; (c) clips in the tens of thousands from the leg's pose rows (194,987 rows carry `gt_pose9`), which needs G3T outputs on those clips; (d) a residual form, log s = log s_rule + f(features) with f zero at init, so it equals the rule until it learns; (e) inputs from inside the checkpoint only: G3T camera tokens, the own depth grid, and the pose head's scale token, which the new tree already trains (weight 1.0, a guess; `W/out/BUILD7_REPORT.md` lines 21, 97-99); (f) a bar priced on CPU with calls fixed: dev-S1 displacement lower bound above 0 against the rule and K1 held-out distance at least the rule's (`tests/price_devs1.py` in b04 reproduces 634 of 634 job scores).
- **Own depth or tower depth for lifting: tower depth times the scale.** On K1 held-out with GT masks, G3T depth x own-depth scale with `bestspread` scores 65.7 against 66.3 for the deployed path (-0.6 [-3.1, +1.5]; b04 record). The own arm (own depth and own pose lifting) gives a gap error of 0.726 m (relative 0.436) and a `not seen` response on 42% of reads (Orchard 170706), against 14 of 98 boxes lost in b04's interim tower-arm read (51 keys, before `bestspread`; unpaired). The own depth head enters only through the median, where one clip-level number absorbs its per-pixel error. Unverified: the per-scene depth-adoption outcome behind the rule file; the tower-arm read of section 4 settles the choice on paired items.

### 1.3 Statuses and how the own heads keep training
- **Statuses.** The 1,532 recovery rows all print `A: not seen`, 769 on the first operand and 763 on the second (my count, `W/work/rows_slices/slices_final/a0_recovery.jsonl`). The reader can also print `box unavailable` when fewer than four points survive the cut (b04 record, "Shipped bestspread"), and error codes. Either the reader prints `not seen` for every empty result, or the rows cover each status; brief 03 asks the rows lane for `box unavailable` rows, and lane notseen_diag supplies the real status census.
- **Own heads train as auxiliaries and are read beside the tower.** The pose stream (64 rows per step, weight 1.5), depth (0.25), gravity (1.0) and, on the new tree, the scale token keep their losses. S2 (pose targets on camera routing rows) rides only if H1-1's m100 read shows it helps (2.3). At every milestone the evaluator reads the camera types on the own arm (about 1 H100-hour) beside the tower arm. A type moves to its own head when own minus tower has a lower bound above -5 on dev-S1 at two consecutive milestones, the H1 record's M2 bar.

### 1.4 What "its own heads" may claim, and what needs the user's word
Under the rulings (memory notes `no-harness-end-to-end`, `user-ruling-sam3-tower-own-encoder-20261110`), every response must depend only on weights in the checkpoint plus fixed math, in one generate call; frozen towers shipped in the checkpoint count, SAM 3 with the same standing as the geometry tower. The artifact above may claim: the model's chain of thought calls perception heads inside its own checkpoint and answers from what they print. It may claim as trained by us the routing policy, the depth head that sets metric scale, the gravity head, and the selector head. It may not claim that a student-trained pose head answers camera questions, or that grounding uses the student's own encoder.

| | Needs the user's word | Default in force |
|---|---|---|
| U1 | Camera pose comes from a frozen public tower's camera head, not from a head we trained | Proceed (the standing form admits shipped towers); every read prints the own arm beside it |
| U2 | The 11-16 ruling names a "learned scale"; the scale here is fixed math between the own depth head and the tower, with its three constants held as registered buffers | Fixed math now, because the learned head lost 9.3 points; the residual head replaces it when it passes its bar |
| U3 | Size: the checkpoint is the 9B model plus about 2B of frozen towers (SAM 3 0.85B, `DD/ARCHITECTURE_CURRENT.md`; G3T about 1.2B, a guess) | Report "9B with frozen perception towers, about 11B in all", as GeoWeaver-10B reports itself |
| U4 | Room direct rows are one line that restates the question, then the number (`a0_room.jsonl`) | Keep them: the trace ruling admits them and no room tool clears its bar (DA3 +16.67 held-out, 0.5 short; `DD/GEO_TOWERS_K1_PRICING_20261116.md`) |

## 2. The leg

### 2.1 Choice
| Candidate | Verdict | Reason |
|---|---|---|
| **R1: A0's routing repairs plus store v6, init step 544, GT-valued responses** | **Recommended** | Every row family exists and is reviewed; it targets the measured failures of the claimed read (no recovery, no unit conversion, unserved room call) and the two largest measured row gaps (VSTI relative types, facing away) |
| A2 = R1 plus GF-1 | Runner-up; enters at R1's first passing boundary | Its inputs do not exist: no dense frame is fetched, the tower cache (245-280 GB) is not built, the step cost is unmeasured and the BF16 cache fails gradient parity (`EV/b06_a2dense/STATUS.md`). Its schedule trains adapters only for 400 steps (tree default), so every read of the repairs would wait 400 steps. Its gain (+1 to +3 VSI) is a guess on the secondary benchmark |
| H1-1 continued to m200 | Rejected | Its registered stop rule fired at step 50, so the leg ends at m100 by registration. S1's premise is also gone: step 544 already follows printed values on 100% of perturbed camera reads, trained on GT rows alone (H1 record, Status) |
| H1-2 (head routes for relative distance, size, counting) | Not launchable | Its rows wait on a response cache of 28,711 training items that needs 20-32 A6000-hours (`EV/b08_headrows/STATUS.md`), and with deployed masks the head form loses 4 to 14 points on these types (`DD/NEXT_QUEUE_20261116.md` section 4). Size alone becomes a candidate if R1's step-200 read repeats D0's size loss |
| A0 alone on its 11-15 mix | Superseded by R1 | Same leg without the VSTI relative rows, the away wording and the b12 rows |

R1 follows the user's rules: it stacks every ready lever, runs no control and no replicate, and reads within hours. GF-1 is left out because it is not ready and would delay the read, not because it needs an ablation.

### 2.2 The five lines
1. **Question.** After SFT on GT traces that add recovery, unit and direct-room rows and the missing direct families, does one checkpoint place its calls, terminate, and answer from the responses when every call is served inside the checkpoint, without losing direct types?
2. **The one difference from its comparison.** The comparison is step 544 read by the same reader build on the same items; the difference is R1's training. The rows are a bundle by the stack-first rule.
3. **Confounds.** Warm start with a fresh optimizer and a restarted schedule (D0's m100 carried a dip). Six row changes at once. D0's size loss has an unverified cause, so v6's first-seen repair may not remove it. The parents of step 544 saw dev-S1's scenes, which favours direct answers there; only R0-dev is unexposed. Recovery rows print simulated statuses at about half the reader's miss rate. G3T and SAM 3 have unaudited pretraining scenes. If vehicle P launches, the routing stream lacks the repairs until step 200. S2, if on.
4. **Pre-registered rule (step 200, dev-S1 and R0-dev, paired against step 544, bootstrap over rooms, 10,000 draws, seed 20261115).** Stop and export if: (a) any of the seven direct types has its paired interval wholly below zero (D0's F1; per-type half-width 6 to 8 points at 150 items, from `DD/D0_M200_READ_20261116.md`); or (b) the mean of the seven differences is below -1.0 (the init rule's floor; its noise is about 1 point, an estimate); or (c) any camera type falls with an interval wholly below zero on the tower arm, or any of the 450 camera items draws no call. Repair marks, read at step 200 and binding at step 400: distance reads that hit the call cap at most 10% (step 544: 22% of baseline reads; a binomial standard error of about 2 points at 150 items); room call rate at most 25% at step 200 and 5% at step 400 (step 544: 100%); non-metre distance answers converted on at least 80% (step 544: 45 of 146). A mark that fails at step 400 stops the leg.
5. **Decision it changes.** Pass: R1 runs to step 1,000, the export the init rule's tests select gets the leg's one official read through a reader that passes EAT-1, and it becomes the base for GF-1 and RL. F1 fails on size only: size moves to a head route (H1-2, size first) before any further step. A repair mark fails: the rows lane rebuilds that family (share, real statuses) and the leg restarts from its last passing export.

### 2.3 Decision table keyed on H1-1's m100 read
The leg choice does not depend on this read. It sets S2 and confirms the serving default.

| Measurement | Outcome | Action for R1 |
|---|---|---|
| Stop-rule share, steps 1-50 | 0.367 > 0.35, known (per step 0.25-0.30 after step 30) | No own-valued camera rows (`max_own_probability 0`); the own pose head prints no training response; no H1-1 m200 |
| M2, own arm, H1-1 m100 against step 544 (0.605 m, 17.9 deg, 75.3%) and, if ORCH's condition fires, against D0 m100 | Per-call error falls with a paired interval that excludes zero on displacement or rotation, none rises | S2 on |
| | No interval excludes zero | S2 off: no evidence, and it adds about 48 pose-supervised rows per step |
| | Any error rises with an interval that excludes zero | S2 off |
| | Own minus tower (82.3 / 94.7 / 75.7) has a lower bound above -5 on a type | That type becomes a take-over candidate; it needs the paired tower-arm read (section 4) and a second milestone before serving changes |
| Harm on direct types (h1read, H1-1 m100 against D0 m100, F1 list) | No interval wholly below zero | As the M2 rows say |
| | Any interval wholly below zero | S2 off whatever M2 shows; the pose weights stay at D0's |
| M1 and M3 at m100 | M1 passes and follow is at least 0.80 | Nothing |
| | Either fails where step 544 passed | Recorded as a cost of own-valued rows; R1 unchanged |

### 2.4 Cost, first read, expected effect
- **GPU-hours.** About 153 H100-hours for 1,000 steps (D0 ran 133-140 s per step, H1-1 145 s with the S1 readout; `EV/cont_ops/STATUS.md`), plus about 11 per allocation for staging and preparation (170710: running 08:31Z, step 1 at 11:13Z), plus about 20 for reads. The first 200 steps cost about 42 with staging.
- **First decisive read.** Step 1 at T+2.7 h, the m100 export at T+6.6 h (reported, decides nothing), the m200 export at T+10.5 h, the verdict at about T+13 h after two reads in the single job place (h1read direct types about 0.75 H100-hours from job 170320's 44 minutes; the evaluator's routed types 1 to 5).
- **Expected effect** (official reads come only for the selected export; these are the planning numbers):

| Benchmark | Step 544 | R1, expected | Basis |
|---|---|---|---|
| VSTI-450 primary | 73.89 [71.04, 76.79], camera calls served by G3T | 79 to 83 | The six relative types have zero training rows and copy VSI templates; restoring them to P1 m200's level is worth +8.9 (`DD/VSTI_RELATIVE_TYPES_DIAGNOSIS_20261116.md`); 11,926 GT rows are in v6. Discounted to +5 to +9. Closed models: 73.73 and 72.65 |
| ReVSI, seven categories | about 63 with harness-served stand-ins (`DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md` 4.1); about 53 through the claimed reader (guess: room unserved at MRA 0.14 and distance at 0.20 on dev-S1) | 66 to 69 through the claimed reader | Facing: away 78 / 84 / 80 against 38 / 20 / 6 at D0 m200, but 34 of 49 on ReVSI's own wording, which no row trains (`DD/FACING_AWAY_DIAGNOSIS_20261116.md`); with the wording rows direction rises from 51.2 toward 79-87, +3.5 to +5 ReVSI points. Direct room restores about 5.6 against an unserved call ((53 - 14) x 0.143). Recovery bounds the distance loss. Closed models 86.6 and 89.8: out of this leg's reach |
| VSI-Bench, eight tasks | about 67.1 (estimate, two tasks unread) | 67.5 to 68.5 | Trace repairs +0.5 to +1.5 (guess); D0 m200 on dev-S1: counting +5.5 [-2.8, +13.0], route +5.3 [-1.3, +12.3], size -9.5 [-15.7, -3.6] |

## 3. Readiness

### 3.1 Table
"P" = vehicle P, the deployment that runs H1-1 (sealed tree b01ce449 plus the H1 patches; Orchard `okh7/x_3fdda0fb`, job 170710). "N" = vehicle N, the new tree at build 9. A2 needs everything N needs plus the rows marked A2. Hours are work left, guesses unless a source is given.

| Prerequisite | Status | Evidence | Owner | Hours left | Blocked by |
|---|---|---|---|---|---|
| Tree seal and reviews | P: sealed, reviewed, training since 11:13Z (step 52 at 13:40Z); its in-process stop and m100 export are due about 15:35Z and are the last unproven part of the path. N: build 8 sealed (bdec5e50); build 9 running, one review owed; build 10 is not needed to train (its gate is byte parity of printed numbers, so rows do not change; it serves the reader) | `EV/h1_headsft/REVIEW_VERDICT_H1KIT.md`; `EV/cont_ops/STATUS.md`; `EV/tree_rebuild/STATUS.md` | tree_rebuild | P 0; N 1.5 build + 2 review | build 9's final pass |
| 14 evidence records | P: carried inside kit 07ca49df. N: all 14 missing; both kits refuse at `init_m544`; no lane owns them | `W/out/RECORDS_TO_REGENERATE.md`; `W/work/build9/CARRIED_BLOCKERS.json` | none (brief 02) | P 0; N 6 to 10 | parent receipts, some lost with trinity-2-18; five records describe parts the claimed reader removes |
| Rows store and admission | v6 admitted and mirrored (0608dd98, 195,471 rows). Owed: v7 = v6 + direct room (476 + 95) + away rows in ReVSI's wording; upload to Orchard; kit binding. P: whether the sealed VQA admission takes the new families is untested. N: binding D3 missing; the mix table has no cell for VSTI relative or first-seen rows | `DD/A2_FIRSTSEEN_ROWS_20261116.md`; `/scratch/jjyeung/orch_n30/rows_a2/out/KIT_INPUTS_A0_A2.md`; `W/out/MIX_A0.md` | rows lane successor (brief 03), tree_rebuild | 3 to 4 | a rows lane (rows_a2 has exited) |
| Grammar validator | Sealed (a41ba191); 0 failures on all 195,471 v6 rows; rerun on v7 | `rows_a2/out/a2_vqa_v6/VALIDATOR_FULL.json` | rows lane | 0.5 | v7 |
| Five rows per type | Partial: this lane read 3 recovery, 3 unit, 2 room rows and 1 to 3 rows of eleven VQA types from the local files; all derive or locate as the ruling asks, and the room rows are one restating line. The full sheet from the bound Orchard files is owed | section 5; `L/work/v6_examples.json` | operator (brief 04), then orchestrator and user | 1 | staging |
| Init export | Decided: step 544 (1d6eeb28). D0 ended under its stop rule, and an export whose read returned STOP is not a candidate | `DD/NEXT_LEG_INIT_RULE_20261116.md` items 1, 7; `DD/D0_ENDED_20261116.md` | orchestrator | 0 | none |
| Dense frames (A2) | Not fetched: three Orchard jobs staged, none submitted; 11,410 new decodes and 46,424 ARKit range reads | `EV/b06_a2dense/STATUS.md` | none (b06 rotated) | 6 to 10 | the single job place |
| Tower cache (A2) | Not built: 245 to 280 GB at FP32; BF16 cache fails gradient parity; step cost unmeasured | same | none | 6 to 12, 1 H100 | dense frames |
| Scale-head loss | N: built (scale token, weight 1.0 guess), unmeasured; it does not serve. P: absent, and not needed, because the scale that serves is fixed math | `W/out/BUILD7_REPORT.md` lines 21, 97-99 | tree_rebuild; brief 05 for the residual head | 0 to train | none |
| Recovery rows from real failures | 1,532 rows, all simulated `not seen`; no `box unavailable` row; share 2.39 per step against a reader that misses about one ground in four | `W/work/build9/proofs/row_counts/RESULT.json` (per tree STATUS); section 1.3 | rows lane (brief 03), notseen_diag | 3 | notseen_diag's status census (due 16:41Z) |
| Unit rows | 10,945 admitted, 2.87 per step, one written conversion line; read by this lane | `W/work/rows_slices/slices_final/a0_units.jsonl` | done for N; rows_r1 for P | 0 | P (sealed b01ce449, r1_ops 14:42Z): 216 of 2,000 slice rows admitted; 1,784 fail `ground_rows.py:92` because the trace answer (2-dp metres x 3.28084) differs from round(GT_ft, 2); recovery rows: 0 of 1,532 admitted (`ground_rows.py:82`, not_seen) |
| Room | 476 direct rows plus 95 in square feet, 1.39 per step in the plan; R1 asks 2.0. P must also drop the 581 room programs from its routing selection, a pin change | `a0_room.jsonl`; `rows_a2/out/a2_room_ft2_v1/` | rows lane; brief 01 | 1 | none |
| Orchard packaging | P: exists; the change is the VQA binding, `max_own_probability 0`, S2 and the room selection. N: never derived; staging entries D1 to D3 open | `C/h1/REPORT.md`; `KIT_INPUTS_A0_A2.md` | cont_ops (brief 04) with one Codex build (brief 01) | P 3 to 5; N 10 to 16 | store upload; for N the records and the frame-host job |
| Production-config CPU proof, real node | P: tool exists and passed for H1-1 (job 170669, 2.6 h); rerun owed on the new config. N: no proof tool; the frame-host CPU job has never run | `EV/cont_ops/20261117T0513Z_RESULT_h1_1_proof_170669_running.md`; `C/h1/build/a_8c74b291.sh` | cont_ops | P 2.6 per attempt; N 8 or more | the single job place |
| Registration card | Not written; section 2.2 is its text | this record | orchestrator | 0.5 | none |
| Read kits and evaluator | h1read fix 2 in use; the H1 evaluator is being re-pinned to take any export (ORCH 1356Z, review owed); official kits R and N are GO; no reader passes EAT-1 (b04's fails A3 and A4 until build 10) | `EV/cont_ops/20261117T1356Z_ORCH_ANSWER_h1_evaluator_repin_GO.md`; `DD/EAT1_ACCEPTANCE_TEST_20261116.md` | cont_ops, tree_rebuild | 2 to 8 | build 10 for the claim only |

### 3.2 Critical path
The slot opens when main returns advanced: about 16:15Z on 11-18 by main's 12:59Z note ("about a day"), or as early as about 02:15Z if its 13:29Z note holds (8 to 10 hours of jobs). Plan for the early time.

| UTC (PT) | Step | Owner |
|---|---|---|
| 14:30 (06:30) | Dispatch briefs 01, 03 and 04; hand brief 02 to the tree lane for after build 9 | orchestrator |
| 15:30 (07:30) | Build 9 ends (guess); its one review starts | tree_rebuild |
| 16:41 (08:41) | notseen_diag reports the status census; the rows lane folds it into v7 | rows lane |
| 17:30 (09:30) | v7 store built and validated; its refute review ends 19:00 | rows lane |
| 18:00 (10:00) | H1-1 m100 reads land; S2 is set from table 2.3 | orchestrator |
| 18:30 (10:30) | P packet passes its local gates with the production config; store uploaded through the governor | brief 01, cont_ops |
| 19:30 (11:30) | Production proof 1 of P submitted (CPU job, takes the job place); verdict about 22:10 | cont_ops |
| 22:10-02:00 | One fix round and proof 2 if needed (3.5 h per round) | cont_ops |
| slot - 2 h | Vehicle gate: N launches only if its seal, review, records, frame-host job and production proof have all passed; otherwise P, provided it admits recovery and unit rows or the hard-requirement ruling has been amended (Answer 3); otherwise the slot waits for N | orchestrator |
| slot | Submit; first-steps RESULT at T+2.7 h; m100 at T+6.6 h; m200 at T+10.5 h | cont_ops |

N's own path (build 9 review, brief 02's build and review, the frame-host job, packaging, two proofs) ends near 12:00Z on 11-18 at best (guess), so N can make the late slot and not the early one. What must start now: brief 01 (P packet), brief 03 (rows v7), brief 04 (operator), and the request to main in 3.3.

### 3.3 How the packaging is rehearsed before the slot
H1-1 lost about nine hours to five defects that fixture rehearsals could not see: the disk plan against the recipe's milestones (job 170527), the routing-selection pin, a pre-made `/tmp/jjyeung` (proof 170656), a hard-coded `/usr/bin/bwrap` (170662), and directory modes (`EV/cont_ops/STATUS.md`, cont_ops9 entries). R1 rehearses as follows.
1. **The rehearsal is the production path.** One CPU job on an Orchard compute node runs the certified deployment root, the exact config identity, `jb.sh`'s cold-start prefix, staging, and `s1_admission.admit(prepare_only=True)` to the first-batch boundary of every rank. `C/h1/build/a_8c74b291.sh` does this and is the template.
2. **It starts from an empty root** that holds only what staging creates, with a fresh per-job `/tmp`.
3. **Each of the five defect classes has its own assertion** in the proof receipt: the disk plan equals `checkpoint_space.plan` for the recipe's milestones and export count; the routing selection is regenerated and either equals the pinned bytes or carries a reviewed new pin; no path outside the job's `/tmp` is assumed to exist; every binary is resolved and hashed at run time; every created directory is 0700.
4. **Any change reruns the whole proof.** A new S2 value, store sha or selection pin changes the config identity, and the proof binds that identity.
5. **The first proof is submitted at least eight hours before the earliest slot,** so two fix rounds fit.
6. **The proof needs the job place.** Ask main, through the orchestrator, whether one CPU-only job (48 cores, 800 GB node-local disk, 4 h limit) may run beside the one GPU read. Default if unanswered: it takes its turn, ahead of every read except the two H1-1 m100 reads.
7. **No GPU step can be rehearsed before the slot,** so the allocation's first four steps are the smoke test, with `early_loss_check_d0.py` and a first-steps RESULT, as for 170710.

## 4. The single Orchard job place until the slot
In force: one distillation job on Orchard at a time, and main has priority on every GPU (ORCH 1355Z item 5). Queued by ORCH 1355Z and 1356Z: job 170777, then the two H1-1 m100 reads (h1read for harm, the evaluator's camera read for M2). After them:

| Rank | Job | Decision it changes | Hours |
|---|---|---|---|
| 1 | Production CPU proof of R1 (P first, N when its kit exists) | Whether R1 submits at the slot; nothing else here gates a 150-hour launch | 0 GPU; 2.6 wall per attempt |
| 2 | Tower-arm read of step 544 on the 636 dev-S1 routed items through b04's reader (G3T pose and depth, own-depth scale, own gravity, `bestspread`), paired with H1-0's own arm | Fixes section 1 by measurement: own minus tower per camera type on one reader build, the `not seen` rate under tower lifting against 42%, and so the recovery share in R1's rows | 2 to 3 H100 (job 170056 took about 1.3 per arm; SAM 3 in the call adds 2 to 7 s per name) |
| 3 | EAT-1 on GPU with b04's reader on build 10, 200 call items from dev-S1 and R0-dev (no official item) | Whether any read may be claimed, and which clause still fails | about 3.5 H100 (`DD/EAT1_ACCEPTANCE_TEST_20261116.md`); after build 10 and its review |
| 4 | Official ReVSI, VSTI and VSI-Bench reads of step 544 through the reader that passed rank 3 | The first claimed seven-category and eight-task numbers, which are the baseline R1's official read is compared with; whether distance stays routed (direct at the next seal if native distance is at or below 53.4, `DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md` E4) | at least 2.3 (ReVSI) and 6.4 (VSI-Bench) H100 (`DD/OFFICIAL_READ_KIT_B07_20261116.md`) |
| 5 | GF-1 inputs: the three dense-frame CPU jobs, then the step-cost packet | Whether GF-1 can enter at R1's step-200 or step-400 boundary, cached or online | 6 to 10 wall on CPU, then about 1 H100 |
| 6 | Residual scale head: one G3T pass on K1 at the serving layout, then CPU fit and CPU pricing | U2: whether the scale that serves is learned | about 1 H100, the rest CPU (brief 05) |
| 7 | Own grounding head, pilot 2 resumed from its update-200 checkpoint | Whether branch O continues (bar at update 600), which decides H1-2's grounding source | about 1 H100 after about 3 h of packaging for Orchard |
| 8 | RL sampler dry run on R0-rl | Seconds per rollout and gate rate before any RL round | 1 H100; after R1's step-200 read passes |
| not run | H1-0's ReVSI part on the own arm | None: the own arm is not the claimed configuration, and the leg's one official read belongs to rank 4 | |
| conditional | D0 m100 evaluator camera read | The M2 control, only under ORCH 1355Z item 4 | about 1 H100 |

Once R1 trains, its milestone reads take the place ahead of ranks 3 to 8.

## 5. Pre-launch checklist for R1 (memory note `prelaunch-thinking-checklist`)
"Unverified" marks what this lane could not check.
1. **Problem fixed.** (a) Distance reads loop after `not seen` (42% of reads, 22% capped; H1-0): recovery rows. (b) Non-metre answers stay in metres (101 of 146): unit rows. (c) The room call is unserved and 75% of reads never terminate: direct room rows, room programs removed. (d) VSTI relative types copy VSI templates (0 rows): 11,926 rows. (e) ReVSI away at 14.0: facing twins plus away rows in ReVSI's wording. (f) D0's size loss: first-seen repairs; cause unverified. The camera heads' accuracy is fixed by serving, not by this leg. Expected gains: section 2.4.
2. **Data mix per step** (proposal; the A0 plan of `W/out/MIX_A0.md` with sixteen VQA slots moved from direction and facing; post-filter populations and repeats at most 4 are unverified).

| Stream | Cells (rows per step) |
|---|---|
| VQA 128 | direction 20.08; facing pairs 18.17; relative distance 22.74; object size 10.81; counting 10.87; totals 3.39; appearance order 14.42; first-seen frame 2.00; 3D box 1.82; room direct 2.00; route planning 9.70; VSTI relative 12.00 (2.00 for each of six types) |
| Routing 64 | camera displacement 16.55; movement direction 14.39; rotation 11.36; absolute distance 14.83; recovery 4.00; units 2.87 |
| Pose 64, pointing 32 | unchanged |

   Reasons: each VSTI type gets about 2,000 draws in 1,000 steps, the diagnosis's dose; counting and totals rise from 10.3 to 14.3 because counting holds the largest gap to the open bar (2.66 VSI points, `DD/NEXT_QUEUE_20261116.md` Answer 1) and b12 added 10,177 rows; direction and facing fall from 54.3 to 38.3, still the largest cell (D0 fixed facing in 200 steps at 29.4); recovery rises to 4.0 (2.6 to 2.7 repeats of the 1,532 rows, 1,458 eligible) toward the reader's miss rate. No answer-only row: the room rows come closest (U4). Dataset coverage: unverified; the room rows I sampled are ScanNet and ScanNet++ only, and ARKitScenes is about half of VSI-Bench.
3. **Traces.** Read by this lane from the files the kits would bind: recovery (3 rows; two box calls, `not seen`, "I do not call it again", two Locate lines, the answer), units (3; the printed metres, one line such as "1.94 x 3.28084 = 6.36", the answer), room (2), and from v6 one to three rows each of camera-object relative distance v1 and v3, object-object near/far and up/down, counting, size, direction hard, relative distance, route planning, appearance order and first-seen frame. None states an unprinted measurement; every answer follows from the trace or is a direct estimate after Locate lines. Owed: five rows per type, read by the orchestrator and the user, from `rows.sqlite` of v7 and the four routing slices as staged on Orchard (brief 04 writes the sheet); the away rows in ReVSI's wording and the `box unavailable` rows do not exist yet; camera rows were not read here (unchanged from the sealed leg).
4. **Recipe.** Init step 544 (init rule). 32 frames, duplicate layout, markers on, as trained. World 4, 288 rows per step, D0's recipe and 1,000-step schedule, milestones 100, 200, 400, 600, 800, 1,000, `stop_after_step` as a parameter. `max_own_probability 0`; S2 by table 2.3. Reads: dev-S1 and R0-dev only until the selected export; evaluation layout equal to training.
5. **Cost and readout.** Section 2.4: about 42 H100-hours to the decisive read at step 200 (T+13 h), about 185 to step 1,000 with reads; stop rule 2.2 item 4.

## Options rejected, and why
- **A learned scale head as the default** (the orchestrator's 13:41Z reading): the only one built loses 9.3 points of displacement to the fixed-math rule, and the rule is what the lineage's camera numbers were measured with.
- **A2 next** (rank 1 of `DD/NEXT_QUEUE_20261116.md`): section 2.1. Its rank assumed a kit that D0's end would wait for; D0 ended a day early and the GF-1 inputs were never fetched.
- **Waiting for vehicle N alone:** it has never run on Orchard, and a seven-field config change cost H1-1 nine hours there.
- **Build 10 before training:** its gate is byte parity, so it cannot change a row; it gates the claim, not the launch.
- **Own-valued or tower-valued camera rows (S1 in any form):** usage is already 100% from GT rows, and faithful rows on a weak head teach wrong answers (36.7%).
- **A size head route inside R1:** the both-path ruling wants hindsight-assigned rows, which need the response cache; GT-valued head rows without it would break that ruling. It is the registered consequence of a size failure instead.
- **Stopping the reads to free the job place:** the two H1-1 m100 reads finish the user's near-term question for the leg that just ran.

## What might not work, and how we would notice
- **Size falls again.** v6's size rows read "find the X, first seen in frame N ... I estimate it from the frames" and then the number, D0's form plus a frame; the sealed leg's rows stated a measurement. If the loss came from the form, the repair does not remove it. Sign: object size at m100 and m200 against step 544; rule 2.2 stops the leg and size moves to a head route. My estimate that it recurs: about one in two (guess).
- **The sealed tree refuses the new families,** so P carries only part of R1. Brief 01's first gate shows it within two hours on CPU; whether P then launches with what it admits is the orchestrator's ruling (Answer 3), and the report names what is missing.
- **Recovery rows teach a direct estimate the lineage never trained** (no direct distance rows since the sealed leg), so answers after `not seen` may be poor. Sign: MRA on recovered reads at m200 against the constant; the lever is then grounding recall, not rows.
- **The room call survives 200 steps.** Sign: the room call rate mark; it binds at step 400.
- **The fixed-math scale fails EAT-1's A3 scan** even with its constants as buffers. Sign: rank 3; fallback: the residual head, or the pose head's scale token if it prices within the rule.
- **The slot opens early and no proof has passed.** Then the four H100 wait; nothing else here is worth 4 H100 unproven. Sign: the vehicle gate.
- **R0-dev has no VSTI-style or camera item** (unverified from `DD/R0_RESERVE_SCENES_20261116.md`), so the VSTI relative repair has no mid-leg read. Brief 03 asks for a dev set on R0-dev rooms.

## Tests that would settle it
1. Brief 01's CPU gate: which R1 families the proven deployment admits.
2. The production proof of the chosen vehicle on a compute node.
3. The tower-arm read of step 544 (rank 2): section 1's serving choices on paired items.
4. R1's step-200 read under rule 2.2.
5. EAT-1 on GPU after build 10 (rank 3): U2 and the claim.

## Status
ACCEPTED by the orchestrator 2026-11-17T14:15Z (events/next_leg/20261117T1415Z_ORCH_RULING_r1_accepted.md: recovery and unit rows bind from step 200 on; brief 02 before build 10; room rows get a qualitative trace; U1-U4 asked once, defaults in force). Lanes r1_ops (briefs 01, 04) and rows_r1 (brief 03) started 14:15Z on trinity-1-3. DECIDED by lane next_leg. Nothing was launched, dispatched or changed outside `L` and this record. Briefs, not dispatched: `EV/next_leg/briefs/` (start now: 01 P packet, 03 rows v7, 04 operator; after build 9: 02 N kit closure; when the job place allows: 05 tower-arm read; when a builder is free: 06 residual scale head). Open for the orchestrator: the amendment of Answer 3, the order of brief 02 against build 10, and the request to main in 3.3 item 6. Open for the user: U1 to U4, each with its default in force.
