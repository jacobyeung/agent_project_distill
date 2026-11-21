W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
hostname -s; df -h /scratch | tail -1; uptime
echo "=== T_JN6_USAGE"; cat $W/w24z16b/out/T_JN6_USAGE.md
echo "=== ls w26t5"; ls $W/w26t5 $W/w26t5/work 2>&1 | head -40
echo "=== ls w24z16b"; ls $W/w24z16b $W/w24z16b/out $W/w24z16b/work 2>&1 | head -40
echo "=== kit"; K=$W/w27fix/n_go; ls -la $K $K/b | head -60
echo "=== job.sh"; cat $K/job.sh
echo "=== j.sh"; cat $K/j.sh
echo "=== ls w28fix"; ls $W/w28fix 2>&1 | head
