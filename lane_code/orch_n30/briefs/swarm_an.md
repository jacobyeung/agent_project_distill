# Lane swarm_an (Devin Fable xhigh, trinity-3-30): coordinator of the trace-analysis swarm on leg R1's reads

First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Events: B/events/swarm_an. Lane folder: /scratch/jjyeung/orch_n30/swarm_an on trinity-3-30. You coordinate; Codex analysts read. You verify what they report before you pass it on.

## Goal
A ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print; ReVSI first, then VSTI and VSI-Bench. SFT on ground-truth head-calling traces must show placement (the call is placed), head accuracy, and usage (the answer follows the response). Your product: for every question type, what goes wrong in the model's traces, priced in points, and the row or trace change that fixes it for the next training vehicle (N). The user has asked for analysis at scale and has budget to spend today (USER 2026-11-19): Codex about 2,000 dollars for this lane today; Devin sessions for hard reading and synthesis are welcome.

## What is already known (do not redo)
- B/events/cont_ops/20261119T0306Z and 0319Z RESULTs, B/events/dist_diag/20261119T0345Z RESULT: at step 200 the model makes no tower call on 62 of 150 distance items; the no-call traces copy the relative-distance direct template; fix = coverage rows (lane dist_diag builds them).
- /data2/jjyeung/agent_project_data/distill_design/R1_COUNTING_LOSS_DIAGNOSIS_20261118.md: the first-seen list form made counting loop; those rows are removed in the continuation.
- Memory of results: step-200 direct read, VSTI and facing gates (B/events/cont_ops/files_m200/).

## Where the traces are (trinity-3-30, read in place, never copy or change; lane cont_ops17 owns them)
C = /scratch/jjyeung/orch_n30/cont_ops16/work/c15
- Direct decision read of step 200 (run 673bc60f, Orchard 172646): C/h1read/kit/build/a8102c3207b/fetched/x. Read SPEC.json and SUMMARY.json first. main/ is dev-S1 (1,339 items), a7/ is R0-dev (1,781 items); report/B2048.json is the scored arm (forced close at 2,048 tokens), ON16k.json the full generation with the traces. Verify this reading from the files and say so if it differs.
- Step 544 baselines: R0-dev in C/h1read/kit/build/adff67f7ae9/fetched/x; dev-S1 named in B/events/pooled_rule/BASE_MANIFEST_dev-S1_544.json. Other builds in C/h1read/kit/build are older exports (R1 step 100 a5d2d909067, D0 step 200 ae470417b41, H1-1 step 100 a24ea1a1936); use them for dose comparisons.
- Facing twins, step 200 (172658): C/h1face/kit/build/a2e46c0504e/fetched. VSTI relative dev set: C/h1vsti/kit/build/acb2faedd41 (step 544 base) and a35f73e87f0 (verify which is which from their SPEC files).
- Routed read, G3T arm: step 200 in C/r1route/out3/A4/ret; step 544 in C/r1route/out3/bases/b1/work/ret. Loader examples: C/r1route/out3s/score_r5.py, /scratch/jjyeung/orch_n30/dist_diag/work/q1/classify.py, C/cfix/derived_v3.py.
- Training rows: store v7 /scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7 (sqlite, read-only, query with LIMIT); feet unit rows /scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl; trace rules /data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md.
- No official VSI-Bench, VSTI or ReVSI item is read or used for any choice. Dev sets only.

## The swarm
1. Write one prompt per analyst under B/events/swarm_an/prompts/ and dispatch each as Codex Astra, read-only: `bash B/tools/codex_local.sh review <dir> <prompt-file> --model gpt-6-astra --effort high --label san_<id> --skip-git-check` (receipts stay on local disk: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/<stamp>_san_<id>/final_message.md). Run at most 5 at a time, each inside tmux or a detached shell; never one ssh per job.
2. Analysts (split further if a set is large; one type per analyst is the rule):
   - direction easy, direction medium, direction hard (each on dev-S1 and R0-dev);
   - relative distance; appearance order; route planning; object size with relative size; counting with relative count;
   - VSTI relative, one analyst per two types (three analysts);
   - facing twins (away and toward, ReVSI wording, the over-use of "back" on away-hard);
   - routed camera displacement; routed camera rotation and movement direction; routed distance items that do call (grounding, selector choice, frames, usage of the response);
   - chain-of-thought cost: tokens per type, caps hit, loops, at step 544 against step 200;
   - training-row audit, two analysts: for each row family of store v7 and the unit rows, 60 rows read against the trace ruling; which forms could be copied onto another question type or repeated into a loop.
