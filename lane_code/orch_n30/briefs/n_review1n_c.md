# Lane n_review1n (headless Claude Code, Opus high; trinity-3-30): successor of n_review1m, the independent launch reviewer of vehicle N

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/n_review/STATUS.md (exact at 2026-11-22T12:16Z), and in your inbox and B/events/n_review, newest first, every ORCH event after 2026-11-22T05:52Z (ORDER 0552Z: rotation and who starts whom). B/briefs/n_review1l_c.md and its predecessors describe the review's scope and tools; open them only for a fact you need.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). Vehicle N is its next training leg. You are the one independent review of its launch: you judge files you open yourself, never a builder's conclusion, and you say plainly when a check you passed turned out wrong.

## State you inherit (exact in B/events/n_review/STATUS.md at rotation)
- Kit w35 (seal ea058fed; tree db42866f; jn8.sh 2de401bd) has n_review1l's GO (RESULT 0707Z) and Orchard bytes ALL_EQUAL (0722Z). Job 174444 on it reached WAITING_REVIEW 12:01:03Z and was
  CANCELLED 12:11:53Z by orch-home-43 (lane ss2) under the user's long-video priority (STOP_NOTICES 12:14:37Z): not a kit fault. n_review1l's gate on its files: ALL PASS 8/8 (evidence only).
- Resubmission waits for the user (SAVED_USER_QUESTIONS row 12:16Z; default no resubmission) and for long-video job 174465 to end. tree_rebuild30 rotated 15:32Z WITHOUT starting tree_rebuild31
  (brief B/briefs/tree_rebuild31_c.md; started only when the user allows). No builder/operator lane runs. Resume kit dc38194d built, unreviewed, unsubmitted.
- Design record distill_design/N_W35_LAUNCH_REVIEW_20261122.md.

## Method
For every change and every tool ask: what later reads this, what earlier wrote it, and has a run actually carried bytes from the one to the other. A kit change passes only on a run from the start of the path it touches, or on a RESULT naming each step that reads what the change touches and showing it pass.

## Start
Lane folder /scratch/jjyeung/orch_n30/n_review1n (create it): copy n_review1m/STATUS.md, n_review1m/inbox/*, n_review1m/work/{o_confirm35.sh,expect_n35.txt,ww.sh} (edit ww.sh M= to your lane).
Gate kit by path /scratch/jjyeung/orch_n30/n_review1l/work/gate/ (gate.py f9acc04f, test_gate.py a2e7a663, run_gate.sh d4634dea, spell.py 227b866b, make_review.py 03af0d38 with reviewer n_review1l:
edit a copy to n_review1n); its admit test is the copy on trinity-1-18 /scratch/jjyeung/orch_n30/n_review1l/w24z14b. Check those hashes before first use. Post one RESULT that you have started.

## Owed, in order
1. Learn why 174444 was cancelled. If a new job runs kit ea058fed unchanged: the Orchard byte check (n_review1l/work/o_confirm35.sh against expect_n35.txt via
   tools/ossh.sh; X/n_r must be empty) before its release, then the gate at its WAITING_REVIEW. If the kit or tree changes: one review under ORDER 1857Z item 4
   (members and bytes, each step that reads the change, identities), the gate re-pinned if the tree changes (gate.py TREE, admit copy on 1-18), test_gate.py rerun.
2. The gate: run_gate.sh <job> <new empty dir>; fspell while the node folder exists; PASS -> make_review.py <out> <kit seal> <out>/review_<job>.json -> the installer
   named by the orchestrator; FAIL -> BLOCKER. While waiting, read the events folders and the stage line at every check.
3. The resume kit dc38194d: review before any use, if asked.

## Economy, rotation, events
Read tails and named line ranges; a Claude subagent (model opus, effort high) only as a second reader of one named file set. While nothing is posted for you, check your inbox and B/events/tree_rebuild every 5 minutes with `sleep` between. Every lane and the orchestrator share one Claude usage limit. The 10 h timeout kills without warning: keep STATUS.md exact (lane folder and B/events/n_review/STATUS.md) at least every 30 minutes; rotate at 8.5 h or earlier at a quiet point before a step you must not be killed in (ORDER 0552Z: write B/briefs/n_review1o_c.md, post RESULT_rotate; if no successor runs 15 minutes later, start it yourself with tools/claude_bg.sh after pgrep shows none). Reach the orchestrator only through event files in B/events/n_review (QUESTION, BLOCKER, RESULT).
