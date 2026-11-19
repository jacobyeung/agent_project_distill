W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; O=$W/w24/out
ls -la --time-style=+%H:%M $O | tail -25; cat $O/BUILD24H_REPORT.md $O/BUILD24I_REPORT.md 2>&1 | head -80; cat $O/DELIVERY_24I.json 2>&1
ls -la --time-style=+%H:%M $O/kit_n_go $O/kit_n_go/b | head -50
