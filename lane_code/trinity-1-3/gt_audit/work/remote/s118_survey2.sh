set -u
cd /scratch/jjyeung || exit 1
PY=/scratch/jjyeung/envs/p1cpu/bin/python; [ -x $PY ] || PY=python3
echo "== py $PY"
K=orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json
sha256sum $K
$PY - "$K" <<'PYEOF'
import json,sys,collections
d=json.load(open(sys.argv[1]))
print('top', type(d).__name__, list(d.keys())[:30] if isinstance(d,dict) else len(d))
caps=d.get('captures') if isinstance(d,dict) else d
if isinstance(caps,dict): caps=list(caps.values())
print('ncaps',len(caps))
c0=caps[0]; print('cap keys',sorted(c0.keys()))
for k,v in c0.items():
    if k!='rows': print(' ',k,json.dumps(v)[:300])
rows=c0.get('rows',[]); print('nrows cap0',len(rows))
if rows: print('row0',json.dumps(rows[0])[:2500])
cnt=collections.Counter()
for c in caps:
    for r in c.get('rows',[]):
        cnt[(c.get('k1_split') or c.get('split'), (c.get('canonical') or '').split('/')[0], r.get('type') or r.get('question_type'))]+=1
for k,v in sorted(cnt.items(), key=str): print(k,v)
PYEOF
echo "== harness out"; ls -la orch_n30/e3_geom/work/harness/out | head; head -c 2000 orch_n30/e3_geom/work/harness/out/PER_ITEM.jsonl; echo
echo "== harness item()"; grep -n -E "def item|gt|label|answer" orch_n30/e3_geom/work/harness/harness.py | cut -c1-200 | head -50
echo "== t1_gt prefixes"; ls orch_cd/dose_pool/out/t1_gt/gt | sed 's/__.*//' | sort | uniq -c; du -sh orch_cd/dose_pool/out/t1_gt/gt orch_cd/dose_pool/out/arkit_gt/gt
echo "== render sample"; ls orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/render | head -3; d=$(ls -d orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/render/*/ | head -1); ls -la $d; for f in $d*; do echo "-- $f"; head -c 1500 $f; echo; done 2>/dev/null | head -60
