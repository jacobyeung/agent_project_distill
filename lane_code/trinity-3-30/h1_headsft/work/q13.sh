set -u
D=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB
echo "=== ls"; ls -la $D | head -40
echo "=== over_b"; cat $D/over_b.json 2>&1 | head -c 20000
