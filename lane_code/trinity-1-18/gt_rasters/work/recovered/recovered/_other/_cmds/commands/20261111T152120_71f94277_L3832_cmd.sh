<!-- recovered by seal_plan: transcript=71f94277 line=3832 utc=2026-11-11T15:21:20.496Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > frontier_read/inbox/${T}_ORCH_explain_revsi_gap.md <<'EOF'
# ORCH: while paused, explain on CPU why Argon and Carbon score about 10 points higher on ReVSI than on VSI-500
Your partial table has Argon high at 76.68 on VSI-500 and 86.7 on ReVSI (748 items), Carbon medium 75.97 and 88.2, while Gemini 3.1 Pro moves only from 62.8 to about 65. This sets the bar for our student ("beat Argon and Carbon"), so I need to know what the gap is made of before I quote it. No call on the key; use the answer files you have and main's VSI-500 answer files if they are readable as named files (ask main's lane paths from your notes; do not search).
1. Is the 748 or 782 subset biased? Compare its type mix and scene mix with the full 999, and give the score reweighted to the full type mix.
2. Per question type, VSI-500 against ReVSI for each model: which types carry the gap.
3. Where ReVSI items derive from VSI-Bench questions (same scene and question, changed label or options), pair them: on items whose label changed, how often does the model match the new label and not the old one? That measures how much of VSI-Bench's shortfall is label noise.
4. Differences of protocol that could inflate ReVSI: answer format and options, metric (MRA thresholds, exact match), frame tier, prompt. State each and whether it differs.
5. The no-information baselines on both sets (best constant or prior per type), so the scores can be read above chance.
Post one RESULT (at most 15 lines) and add the table to your record draft.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) frontier_read asked (CPU, key paused) to decompose the VSI-500 vs ReVSI gap of Argon/Carbon: subset bias, per-type, paired label changes, protocol differences, no-info baselines." >> ORCH_HANDOFF.md