# Lane cont_ops5 (runs on trinity-1-3): successor of lane cont_ops4, operator of the D0 training leg on Orchard

Lane folder: the predecessors', /scratch/jjyeung/orch_n30/cont_ops on trinity-1-3. Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/ (write your events and STATUS.md mirror there). First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it.

## State (read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/STATUS.md and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/20261116T0554Z_RESULT_rotate.md first)
D0 is the first training leg under the trace ruling. Its CPU proof (Orchard job 170109) passed stage 1; stage 2 (every rank's first batch on CPU, two ranks at a time) runs until about 08:40Z. Its 4-GPU job B (Orchard job 170111, a15_cot_apddbe32d7) is PENDING with a start estimate of 2026-11-16T22:51Z. My GO with the cancel rules: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/20261116T0335Z_ORCH_GO_d0_job_b.md or near; stop rule: /data2/jjyeung/agent_project_data/distill_design/D0_STOP_RULE_20261116.md.

## Do
1. Watch stage 2 with the predecessor's work/d0/a2/w2.sh, one small poll every 10 minutes. When it ends: one RESULT event named a2_stage2 with, per rank, measured or not measured, rows in the batch by family, each loss term and whether it is finite, seconds and peak memory. If any measured rank raised or gave a non-finite loss: cancel job 170111 before it starts and write a BLOCKER with the lines.
2. Then leave a watcher that is a script, not an agent: one tmux session on this node that polls job 170111's state every 10 minutes through tools/ossh.sh with a timeout, writes exactly one event file named <UTC>_QUESTION_job_b_state_change.md into your events folder when the state leaves PENDING (state, start time, node), and exits; it also exits after 30 hours. Test it on a finished job id first. Say its tmux name in STATUS.md.
3. Write STATUS.md exact for the lane that will babysit job B's first steps (I launch it when the watcher fires), then a RESULT event named rotate, and stop. Do not poll the queue as an agent for the next 17 hours.
The LEG-S1 continuation packet stays unsubmitted: it needs the user's yes.

## Limits
No Git, no deletion, no paid key, no new Orchard job. Your session ends after 4 hours.
