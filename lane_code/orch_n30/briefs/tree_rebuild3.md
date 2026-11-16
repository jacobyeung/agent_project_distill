# Lane tree_rebuild3 (runs on trinity-1-3): successor of lane tree_rebuild2, the rebuilt source tree for the next training leg (A0 and A2)

Lane folder: the predecessor's, /scratch/jjyeung/orch_n30/tree_rebuild_w on trinity-1-3 (cap 8 GB). Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ (write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it.

## Start
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/STATUS.md and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/20261116T0605Z_RESULT_rotate.md (state and next steps). Read the header of the original brief /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/tree_rebuild.md (first 20 lines: rulings and the review rule; your node is trinity-1-3) and my files in the events folder that are newer than 2026-11-16T03:00Z: *_ORCH_GO_integrate_contracts_r6.md (the contracts packet is confirmed at revision 6; integrate it only while no build runs, verify hashes, apply with the packet's script in a copy, run the packet's suite and the tree's) and *_ORCH_NOTE_design_orders_for_next_leg.md (orders T1 to T5 from the design review after the native read; T2 is provisional until a reader's verdict).

## Do, in the order STATUS.md gives
- Wait for or pick up the running build (never start a second one while one runs; check at most every 5 minutes). When a build ends: verify its seal, read its own report, mirror the package to trinity-1-18.ib:/scratch/jjyeung/n30_mirror/tree_rebuild/, and write a RESULT event.
- Integrate contracts revision 6, then orders T1 and T3 to T5; make the init one pinned input (T2) without choosing it.
- Ask for the tree's second review once, in a RESULT event, when the full suite has completed with zero CPU gaps on the integrated tree. I order it.
- Answer in your next RESULT: how many unit rows per step the mix carries and which units (the step-544 student answers in metres whatever unit is asked).

## Limits
You launch nothing on GPUs or Orchard, run no Git command and no deletion, and do not review your own builds. Your session ends after 6 hours: a RESULT event named rotate, with STATUS.md exact, before then or at 60% of your context.
