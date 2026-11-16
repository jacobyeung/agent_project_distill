<!-- recovered by seal_plan: transcript=71f94277 line=33345 utc=2026-11-14T20:03:57.829Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_local_headroom_for_cpu_work.md heredoc_quoted -->
# ORCH ruling: proceed; small writes are allowed, no full fresh staging copy

The 200 GiB reserve guards large staging copies, not ordinary CPU work. The node has about 166 to 177 GB free because another user copied data onto it; that is above the cluster's own floor.

1. Allowed now, without further questions: source edits, tests, building the replacement code object (a few MB) and any metadata object this order needs, their upload, and the pin list. Keep the lane's new writes for this task under 3 GiB in total, and stop and tell me if /scratch falls below 150 GiB free.
2. Not allowed: a second full staging copy of the unchanged objects (about 1.8 GiB) while the node is under 200 GiB free. Use the reuse path as for pilot 6: the four unchanged objects are proved by hash, upload receipt and a fresh hash walk of the existing staged tree; stage freshly only what changed (the new code object, and the step-544 metadata if it is a small object).
3. Step 544: good. Build pilot 7 and the full read for the step-544 stop export (artifact 1d6eeb28...). Note that the export archive itself (21.58 GB) is fetched by the job on Orchard, never copied here.

Proceed with the order.