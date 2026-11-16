# Review verdict: A0 design after the native read (review_a0d, trinity-3-30, 2026-11-16)

Reviewed: `DD/A0_AFTER_NATIVE_READ_DESIGN_20261116.md` (sha256 6ac3e2f8…) and its RESULT event 0554Z. DD = `/data2/jjyeung/agent_project_data/distill_design/`, EV = `.../orch_n30/events/`. Read-only; no GPU, Git, Orchard or deletion. Second family: Codex review (gpt-6-astra, high, read-only, 123 s), receipt `agent/scratch/codex_runs/20261116T061609Z_review_a0d_o1t2/`, copy `trinity-3-30:/scratch/jjyeung/orch_n30/review_a0d/codex/CODEX_FINAL_O1_T2.md`.

## Verdicts
- **O1(a), D1 takes route without the 640-item extension: ACT WITH CHANGES.** The decision does not change. The registered rule yields route either way, and the 640 items would buy no information. But the amendment must say D1 is withdrawn, not "taken at its default". It must also drop E4 as a route decider (changes 1–3 below).
- **O1(b), serve room calls for step 544 and D0: ACT WITH CHANGES.** Serving is the right reader for checkpoints that call the tool on every item. But it reverses a registered default after the served and unserved numbers were seen, so it has to be labelled as a post-read deviation (changes 4–6).
- **T2, init from the newest passing D0 export: ACT WITH CHANGES.** The rule can be bound before D0's reads exist, but as written it leaves the choice open, and it lets a checkpoint that failed F2 count as passing (changes 7–11).

## Point 4 (O1): what D1 and D2 register, and what an honest amendment discloses
Registered (`DD/REFREEZE_PREREGISTRATION_20261115.md`, sha256 ca4a4fbe…; .json 6375d400…, `choices` D1/D2):
- **Arms:** route = the native routed read, with the export's calls served by the **P1–P6 backend**; direct = the export's direct reader with calls unserved.
- **Rule:** route if the paired 95% lower bound is above 0; direct if the upper bound is below 0; otherwise undecided.
- **D1:** all 790 dev-S1 distance items in 59 rooms. If undecided, the default is route, with "the claim of a routing gain withheld".
- **D2:** all 36 room items in 9 rooms. If undecided, the default is "direct (calls unserved); report room as not established".
- **Order:** P7 runs D1 and D2 after P1–P6, and P8 freezes.
- **Amendments:** a change "needs a new dated pre-registration written before the data it would use is read". Amendments 1 and 2 were written before any K1 score existed and changed no decision rule. Amendment 3 differs in kind, because it is written after the 150 distance and 36 room items were read.

Findings:
- **The read was not P7.** The 0554Z native read used the backend before the refit, not the P1–P6 winners, and 50,000 bootstrap draws instead of the registered 10,000 (`DD/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`, Evidence). Its numbers therefore cannot stand in for D1 or D2 (Codex says the same).
- **D1 lands on route whatever happens.** On the 150 items, the registered comparison (native minus unserved direct) gives +11.667 [−1.229, +25.529], which is undecided and so defaults to route. The capped_zeroed sensitivity gives +25.733 [+16.474, +35.723]. An upper bound below 0 on 790 items is implausible.
  - This is my judgement. Codex calls the full-790 outcome unverified and treats the change as "data-informed, favouring routing".
  - Either way, O1(a) gives up only a meaningless "beats its own unserved reader" claim, and the default already withholds the gain claim.
- **D2 changes its outcome.** The registered comparison gives +21.944 [−1.765, +44.474], which is undecided and defaults to direct with calls unserved. O1(b) replaces that with served room calls. The amendment was written after seeing served 53.889 against unserved 31.944, and it raises the official number.
  - Its justification is real. Unserved calls end in forced closes (28 of 36), so the default measures serving failure, not a direct answer.
