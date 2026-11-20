W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; H=$W/w24h; date -u +%TZ
cd $H/out/kit_n_go && nice -n 10 python3 - <<'PY'
import json,base64,glob
for f in sorted(glob.glob('k/*.json')):
    try: d=json.load(open(f)); s=base64.b64decode(d['payload']).decode() if isinstance(d,dict) and 'payload' in d else json.dumps(d)
    except Exception as e: s=open(f).read()
    i=s.find('7a910565')
    if i>=0: print(f, s.count('7a910565'), s[max(0,i-300):i+120].replace('\n',' '))
PY
grep -rn "7a910565" $H/out/BUILD24M4H_EVIDENCE.md | head -5 | cut -c1-500; grep -n "7a910565" $H/out/OFFLINE.json $H/work/build24m4h/OFFLINE.json 2>/dev/null | head -3 | cut -c1-400
