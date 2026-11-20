cd /scratch/jjyeung/orch_n30/sb_own400 && /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json
b=json.load(open('out/BARS_FROZEN.json')); print('bars keys',list(b)); print('step400',b.get('step400')); print({k:b[k] for k in b if k not in ('captures','folds','input_sha256')})
r=b['captures'][0]; rec=json.load(open(r['own544']['receipt'])); print('544 ckpt',rec['checkpoint'])
g=json.load(open('kit/inputs/G3T_FOV.json')); print('G3T_FOV keys',list(g)[:8], type(g))
bb=json.load(open('out/BARS_FROZEN_B.json')); print('barsB keys',list(bb)); print({k:(bb[k] if len(json.dumps(bb[k]))<600 else '...') for k in bb})
P
ls /scratch/jjyeung/orch_n30/fb_pack/; df -h /scratch | tail -1
