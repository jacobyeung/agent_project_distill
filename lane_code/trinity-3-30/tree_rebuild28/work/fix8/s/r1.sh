W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W || exit 1
echo "== ls W"; ls
echo "== w24z11b/out"; ls -la w24z11b/out | head -50
echo "== arm_launch.sh"; wc -c w24z11b/out/arm_launch.sh; cat w24z11b/out/arm_launch.sh | head -200
for d in w24z12 w27fix w28fix; do echo "== $d"; ls -la $d | head -30; done
df -h /scratch | tail -1