3. Each analyst prompt carries: the rules block below verbatim, the exact paths, the type's items, and the required report (at most 120 lines): failure modes with counts over all wrong items of the type (not a sample when the type has under 400 items), three verbatim examples per mode (item id, question, truth, answer, trace excerpt), the step-544 against step-200 flips with what changed in the trace, a hypothesis for each mode labelled as a hypothesis with the row family it points to, any label or scoring defect found, and the three changes it would make, each with the number of items it could fix.
4. Rules block for every analyst: read-only; no ssh, network, Git or deletion; no recursive search under /home or /data*; under /scratch/jjyeung/orch_n30 list and read only the named folders, any find limited to depth 4; python from /usr/bin/python3 or /scratch/jjyeung/envs/planner_local_v1/bin/python, CPU only, under 4 GB RAM, scratch files only under /tmp; never load a whole sqlite file; quote counts from files, label guesses.
5. Verify before you believe: for each report, recompute its two largest counts yourself from the files and open three of its cited items. A report that fails this goes back once with the discrepancy; then it is dropped and said to be dropped.
6. Where a type's failures need deeper reading than a Codex analyst gave (a placement or usage failure on a routed type, or a mode worth more than one point), launch a Devin analyst for it: `bash B/tools/devin_bg.sh san_<id> <brief> claude-opus-5-5-max 10800` from this node, at most three at a time, each with a brief you write that carries LANE_RULES.md by reference and the rules block.
7. Synthesis (you): a design record /data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md with its INDEX.md line: per type the failure modes with counts; the price of each in points on that type and, where the type maps to a benchmark category, in category points; the ranked list of row and trace changes for vehicle N (what to add, reword, drop; how many rows; which family; expected effect and its basis; how we would notice it failed); a call-rate and usage table for every routed type; label or scoring defects; what could not be established. Options you considered and rejected go in with the reason.
8. Keep the kit reusable: lane cont_ops17 posts the step-400 reads about 10:00Z to 14:00Z (B/events/cont_ops). When a step-400 return is fetched, rerun the same analysts on it against step 200 and step 544 and append a dated section. Until then, after the first synthesis, deepen the highest-priced modes.

## Limits on this node (binding)
- trinity-3-30 /scratch is below its floor: write under 200 MB in total, no file above 5 MB, no copies of returns or stores.
- Before each wave of dispatches read line 4 of /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md (the account's NFS traffic). Above 10 MB/s weighted: wait 5 minutes and read again. Also `uptime` and `free -g`: load above 30 or under 60 GB available means wait.
- Spend: read /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log after each wave; stop new Codex dispatches at about 2,000 dollars and tell the orchestrator. If the log has no dollar figure, count dispatches and wall time and report those.
- No GPU, no Orchard job, no training, no Git, no deletion.

## Reporting and continuity
- First RESULT (20 lines) when the first wave is verified: the five highest-priced findings. Synthesis RESULT when the record is written (target 07:30Z). Events only for results, questions and blockers. STATUS.md in your lane folder, copied to B/events/swarm_an/STATUS.md after each step.
- Rotate 5.5 hours after your start or at 60% of context: write STATUS.md exact and a rotate RESULT, copy this brief to briefs/swarm_an<N+1>.md with state updated, run `bash B/tools/devin_bg.sh swarm_an<N+1> <that brief> claude-fable-5-2-xhigh 21600`, append it to B/tools/LANES.txt, check with pgrep that exactly one successor runs, and stop acting.
