# Lane trin_read3 (runs on trinity-1-3): successor of lane trin_read2, a proven read path for this lineage's exports on Trinity 48 GB cards

Lane folder: the predecessors', /scratch/jjyeung/orch_n30/trin_read on trinity-1-3 (cap 70 GB). Events folder: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/trin_read/. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. You are an operator: code changes go to Codex as the rules describe.

## Why it matters more than yesterday
D0, a training leg on 4 H100, started early. Its exports are read at steps 100 (near 13:00Z), 200 (near 16:40Z, a stop-rule read) and later, and Orchard's general queue, the primary path for those reads, is congested by hours. A proven reader on one Trinity card would take those reads out of the queue.

## Start
Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/trin_read/STATUS.md, section "Successor (trin_read3): resume here" (eight steps from the base landing to the proof RESULT), and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/trin_read/20261116T0936Z_RESULT_rotate.md. My answers in the folder, newest first, hold the conditions: the llguidance stub (accepted, four conditions), no staging on trinity-0-13, the card rule (two empty readings five minutes apart plus the process list, card line in a RESULT first, under vnice, never hold a card you do not use), base stream at priority 40 (if it has still moved no byte when you start, re-register it once at priority 0 with launch_pull2.py: the mover asked us to put urgent streams there, and the base is now urgent).

## Do
1. Poll the cards of trinity-1-18 and trinity-1-3 every 10 minutes with one batched ssh. The moment the base has landed and a card is empty in two readings: the 20-item proof with its repeat, RESULT event named proof (token-equality share, first divergences, score equality, tokens per second, minutes per item set, peak memory, the stub's call count).
2. On a passing proof, without waiting for me: read the step-544 export on the dev-S1 families (main 1,525, away 150, forward 150) on that card as the paired baseline for this reader, then each D0 milestone export as it appears (the .done markers and objects are named in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/READS_PLAN_D0.md), and write each read's packet where lane cont_ops's scoring script can take it. These are direct reads on dev-S1 items only. Say in a RESULT each time what was read and where the packet is. The stop-rule verdict is computed by cont_ops's reviewed script, not by you.
3. The launcher's camera wrapper was rebuilt and is beyond paths: I order one reader on your proof RESULT; reads of the three non-camera families do not wait for that review, camera reads do.
4. Record: /data2/jjyeung/agent_project_data/distill_design/TRINITY_READ_RUNTIME_20261116.md, kept current.

## Limits
No official benchmark item, no native or routed path, no paid key, no Orchard job, no Git, no deletion. Your session ends after 6 hours: a RESULT event named rotate before then or at 60% of your context.
