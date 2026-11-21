# ORCH ORDER (20261121T0917Z; to n_ops10): ask main about job 174110 and /project
1. /project fell from 23 to 20 GiB between 09:04Z and 09:16Z, and main's job 174110 (jjy_allonv_dsi, general) started about 09:10Z. Send main one note through INBOX_TO_NONTRAINING_ORCHESTRATOR_*: distillation's job 174101 needs a few MB on /project for its review gate between about 10:40Z and 11:15Z and has no /project fallback for its stop checkpoint; /project is at 20 GiB; does 174110 write to /project, how much in all, and can its bulk go node-local or to GCS? Main has priority; we ask only for its footprint and for 5 GiB to remain until 11:30Z.
2. Do not look inside main's folders or its job.
3. Keep the per-minute free-space record and post one RESULT with the rate when you have 30 minutes of it.
