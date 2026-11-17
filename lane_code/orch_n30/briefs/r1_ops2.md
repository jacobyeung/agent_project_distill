# Lane r1_ops2 (Devin Opus high, runs on trinity-1-3): successor of r1_ops. Carry R1 vehicle P from proof 1 to the vehicle gate, run proof 2, and hold both submits ready
First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. The lane folder is /scratch/jjyeung/orch_n30/r1_ops on trinity-1-3, with a cap of 12 GB (about 7.5 GB used). Keep REMOVAL_CANDIDATES.md current; agents cannot delete files. Events go to /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops/. Your predecessor, r1_ops, rotated at 19:08Z on context.

Resume from /scratch/jjyeung/orch_n30/r1_ops/STATUS.md alone: its last block, "NOW (19:10Z) for a successor", and the lines after it. Read every events/r1_ops/*_ORCH_* file newer than 20261117T1838Z, and the newest /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/INBOX_TO_DISTILL_ORCH_*.md. The binding rulings are the 1415Z ruling in events/next_leg/, the 1423Z adjudication, and ORCH 1440Z, 1523Z, 1543Z, 1557Z, 1559Z (eight card corrections), 1605Z, 1613Z, 1634Z, 1758Z, 1806Z and 1838Z, all in events/r1_ops/. The design record is /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md; keep its Status line and the readiness rows you close current.

Goal (user): a ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint and answers from what they print. R1 is the next SFT leg: step 544 plus repair rows.

State at 19:08Z:
- Proof 1 is Orchard job 170885: general partition, config d8b03fd1, kit x_c5f3847d, running since 18:56Z, verdict about 21:35Z. tmux r1_mon polls it and applies the yield rule automatically; read work/drv/mon_last.txt and mon_flag.
- The proof-2 kit x_6f8ed106 is READY: config 2c67f1f2, feet unit rows bound, all four reviews GO. It waits for ANON_OK from lane review_r1anon3 (events/review_r1anon3/) and for proof 1's verdict.

Do, in order:
1. Monitor 170885 at the cadence below until it reaches PASS or FAIL. On PASS, write a RESULT with the receipt's eight checks, the admitted counts per family, and the loader audit: routing caps and final cells, routing distance rows by dataset prefix, facing toward/away shares, the "back" share among away-hard draws, and unit draws. Get these from KH/o/170885.proof.json and .proof.log on Orchard, read with one bounded ossh call.
   On FAIL: one Codex fix round (gpt-6-astra high, `implement`, in /scratch/jjyeung/orch_n30/r1_pkt; pattern in work/brief01_r8.md), applied to both packets, then one short Devin review, then proof 2 first (ORCH 1838Z item 3). A second failure of the same check is a BLOCKER.
2. When review_r1anon3's ANON_OK.json exists, copy it into work/drv_p2 and run `$PY -B cert_build.py ANON_OK.json`, then `orch sc1.sh` (see work/drv_p2/README.md). After proof 1's verdict, check squeue and the newest inbox. Then submit proof 2 on general with `timeout 300 bash $OSSH 'bash -s -- general' < work/drv_p2/pr1.sh`, and monitor it like proof 1 (copy work/drv/mon.sh with the new job id).
   If review_r1anon3 reports HITS: classify them against ORCH 1557Z item 1 and 1758Z, ask the orchestrator in a QUESTION with your default, and continue on that default.
3. Vehicle gate RESULT by 22:00Z, or two hours before the slot time main posts, whichever is later:
   - Write PRELAUNCH_CARD_R1.md with `python3 work/make_card.py values.json PRELAUNCH_CARD_R1.md`. Fill every {placeholder} from the proof receipt and STATUS: run, job, tree, identity, selection, units, mix sha, archive, proof receipt, reader build, the cell values, missing families with their entry boundaries, the pins table and the open items.
   - Write PRELAUNCH_ROWS_R1.md: the VQA part from work/PRELAUNCH_ROWS_R1_vqa.md, plus five routing traces per family from the proof's loader audit.
   - Copy both into events/r1_ops/.
   - Report proof 1 as the proven vehicle and give proof 2's state.
4. Keep both training submits ready: work/drv/go_submit_c5f3847d.sh and work/drv_p2/go_submit_6f8ed106.sh. They are thin, unreviewed wrappers that write go.json and run the sealed s.sh; ask for a short review in a RESULT before the slot. Never submit training or any GPU job without the orchestrator's written GO. Main must also have released advanced; check squeue.
Orchard only through tools/ossh.sh, under the job-place rules: one proof at a time, main first, and the yield rule of ORDER 1359Z.
Launch and monitoring cadence (USER 2026-09-16): after any submission, restart or alarm, check BOTH job liveness AND outputs landing every 1 minute. Two empty one-minute checks mean debug immediately. Once outputs land, lengthen step by step to 10 minutes with a status note each time, and drop back to 1 minute if any signal regresses. Two failed checks on one defect go to a Codex Astra review.
Continuity: rotate 5.5 hours after your start or at 60% of context (your process is killed at 6 hours). Write STATUS.md exact and a rotate RESULT, then launch your own successor ONCE on this node:
- copy this brief to briefs/r1_ops<N>.md with the lane name, predecessor and state updated;
- run `bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/devin_bg.sh r1_ops<N> <that brief> claude-opus-5-5-high 21600`;
- append the lane to tools/LANES.txt and check with pgrep that exactly one successor runs;
- stop acting the moment it starts.
Write events only for questions, blockers, verdicts, results and rotation, at most 20 lines each.
