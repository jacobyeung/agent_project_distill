<!-- recovered by seal_plan: transcript=71f94277 line=12045 utc=2026-11-12T11:58:12.788Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/result-devs1-route-table-predicted-masks-20261112.md <<'EOF'
---
name: result-devs1-route-table-predicted-masks-20261112
description: First route table decided on held-out scenes with deployed predicted masks - only absolute distance routes (+8.1); direct wins by 8 to 28 points on direction, relative distance, counting, size; unproposed objects are the main mask loss
metadata:
  type: project
---

Route table on dev-S1 (held-out scenes), 2026-11-12: deployable program (segmenter candidates + frozen selector, tower pose and G3T depth, frozen fusion policy) against CP1 m200's own answers on the same primary items, paired 95% intervals over rooms. File: `/scratch/jjyeung/orch_cd/evalx/events/20261112T1156Z_RESULT_devs1_route_table_predicted_masks.md`; data `/scratch/jjyeung/orch_cd/devs1_masks/cache_r1/ROUTE_PREDICTED.md`.

| Type | Direct | Program | Program minus direct | Verdict |
|---|---|---|---|---|
| Absolute distance | 38.9 | 46.9 | +8.1 [+0.9, +16.9] | route |
| Room size (36 items) | 55.6 | 62.2 | +6.7 [-14.4, +25.0] | undecided |
| Object size | 68.1 | 60.5 | -7.6 [-14.5, -0.9] | direct |
| Direction hard | 78.7 | 68.7 | -10.0 [-19.8, -1.4] | direct |
| Counting | 58.4 | 44.2 | -14.2 [-24.6, -4.9] | direct |
| Direction easy | 91.3 | 70.7 | -20.7 [-34.7, -8.7] | direct |
| Direction medium | 88.7 | 61.3 | -27.3 [-41.9, -14.3] | direct |
| Relative distance | 72.0 | 44.0 | -28.0 [-40.3, -16.4] | direct |

- With ground-truth masks the same programs score 66.1 on absolute distance and 83.8 on counting ([[result-devs1-baseline-cp1-20261112]]), so masks are the binding constraint; the largest loss is "object never proposed" (+28.3 points on absolute distance, +23.2 on counting), losses are largest on ScanNet++.
- "Direct" here is CP1's own reasoning with self-asserted tool responses (no tool runs in the read).

**Why:** it confirms on held-out scenes that the leg should train program rows only for absolute distance, room size and the camera types ("frozen table, no flag"), and that a route-everything configuration would cost 10 to 28 points on four types at runtime.
**How to apply:** treat proposal recall of the segmenter (denser prompts or frames, or grounding from the student's own encoder) as the next lever before routing any further type; re-price this table after any mask change with `devs1_masks` (0.4 GPU-h + CPU).
EOF
printf '%s\n' '- **READ FIRST, result 11-12:** [Route table on held-out scenes](result-devs1-route-table-predicted-masks-20261112.md) predicted masks: only abs distance routes (+8.1); direct wins by 8-28 on direction, rel distance, counting, size; unproposed objects are the main loss' >> $M/MEMORY.md
DD=/data2/jjyeung/agent_project_data/distill_design; printf '%s\n' '| Route table decided on held-out dev-S1 with deployed predicted masks (CP1 m200 direct vs deployable program, paired intervals over rooms): route absolute distance (+8.1 [+0.9, +16.9]); room size undecided (+6.7 [-14.4, +25.0], 36 items); direct for size (-7.6), direction hard (-10.0), counting (-14.2), direction easy (-20.7), medium (-27.3), relative distance (-28.0); main mask loss = object never proposed (+28.3 abs distance, +23.2 counting) | DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT_20261112.md | RESULT 11-12 (data: /scratch/jjyeung/orch_cd/devs1_masks/cache_r1/ROUTE_PREDICTED.md) |' >> $DD/INDEX.md
echo "$(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1156Z ROUTE TABLE on held-out dev-S1 with deployed predicted masks: route abs distance (program 46.9 vs direct 38.9, +8.1 [+0.9, +16.9]); room size undecided (+6.7 [-14.4, +25.0]); direct wins: size -7.6, direction hard -10.0, counting -14.2, direction easy -20.7, medium -27.3, rel distance -28.0; main loss = object never proposed (+28.3 / +23.2 pp); losses largest on ScanNet++; ARKit routes abs distance +18.1. Confirms the 'frozen table, no flag' ruling. Kit defect: price_masks.py fails writing MASK_DIAGNOSTICS (int64 JSON cast) after PER_ITEM is complete; fix owed (small). Memory + INDEX saved." >> ORCH_HANDOFF.md