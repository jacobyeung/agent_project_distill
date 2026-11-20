W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; H=$W/w24h; I=$W/w24i; P=/scratch/jjyeung/envs/p1cpu/bin/python; M=/scratch/jjyeung/orch_n30/n_review/r1b; R=/scratch/jjyeung/orch_n30/n_review/r1d
date -u +%TZ
echo "== rt24h2"; ls -la $W/work/rt24h2 | head -30; sha256sum $W/work/rt24h2/RESULT.json; cat $W/work/rt24h2/REPORT.md
$P -I -s -B - <<'PY'
import json
v=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/rt24h2/RESULT.json'))
print('keys',list(v)[:30])
for k in ('verdict','status','failures','file_verdicts','integrity'):
    if k in v: print(k, json.dumps(v[k])[:1500])
for a in v.get('assertions',[]): print('A', a.get('pass_'), a.get('assertion'), json.dumps({x:y for x,y in a.items() if x not in ('assertion','pass_')})[:200])
for c in v.get('cases',[]): print('C', c.get('verdict'), c.get('case'), c.get('command_exit_code'), c.get('target_files'), [ (a.get('assertion'),a.get('pass_')) for a in c.get('assertions',[]) if not a.get('pass_')])
PY
echo "== w24i out"; ls $I/out | head -80
for f in CASE_24M4I.md EXACT_CONFIG_DELTA.json; do echo "#### $f $(sha256sum < $I/out/$f | cut -c1-64)"; head -c 6000 $I/out/$f; echo; done
