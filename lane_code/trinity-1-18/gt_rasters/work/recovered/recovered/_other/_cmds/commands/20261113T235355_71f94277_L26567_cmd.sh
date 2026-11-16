<!-- recovered by seal_plan: transcript=71f94277 line=26567 utc=2026-11-13T23:53:55.176Z kind=commands original_path=(bash command)  -->
I=/data2/jjyeung/agent_project_data/distill_design/INDEX.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$I" <<'EOF'
import sys
f = sys.argv[1]
t = open(f).read()
old = "own-policy arms decide."
key = "LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md): LEG-S1 step-100 rules clarified before any leg read: seven tested types, forced closes for the cap clause (parent already at 2.23 per 100), own-policy arms decide."
assert t.count(key) == 1
t = t.replace(key, key[:-1] + "; producer errors are their own disposition (kept at zero, validity bound, paired-exclusion sensitivity).")
open(f, "w").write(t)
print("ok")
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: appended Ruling 4 (producer errors) to distill_design/LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md and extended its INDEX line." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md