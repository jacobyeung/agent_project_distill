<!-- recovered by seal_plan: transcript=a97ad692 line=178 utc=2026-11-15T04:28:37.018Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; mkdir -p $R/next_queue/{events,inbox,out,work} && cat > $R/next_queue/BRIEF.md <<'EOF'
NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder /scratch/jjyeung/orch_cd/next_queue, using absolute paths.

# Lane next_queue: rank what the spatial student should run and build next, priced in official benchmark points (analysis and design only; no GPU, no launch, no code build)

## Why
The project trains a 9B spatial vision-language model that answers from RGB video end to end; some question types are answered by programs that call the model's own heads and frozen perception towers ("routed" types). The user's goal is a state-of-the-art 9B spatial model that beats the frontier closed models on VSI-Bench, ReVSI and VSTI, and afterwards a cheaper, better VLA fine-tuned from it.

Today no GPU job of ours runs. Large Trinity cards have been free since 2026-11-15T00:14Z (usable under `vnice.sh`), and Orchard's `advanced` partition gives 4 H100s per user. The ranked queue of ready experiments (`/scratch/jjyeung/orch_cd/READY_QUEUE.md`) dates from 2026-11-11 and predates everything measured on 11-12 to 11-15. Two decisions wait on a current ranking:
1. The user must decide whether the newest training leg (LEG-S1, stopped at step 544 of 1,000) continues for about 70 H100-hours, or is resealed with fixed data and tools. Facts: `/scratch/jjyeung/orch_cd/leg_s1_review/CONTINUATION_FACTS_20261114.md`.
2. I must decide what fills the free cards in the next hours and which builds start now, so that no GPU run waits on its own code.

Two lanes already work on reads of the step-544 model and are not your task: `evalx` (the native routed reader, pilot 9 on dev-S1) and `official544` (the official VSI-Bench 5,130 direct read; inventory for ReVSI and VSTI). Read their STATUS files; change nothing of theirs and send them nothing.

## What I need from you
### 1. Gap table
For VSI-Bench (official 5,130), ReVSI (official999) and VSTI (450 and 5,736), per task: the best measured number of any of our students (name the model, the read, direct or routed, the frame format), the open-model bar and the closed-model bar, the task's weight in the benchmark's primary score, and the gap priced in points of that primary score. Mark every number as official or dev-S1 (dev-S1 scenes were seen by the parents in training, so it supports paired comparisons only). Where a cause was measured, cite the record and the number (for example masks never proposed, wrong object accepted, metric scale, capped answers, the facing-away rotation, units). List what has never been measured, with the read that would measure it.

