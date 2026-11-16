# Lane: converter v5.1 - per-object frame scopes, evidence-quoting repair feedback, parallel stage A on eight questions (REQ-20260917-232)

Workspace: `/home/jjyeung/agent_project_distill`. Lane directory: `agent/scratch/devin_lanes/converter_v5_1_20260918/` (LANE; outputs to LANE/out, working copies to LANE/work). Run everything locally on this node: no ssh, no nohup, no detached processes. Use shell commands (`cat`, `cp`, `git`, `python`) for every path under `/data2`; file tools work only inside the workspace. Never delete, rename, or edit any existing file outside LANE and your worktree; create new files only. Never run `find`, `grep -r`, `du`, or `ls -R` outside ONE named directory (sweeping searches have crashed nodes). Never read any path containing `offline_labels`. `PYTHONDONTWRITEBYTECODE=1` and `python -B` everywhere.

Liveness heartbeat (mandatory): within your first minute and at least every 5 minutes append `<UTC> | <step in <=12 words>` to `LANE/out/HEARTBEAT.log` and rewrite `LANE/out/PROGRESS.md` (done / doing / next / blockers). Finish with `LANE/out/REPORT.md` (<=30 lines, last line `DEVIN_LANE_DONE`), written even on failure.

Scope discipline: the three changes below and the run protocol. No refactors, no new checks, no evaluation-harness work. Anything else goes in `LANE/out/NOTES.md`.

## Why
The v5 converter (branch `converter-v5-20260918`, tip `ba04476cd301367d17067a6e7d3719f25233ede1`, report `agent/scratch/devin_lanes/converter_v5_20260918/out/REPORT.md`) resolved every one of its 168 line-identifier citations; the citation failure class is closed. Its pilot question 1600 was rejected at stage A twice for `identity_frame_scope_unsupported`: the model's sheet asserted an object/frame cross-product (several objects listed against the union of their frames), and the repair, which received only the finding name, kept it. See `.../converter_v5_20260918/out/FAILURE_ANALYSIS.md` and `PILOT_REJECTION_ANALYSIS.json`. Seven questions never ran because the pilot gate was closed by that one question, so nothing is known about the others or about stages B and C on paid output.

## Inputs
- Worktree: `git -C /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo worktree add /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v5_1_20260918/work/trainer_repo -b converter-v5-1-20260918 converter-v5-20260918`. Do not touch the repository's checked-out tree or the earlier worktrees under `agent/scratch/devin_lanes/`.
- The v5 launcher, lease handshake, budgets and review-bundle structure; the v5 run artifacts under `.../converter_v5_20260918/out/eight_v5/` (read the two rejected sheets and the validator findings for 1600 before changing anything).
- Collector capacity: 2 annotation workers; record cap and basis in the handshake as before.

## Changes (orchestrator decisions 2026-09-18 16:25Z)
1. Sheet format: a frame-scope entry names exactly one identity and its frames, with the line ids that place that identity in those frames. Lists of identities against lists of frames are a schema violation the parser reports before the validator runs. The identity table itself stays as in v5.
2. Repair feedback: when the validator rejects a scope, the repair request quotes, per identity, the frame set the evidence supports and the line ids that support it (the validator already computes this to reject; expose it), and states which asserted (identity, frame) pairs have no support. Stage A allows up to three attempts (initial plus two repairs); every finding and sheet is kept.
3. Run protocol: stage A runs for all eight questions (1600, 3919, 2544, 1506, 1555, 1569, 1575, 1582) with 2 workers, no pilot gate. Every question whose sheet validates proceeds through B and C with the v5 repair rules. Budget: at most 9 stage calls per question (3 A, B, C, B-repair, C-repair, condensation, spare) and 64 in total; 32,768 output tokens per call; infrastructure retries as in v4.1.

## Tasks
1. Worktree, starting commit, CPU suite green before changes.
2. Implement changes 1 and 2 with fixtures from the v5 rejection of 1600 (the cross-product sheet is now a schema violation; a corrected per-object sheet validates; the repair request contains the evidence-derived frame sets). Full CPU suite; totals before and after.
3. Paid run per change 3 under the lease. Outputs, renderings, per-attempt logs and sha256 pins under `LANE/out/eight_v5_1/`. Write `LANE/out/STAGE_A_SUMMARY.md` as soon as all eight stage-A outcomes are known (validated / rejected with finding / requeue), before running B and C.
4. `LANE/out/eight_v5_1/revalidated/` with the review bundle in the v5 structure and `LANE/out/REVIEW_PROMPT.md` listing only questions that produced candidates. Do not judge your own outputs as passing.
5. Commit each logical change on `converter-v5-1-20260918`; list the SHAs in the report.

## Report (LANE/out/REPORT.md, <=30 lines, last line `DEVIN_LANE_DONE`)
Changes implemented with fixture evidence, test totals before/after, stage-A outcome per question, B/C outcome per question that reached them, calls per question and total, output paths and pins, REVIEW_PROMPT.md path and sha256, commit SHAs, blockers.
