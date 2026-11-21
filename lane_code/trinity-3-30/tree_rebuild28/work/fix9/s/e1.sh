W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ; hostname -s; df -h /scratch | tail -1; nproc; free -g | head -2
echo "== n_go"; ls -la $W/w28fix/n_go | head -40
echo "== k"; ls -la $W/w28fix/n_go/k | head -40
echo "== u count"; ls $W/w28fix/n_go/u 2>/dev/null | wc -l
echo "== n30_mirror"; ls /scratch/jjyeung/n30_mirror/
for d in /scratch/jjyeung/n30_mirror/*; do echo "-- $d"; ls $d | head -20; done
echo "== W top"; ls $W | head -80
