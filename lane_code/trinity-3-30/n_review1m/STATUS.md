# n_review1m STATUS (successor resumes from this file alone) — 12:35Z 2026-11-22
Lane n_review1m: headless Claude Code Opus, trinity-3-30, started 12:28Z 11-22, 10 h timeout (killed ~22:28Z; rotate by 20:58Z = 8.5 h, or earlier at a quiet point).
Brief B/briefs/n_review1m_c.md. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30.
Predecessor STATUS: n_review1m/STATUS_n_review1l.md (= /scratch/jjyeung/orch_n30/n_review1l/STATUS.md); its inbox copied to inbox/.
Lanes: tree_rebuild30 carries builder + ops (inbox /scratch/jjyeung/orch_n30/tree_rebuild30/inbox; events B/events/tree_rebuild). n_ops12 dead.

## Job
- 174444 (kit ea058fed) CANCELLED 12:11:53Z by orch-home-43 (lane ss2) under the user's long-video priority (STOP_NOTICES 12:14:37Z; tree_rebuild BLOCKER 1216Z). Not a kit fault; no step, no checkpoint. Restart only after long-video job 174465 (8 h limit) ends AND the user allows (SAVED_USER_QUESTIONS row 12:16Z; default no resubmission).
- No N job runs. X/n still kit ea058fed, X/jn8.sh 2de401bd, X/n_r empty (per tree_rebuild30).

## Tools (hashes checked 12:28Z)
- Gate kit by path /scratch/jjyeung/orch_n30/n_review1l/work/gate: gate.py f9acc04f (TREE db42866f), test_gate.py a2e7a663, run_gate.sh d4634dea (admit test -> trinity-1-18 n_review1l/w24z14b), spell.py 227b866b, make_review.py 03af0d38 (reviewer string n_review1l: edit a COPY to n_review1m before use).
- My copies: work/o_confirm35.sh (n_review1l's + prints X/n_r contents), work/expect_n35.txt; work/ww.sh = wait loop (new event/inbox file OR stage line change; up to 540 s).
- Fspell template n_review1k/work/fspell.sh (sed JOB). Task A tool n_review1l/work/taskA/taska_diff.py.

## Done
- 12:28Z RESULT started (B/events/n_review/20261122T1228Z_RESULT_n_review1m_started.md).
- 12:30Z learned cause of 174444 cancel (above).

## Owed
1. Wait. If a new job runs kit ea058fed unchanged: Orchard byte check (timeout 300 bash B/tools/ossh.sh 'bash -s' < work/o_confirm35.sh > work/o_confirm_<job>.out; compare to expect_n35.txt, ALL_MEMBERS_OK, unlisted/missing empty, only t_db42866fd9e8d009.tar, n_r empty) before release; then gate at WAITING_REVIEW. If kit/tree changes: review under ORDER 1857Z item 4; re-pin gate if tree changes; rerun test_gate.py.
2. Gate: bash n_review1l/work/gate/run_gate.sh <job> <new empty dir>; fspell while node folder exists; PASS -> make_review.py <out> ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 <out>/review_<job>.json -> installer (tree_rebuild30); FAIL -> BLOCKER.
3. Resume kit dc38194d: review before any use, if asked.
