F=/scratch/jjyeung/orch_n30/fb_pack; cat $F/relcnt/out/REPORT.md | head -60; echo ===BIND; head -c 2500 $F/relcnt/out/BINDING.json; echo; ls $F/route/out
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/BLOCKER_DIAGNOSTICS.json'))
s=json.dumps(d); print(len(s)); print(s[:3000])
PY
