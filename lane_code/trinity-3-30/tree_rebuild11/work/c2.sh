W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; L=$W/w19; date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr11_cf19a "bash $W/work/conf19/cf19a.sh > $W/work/conf19/seal.log 2>&1"
sed -n 1,30p $L/work/build19/final_checks19.py | cut -c1-400
grep -n "environ" $L/work/build19/test19.py | head -8 | cut -c1-250
