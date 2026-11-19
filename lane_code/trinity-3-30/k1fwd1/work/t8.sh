K=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
sed -n 30,80p $K/native_kit/boundaries.py | cut -c1-400
grep -rn "def verify_trainer" -A25 /scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7/reference 2>/dev/null | head -40
