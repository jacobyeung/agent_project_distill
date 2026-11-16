hostname -s
ls -la /scratch/jjyeung/envs/ 2>&1
ls /scratch/jjyeung/envs/p1cpu/bin 2>&1 | head -5
readlink -f /scratch/jjyeung/envs/p1cpu/bin/python 2>&1
/scratch/jjyeung/envs/p1cpu/bin/python -V 2>&1
cat /scratch/jjyeung/envs/p1cpu/pyvenv.cfg 2>&1
ls /scratch/jjyeung/orch_n30/tree_rebuild 2>&1; cat /scratch/jjyeung/orch_n30/tree_rebuild/STATUS.md 2>&1 | head -30
