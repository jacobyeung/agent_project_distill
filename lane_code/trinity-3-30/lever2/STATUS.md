# lever2 STATUS (trinity-3-30; started 20:06Z 11-20; 6 h timeout ~02:06Z 11-21 -> write B/briefs/lever3.md and start lever3 by ~01:35Z)
Lane dir /scratch/jjyeung/orch_n30/lever2 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c (shared with lever1); poll: work/poll228.sh via tssh.
Inherits lever1 (B/briefs/lever1.md, lever2.md); lever1 history: /scratch/jjyeung/orch_n30/lever1/STATUS.md.
## Running (2-28; reviews auto-start after fixes)
- Rank 1: cause of 173925 = KeyError A_N under --export=NONE (RESULT 2238Z; ORCH accepted 2244Z). Reviews 8, 9 NO-GO; fix rounds FIX7, FIX8 (vendor launcher /dev/null; bounded startup sink). Now tmux l2_r1fix8 then l2_r1rev10 (auto). Token a6f198d3c7b20 (not placed). Submit when review GO (pre-approved ORCH 2211Z/2244Z: general, 1 H100, 50 min), /project >= 30 GiB, rank 1 before rank 4, never both on general. A death with no return -> BLOCKER; a death that returns its cause -> RESULT, fix, one more resubmission.
- Rank 4: debug done; reviews 5, 6 GO AFTER FIXES; FIX4 done (memory guard 180 GiB, 44 MB /project budget); now tmux l2_r4fix5 (cache writes) then l2_r4rev7 (auto). Token e71c940a6b283 (not placed). ORCH 2244Z: one preflight rerun after review GO, then the GPU read (30 min) with no further ANSWER; state memory request/peak; CPU check same flags/env as GPU job.
- Steps per job: fetch orchard/ (rank 1) or out/delivery.tgz+PLACE.md (rank 4) to /dev/shm/lever2, check /project free (B/events/n_ops/PROJECT_FS_FREE.txt), place, CPU check, submit GPU, monitor/min, fetch, decode; rank 1: pull depth (work/pull_tpl.sh on 2-28), relift.py, boxdev/run.py.
## Done
- Rank 5 ARKit: 21/22 pass, 22 built; RESULT posted; archive nogt_arkit7_20261120.tar.zst (sha b904ed67...) + mirror 1-18 (tar 84098c02...); INDEX + plan updated.
- Rank 5 archive (15 NPZs): /data3/jjyeung/distill_archives/lever1/nogt_gt15_20261120.tar.zst (121,289,552 B, sha c5d0c5ed..., readback ok); INDEX line added.
- Rank 5 mirror: trinity-1-18 /scratch/jjyeung/n30_mirror/lever1/nogt_gt15_20261120.tar (+ extracted nogt_gt15/), sha256 9287ce41... equal to 2-28 lever1_c/arch5/nogt_gt15_20261120.tar.
## Queued
- Rank 5 optional: ARKit restage in timestamp order (~10 MB governed) + rebuild.
- Removal candidate: 3-30 lever1/work/r6in.tar (8 GB; in lever1/REMOVAL_CANDIDATES.md).
