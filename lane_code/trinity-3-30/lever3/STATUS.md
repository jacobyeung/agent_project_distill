# lever3 STATUS (trinity-3-30; started ~00:05Z 11-21; 6 h timeout ~06:05Z -> write B/briefs/lever4.md and start lever4 by ~05:35Z)
Lane dir /scratch/jjyeung/orch_n30/lever3 (work/, out/, inbox/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c; poll: lever3/work/poll228.sh via tssh. Inherits lever1/lever2 briefs; lever2 history: /scratch/jjyeung/orch_n30/lever2/STATUS.md.
Orchard ledger: lever3/work/ORCHARD_LEDGER.jsonl (continued from lever2). Removal candidates: lever3/REMOVAL_CANDIDATES.md.
## Running (2-28, Codex; reviews auto-start after fixes)
- Rank 4: l2_r4boot stopped at 20.11 GB > its 10 GB cap with no new delivery (r4kit/out is 19 GB); lever3 killed the auto review l2_r4bootrev (00:23Z) and relaunched as tmux l3_r4boot2 (cap 35 GB, BRIEF lever3/work/briefs/r4boot2.md) -> l3_r4boot2rev (auto). Token f68a2d7c903be. On GO: upload, place, `3.py cpu` (the ONE preflight resubmission under 2244Z), fetch c, `3.py submit` (GPU read 30 min), fetch g, score.py.
- Rank 1: l2_r1boot done (72 tests, sha 8326c8ee..., 3,717,946 B, pre-bulk 15.8 GB, boot_cpu 2.6 s, 0 bulk); review l2_r1bootrev running. On GO and after rank 4 has left general: o_place, o_cpu, o_sub_hand (general, 1 H100, 50 min), fetch, pull, relift, boxdev.
- Nothing of ours on Orchard or GPUs now; no governed stream open.
Launcher: lever3/work/mk.sh (mk NAME MODE BRIEF WAIT WORKDIR), l3_launch*.sh.
## Rulings in force
2211Z/2244Z resubmission terms; 2329Z /project floor 15 GiB (read df in submitting call); 2222Z item 2 (ext4 job_tmp, <=50 MB /project); 2337Z rank 4 first, never both on general; 2244Z item 3 same flags for CPU check; 2351Z boot+import before staging; 2152Z host-key: 2nd warning -> stop Orchard, BLOCKER.
