<!-- recovered by seal_plan: transcript=71f94277 line=10140 utc=2026-11-12T05:06:34.317Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat > $M/result-revsi-student-reads-20261112.md <<'EOF'
---
name: result-revsi-student-reads-20261112
description: First final student reads on ReVSI official999 - CP1 m200 58.63 (budget 2,048), T0 m800 45.65; facing-away direction items fail by a 180-degree rotation
metadata:
  type: project
---

ReVSI official999, label tier 32, 32 frames in the duplicate layout, greedy, reviewed kits (2026-11-12; files under `/scratch/jjyeung/orch_cd/evalx/events/`, `20261112T0506Z_RESULT_reviewed_kits_adopted.md` and `20261112T0453Z_RESULT_rv999_cp1on_PROVISIONAL.md`):

- CP1 m200: 57.26 thinking on (16K cap), 58.63 at the dev-frozen budget 2,048, 58.86 at 4,096. Per type at 2,048: route 42.9, abs distance 65.6, size 63.4, rel direction 48.4, counting 64.6, rel distance 72.6, room 53.0. Only 16 capped items.
- T0 m800 thinking on: 45.65; 253 of 999 items hit the cap (size and abs distance run away).
- Bars: GeoWeaver-10B 57.5 (open), Argon 86.60 and Carbon 89.76 (closed); see [[closed-model-bars-20261111]].
- Defect: the 33 "facing in the opposite direction of X" direction items score 15.4 (easy) and 0.0 (hard) for both checkpoints; the chosen option is the label rotated 180 degrees on 26 of 33. No training row has that wording. Lane `back_dir` builds facing-away rows; scores on those items must be reported as adapted to the benchmark's question format.
- Scoring contract (kits' SEMANTICS.md): a parsed answer scores even when the generation hits the cap; unclosed thinking scores 0.

**Why:** this is the parent's baseline for the next leg and the first measured gap to the closed models on ReVSI (about 28 points).
**How to apply:** compare later checkpoints on the same protocol line; thinking on with budget 2,048 for the CP1 lineage ([[lesson-eval-frame-layout-must-match-training-20261111]]).
EOF
printf '%s\n' '- **Result 11-12:** [ReVSI student reads](result-revsi-student-reads-20261112.md) CP1 m200 58.63 (B2048) / T0 45.65 on official999; open bar 57.5, closed 86.6-89.8; facing-away direction items rotated 180 deg (26/33)' >> $M/MEMORY.md
cd /scratch/jjyeung/orch_cd; echo "$(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 0506Z reviewed_kits_adopted: four reviewed kits adopted on 2-18 and 1-18 (stages reviewed_r3; seals 7beedfe5 / ebba5f5d / 3721dc72 / 02cf823e / d5d00e1f; authorization ~3 h, rebind after). CP1 m200 ReVSI official999 FINAL = provisional: 57.26 ON16k, 58.63 B2048, 58.86 B4096. Memory saved (result-revsi-student-reads-20261112)." >> ORCH_HANDOFF.md