<!-- recovered by seal_plan: transcript=71f94277 line=33585 utc=2026-11-14T20:57:07.212Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ANSWER_middle_scenario_basis.md <<'EOF'
# ORCH answer: yes to the middle scenario's basis; lookup received

1. Middle scenario: as you propose. From pilot 7's own token and call journals, classify budget and call-limit finishes as capped; estimate each type's capped count in the full cohort as ceil(type count × capped pilot fraction); show the pilot's sample counts beside it and say it is an extrapolation from ten pairs. The zero-capped and all-capped bounds bracket it.
2. Training-universe lookup: noted (the generator resolves a row's operands against ground-truth instance labels, with no capture-wide candidate list). Put one sentence on it in every report of this family, next to the universe rule: the model was trained on responses from ground-truth instances, and this read serves the same calls from frozen mask proposals chosen among the capture's cached phrases. No code change follows from it.

Continue with the order; no further confirmation needed.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 2056Z: middle cap scenario = pilot 7's capped fraction per type x cohort count (approved). Lookup: the sealed row generator resolves operands against GT instance labels (no capture-wide universe) -> caveat sentence in every report; no code change." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md