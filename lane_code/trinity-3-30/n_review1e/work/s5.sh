W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
ls -la --time-style=+%H:%M $W/w24m/out | grep -v "Dec 31\|1969" | tail -25
cat $W/w24m/out/BUILD24M4M_REPORT.md $W/w24m/out/*.sha256 2>/dev/null
ls -t /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/ | head -6
