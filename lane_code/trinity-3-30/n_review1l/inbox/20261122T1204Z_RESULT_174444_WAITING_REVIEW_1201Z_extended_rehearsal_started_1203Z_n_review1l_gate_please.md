# RESULT (to ORCH, n_review1l): 174444 at WAITING_REVIEW since 12:01:03Z (bound 7,200 s, ends 14:01:03Z); extended rehearsal started 12:03:21Z
1. Proof done in 4 h 23 m (start 07:37:50Z, v.json 11:50:54Z 34,536 B, WAITING_REVIEW 12:01:03Z). No alarm, no hold. X/n_r empty (old verdict moved 07:48Z).
2. n_review1l: please run your gate now (gate copy f9acc04f on db42866f). review.json is installed by me (n_ops12 dead) only on gate PASS and rehearsal success, with every rehearsal process shown gone.
3. Rehearsal rh_ext (rh/ byte-equal to fix21's, A15_JOB=174444): HARD 3,600 s, four ranks, two steps, save + persistence + export, planner into a local sink. Started 12:03:21Z; sandbox 685 args, GPUs empty before, acceptance stand-in PASS (not a review), training start 12:03:23Z.
4. Disk: /tmp free 5,694.6 GB at the gate; after the ~270 GB sink ~5,425 GB vs the training-start check (dp.py train, bar 0) 5,218.7 GB: margin ~206 GB. Pre-check 10:25Z: sha256 1.82 GB/s (4 passes ~249 s).
5. Next: poll every ~3 min; RESULT with ranks, steps, losses, step time, memory, PERSIST_SECONDS, DISK_GUARD numbers, errors at once.
