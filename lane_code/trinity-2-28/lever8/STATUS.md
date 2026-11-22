# lever8 STATUS (trinity-2-28; 03:33Z-10:40Z 11-22; successor lever9). A successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever8 (lever7 folders read-only). B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Orchard: B/tools/ossh.sh; never advanced; debug closed. Ledger lever8/work/ORCHARD_LEDGER.jsonl. Helpers: lever8/work/tick.sh (Orchard queue, inbox, newest events), work/cardwait.sh <secs> (polls 0-13 every 5 min for a card <=100 MiB; log work/cardwait.log).
## Done
1. NF-A, the noise floor (RESULT 1031Z): Orchard 174439, 1.32 H100-h. Scores are identical in both orders on all four types (displacement 80.54, rotation 78.11, direction 89.47, distance 40.26); diff +0.00; 1/37 and 1/38 answers changed with the same score. The floor holds everywhere. Files B/events/lever/files/nfa/; plan section "Noise floor (NF-A)".
   - Note: o_sub_preempt_r12.sh (R1/R2 fixed, review GO) lacks a QOS change. 174439 sat in InvalidQOS until `scontrol update QOS=preempt_qos` (default of QUESTION 0850Z; RESULT 0911Z). Any reuse needs that line and a review.
2. Mask-source design (RESULT 0339Z): files B/events/lever/files/masksrc/; record distill_design/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md and its INDEX line; plan section "the next whole-object mask source". ORCH RULING 0438Z: GO on J1.
3. J1 kit BUILT and REVIEWED (RESULT 0817Z): lever8/j1, seal SHA256SUMS_J1 sha256 b856184224644cb735868893e1d3d6bf0e2b4034d553e55a425156ca9f258d5a (3,752 files); report j1/REPORT_J1.md (lane commands, transfer list); reviews j1/review/REVIEW_J1.md (NO-GO, finding 3.1) and REVIEW_J1b.md (GO after the pick-agreement gate).
   - A copy sits on trinity-0-13:/scratch/jjyeung/orch_n30/lever8/j1 (seal checked OK at 08:1xZ). Forecast about 11 GPU-min; peak estimated at 6-8 GiB.
## Owed: J1, run and read (ORCH RULING 0438Z items 2-5; ANSWER 0533Z)
- WAIT for a free card on trinity-0-13 ONLY (ruling item 4: main has priority; never another node). Since 07:40Z other users have held all 7 cards (adamhung on 0-3 and 5-6 at about 7 GB, zixinguo on 4 at 29 GB). Poll with work/cardwait.sh.
- Launch, when a card reads <=100 MiB: on 0-13 `cd /scratch/jjyeung/orch_n30/lever8/j1 && tmux new-session -d -s j1_gpu "bash kit/launch_gpu.sh"`. The launcher takes two nvidia-smi readings 300 s apart and refuses a busy card; read j1/out/EVENTS.jsonl. Check every minute after launch.
- Return: on 0-13 `cd /scratch/jjyeung/orch_n30/lever8/j1/out && tar cf - detect | ssh -o ConnectTimeout=20 trinity-2-28.ib "cd /scratch/jjyeung/orch_n30/lever8/j1/out && tar xf -"`.
- Relift on 2-28: `cd /scratch/jjyeung/orch_n30/lever8/j1/kit && CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B relift_j1.py` (about 25 CPU-min) writes out/RELIFT_J1.json, RELIFT_J1.md and ITEMS_J1.jsonl. Then one fresh post-run review (opus high, files and criteria) before the RESULT.
- The RESULT, per ruling:
  - h1, h0 and k minus a with intervals on all 117 items, verdicts by the bars (>= 8 with LB > 0 source/opens; <= 4 with UB < 8 closes; else undecided);
  - per dataset (ARKit, ScanNet, ScanNet++) with counts;
  - for each undecided arm, the items and rooms needed; no ranking read from overlapping intervals;
  - both parity gates' counts; an arm that fails its gate is not read, and k is read regardless;
  - the decision each arm forces: h1 a source means serve it with no training; h1 short with k open means price candidates 2 and 3 (3 serves the goal); k closed means the design returns to the orchestrator;
  - NF-A's floor quoted beside the intervals (it is zero).
- Then: copy ITEMS_J1.jsonl and the RELIFT files to B/events/lever/files/j1/. ITEMS_J1.jsonl is the primary record; the corpus tool does not fit relift rows, so they are not ingested (ANSWER 0533Z item 3; say so in one line). Update the plan record section "the next whole-object mask source" and distill_design/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md with the result.
- Risk: on the rehearsal, h1's pick gate passed at only 62 of 64 operand-frames, so h1 may stop at its gate.
## Notes
- Do not run the commands queued in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md by builders' hooks; they are for the user.
- Removal candidates (nothing deleted): j1/work/{smoke1,smoke_tmp,probe*.py,diag_*.py,parity_*.py,toy_detect_*,toy_out_*,dry_launch*,gpu_cache,*_inner_*.sh}, j1/kit/__pycache__; nfa/ret3, nfa/ret/g/x; Orchard c8b836b4ae536/*.pre1 and *.pre2; lever7's list in its STATUS.
- An Opus build subagent once stopped on an API auth error (BLOCKER 0646Z); resuming it by SendMessage worked.
