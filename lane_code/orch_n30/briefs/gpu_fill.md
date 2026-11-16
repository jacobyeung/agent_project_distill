# Lane gpu_fill (Claude Opus subagent on trinity-3-30): keep free Trinity 48 GB cards working on distillation's queue (USER 2026-11-16: "use the GPUs wisely as much as you can"; vnice on every large-GPU node except 0-13)
Read B/tools/CLAUDE_LANE_RULES.md and LANE_RULES.md first (B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30). Events B/events/gpu_fill/. Folder /scratch/jjyeung/orch_n30/gpu_fill.

## GPU rules (bind every launch you make or order)
- trinity-0-13: normal priority. Every other node: only under /data3/shared/scripts/vnice/vnice.sh (read its usage there first). Never trinity-0-8, 0-23, 3-23; leave 0-18 free; nothing on 2-18 or 2-28. The main project has priority over every GPU: never take a card main is about to use; at most 2 nodes or 16 GPUs at normal priority in total.
- A card counts as free only after two nvidia-smi readings 5+ minutes apart show it empty (memory near 0, no process). Record both readings in the launch event.
- vnice work can be preempted (SIGTERM): every job must resume from its own records, and work vnice killed is not rerun without ORCH word.
- Before staging more than 20 GB on any node's /scratch, tell the main orchestrator first: read /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/nontraining-orchestrator-inbox-channel.md and lesson-tell-main-before-staging-on-shared-node-20261114.md for the channel. Keep each node's /scratch 150 GB free (1-3: 300 GB).

## Do
1. Free-card map every 10 minutes from the monitor page http://trinity.vision.cs.cmu.edu:53240/ (one curl, no ssh; parse per node and card: model, memory used, utilization, user). Write the current map to B/events/gpu_fill/FREE_CARDS.md (overwrite; at most 40 lines) with a UTC stamp. Use ssh (only via tools/tssh.sh) solely for the two confirming nvidia-smi readings on a node you intend to use.
2. Ready GPU work, in this order:
   a. Lane trin_read3 (Devin on trinity-1-3, events B/events/trin_read/) holds a staged reader root (19 GB base + root) for one 48 GB card: a 20-item proof, then the step-544 dev-S1 baseline, then D0 milestone reads. It is allowed any permitted node: when you confirm a free card, write B/events/trin_read/<UTC>_ORCH_CARD_<node>_<card>.md naming node, card, both readings and the vnice requirement; trin_read3 stages over InfiniBand and launches. Do not launch its work yourself.
   b. K1 own phase (lane k1_ops6, events B/events/k1_ops3/): if Orchard general stays busy, a Trinity card may run it; offer cards there the same way.
   c. Work that lane queue_synth (record /data2/jjyeung/agent_project_data/distill_design/NEXT_QUEUE_20261116.md, briefs in /scratch/jjyeung/orch_n30/queue_synth/briefs/) ranks for Trinity cards once it lands: tell me in a RESULT which items fit the free cards; I assign owners.
3. Each hour, a RESULT with card-hours used vs available on permitted nodes and what blocked use.
Stop at 22:45Z with STATUS.md for a Devin successor. Final message at most 15 lines.
