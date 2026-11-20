W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
ls -d $W/w24n 2>/dev/null && ls -la --time-style=+%H:%M $W/w24n/out 2>/dev/null | grep -v " 19:00 " | tail -12; cat $W/w24n/out/BUILD24M4N_REPORT.md 2>/dev/null