- **Scope grows.** D1 and D2 were registered for the step-544 export only. O1(b) adds D0 checkpoints (Codex).
- **"The decisive distance number is E4" breaks the registration (both reviewers).** E4's rule is "official native distance ≤ 53.4 → distance goes direct at the next seal" (design §5 E4, §8). That uses benchmark scores to select a route. The registration says dev-S1 decides route or direct, and that benchmark items, answers and scores are forbidden (Data, "Forbidden").
- **The room rule is benchmark-selected.** Serving room calls officially uses room rule rv, which was chosen on 88 VSI-Bench ScanNet items. C4 keeps rv unless a K1 challenger beats it (POLICY_AUDIT #7; pre-reg C4).
- **Size of the D2 effect.** On dev-S1 the measured served-minus-unserved gap is 21.9 task points, about 2.7 VSI points. "3 to 4" holds only if official served room reaches the external 63.4 to 66.5 (2.7 to 4.3 VSI points).

Changes for amendment 3:
1. State that D1 and D2 are withdrawn for the step-544 export: P7 is not run as registered. Give the reason: the registered direct arm leaves calls unserved, so it measures serving, not a direct answer.
2. State that amendment 3 was written after reading the 150-item and 36-item native read. Report all of its numbers:
   - native minus unserved, primary and capped_zeroed;
   - native minus parent, all units and by unit: distance −9.000 [−17.031, +0.234], metres +0.930, non-metre −12.991, room −1.667;
   - what each registered default would have produced.
3. Delete E4 as a decider of the next seal's distance form. Bind one of two instead, before any read:
   - (i) a clean decider: a registered dev-S1 read on metre items only, all metre items of the 790, native against the parent. Disclose that restricting to metres is a post-read subset, justified by verified benchmark units, and that parent exposure biases it against routing;
   - (ii) or keep distance routed by training design, with no data decision, and report E4 as a measurement only.
   - If the orchestrator keeps an E4 trigger, the amendment must declare VSI-Bench development data for that choice, and every later VSI-Bench and ReVSI distance number is then S.
4. D2 for step 544 and D0: official room reads serve calls as the primary arm, labelled "served routed room, post-read deviation from D2, no gain established, room rule from C4 (incumbent rv selected on VSI-Bench ScanNet items)". The unserved read is the secondary arm, so the registered counterfactual is kept.
5. List D0 by name as a new scope.
6. Write amendment 3 before P8 and before any official native read. Hash it into the P8 freeze file.

## Point 5 (T2): what a D0 init changes, and whether the rule binds
What it changes:
- **The next leg's claim becomes "on top of a selected D0 export".** A comparison with step 544 then mixes D0 and A0 or A2. D0 contributes these confounds (`EV/cont_ops/PRELAUNCH_CARD_D0.md` §3):
  - every VQA trace form changed (7);
  - route planning moved into VQA (3);
  - the routing opener was reset and relearned (1);
  - optimizer and schedule restarted (2);
  - 581 room programs with GT responses trained, so the room-call habit is reinforced while A0 trains room direct (4);
  - 19,146 procedure-only counting, size and appearance rows (8, §3a);
  - uncertain source frames (9).
- **Under the no-controls rule this is acceptable.** Each confound must then appear in the run identity and in every read report.
- **The 80 withheld rooms are held out under neither init.** The design is right on this, though it understates it.
  - The pre-registration's D2 power text says the eligible pool trained step 544. That makes the A0 withhold of 80 rooms a recency reduction, not a held-out set, for any descendant of step 544.
  - D0 adds 783 distance and 105 room programs, plus camera, pose and pointing rows, on those rooms (card confound 6).
  - So T2 adds exposure in degree, not in kind. Replace "costs no held-out claim" with: "no step-544 descendant has held-out rooms; D0 adds routed and camera exposure on the 80 rooms; report exclusion within the leg separately from ancestral exposure."
  - Exact membership of the 80 rooms in step 544's pool: unverified by both reviewers.
  - Consequence the record misses: the pre-registration's plan to build an 80-room held-out set for room routing cannot be met inside this lineage.

Whether it binds (both reviewers):
- **Changes 7–8, the schedule:**
  7. D0 registers reads only at steps 100 and 200, and at 400 conditionally (`DD/D0_STOP_RULE_20261116.md`). "Newest passing export" therefore leaves open which exports ever get read. Bind the candidate set now. Recommended: the final (or stop) export, with a registered F1+F2 read on it, else the newest of steps 400/200 that passed, else step 544.
  8. Bind the cutoff: which exports count must not depend on when A2 is ready.
- **Change 9, the trend clause:** it is a continuation, not a pass (stop rule item 2). Remove "(or F2's trend clause)".
- **Changes 10–11, scope:**
  10. F1 tests only direct types and F2 only the facing twins. Neither covers camera displacement, movement or rotation, metre distance or room; F3 and F4 are report-only. Add an init guard, bound now: on the same dev-S1 reader, no paired difference against step 544 wholly below zero on the three camera types and on metre distance, with the camera call rate at least step 544's (100%). Camera routing is the lineage's strongest claim, and D0 reset the routing opener.
  11. F1's "not wholly below zero" is not equivalence. Require also a point-estimate floor on the direct-type mean (for example ≥ step 544's minus 1 point), because D0's procedure-only rows put counting and size at risk.

