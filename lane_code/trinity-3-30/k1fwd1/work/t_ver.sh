D=/scratch/jjyeung/orch_n30/sb_own400/in/own_400; cd $D; ls -la
F=own_400_173346.result.tar.gz.partial
s=$(stat -c %s $F); h=$(sha256sum $F | cut -c1-64); echo "$s $h"
if [ "$s" = 97932195 ] && [ "$h" = b531fefc8f473dd7cb84f7ebc8c575089a9609e128fb2ef536ef71d9e2e9a636 ]; then mv $F own_400_173346.result.tar.gz; echo VERIFIED; fi
df -BG --output=avail /scratch | tail -1
python3 - <<'PY'
import json
n=json.load(open('/scratch/jjyeung/orch_n30/sb_scale1/out/NEEDS_INPUTS.json'))
print(type(n), list(n.keys())[:10] if isinstance(n,dict) else len(n))
caps=n['captures'] if isinstance(n,dict) and 'captures' in n else n
c=caps[0] if isinstance(caps,list) else list(caps.items())[0]
print(json.dumps(c)[:600])
PY
ls /scratch/jjyeung/orch_n30/sb_own400/kit | head; grep -n "own-root\|own_root\|glob\|own.npz\|PHASE_COMPLETE\|COMPLETE.json" /scratch/jjyeung/orch_n30/sb_own400/kit/score_400.py | head -20
