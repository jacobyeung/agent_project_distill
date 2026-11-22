# RESULT (20261122T0459Z; n_ops12 to ORCH): /project/community free space is falling; at the recent rate it runs out about 08:30Z
1. Source: B/events/n_ops/PROJECT_FS_FREE.txt (every 5 min). It read 159 GiB at 02:46Z, 142 at 04:29Z and 126 at 04:58Z.
2. The average since 02:46Z is about 0.25 GiB/min. Over the last 30 minutes it is about 0.6 GiB/min. At those rates the 126 GiB lasts until about 13:20Z (slow) or about 08:30Z (fast). nauto's BLOCKERs fire at 22, 10, 8 and 5 GiB, and the submission floor is 3 GiB.
3. I do not know who is writing; /project/community is shared. Tonight's CPU jobs on our side (mode r, the persistence measurement) are candidates if they write under X instead of the node's /tmp. tree_rebuild29 can say.
4. Why it matters: the next job's proof and gate take about 6 h on /project, so a submission after about 03:00 PT may meet a full disk. The user's removal list (B/events/n_ops/ORCHARD_REMOVAL_CANDIDATES_20261121.md, "Safe now" 48 GB) still stands. No agent removes anything.
5. Default: I watch the trend every 10 minutes and post again only if the rate stays above 0.5 GiB/min for an hour, or if free space falls below 60 GiB.
