<!-- recovered by seal_plan: transcript=71f94277 line=11095 utc=2026-11-12T08:19:21.049Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > evalx/inbox/${T}_ORCH_r5_review_accept.md <<'EOF'
# ORCH: the r5 dev merge is ACCEPTED (review: /scratch/jjyeung/orch_cd/devs1_direct/REVIEW_VERDICT_R5.md)
The reviewer rescored every primary item from the raw journal text with its own scorer: 0 items differ in all three arms. So the CP1 m200 dev-S1 baseline is FINAL: primary stratum (1,375 items, true timing) 71.28 thinking on, 71.64 at budget 2,048 (its dev-frozen budget) and at 4,096; the facing-away cell 14.0. Drop the provisional label on these.
Rules from the review: (1) the ONLY baseline number is the primary stratum from the report files (report/*.json); never quote the `summary_*.json` overall (0.6715 / 0.6788), which mixes in the route items scored against their own labels; (2) when you report a budget arm, add the forced-close count per type from the receipts (the report's capped columns read 0 there); (3) a test fixture with a valid but wrong letter is still missing; I will have it added in a later small pass, it changes no score.
Use the r5 adapter for the merges of the remaining cells when a card returns.
EOF
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat > $M/result-devs1-baseline-cp1-20261112.md <<'EOF'
---
name: result-devs1-baseline-cp1-20261112
description: Baseline of the next leg's parent on the held-out dev set dev-S1 - CP1 m200 71.64 primary (budget 2,048); facing-away items 14.0; the comparison rule and its limits
metadata:
  type: project
---

dev-S1 comparator read of CP1 m200 (2026-11-12; reviewed, final). Files: `/scratch/jjyeung/orch_cd/devs1_direct/out/r5/MERGE_RESULTS.md`, review `/scratch/jjyeung/orch_cd/devs1_direct/REVIEW_VERDICT_R5.md`, cells `/scratch/jjyeung/orch_cd/devs1_direct/out/r3` (main) and `out/r4` (facing-away and forward twins), fixed item list `/scratch/jjyeung/orch_cd/evalx/out/DEV_S1_ITEMS_v1.jsonl`.

- Protocol: 32 frames duplicate, true frame timing (24 / 60 / 10 fps by dataset), greedy, thinking on; primary stratum = 1,375 items whose label agrees with the released answer by option content; 150 route items reported apart.
- CP1 m200: 71.28 thinking on, 71.64 at budget 2,048. Per type: abs distance 38.9, counting 58.4 (below the constant "2" at 60.9), direction easy 91.3 / medium 88.7 / hard 78.7, rel distance 72.0, size 68.1, relative count 59.7, relative size 92.0, room 55.6 (36 items). Route items (own labels) 29.3.
- Facing-away direction items (150, held-out): 14.0 (easy 24, medium 12, hard 6), below every constant; 95 of 150 answers are the facing-toward answer.
- With ground-truth masks and tower geometry under the frozen fusion policy, programs score 66.1 on abs distance on these scenes (`devs1_price/out/PRICE_DEVS1.md`).

**Why:** this is the baseline for the leg's m100 reversal rule. dev-S1 scenes are held out of the new leg only; the parents saw them, so use paired leg-versus-parent comparisons, not absolute claims.
**How to apply:** read every later checkpoint on the same cells with the r5 adapter; quote only the primary stratum from the report files, never the summary overall. A placeholder frame rate voided the first run ([[lesson-eval-frame-layout-must-match-training-20261111]] applies to timing too).
EOF
printf '%s\n' '- **Result 11-12:** [dev-S1 baseline of the parent](result-devs1-baseline-cp1-20261112.md) CP1 m200 71.64 primary (B2048); abs distance 38.9; facing-away 14.0; true frame timing required; quote the primary stratum only' >> $M/MEMORY.md
echo "$(date -u +%Y-%m-%dT%H:%MZ) Opus review of the r5 dev merge: ACCEPT (independent rescoring: 0 of 1,375 primary items differ in all three arms; kits' bytes unchanged; budget counts confirmed). CP1 m200 dev-S1 baseline FINAL: 71.28 ON / 71.64 B2048; facing-away 14.0. Optional fixes (wrong-letter test fixture; forced-close counts in the budget report; summary overall must not be quoted). Told evalx; memory saved." >> ORCH_HANDOFF.md