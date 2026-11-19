W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review
readlink -f /scratch/jjyeung/envs/p1cpu/bin/python; ls -la /scratch/jjyeung/envs/p1cpu/bin/python*
cd $M/tree && mkdir -p $M/tmp && TMPDIR=$M/tmp OMP_NUM_THREADS=2 nice -n 10 timeout 900 /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest tests.test_r1_build19 2>&1 | tail -6
python3 - <<'PYEOF'
import json,base64,glob,os,re,sys,hashlib
K='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go'; O='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out'
m4=json.load(open(O+'/M400_PINS.json'))
print('M400_PINS keys',list(m4)[:20] if isinstance(m4,dict) else len(m4))
s=json.dumps(m4); 
post=set()
for m in re.finditer(r'"([^"]*(?:000414|complete\.json|rng\d+)[^"]*)"\s*:\s*"?([0-9a-f]{64})?',s): pass
print(s[:3000])
PYEOF
