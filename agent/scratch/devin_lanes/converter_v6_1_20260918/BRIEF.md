# Lane: converter v6.1 - read-only source root for the clean adapter, then the clean-pool pilot with the v6 pipeline (REQ-20260917-232)

Workspace: `/home/jjyeung/agent_project_distill`. Lane directory: `agent/scratch/devin_lanes/converter_v6_1_20260918/` (LANE; outputs to LANE/out, working copies to LANE/work). Run everything locally on this node: no ssh, no nohup, no detached processes. Use shell commands for every path under `/data2`; file tools work only inside the workspace. Never delete, rename, or edit any existing file outside LANE and your worktree; create new files only. Never switch or create branches in any checked-out working tree; all git work happens in the worktree you create below. Never run `find`, `grep -r`, `du`, or `ls -R` outside ONE named directory (sweeping searches have crashed nodes). Never read any path containing `offline_labels` or `answer_bank`. `PYTHONDONTWRITEBYTECODE=1` and `python -B` everywhere.

Liveness heartbeat (mandatory): within your first minute and at least every 5 minutes append `<UTC> | <step in <=12 words>` to `LANE/out/HEARTBEAT.log` and rewrite `LANE/out/PROGRESS.md` (done / doing / next / blockers). Finish with `LANE/out/REPORT.md` (<=30 lines, last line `DEVIN_LANE_DONE`), written even on failure.

Scope discipline: the adapter interface change, its tests, and the clean-pool pilot run with the v6 pipeline unchanged (apply only the v6 review's required fixes if the orchestrator lists them in `LANE/V6_REVIEW_FIXES.md`; if that file is absent, change nothing in the pipeline). Anything else goes in `LANE/out/NOTES.md`.

## Why
The student training source is the accepted clean-pool traces of the live teacher collector (about 1,000 accepted at 19:40Z, growing 400 per hour), not the benchmark pilot questions. The clean adapter's strict `snapshot` refused to run (`agent/scratch/devin_lanes/converter_v6_20260918/out/SNAPSHOT.md`): `clean_source.py:647` requires source and output paths under one explicitly admitted workspace, and the live collection root on `/data2` and the lane output under `/home` are disjoint. The guard's purpose (never write into the live pool, never read outside the admitted source) must survive with two roots.

## Inputs
- Worktree from the v6 tip named in `agent/scratch/devin_lanes/converter_v6_20260918/out/REPORT.md`: `git -C /data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo worktree add /home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/converter_v6_1_20260918/work/trainer_repo -b converter-v6-1-20260918 converter-v6-20260918`.
- Live collection root `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collection_gt_r1313` (terminals/, attempts/<qid>/b16384/archive/, archive_blobs/), newest census under `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/census_r1313/` (largest numeric directory; `ACCEPTED.json`, `DECISIONS.json`). The collector is live and writing: read only, never lock, never wait on pool files, never open `offline_labels`.
- Collector capacity: 2 annotation workers; record cap and basis in the handshake as before.

## Changes
1. `clean_conversion snapshot` (and whatever `clean_source.local_path` guards) accept `--read-root <live collection root>` and `--output <lane path>` as two explicitly admitted roots: every read must resolve under the read root (or the census directory, also passed explicitly as `--census`), every write under the output root; any path outside both is refused with the existing error; symlinks are resolved before the check; the read root is never written (assert no open-for-write under it, with a test). The single-workspace form keeps working unchanged.
2. Tests: reads under the read root pass; a read outside both roots is refused; a write under the read root is refused; a write under the output root passes; symlink escape is refused; the legacy single-workspace invocation is unchanged. Full CPU suite; totals before and after.

## Pilot
3. Strict snapshot with the new interface for 8 accepted qids chosen from `ACCEPTED.json`: the 8 oldest whose question types cover at least four types (prefer two each of object_rel_direction_medium, object_rel_distance, object_abs_distance, obj_appearance_order); write `LANE/out/SNAPSHOT.md` with the qids, types, scenes and any readiness refusals (if a qid's archive is incomplete, take the next oldest and say so).
4. Run the v6 pipeline (stage A, deterministic rendering, B', conservative C) on those 8 with 2 workers; budget 7 stage calls per question, 56 total, 32,768 output tokens per call, infrastructure retries as before. Write `LANE/out/STAGE_A_SUMMARY.md` and `LANE/out/STAGE_C_SUMMARY.md` as outcomes land.
5. `LANE/out/eight_clean_v6_1/revalidated/` with the review bundle in the v6 structure and `LANE/out/REVIEW_PROMPT.md` listing the candidates. Do not judge your own outputs as passing.
6. Commit each logical change on `converter-v6-1-20260918` in your worktree; list SHAs in the report.

## Report (LANE/out/REPORT.md, <=30 lines, last line `DEVIN_LANE_DONE`)
Interface change with test evidence; snapshot outcome (qids, types, refusals); stage-A and stage-C outcome per question; calls per question and total; output paths and pins; REVIEW_PROMPT.md path and sha256; commit SHAs; blockers.
