K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd
nice -n 10 python3 -B -I -s - $K <<'PY'
import sys,base64,json,re;from pathlib import Path
k=Path(sys.argv[1]);s=base64.b64decode(json.load(open(k/'k/j.json'))['payload']).decode()
lines=s.split('\n')
for i,l in enumerate(lines):
    if re.search(r'HX|HM|\brm\b|\bmv\b|CUR|cd |tk_stage\(\)|joined|KITX|model staged|stage full',l): print(i,l[:240])
PY
