# lever2 STATUS (trinity-3-30; started 20:06Z 11-20; 6 h timeout ~02:06Z 11-21 -> write B/briefs/lever3.md and start lever3 by ~01:35Z)
Lane dir /scratch/jjyeung/orch_n30/lever2 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c (shared with lever1); poll: work/poll228.sh via tssh.
Inherits lever1 (B/briefs/lever1.md, lever2.md); lever1 history: /scratch/jjyeung/orch_n30/lever1/STATUS.md.
## Running (2-28)
- Rank 1: GPU job 173872 FAILED (TowerError; return in lever1_c/r1/returned_fail1; cause: 26 tower vendor files omitted, DEBUG.md). ORCH ANSWER 2051Z: ONE resubmission after Astra review; return must carry traceback; capture 1 end to end first + memory per capture; second failure -> BLOCKER, nothing more. Debug fix token a784b94c2e6af; follow-up tmux l2_r1fix5 (BRIEF_R1FIX5.md). Next: Astra review (copy work/briefs/BRIEF_R1REV4.md, point at DEBUG.md + FIX5), fetch orchard/ to /dev/shm/lever2/r1 (new token dir), floors check (n_ops PROJECT_FS_FREE.txt >= 20 GiB), place/CPU/submit, monitor every minute, o_fetch, o_get, pull_depth (governed io-weight 1), relift, BOX dev (lever1_c/boxdev/run.py).
- Rank 4: review 2 GO AFTER FIXES (lever1_c/r4rev2/REVIEW.md); fix round 2 tmux l2_r4fix2 (BRIEF_R4FIX2.md). Then review 3, then job after rank 1's job (also if rank 1 fails twice).
## Done
- Rank 5 ARKit: 21/22 pass, 22 built; RESULT posted; archive nogt_arkit7_20261120.tar.zst (sha b904ed67...) + mirror 1-18 (tar 84098c02...); INDEX + plan updated.
- Rank 5 archive (15 NPZs): /data3/jjyeung/distill_archives/lever1/nogt_gt15_20261120.tar.zst (121,289,552 B, sha c5d0c5ed..., readback ok); INDEX line added.
- Rank 5 mirror: trinity-1-18 /scratch/jjyeung/n30_mirror/lever1/nogt_gt15_20261120.tar (+ extracted nogt_gt15/), sha256 9287ce41... equal to 2-28 lever1_c/arch5/nogt_gt15_20261120.tar.
## Queued
- Rank 5 optional: ARKit restage in timestamp order (~10 MB governed) + rebuild.
- Removal candidate: 3-30 lever1/work/r6in.tar (8 GB; in lever1/REMOVAL_CANDIDATES.md).