## Points 1–3, 6, 7: each claim
**1. "+7.7 strict [+3.8, +11.6] on 834 official metre items": confirmed as arithmetic; corrected as to cleanliness.**
- **Arithmetic.** POLICY_AUDIT gives abs-only, strict, frozen 64.76, +0.96 [+0.47, +1.45]. Times 8 that is +7.68 [+3.76, +11.6], equal to 61.09 − 53.38.
- **Read.** Lane evalx, 2026-11-13, trinity-1-18 (`MEM/result-vsi-routed-official-20261113.md`). The direct answers are f17's; the program is external, on G3T geometry, with SAM 3 and selector masks under the frozen fusion policy.
- **Strict is not free of benchmark choices.** POLICY_AUDIT #1, #6, #8 and #9 were first selected on VSI-Bench ScanNet items: the abs route, the box rule (25 candidates, optimism ≤ 0.5 task points), the depth cut (its constants U) and the depth source. The alias origin (#12) and the G3T scale rule (#20) are U.
- **New: the dev confirmation of the abs route was the dev-S1 route table's +8.1** (POLICY_AUDIT row 1). The design's own Q2 attributes that +8.1 to feet conversion. The abs route therefore loses its clean confirmation, and the record should say so.
- **Off the selection scenes, strict is unresolved.** "Routed only on ARKitScenes + ScanNet++, strict": +0.42 [−0.23, +1.08] VSI points. That row appears to cover abs plus room (0.92 + 0.42 = 1.34 ≈ 1.35). With fallback: ARKitScenes +11.7 [+5.2, +18.2]; ScanNet++ +6.3 [−0.7, +13.8], and strict ScanNet++ only +1.1.
- **Transfer to the student is unverified on benchmarks.** On dev-S1 metres, native 61.6 equals scripted 59.3, so the student writes usable programs. Officially, the operands come from benchmark phrasing, and the geometry scale differs: the external read used the GT-free scale rule, while the native read uses the step-544 heads.

**2. "The parent is exposure-advantaged on dev-S1": confirmed qualitatively; size unmeasured.**
- The CP1 lineage saw the 152 dev-S1 scenes; f17 saw 47 of them, with 3–4% of its rows on those scenes (`MEM/result-f17-devs1-vs-parent-20261112.md`; pre-reg Data).
- No measurement of the advantage on distance exists.
- The student is warm-started from the same lineage, so the bias against routing is asymmetric only to the degree that programs depend less on memorised scenes. That is plausible but unmeasured.
- The heads that scale the native program carry their own scene overlap (POLICY_AUDIT line 82).

