W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21/pkg
head -c 1500 $W/work/conf21/ff_focused.log; echo; head -c 600 $W/work/conf21/ff_edges.log; echo; ls $C/work/build21 | wc -l; ls $C/work/build21 | tr '\n' ' ' | head -c 3000
python3 - <<'PY'
import json,collections
for m in (400,600):
  f=json.load(open(f'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/build21/proofs/capacity/{m}/q/f.json'))
  print(m,'ranks',json.dumps(f['ranks'])[:600])
  by=collections.defaultdict(list)
  for r in f['records']: by[r['rank']].append((r['step'],r['microstep'],r['stream'],r['index'],round(r['loss'],4)))
  for k,v in by.items(): print(m,k,len(v),v[:4])
PY
