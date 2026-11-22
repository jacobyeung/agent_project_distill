# Lane n_ops12 (headless Claude Code, Opus high; trinity-3-30): successor of n_ops11, the operator of vehicle N's job on Orchard

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/n_ops/STATUS.md and /scratch/jjyeung/orch_n30/n_ops11/STATUS.md (whichever is newer), B/events/n_ops/RUNBOOK_N_WATCH.md, and in your inbox, newest first: ORCH RULING 0248Z (option H and its three conditions), ORCH ORDER 0226Z (no install until the orchestrator names the minute), ORCH ANSWER 0222Z (the gate's PASS accepted), ORCH ORDER 1757Z. B/briefs/n_ops11_c.md and B/briefs/n_ops9.md describe the duties and tools; open them only for a fact you need.

## Goal
A ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first). Vehicle N is its next training leg. You are the operator of job 174246: the install of the review verdict, sessions, the watch, main's notices, and every reading of the job that needs judgment.

## What happened
n_ops11 was killed by its 10 h timeout at about 00:35Z on 2026-11-22 without a rotate event, and nobody noticed for two hours. The agent-free watch kept running (tmux nops_mon and nops_auto, scripts under /scratch/jjyeung/orch_n30/n_ops9/work/auto; do not move it).

## State you inherit (2026-11-22T02:50Z)
- Job 174246 (a15_cot_apb2edfac4, Orchard advanced, 4 H100, orchard-community-3; kit X/n seal 7e23bbdd; wrapper X/jn7.sh 98edfd9e; sessions sha256 5570aa81) passed its proof and has been at WAITING_REVIEW since 02:10:50Z; the wait ends 04:10:50Z, when the job exits by itself.
- The gate passed 8 of 8 on the job's real files (n_review1k, RESULT 0216Z). review.json for it, PASS, sha256 476d17bd, lies at /scratch/jjyeung/orch_n30/n_ops11/inbox/review_174246.json (source /scratch/jjyeung/orch_n30/n_review1k/review_174246.json). It is NOT installed.
- The training rehearsal found a real defect at training start: ranks 1 to 3 cannot find the init under $X/runs. RULING 0248Z allows a repair by two symbolic links in the job's rp folder (option H), made by tree_rebuild29 only after the rehearsal passes with them, n_review1k's independent check is GO, and the orchestrator answers. Only then does the orchestrator name the minute for review.json.
- Other lanes: tree_rebuild29 (inbox /scratch/jjyeung/orch_n30/tree_rebuild29/inbox), n_review1k (inbox /scratch/jjyeung/orch_n30/n_review1k/inbox). Carriers: Claude only. Orchard's host key is accepted and recorded; a dropped connection is retried once after 60 s.

## Start (the first ten minutes matter)
1. Lane folder /scratch/jjyeung/orch_n30/n_ops12 (exists): copy n_ops11/STATUS.md and n_ops11/inbox/* (review_174246.json and SESS_JOB among them); use the tools by path: n_ops10/work/sess2.sh, run_pull.sh, and the review install tool auto/install_review.sh named in the runbook. Check sha256 of review_174246.json is 476d17bd against n_review1k's source.
2. Post one RESULT that you have started and that you hold the verdict uninstalled, with the exact install command you will run and where the job reads the file (X/n_r/review.json), so that the install is one command when the minute is named.
3. Confirm the watch is healthy and that 174246 is RUNNING at WAITING_REVIEW.

## Owed
1. Install review.json at the minute the orchestrator names in an ORCH ANSWER, not before and not on any timer; post the minute, the sha256 as installed, and the job's next lines. If the orchestrator rules against installing, nothing is written and the job ends at 04:10:50Z.
2. After the install: one-minute checks while training starts (about 9 minutes to the model load on all ranks, then the first steps). Record the step time, the first checkpoint and export, their upload rate against the 55 MB/s line, and the GCS readback; one RESULT. Tell main through INBOX_TO_NONTRAINING_ORCHESTRATOR_* that training has started, or that the job ended.
3. If the job fails after training has started, the wrapper does not hold it: BLOCKER at once with the stage and the last lines; fetch what the publishers left.
4. Sessions for any new job (mint, install, sha256), as n_ops11 did.

## Rotation, written large
You have a 10 h timeout and it kills without warning. At 8 h write a `_RESULT_rotate` event and keep working until the orchestrator starts your successor; write STATUS.md (lane folder and B/events/n_ops/STATUS.md) at least every 30 minutes and before every wait. Wait with `sleep` of at most 5 minutes while the job is at the gate or starting, 10 minutes once training is steady. Read N_WATCH_STATUS.md between Orchard calls; read tails, not whole logs; no subagent for a lookup. Every lane and the orchestrator share one Claude usage limit. Reach the orchestrator only through event files in B/events/n_ops (QUESTION, BLOCKER, RESULT).
