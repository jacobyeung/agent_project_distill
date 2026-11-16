<!-- recovered by seal_plan: transcript=71f94277 line=23423 utc=2026-11-13T18:15:17.150Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/20261113T1816Z_ORCH_ANSWER_local_scanner_benchmark_approved.md  -->
# ORCH answer (2026-11-13T18:16Z): the local scanner benchmark is approved; run it now

Approved as you describe it: the four SQLite files under `/scratch/jjyeung/orch_cd/legs1_dbs/ap/` (7.76 GB), hashed once and streamed once, serially, at most 2 CPUs and 4 GiB, 900-second wall limit, nice 19, idle IO priority, no copies, nothing written beside the databases. This is node-local disk, not network storage, so it is not heavy IO in the cluster's sense and needs no further answer from anyone. For the rest of this task, reads of files already on `/scratch` under `/scratch/jjyeung/orch_cd/` up to 30 GB need no question; say what you read in the RESULT.

Post the bundle as soon as the timing and the read-only test exist.
