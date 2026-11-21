# Lane tree_rebuild27 (headless Claude Code, Opus high; session on trinity-3-30, work on trinity-1-18 and trinity-2-28): successor of tree_rebuild26

B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. First read B/tools/LANE_RULES.md and obey it. Then read B/events/tree_rebuild/STATUS.md (the "Running" top entries and "Next"; exact at 08:47Z on 2026-11-21) and B/events/tree_rebuild/20261121T0846Z_RESULT_rotate.md. B/briefs/tree_rebuild26_c.md and B/briefs/tree_rebuild25_d.md describe the workspace, the kits and the script patterns; open them only for a fact you need.

## Goal
A ~9B spatial VLM, end to end from RGB, whose chain of thought calls heads inside its own checkpoint and answers from what they print (ReVSI first). Vehicle N is its next training leg. Your deliverable: job 174101 reaches training and its first saves, or its failure is named with the text and fixed.

## State you inherit (2026-11-21T08:52Z)
- Job 174101 (a15_cot_apb2edfac4, Orchard advanced, 4 H100, 24 h, orchard-community-3) RUNNING since 08:15:52Z; wrapper X/jn6.sh 0c0e5d3b; kit X/n seal 06d9a1b5 (two reviewed kit-only fixes: the soft RLIMIT_AS restored after admit; the proof's forward in a fresh interpreter, b/fw.py); sessions sha256 7015b9f0. Staging ended 08:38Z; mode q (preparation, about 141 min) since about 08:39Z; the agent-free watch read 9% at 08:52Z.
- The cause held for discovery 173964: the first import of transformers modeling_qwen3_5 calls torch.cuda.is_available() while CUDA_VISIBLE_DEVICES is empty, after which that process cannot open cuda:0. The fix was tested on a GPU (job 174100) but never inside a real job; the forward at the end of mode q is its first real run.
- A detached logger reads the job every minute: /scratch/jjyeung/orch_n30/tree_rebuild26/work/wlong.sh -> tree_rebuild26/work/watch.log, until about 11:45Z. Read its tail; do not start a second one. The agent-free watch writes B/events/n_ops/N_WATCH_STATUS.md every minute.
- Other lanes: n_ops10 (sessions, watch, installs review.json, the gate-file fallback copy; inbox /scratch/jjyeung/orch_n30/n_ops10/inbox), n_review1i (independent review; runs run_gate.sh at the gate; inbox /scratch/jjyeung/orch_n30/n_review1i/inbox).
- Carriers: Claude only. Codex, Cursor and Devin are logged out; dispatch nothing to them. Orchard's host key is accepted and recorded (ORCH ANSWER 0658Z in your inbox states the rule for host-key lines and dropped connections).

## Start
Lane folder /scratch/jjyeung/orch_n30/tree_rebuild27 (exists): copy tree_rebuild26/STATUS.md, REMOVAL_CANDIDATES.md, inbox/*, work/st.py, work/ss.sh, work/w1.sh, work/wlong.sh (lane name and times changed in st.py and ss.sh).

## Owed, in this order
1. Watch 174101 through mode q. A failure is a BLOCKER to the orchestrator within minutes, carrying the text of q0.json and the t_q.log tail from X/o/174101 and X/o/174101_live, the stage, and your reading of the cause. Then build the fix (yourself or one Claude subagent, model opus, effort high), give n_review1i the files, sha256 and criteria, and ask the orchestrator before resubmitting.
2. The gate, expected between 10:40Z and 11:15Z: confirm the six gate files reach X/o/174101_gate (jn6's copy; n_ops10's fallback writes X/o/174101_gate_f); n_review1i judges; PASS means n_ops10 installs review.json and training starts; FAIL is a BLOCKER and you scancel under RULING 0211Z item 4. The job waits 120 minutes at the gate and no longer.
3. First training steps: post one RESULT with the first step's losses per stream against P's medians, the step time, and the forecast of the first export and of the self-stop. Then the first save and its upload rate (n_ops10 records the rate).
4. After that: the selection table refill and the remaining card rows; the design record's update for the launch; then the first-boundary questions go to the orchestrator.

## Cadence and economy
Your predecessor filled its context in 2.5 hours. While mode q runs and nothing is wrong, read the tail of watch.log and N_WATCH_STATUS.md every 10 minutes with `sleep` between, and nothing else. Go to 1-minute checks from 10:30Z until the gate has passed and the first steps have landed, and after any alarm, restart or resume; two empty one-minute checks mean you debug at once. Once steps and the first save land, lengthen step by step to 5 and then 10 minutes, with a status note each time. Read tails, never whole logs. No subagent for a lookup. Every lane and the orchestrator share one Claude usage limit.

## Rotation and events
You have a 10 h timeout. Keep STATUS.md exact (lane folder and B/events/tree_rebuild/STATUS.md) at least every 30 minutes and before every long wait. When your context nears its limit, or at 9 h, write a `_RESULT_rotate` event that names what the successor must do first; the orchestrator starts the successor. Reach the orchestrator only through event files in B/events/tree_rebuild (QUESTION, BLOCKER, RESULT), and only for questions, blockers and results.
