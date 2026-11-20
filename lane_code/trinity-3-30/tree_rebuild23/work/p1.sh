J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2; date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1
tmux ls 2>&1 | grep -E "tr2|cur" ; ls -l $J/out | tail -30; tail -15 $J/work/build24m4y2/package_rerun_lane.log
ls $J/out/*.sha256 2>/dev/null && cat $J/out/*.sha256
f=$(ls $J/out/PACKAGE_CHECK*.json $J/work/build24m4y2/PACKAGE_CHECK*.json 2>/dev/null | head -1); echo PC=$f; test -n "$f" && head -c 1500 $f