### 2. Candidates
Collect every candidate experiment or build, at least from: the next-seal list in `/scratch/jjyeung/orch_cd/leg_s1_tree/STATUS.md` (search it for the list; the file is 77 KB, do not print it whole) and in the state file below (geometry guard, facing-away defect, frame-pin cache, MDG box contract, unit conversion, rows that show a failed ground, routing rows on ARKitScenes); the rows of the 11-11 queue that are still open; the never-proposed masks (`mask_recall/out/NEVER_PROPOSED.md`) and the trace diagnosis (`trace_diag/out/TRACE_DIAG.md`); the roughly 76K program rows deferred from LEG-S1; evaluation frame count (the user lifted every frame-count restriction); the thinking-budget arms; the reads still owed; the continuation; architecture changes the user has allowed (another base of 9 to 13B, 64 or 96 training frames, SAM 3 as a frozen tower, the model's own encoder for grounding); and candidates of your own that the gap table suggests. For each candidate give:
- the question it answers and the decision its answer changes;
- the expected gain in official primary points with the arithmetic (items affected x gain per item x weight) and the evidence, or the words "guess" and why;
- the result a model with no new information would get (the no-information baseline), and the earliest read that would kill the candidate;
- cost: GPU-hours, wall-clock, where it can run; what exists (kit path, tests passed) and what is missing;
- what it depends on.

### 3. Ranked queue
(a) Runs that can start within hours on free cards with kits that exist, in order, with what each card would run. (b) Builds to start now, in order; for each, a build brief of one paragraph (scope, inputs with paths, the CPU proof that makes it launch-ready). (c) Decisions that belong to the user, each with your recommendation and the measured number that would flip it; for continuation against reseal, state which outcomes of the two pending reads (the routed score on dev-S1, the official 5,130 direct read) favour which choice.
Then argue against your own top three: the strongest reason each could be a waste, and what you checked.

## Rulings that bind every candidate
End-to-end RGB only: the model's own heads run inside its forward pass and numbers reach the language model as text tokens; no external harness. No control runs, no seed replicates, no replication of others' results: GPUs go only to method arms. Traces are never answer-only. Stack the best pieces first and ablate afterwards. Reconstruct from dense frames, then subsample; never fit geometry on 32 frames. Evaluation frame count is free on every benchmark. An evaluation uses the frame layout the model trained on. Before any init or data source is used, check its training scenes against the benchmark scenes (the MDG-A init is ineligible for this reason). Licences restrict nothing. AWS is not available. The other project ("main") has priority on every shared resource; on Trinity only trinity-0-13 runs at normal priority, other nodes only under vnice, never trinity-0-8, 0-23 or 3-23, and 0-18 stays with main. The Codex credit ends 2026-11-20.

## Sources (read named files and line ranges; print no large file)
- State: `/scratch/jjyeung/orch_cd/ORCH_STATE_20261111T0935Z.md` (107 lines; read it whole, first).
- Plan of record: `/scratch/jjyeung/orch_cd/model_design_review/PLAN_DELTA_REV2.md`, then the sections of `MODEL_IMPROVEMENT_PLAN_20261111.md` you need (70 KB).
- Record index: `/data2/jjyeung/agent_project_data/distill_design/INDEX.md` (one file); open the records it names that you need, among them ROUTED_READ_PARITY_PROBE_169501_20261114.md, ROUTED_READ_FIRST_ITEMS_169605_20261114.md, ROUTED_READ_GEOMETRY_GUARD_169670_20261115.md, ROUTED_READ_PIN_GRAPH_AUDIT_20261114.md, LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md, INFUSION_VISION_CAPACITY_20261113.md.
- Result notes, one small file each, under `/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/`: first `MEMORY.md` (the index), then by name: sota-bars-9b-20261109.md, closed-model-bars-20261111.md, result-vsi-routed-official-20261113.md, result-legs1-m100-20261114.md, result-f17-devs1-vs-parent-20261112.md, result-devs1-route-table-predicted-masks-20261112.md, result-devs1-baseline-cp1-20261112.md, result-revsi-student-reads-20261112.md, result-presence-pose-routing-20261110.md, result-pose-limit-qwen-encoder-20261109.md, toolprog-results-20261107.md, trace-review-20261107.md, experiment-design-lessons-20261108.md, lessons-process-rules-20261102.md, drastic-architecture-ok-20261109.md, lesson-eval-frame-layout-must-match-training-20261111.md. Read single named files only; never list or search that folder.
- Official results: `/scratch/jjyeung/orch_cd/official_reads/OFFICIAL_RESULTS.md`, `ROUTED_ABSDIST_ROOM_VSI5130_20261113.md`; accepted leg packets under `/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/` (step544_e193c2a3c first).
- Earlier queue: `/scratch/jjyeung/orch_cd/READY_QUEUE.md` and `READY_QUEUE_DRAFT.md`.
- Kits that exist: the STATUS.md of the ended lanes named in the state file's lane block (each under `/scratch/jjyeung/orch_cd/<lane>/`).

## Deliver
- `out/NEXT_QUEUE_20261115.md`: the gap table, the candidate table, the ranked queue with build briefs, and the argument against the top three. Every number carries its source path.
- A first RESULT event within about 90 minutes with the gap table and your top five; the full RESULT when the file is complete. Each event is at most 40 lines; detail lives in the file.
- A draft design record `out/NEXT_QUEUE_DESIGN_RECORD_20261115.md` (question, answer, reasons with evidence, every option considered and rejected with the reason, what might not work and how we would notice, the tests that would settle it, status). I copy it to the record folder.
- `STATUS.md`, short and current.

## Bounds and working rules
- Work in `/scratch/jjyeung/orch_cd/next_queue` on trinity-2-18. CPU only, light reads; no GPU; no launch; no ssh; no agents; no Git commands anywhere; no code build. Python, if needed: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`.
- Read-only everywhere outside your lane folder; write nothing on `/home` or `/data*`. Read single named files under `/data2/jjyeung/agent_project_data/` and the memory folder only; never list or search `/home` or `/data*`; no recursive search outside `/scratch/jjyeung/orch_cd`, and inside it search only named lane folders.
- This node's `/scratch` has 139 GB free and must not fall: the lane holds at most 100 MB and copies no data.
- No agent runs a deletion command, and names of deletion operations must not appear in shell command text (a local guard blocks such commands and they may not be retried).
- Keep your context small: read named files and line ranges; never read a file larger than 20 MB into memory.
- Events go in `events/`, named with `date -u +%Y%m%dT%H%MZ` in the writing command, and only as RESULT, QUESTION or BLOCKER. A QUESTION states your default; continue on the default. After the full RESULT stay alive for two hours: check `inbox/` once a minute and act on what arrives.
- Where the evidence does not settle something, say what is known and what is not. A gain you cannot support with a measured number is labelled a guess; do not rank a guess above a measured gain without saying so.
EOF
wc -lc $R/next_queue/BRIEF.md; bash $R/orch_tools/devin_bg_acp.sh /home/jjyeung/agent_project_distill $R/next_queue/BRIEF.md gpt-6-astra-max 28800 $R/next_queue/out/devin_stdout_01.log