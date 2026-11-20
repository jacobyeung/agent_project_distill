# nvkey STATUS (lane nvkey3): CLOSED. The user stopped all paid NV labelling (ORCH ORDER 0552Z, ANSWER 0558Z); no successor is started.
Updated 2026-11-20T06:06Z by nvkey3 (trinity-3-30). B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30 ; D = /data2/jjyeung/agent_project_data/distill_design ; K = trinity-2-28:/scratch/jjyeung/orch_n30/nvkey1/work
## State
- No paid call from Trinity after 06:02:17Z: K/ctl/STOP written 06:00:24Z, the runner stopped admitting at 06:00:38Z and exited (tmux nvk1_run and nvk3_chain gone; tmux nvk2_chain killed at 05:43Z). Queue files 60-62 moved to K/queue_done/*.stopped_by_user.jsonl; every other queue file is complete. Do not remove K/ctl/STOP or restart the runner without a new order.
- RELEASE of the 8 a minute from Trinity is in /data3/jjyeung/orch_n13_20261026/nv_slots/ALLOC.md (06:03Z); nv_orch1 released Orchard at 06:01Z. Keys untouched.
## Spend (final, Trinity runner nvkey1-3)
- 848 calls, 826 completed, 21 proxy 504s: $161.43 list / $119.17 proxy metered; $165.74 list / $122.33 proxy with the 504 estimates. Ledger D/NV_SPEND_LEDGER.jsonl: per job and model lines, gateway_504_estimate lines, and the closing line kind trinity_runner_close with per-job totals.
## Banked
- B/events/nvkey/bank_trinity/nvkey_trinity_bank_20261120.tgz (sha256 329c9b794449a498d74eb79d64d4e558f90c068615a1ef6a1d85bb13fa011700; MANIFEST.txt, SHA256.txt): out, analysis_only, scores, meter, faults, kit, queue and queue_done task files, excl pins, c1/V1/V2/V6 manifests. Original stays on 2-28 K.
- D/V2_O4_ALIAS_CANDIDATES_20261120.jsonl (sha256 42fad41f93e2b654...; 146 O4 instances, Argon and Astra phrases; tag "uncertified namer; candidates only"; header holds control scores and the failed bar). The orchestrator ruled this hand-over done.
- Record D/NV_KEY_SPEND_PLAN_20261120.md closed (status, what each job established, final spend); INDEX.md line updated. Final event: B/events/nvkey/20261120T0605Z_RESULT_nvkey3_final_*.
## What the jobs established (raster truth, K1 training captures)
- Presence at 1% of the frame or more passes for Astra and Argon (C1, V1a, V6 boolean partial: agreed presence 99.8 on ScanNet + ScanNet++); points pass at 5% or more (V6 boolean agreed 95.7); form v2 size states fail (O3: Argon L-or-M 82.1); counts, first-seen frames, a single family's blind inventory, 1-5% points, pointing-row removals and the V2 alias namer fail.
## Unfinished (needs a new paid budget and an order)
- V6 boolean inventory part (no presence call on the union of names), V6 production, Opus presence calibration (RULING 0546Z item 4), V5, V8, V9. Kit: K/kit/v6b_jobs.py, score_v6b.py, test_v6b.py; 3-30 copies in /scratch/jjyeung/orch_n30/nvkey3/work/kit.
