# lever2 STATUS (trinity-3-30; started 20:06Z 11-20; 6 h timeout ~02:06Z 11-21 -> write B/briefs/lever3.md and start lever3 by ~01:35Z)
Lane dir /scratch/jjyeung/orch_n30/lever2 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c (shared with lever1); poll: work/poll228.sh via tssh.
Inherits lever1 (B/briefs/lever1.md, lever2.md); lever1 history: /scratch/jjyeung/orch_n30/lever1/STATUS.md.
## Running (2-28; reviews auto-start when their fix ends)
- Rank 1: job 173872 FAILED (cause: 26 tower vendor files omitted; lever1_c/r1/DEBUG.md). ORCH 2051Z: ONE resubmission after Astra review; second failure -> BLOCKER. ORCH 2136Z: allocation 50 min, worker cap 30 or 35. Token a784b94c2e6af (not placed). Review 6 GO AFTER FIXES (budget, import audit). Now tmux l2_r1fix6 (BRIEF_R1FIX6.md) then l2_r1rev7 (auto). Then: fetch orchard/ to /dev/shm/lever2/r1b, floors check (B/events/n_ops/PROJECT_FS_FREE.txt >= 20 GiB), place/CPU/submit, monitor every minute, o_fetch, o_get, pull via work/pull_tpl.sh on 2-28 (ratelimit + register --io-weight 1; NOT the kit's pv pull_depth.sh), relift.py, boxdev/run.py.
- Rank 4: kit GO (review 4; token d93a17be024f5, delivery 4,235,885 B sha 9d023abc..., staged /dev/shm/lever2/r4/out/delivery.tgz; PLACE.md there). Job after rank 1's job (also if rank 1 fails twice); place by streaming delivery via ossh to /project/community/jjyeung/okh7/add93a17be024f5/0.tgz, then PLACE.md steps.
## Done
- Rank 5 ARKit: 21/22 pass, 22 built; RESULT posted; archive nogt_arkit7_20261120.tar.zst (sha b904ed67...) + mirror 1-18 (tar 84098c02...); INDEX + plan updated.
- Rank 5 archive (15 NPZs): /data3/jjyeung/distill_archives/lever1/nogt_gt15_20261120.tar.zst (121,289,552 B, sha c5d0c5ed..., readback ok); INDEX line added.
- Rank 5 mirror: trinity-1-18 /scratch/jjyeung/n30_mirror/lever1/nogt_gt15_20261120.tar (+ extracted nogt_gt15/), sha256 9287ce41... equal to 2-28 lever1_c/arch5/nogt_gt15_20261120.tar.
## Queued
- Rank 5 optional: ARKit restage in timestamp order (~10 MB governed) + rebuild.
- Removal candidate: 3-30 lever1/work/r6in.tar (8 GB; in lever1/REMOVAL_CANDIDATES.md).
