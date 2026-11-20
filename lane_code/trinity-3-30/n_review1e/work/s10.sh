W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
grep -E " (b/v.py|b/resolve.py|b/l.py|job.sh|b/job.sh)$" $W/w24m/out/kit_n_go/SHA256SUMS.txt; ls $W/w24m/out/kit_n_go $W/w24m/out/kit_n_go/b | head -60
ls -la --time-style=+%H:%M $W/w24o/out 2>/dev/null | grep -v " 19:00 " | tail -8
