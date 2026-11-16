# Lane native_r3 (runs on trinity-1-13): successor of lane native_r2, the native routed read of the step-544 student on dev-S1

Lane folder: the predecessor's, /scratch/jjyeung/orch_n30/native_r2 on trinity-1-13 (this node is short of disk: write under 1 GB in total, and check free space before any write above 100 MB). Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r2/ (write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are an operator; code changes go to Codex as the rules describe.

## Why
The project's central claim is that routed programs, written by the student and served by its own heads and frozen towers inside generation, beat its direct answers. Orchard job 170056 (a15_cot_apb07a20b364, general, running since about 00:30Z, expected end 03:30 to 04:30Z, limit 6 h) is the first full native read on dev-S1 after nine failed attempts. Your job is to bring its result home and report it correctly.

## Start
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r2/STATUS.md and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/native_r2/20261116T0059Z_RESULT_rotate.md: they hold the exact state, the fetch command for the return (a governor stream at priority 20), the analysis command, and the record to write. Read the original brief /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/native_r2.md only where a step needs it. The predecessor has ended or is ending: repeat none of its actions.

## Do
1. Watch job 170056 with one small call through the shared Orchard connection at most every 10 minutes. If it fails or is cancelled, write a BLOCKER event at once with the job's own last lines; do not resubmit.
2. Reviewer lane review_an (events folder /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_an/) is reviewing the analysis script (native_vs_direct.py, sha256 64ac19a6...). When its verdict lands: on GO, proceed; on fixes, dispatch them to Codex, write a RESULT event with the diff, and wait for my *_ORCH_* confirmation in your events folder before any number computed with the changed script is called a result.
3. When the job ends: fetch the return as STATUS.md describes, verify every hash, and run the reviewed analysis. If the job hit its limit, the completed pairs are published with status FAILED: report them as a partial read, with the counts per category, and say which captures are missing.
4. Report in one RESULT event named native_read: per category (absolute distance, room size, each camera type) native score, direct score, paired difference with its interval over the 58 physical rooms, items and captures; how many programs were emitted, executed and refused by the guard; nothing rounded in favour of either side. State what the read does not show.
5. Write the record /data2/jjyeung/agent_project_data/distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md (question, answer, evidence, what might be wrong and how we would notice, status) and append one line to INDEX.md there.

## Limits
No official VSI-Bench, ReVSI or VSTI item is read natively. No new Orchard job without my GO. The paused rehearsal process rh_full_op1 stays paused. No Git command, no deletion. Your session ends after 6 hours; write a RESULT event named rotate before then if work remains.
