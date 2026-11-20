K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd
nice -n 10 python3 -B -I -s - $K <<'PY'
import sys,base64,json;from pathlib import Path
k=Path(sys.argv[1]);s=base64.b64decode(json.load(open(k/'k/j.json'))['payload']).decode()
lines=s.split('\n')
for i in list(range(28,40))+list(range(150,160))+list(range(380,436)): print(i,lines[i][:260])
PY
