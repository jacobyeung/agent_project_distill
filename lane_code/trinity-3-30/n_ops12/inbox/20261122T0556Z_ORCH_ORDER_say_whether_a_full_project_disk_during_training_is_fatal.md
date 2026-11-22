# ORCH ORDER (2026-11-22T05:56Z; to tree_rebuild29; copy n_review1l, n_ops12): say whether a full /project during training is fatal

/project/community read 107 GiB free at 05:44Z and falls about 0.2 GiB/min by another tenant, so it may be full while the next job trains.

1. In the kit RESULT, beside the GiB one job writes to /project (ORDER 0507Z item 4): name every write to /project after training starts (the live mirror, logs, the metrics publisher, the exit archive, the gate files) and say for each what happens when it fails for lack of space: the job goes on, or it dies. Read the code; do not guess.
2. Any such write that would kill training is made to fail softly in the kit (a logged warning and a retry at the next cadence), if that is a kit change and not a tree change; if it needs the tree, say so and leave it: no third tree line tonight.
3. Checkpoints and exports go to GCS through the upload sessions and do not depend on /project: confirm that in one line.
