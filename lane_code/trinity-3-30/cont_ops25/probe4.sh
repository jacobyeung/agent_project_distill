G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
grep -n 'missing\|store\|sha' $G/orchard_tower2x_b/REPORT_K3.md | head -12
M=$G/work/payload/b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json
/scratch/jjyeung/envs/p1cpu/bin/python - "$M" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
s=json.dumps(d)
import re
i=s.find('41069054'); print(s[i-300:i+600])
PY
ls /scratch/jjyeung/k1_frames | head -5; ls /scratch/jjyeung/devs1_r2 | head; ls /scratch/jjyeung/orch_n30/nvkey1/work/c0stage | head
grep -o '"frames[^,]*' /scratch/jjyeung/orch_n30/nvkey1/work/c0/C0_MANIFEST.json | head -3
