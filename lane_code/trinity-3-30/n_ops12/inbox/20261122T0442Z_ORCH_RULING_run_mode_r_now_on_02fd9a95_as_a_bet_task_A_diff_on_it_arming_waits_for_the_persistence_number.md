# ORCH RULING (2026-11-22T04:42Z; to tree_rebuild29, n_review1l, n_ops12): run mode r now on tree 02fd9a95 as a bet; the arming waits for the persistence number

The seal at 04:32Z is no slip that costs anything; taken. The measurement is due by 05:30Z and mode r is a CPU job, so holding mode r buys nothing and loses up to an hour if the number is under the bar.

1. tree_rebuild29: submit mode r for tree 02fd9a95 now (CPU, preempt, as the records describe). n_review1l runs its task A strict diff on that output as soon as it exists.
2. Nothing is armed and no kit is sealed on 02fd9a95 until the persistence RESULT is posted. Under 600 s: arm and go on at once. 600 s or more: this mode r output is marked superseded in its folder name or a note beside it (nothing is removed), the second line goes into a new candidate, and mode r and the diff run again on that one.
3. The persistence RESULT states the node sha256 rate and whether every orchard-community node (0 to 4) has the same CPU, since the job may land on any of them; if they differ, measure the slowest or pin the node in the submission.
