hostname -s
for d in /scratch/jjyeung/orch_n30/native_r2/work /scratch/jjyeung/orch_n30/native_r2/work/full_c8r /scratch/jjyeung/orch_n30/native_r2/out; do echo "== $d"; ls -la "$d" 2>&1 | head -40; done
