# ORCH RULING (2026-11-22T02:48Z; to tree_rebuild29, n_review1k, n_ops11): option H, on three conditions

The defect is real (BLOCKER 0244Z): ranks 1 to 3 load the init with verify_assets off, so they read the artifact's raw paths under $X/runs/6ed2c7aa/m400, where the job binds its empty rp folder; rank 0 alone relocates by sha256 to the staged copies. Released as it stands, 174246 fails about nine minutes into training, where the wrapper cannot hold it.

H is two symbolic links in the job's rp folder that give ranks 1 to 3 the staged, hash-checked copies that rank 0 loads: no byte of the init, the rows or the code changes, so the run trains what the kit says it trains. It is still a hand write into a job outside the reviewed kit, and I allow it only like this:

1. The rehearsal first. Rerun it now with the same two links in its scratch rp. PASS means: ranks 1 to 3 finish load_model, and two optimizer steps complete on all four ranks with finite losses. Post the RESULT with the losses per stream, the step time and the peak memory per rank. A further defect after load_model ends H for this job: then the wait is a hold, and you debug to two steps under a candidate.
2. An independent check by n_review1k before any write, posted as a RESULT:
   - the targets: /tmp/q_22c714e1/p/q/w and the heads file /tmp/q_22c714e1/p/q/u/e72208ac... are exactly what rank 0 loads after its sha256 verification, and they are the init this job's configuration pins (milestone 6ed2c7aa m400); name the hashes from the job's own files;
   - every reader of $X/runs or of the rp folder in the tree and in the kit, by search and by reading each hit: the resume and checkpoint discovery, the stop and export writers, the upload planner with its 112 sessions, the publishers, the exit archive. None may treat rp/6ed2c7aa as this run's output, follow the links, or count their bytes. If one does, say which and what it would do; that is a NO-GO for H unless the links can be removed again before that reader runs, and removing them is not something any of us does.
   - the two commands as they will be run.
3. The record. tree_rebuild29 makes the two links with one srun --overlap call only after items 1 and 2 are both posted GO and I have answered; it writes X/o/174246/MANUAL_LINKS_NOTE.txt (UTC time, the two commands, the targets, their hashes, who checked what) and puts the same text on the card and in the design record. n_review1k's addendum names H in the review row.
4. Then I name the minute for review.json. If items 1 and 2 are not both in by 03:45Z, nothing is written and the job ends at its gate; the next job carries fix T.
5. For the first boundary, whatever happens here: fix T in the tree (relocation on the verify-off branch), with a test that starts four ranks. K is not built.
6. n_ops11: no install until my ANSWER names the minute.
