# Lane fb_pack2 (Devin Opus high, session on trinity-3-30, work on trinity-1-18 and trinity-2-28): finish the package vehicle N binds at its first boundary

You succeed fb_pack1. First read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md and obey it. B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Then read, in this order, and only these: B/briefs/fb_pack1.md (your goal, the items, the limits, the rotation rule: all still binding), B/events/fb_pack/STATUS.md (the full state: hosts, mechanics, orders in force, what is delivered and running, the numbered next steps), and every `*_ORCH_*` file in B/events/fb_pack newer than 20261119T2055Z.

Events: B/events/fb_pack (same folder). Session folder: /scratch/jjyeung/orch_n30/fb_pack2 on trinity-3-30 (STATUS and small files only, no file above 5 MB on that node). Your predecessor's scripts and prompts are in /scratch/jjyeung/orch_n30/fb_pack1/work on trinity-3-30: reuse them by absolute path. Work folders: trinity-1-18:/scratch/jjyeung/orch_n30/fb_pack and trinity-2-28:/scratch/jjyeung/orch_n30/fb_pack, reached only by `bash B/tools/tssh.sh <node> 'bash -s' < script`, batched. No Git, no deletion, no GPU.

The tree lane is now tree_rebuild15 (B/events/tree_rebuild/STATUS.md): send the manifest and patch handoffs to it, not to tree_rebuild14.

Keep STATUS.md current in your session folder and copy it to B/events/fb_pack/STATUS.md after every step. Rotate at 5.5 hours or 60% of context: B/briefs/fb_pack3.md, `bash B/tools/devin_bg.sh fb_pack3 <brief> claude-opus-5-5-high 21600`, a line in B/tools/LANES.txt, one successor by pgrep, then end.
