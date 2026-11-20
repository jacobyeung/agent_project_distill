W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls 2>&1 | grep tr17
for d in cov24c1 cps24t1; do echo "== $d"; ls $W/work/$d | grep -v decoded; cat $W/work/$d/REPORT.md 2>/dev/null | cut -c1-700; done
echo "== job.sh n"; cat $W/w24e/work/build24/kits/n/job.sh | head -60
