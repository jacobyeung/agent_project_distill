# nvkey STATUS (lane nvkey2, successor of nvkey1). A successor resumes from this file alone.
Updated 2026-11-20T04:06Z by nvkey2 (trinity-3-30; started 04:01Z; 6-hour timeout about 10:01Z; nvkey3 starts by 09:30Z).
B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30 ; D = /data2/jjyeung/agent_project_data/distill_design ; K = trinity-2-28:/scratch/jjyeung/orch_n30/nvkey1/work (sender and staging)
Lane dir: trinity-3-30 /scratch/jjyeung/orch_n30/nvkey2 (inbox/, work/, out/); kit sources: 3-30 /scratch/jjyeung/orch_n30/nvkey1/work/kit (shipped to K in heredocs); nvkey2 scripts: 3-30 nvkey2/work/remote.
## Orders in force (full text: 3-30 /scratch/jjyeung/orch_n30/nvkey1/inbox/ and B/events/nvkey/*ORCH*)
- 0300Z: $15k expires; every NV job ENDS by 2026-11-21T04:00Z, sends stop 03:30Z. Bar: labels accurate vs GT on a calibration set and feeding a named build/analysis; one QUESTION with calibration numbers per job before production.
- 0350Z: panel ruling D/NV_KEY_PORTFOLIO_PANEL_20261120.md adopted. Trinity order: V1 remainder, V2, V4 (removals only, two families reject), V6, V7 ARKit, V5; V8/V9 last, only with main's agreement. Rules: six hashed exclusion lists + sender assert, dev outputs under analysis_only root, fat calls, one result file per call, ledger. Labels under 1% kept, flagged, never negatives.
- 0353Z ANSWER: USER YES to Orchard (U10 answered by USER). Bulk senders as CPU batch jobs on Orchard preempt (idempotent, resumable), never a login node, nothing on advanced; key only in the sending process env; ALLOC TRIAL then HOLD; ramp 8/16/32 with image calls; at most 40/min from Orchard; tell main via its inbox (B/../INBOX_TO_NONTRAINING_ORCHESTRATOR_<UTC>_<slug>.md). Lane stop $8,000 (proxy), main + distill < $12,000. Orchard results to /data2 hourly. V7 > 300 clips needs D/GROUNDING_LABEL_CONSUMER_SPEC_20261120.md. 3-family labels on every N clip wait for cont_ops24's GPU ceiling read + ORCH ANSWER.
- 0356Z: ScanNet/ScanNet++ leg NOT unlocked (waits for cont_ops24 GPU read + ANSWER). New: 64-frame census on Orchard for the 60 dev-S1 captures (reads carry 64 native tower frames, baseline job 171253, package b9ef552934627; see B/events/grd_funnel/20261120T0308Z_BLOCKER_*), Argon counts, Astra points, GT subset beside every count. Analysis only.
- Spend stops: $3,600 at 8/min, $6,000 at 20/min, $8,000 with Orchard; nothing beyond without an ORCH ANSWER. K/ctl/BUDGET (list $) set to match each GO.
- Trinity share: 8/min from 2-28 (K/ctl/RATE). On argon_static_nv2_1119 RELEASE in ALLOC.md: REQUEST up to 20/min (total < 70); take on GRANT or after 10 min without objection while main's 'gov:' total < 45. Pause on WAF 429, BLOCK, Think3D r3243-r3245. BPS 500000 while a main governed stream runs.
## Sender (2-28, tmux nvk1_run): K/kit/nvrun.py
- Queue K/queue/<prio>_<job>.jsonl; results K/out/<job>.jsonl; meter K/meter/CALLS.jsonl (+ B/events/nvkey/METER.json each minute); faults K/faults/. Ctl K/ctl: RATE 8, INFLIGHT 24 (16 worker threads), BPS 500000, BUDGET 200 (list $).
- Restart: `tmux kill-session -t nvk1_run; tmux new-session -d -s nvk1_run "cd K && SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt NVK=K /scratch/jjyeung/envs/p1cpu/bin/python -B kit/nvrun.py 3600 </dev/null >>K/runner.stdout 2>&1" </dev/null >/dev/null 2>&1`.
- ssh to 2-28 only via `bash B/tools/tssh.sh trinity-2-28 'bash -s' < script` (one start per 35 s per host).
## Jobs
- done: 05_smoke, 10_bake32, 20_c0census32 (ledger lines written).
- running at 04:02Z: 30_c1rest32 31/32, 31_c1all64 46/48, 41_c2audit 11/76.
- to score: `cd K && P=/scratch/jjyeung/envs/p1cpu/bin/python; $P -B kit/score_c1.py out/10_bake32.jsonl out/30_c1rest32.jsonl out/31_c1all64.jsonl`; `$P -B kit/score_c2.py out/41_c2audit.jsonl` -> K/c2/REMOVAL_CANDIDATES.jsonl, THIRD_ROWS.json; blind third = Opus 5.5 via kit/c2_jobs.py with ROWS (note: c2_jobs.py overwrites K/c2_rows_meta.json; keep a copy first).
## Events posted by nvkey2
- 0405Z QUESTION: Orchard per 0353Z (default at 04:20Z) and a second lane for Orchard (default: nvkey2 does both).
## Next
1. Score C1/C2, blind third, RESULTs + ledger. 2. V0. 3. V1 forms. 4. Orchard probe/ramp + 0356Z census. 5. D/NV_KEY_SPEND_PLAN_20261120.md + INDEX line.
