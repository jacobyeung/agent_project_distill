# A04: audit of routed serving in recorded traces (head values printed, answer written, score given)

Task id: A04. Task directory: /scratch/jjyeung/swarm_20261120/work/A04 (create it).

Do not search, list or read the working directory you start in (it is /home/jjyeung/agent_project_distill on NFS). Work only by absolute path inside /scratch/jjyeung/swarm_20261120.

## Rules
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/swarm/SWARM_RULES.md first; it binds you, and so does the LANE_RULES.md it names. No ssh, no GPU, no git, no deletion. Read nothing on /home or /data* except the two rules files. The staged reads contain development items only; if any item looks like an official benchmark item, stop reading it and report its read_id and item_id.

## Goal and why this task matters
We train a ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (`<ground>`, `<gap>`, camera-pose and similar calls; the head's printout comes back in a `<tool_response>` block) and answers from what they print; it must beat open 9B models on ReVSI, VSTI and VSI-Bench. Our routed reads trail where they should lead: distance items score 0.28-0.47 while camera items score 0.66-0.85. This task decides, item by item, whether a lost point comes from the head's value, from the model's arithmetic after the head printed, from a skipped call, or from the serving and scoring code. Only the last kind is a code bug, and it is the cheapest to fix.

## Inputs (node-local, read-only)
- Routed reads: /scratch/jjyeung/swarm_20261120/corpus/ files 673bc60f_s200_devS1_routed_A4.jsonl, 6ed2c7aa_s400_devS1_routed_A10b.jsonl, 469ddece_s544_devS1_routed_b1.r0.jsonl (636 dev-S1 items each, arm `tower`), 469ddece_s544_devS1_routed_b1.r1.jsonl and 359fcc3c_s200_devS1_dist150_E_173242.jsonl (150 distance items), 469ddece_s544_room134_routed_b2.jsonl and 673bc60f_s200_room134_routed_B5.jsonl (134 room items; B5 has no tool calls), 6ed2c7aa_s400_ownarm_cam900_173333.jsonl (arms `own` and `tower`), 469ddece_s544_devS1_native_b07a20b364.jsonl (arms `scripted` and `unflagged`).
- Item keys and a worked example: /scratch/jjyeung/swarm_20261120/CORPUS_MAP.md (section "Three example items"). In that example the `<gap>` head prints "distance 1.42 m", the model answers 4.66 feet (a correct conversion), the truth is 5.6 feet and the item scores 0.8: a head-value loss, not a serving bug.
- Scorer code for reference: /scratch/jjyeung/swarm_20261120/repo_head/student/landing/student_pilot/benchmark_eval/{answers.py, score.py}.

## Question
For every routed item that scores below 1, which of these lost the points?
(a) no call where the program needed one; (b) a call with the wrong object, mode or rule; (c) the head's printed value is wrong (compare the value implied by the printout with the truth after unit conversion); (d) the model's arithmetic or unit conversion after the printout is wrong; (e) the answer span differs from what the trace concluded; (f) the recorded score disagrees with the scorer's rule given the answer and the truth; (g) the call was cut, malformed or its response missing or empty (serving bug); (h) other, described.

## Method
1. Write a script that classifies each item mechanically where it can: parse the tool calls and their printed numbers, recompute the final number from them (units: metres to feet is x3.28084), compare with the answer and the truth, and recompute MRA.
2. Read by hand at least 40 items the script cannot classify and at least 20 it did classify (spread over the reads), and correct the script where you disagree.
3. Write the table: read_id, item_id, question_type, class, points lost (1 minus score), a one-line reason.
4. Summarise points lost per class per read, and say which classes changed between steps 200, 400 and 544 on the same 636 items (63 items went from right to wrong between step 400 and 544).

## What counts as a finding, and its price
A finding for this track is any item in class (e), (f) or (g): a serving or scoring defect, with the code line where you can name it and a reproduction script. Price it in points on dev-S1 routed (636 items) or the 150-item distance slice. Report classes (a)-(d) as the failure budget (points per class), which other tracks use; they are not code bugs.

## Out of scope
Proposing training changes; the direct reads; official benchmark files; code outside the two scorer files.

## Deliverables (exactly as SWARM_RULES.md prescribes)
- /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/results/A04.md (at most 60 lines).
- /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/files/A04/ (classifier script, item table under 5 MB, per-class summary).
- One line appended to /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/DONE.txt.

Time box: 90 minutes. Use `nice -n 10` and at most 4 threads.
