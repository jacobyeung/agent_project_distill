Q=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build21/kits/q
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json,base64;d=json.load(open('$Q/k/j.json'));s=base64.b64decode(d['payload']).decode()
L=s.split('\n');i=[n for n,l in enumerate(L) if 'g.py' in l]
print(len(L),i)
for n in range(max(0,i[0]-3),min(len(L),i[0]+40)): print(n,L[n][:260])
"
