set -u
hostname -s
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
echo "== w26trace exists?"; ls -d $W/w26trace 2>&1
echo "== envs"; ls /scratch/jjyeung/envs/ 2>&1
echo "== W"; ls $W
echo "== w26fix"; ls $W/w26fix; echo "-- n_go"; ls -la $W/w26fix/n_go; ls $W/w26fix/n_go/b $W/w26fix/n_go/k 2>&1
echo "-- tree"; ls $W/w26fix/tree; ls $W/w26fix/tree/* | head -80
echo "== a.py"; cat $W/w26fix/n_go/b/a.py | head -150
echo "== build24k"; ls $W/w24/work/build24k 2>&1 | head -60
for d in $W/w24*/work; do echo "-- $d"; ls $d | head -40; done
