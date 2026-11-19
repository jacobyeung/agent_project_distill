W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
for k in $W/w24/work/build24d/kits/q $W/w24/out/kit_n_go $W/w23/work/build23/kits/q; do echo "== $k"; test -f $k/k/l.json || continue; python3 -B -c "
import json,sys,base64
d=json.load(open(sys.argv[1]))
if 'payload' in d: d=json.loads(base64.b64decode(d['payload']))
for key in ('init','init_old'):
  print(key, json.dumps(d.get(key))[:400])
print([k for k in d][:40])
" $k/k/l.json </dev/null; done
ls $W/w23/work 2>/dev/null | head; ls $W/w24/work/build24d/kits 2>/dev/null
