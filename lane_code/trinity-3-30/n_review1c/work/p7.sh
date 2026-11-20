H=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/hash24h1
date -u +%TZ; ls -la $H $H/DIFFS | head -50
echo "@@@ REPORT"; cat $H/REPORT.md
echo "@@@ LOOP_HASHES.md $(stat -c %s $H/LOOP_HASHES.md)"; head -c 6000 $H/LOOP_HASHES.md
echo "@@@ json keys"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;v=json.load(open('$H/LOOP_HASHES.json'));print(type(v).__name__, list(v)[:30] if isinstance(v,dict) else len(v))
for k in v:
  if k!='files' and k!='rows': print(k, json.dumps(v[k])[:800])
"
