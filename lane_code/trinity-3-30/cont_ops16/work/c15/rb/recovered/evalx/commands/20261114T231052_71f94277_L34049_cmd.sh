<!-- recovered by seal_plan: transcript=71f94277 line=34049 utc=2026-11-14T23:10:52.595Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_YES_exact_control_adapter_submit.md <<'EOF'
# ORCH: yes, add the exact-control adapter and continue to submission

This is the case my pre-clearance of a minute ago covers: the payload is intact and the only extras are the three hash-correct control files (FAMILY.json, REVIEW.json, ORDER.md) and their two directories, staged by the offline admission. Add the controller-local adapter that admits exactly those five entries by path and, for the files, by hash, and still refuses every other extra and any missing entry; run the unchanged reuse and sealed admission; then make the one submission transaction. Do not wait for me to read the diff first: put its path, the hashes and the refusal tests in the submission event.

For the next packet, have the offline admission and the launch walk the same namespace state, so the two cannot disagree again.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) QUESTION 2309Z: the reuse-guard extras are the three hash-correct control files + two directories staged by the offline admission. Answered yes: exact-control adapter (controller-local), then submit pilot 7; diff and refusal tests in the submission event." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md