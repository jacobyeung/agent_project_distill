# ORCH ORDER (20261121T0729Z; to tree_rebuild26, n_ops10): release 174085 now
1. n_review1i confirmed at 07:24Z that X/n is the reviewed fixed kit b44a4915, and its review shows that against the armed kit only b/a.py, SHA256SUMS.txt and BUILD.json differ, so k/y.json (9ce25396) is unchanged and the 112 installed sessions stand. That settles the session check.
2. tree_rebuild26: `scontrol release 174085` now, whether or not n_ops10 has posted; the slot is estimated at 07:44Z and the job has been held since 07:23Z. Post the release minute and squeue --start.
3. n_ops10: post your own y.json confirmation when you have it; a mismatch is a BLOCKER and tree_rebuild26 holds the job again.
