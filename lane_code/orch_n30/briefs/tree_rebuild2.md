# Lane tree_rebuild2 (runs on trinity-1-3): successor of lane tree_rebuild, the rebuilt source tree for the second training leg (A0 and A2)

Lane folder: /scratch/jjyeung/orch_n30/tree_rebuild_w on trinity-1-3 (your predecessor copied its working inputs there and verified seal 0fc11a63209cc6e73827149a78dea070aa72f279ec3ed7f79d8d3777be3f4320 over 846 files; cap 8 GB). Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ (the predecessor's folder; write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it.

## Start
1. Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/STATUS.md (the copy in your lane folder is identical) and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/20261116T0052Z_RESULT_rotate.md. They hold the state and your next steps. Read the header of the original brief, /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/tree_rebuild.md (first 20 lines: my rulings 1 to 3 and the review rule), with "your node" replaced by trinity-1-3; read deeper into that brief only where a step needs it.
2. Build 5 runs under Codex in tmux tree_rebuild_b5 on this node (started 00:11Z; receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T001148Z_tree_rebuild5). Do not start a second build while it runs. Check it at most every 5 minutes with one small read.

## Then, in the order STATUS.md gives
- When build 5 ends: verify its seal yourself, read its own report, mirror the package to a second node over InfiniBand (trinity-1-18.ib:/scratch/jjyeung/n30_mirror/tree_rebuild/; under 1 GB), and write a RESULT event named build5. Ask for the second review in that event only if the full suite completed with zero CPU gaps; otherwise say what is missing and dispatch the next build.
- Contract patches: lane contracts_rebuild2 (events folder /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/contracts_rebuild/) is delivering revision 5 after a review that accepted revision 4 with fixes. Integrate the contract patches only after an *_ORCH_* file in your events folder tells you revision 5 passed my interdiff check.
- The frame-host job and any GPU or Orchard step wait for my GO in your events folder.

## Limits
You launch nothing on GPUs or Orchard, run no Git command and no deletion. You do not review your own builds. Your session ends after 6 hours: write a RESULT event named rotate, with the state in STATUS.md, before 06:30Z or at 60% of your context, whichever comes first.
