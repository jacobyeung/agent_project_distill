W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
cat $W/w24/out/BUILD24F_REPORT.md; echo ==; ls $W/w24/out/*.tar | tr '\n' ' '; echo; ls $W/w24/work/build24f | grep -i -E "rehears|go_" | tr '\n' ' '; echo
echo "== SESS"; cat $W/w24/out/SESSION_NAMES_24F.json
