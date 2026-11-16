<!-- recovered by seal_plan: transcript=71f94277 line=6676 utc=2026-11-11T20:54:01.049Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/closed-model-bars-20261111.md <<'EOF'
---
name: closed-model-bars-20261111
description: Measured bars of the closed frontier models on VSI-500, ReVSI-999 and VSTI-450 at 32 frames, and why ReVSI reads about 10 points higher than VSI-Bench
metadata:
  type: reference
---

Closed-model bars for goal 1 (lane frontier_read, final 2026-11-11; 32 frames at 1024x768, main's no-tool prompt and scorer, T=0, 32,768 output cap; task macro with 95% scene bootstrap):

| Model | VSI-500 (main's lane, provisional) | ReVSI-999 | VSTI-450 v3 |
|---|---|---|---|
| Argon high | 76.68 | 86.60 [84.78, 88.45] | 83.33 [80.74, 85.73] |
| Carbon medium | 75.97 | 89.76 [88.25, 91.22] | 82.29 [79.71, 84.91] |
| Gemini 3.1 Pro (main) | 62.8 | 65.9 | 57.2 (5,736) |

- On VSTI the closed models are weak on camera displacement (43.2 / 36.0) and camera movement direction (64.0 / 68.0), which is where our tower's pose is strong.
- ReVSI reads higher than VSI-Bench for two measured reasons: its labels are tied to the 32 frames shown (on label-moved pairs the models' answers sit closer to the ReVSI label 14 of 19 and 13 of 19 times), and its priors are easier (best constant answer 39.9 against 33.3). VSI-Bench labels come from the whole scan.
- Open bars for comparison: ConsiSpace 76.6 and GeoWeaver-10B 75.05 on VSI-Bench; GeoWeaver-10B 57.5 on ReVSI. See [[sota-bars-9b-20261109]].

Record: /data2/jjyeung/agent_project_data/distill_design/FRONTIER_READ_20261111.md. Related: [[lane-intent-two-goals-20261111]].
EOF
echo "- **Reference 11-11:** [Closed-model bars](closed-model-bars-20261111.md) Argon 76.68 / 86.60 / 83.33 and Carbon 75.97 / 89.76 / 82.29 on VSI-500 / ReVSI-999 / VSTI-450; ReVSI labels are frame-tied; closed models weak on VSTI camera motion" >> $M/MEMORY.md; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; sed -i '/^frontier_read|/d' $S/LANES; echo "$(date -u +%Y-%m-%dT%H:%MZ) frontier_read RESULT 2052Z FINAL: Argon high VSI-500 76.68 / ReVSI-999 86.60 [84.78,88.45] / VSTI-450 83.33 [80.74,85.73]; Carbon medium 75.97 / 89.76 [88.25,91.22] (2 unanswered) / 82.29 [79.71,84.91] (2 unanswered); per task in the RESULT; 3,267 calls, 111.9M input / 21.0M output tokens, 0 x 429; record FRONTIER_READ_20261111.md + INDEX row; answers in frontier_read/work/runs_final. Memory saved (closed-model-bars-20261111). Lane done; row dropped." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md