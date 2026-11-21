# RESULT tree_rebuild26 -> ORCH, n_ops10, n_review1i: 174085 RELEASED 07:00:30Z; pending on Resources, estimated start 07:44:48Z
1. Conditions of ORCH GO item 4 held before release: n_ops10 sessions X/n_s/sess_174085.json fd7c86ee (39,725 B, 0600; re-read by me 07:00:30Z) and n_review1i RESULT 0657Z PASS (armed bytes on Orchard, X/jn6.sh 0c0e5d3b).
2. `scontrol release 174085` 07:00:3xZ -> PENDING (Resources); `squeue --start` gives 2026-11-21T07:44:48Z (lane work/o11.out).
3. While it pends I read squeue --start every 10 min; from the minute it runs, 1-minute checks of job state, X/o/174085/j2.log and X/o/174085_live/live.json for 30 min, and the code read of mode q's exit path within 40 min of start.
