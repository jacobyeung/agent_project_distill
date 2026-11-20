# cont_ops24 STATUS (trinity-3-30; started 03:12Z 11-20; rotate by 08:40Z; successor cont_ops25)
## 03:25Z
- Read rules, brief, grd_funnel BLOCKER, record. Kit unpacked at work/kit2 (sha 17a910f1 verified).
- T1 in progress: (a) parity rule, (b) Orchard integration — inspecting package b9ef552934627 on Orchard.
- Nothing of mine on Orchard. No Codex round running.
## 03:36Z
- (a) Parity rule registered in D/GROUNDING_FUNNEL_20261120.md section "Parity rule for the ground-call rerun" (brief's rule; no better evidence). Baseline payload stage1.py/grounding.py == kit fixtures.
- (b) Design: derive a new orchard_h10 package from b9ef552934627 (one read = read-1 settings; ground worker; capture written job-local and uploaded to GCS by job.py before publish; only CAPTURE.json/PARITY.json return via pool). Codex Astra implement RUNNING on trinity-2-28: tmux c24_gbuild, dir /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild (BRIEF_GBUILD.md: Part A package+Orchard scripts, B GT adapter, C point-prompt mode for T2), log ../gbuild_dispatch.log. Inputs copy also in /dev/shm/c24/in1 on 3-30.
- (d) GT: 38 of 60 staged 1-18 -> 2-28 by one IB tar pipe into /scratch/jjyeung/orch_n30/cont_ops24_c/gt (sha lists match, md5 8e9e5d5e). 22 missing on 1-18 (no alternates): ARKit 41126645 41159771 41159772 41254810 42446097 42899829 47331002; ScanNet scene0261_02 0320_01 0380_01 0515_00 0515_01 0642_01 0666_01; ScanNet++ 246fe09e98 37c9538a2b 38fcf02d0b 3ce6d36ab5 ca3b651c23 d6bb698875 e35232b92f e667e09fe6.
- T2: note with points schema sent to nvkey1 inbox (0405Z). Orchard: nothing of mine. Next: poll Codex every 10 min; then (c) Astra review, place/CPU/submit.
## 03:58Z
- Codex build c24_gbuild DONE (REPORT.md on 2-28 gbuild/; copy /dev/shm/c24/g1). Package token a1abb3a204ff8 (delivery d0dac81b…, payload d7e65fb6…, plan 87449d1f…), 33 CPU tests pass. GT adapter refused (NPZ rasters 240x320 only, conventions undeclared; 142/300 occurrences bind by exact label; 76/150 items have GT). Point mode = refusing stub (SAM3 geometric-prompt source not in payload).
- Astra review c24_rev RUNNING on 2-28 (tmux c24_rev; /scratch/jjyeung/orch_n30/cont_ops24_c/rev/).
- Orchard: placed /project/community/jjyeung/a1abb3a204ff8 (+10.8 MB; free 238 GiB). CPU entry-sequence job 173603 on general (CPU only; o_cpu_general.sh) RUNNING orchard-community-2 since ~03:57Z. GPU submit (o_check_sub.sh) waits for CPU.json pass AND review GO.
## 04:05Z
- CPU job 173603 COMPLETED 6:02; a/c/CPU.json passed (bundle guard, entry sequence, memory fits). GPU submit waits for review c24_rev verdict.
