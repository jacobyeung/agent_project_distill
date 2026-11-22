# lever9 STATUS (trinity-2-28; started 10:48Z 11-22; killed by 20:48Z; rotate by 19:18Z to lever10). A successor resumes from this file plus lever8's STATUS (copied below the line).
Lane dir /scratch/jjyeung/orch_n30/lever9. Kit lever8/j1 used in place. Card wait: lever9/work/cardwait.sh <secs> (log work/cardwait.log).
## Now (1148Z): J1 GPU pass DONE on trinity-0-13 card 0 (11:09-11:21Z, 46/46 captures, 413 s, exit 0, CUDA peak 3.9 GiB). out/detect returned to 2-28 over .ib (14,259,240 B; sha256 of the sorted file-hash list 4c01af31...89c8 on both nodes). Relift RUNNING on 2-28 since 11:47Z in tmux j1_relift (log lever9/work/relift.log, .err). Next: fresh post-run review (opus high), RESULT, copy files to B/events/lever/files/j1/, plan + design record updates. Note: 2-28 load ~124 from NFS wait (rpciod); shells start slowly.
---
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