**3. Units.**
- **VSI-Bench: confirmed** by my bounded read of question text only, no answers (`AD/datasets/original_vsibench_full.json`, 5,130 rows). Distance 834/834 in metres, room 288/288 in square metres, size 953/953 in centimetres.
- **ReVSI: confirmed** (`AD/external_benchmarks/revsi/ground_truth_metadata/32_frame.parquet` plus `hf_metadata/tiny_set_question_ids.txt`). The tiny set holds 283 distance items, 37 room items (21 single, 16 multiple) and 273 size items. Across the whole 32-frame config, every distance question (1,134) asks metres, every room question (302) square metres and every size question centimetres.
- **VSTI: unverifiable.** No VSTI question file is reachable by a bounded read; Trinity holds only `vstibench_hf/ScanNet.tar.gz` and videos.

**6. The points table.**
- **Arithmetic checks:**
  - 412.63 is the six-task sum; (412.63 + 61.09 + 63.40)/8 = 67.14, and (412.63 + 62.83 + 66.49)/8 = 67.74.
  - The gap to the bar is 7.3 to 7.9 VSI points (58 to 63 task points).
  - ReVSI: 324.73 is the five-category sum; (324.73 + 65.6 + 53.0)/7 = 63.33.
  - Distance against f17: 0.96 to 1.18 VSI points.
  - Room: ±0.39.
  - The section-3 tables are exact. Their result is an identity under unit-flat program accuracy; the scripted profile spans 49 to 64 and is not flat. The conclusion holds because the parent's 8.3 on feet drives it.
  - D2 cost: 2.7 measured, against "3 to 4" stated (corrected above).
- **Measured inputs:** the six step-544 direct tasks and the ReVSI five (official reads), the external routed distance and room, and the parent's ReVSI distance and room.
- **Stand-ins:** 67.1–67.7 is an estimate. It uses f17-based external routing and f17's room, not step 544's.
- **Guesses:**
  - GF-1 +2 to +4 (external papers);
  - RL +1 to +4;
  - trace repairs +0.5 to +1.5;
  - the facing fix +3 to +5, bounded by a +5.15 counterfactual computed on ReVSI items, 24 net items (NEXT_QUEUE);
  - the 20–30% pass chance;
  - every GPU-hour figure.

**7. What the record misses.**
- **(a) Refused calls on metre questions.** 544-lineage checkpoints have no recovery training, so a refusal scores 0 (the pre-reg primary). The raw-G3T proxy flags 54 distance and 23 room items on VSI-Bench, at most 1.81 VSI points (NEXT_QUEUE reason 4). That is larger than the whole distance-routing gain, and it rests on C5. A0's recovery rows answer directly after a failed call, from a lineage that trained no direct distance rows. That ability is unmeasured. Report the recovery path's score on the items where calls fail.
- **(b) A direct path for distance alongside the program.** The record rejects it only as "both forms by coin or flag". It does not consider the model-side fallback as the measured answer on refusals, which is a cheap read of what "both" buys.
- **(c) Power of the A0/A2 stop rule.** The metre-only distance stop rule (D-1) has 43 items in the fixed list, with half-width about 14. It cannot detect regressions under about 14 points; use all dev-S1 metre items.
- **(d) The 80-room held-out plan.** Infeasible inside this lineage (point 5).
- **(e) The abs route's lost dev confirmation.** Point 1.

## Where Codex differs
- Codex treats O1(a) as data-informed and the full-790 D1 outcome as open. I judge a direct decision implausible from the registered comparison.
- Codex adds that zeroing forced closes is itself a post-inspection sensitivity choice that needs disclosure.
- Codex adds that D0 widens O1(b)'s scope.
- Otherwise we agree on every verdict and change: E4 breaks the registration; the trend clause is not a pass; F1 and F2 do not cover routed or camera types; the read schedule must be bound; no descendant has held-out rooms.
