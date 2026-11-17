set -u
cd /scratch/jjyeung || exit 1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
H=orch_n30/e3_geom/work/harness
echo "== harness.py 95-170"; sed -n '95,170p' $H/harness.py | cut -c1-220
echo "== harness run.sh/README"; cat $H/run.sh; head -40 $H/README.md
echo "== INVENTORY"; head -c 1300 $H/out/INVENTORY.json; echo
echo "== manifest dirs"; ls -la orch_n30/k1_ops3/work/manifest_v2 2>&1 | head; ls orch_n30/k1_ops3/work | head -80
$PY - <<'PYEOF'
import json,collections,statistics as st
R=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/e3_geom/work/harness/out/PER_ITEM.jsonl')]
print('rows',len(R))
g=collections.defaultdict(list)
for r in R:
    if r['type']=='object_abs_distance' and r['pred'] is not None and r['pred']>0:
        g[(r['arm'],r['split'],r['dataset'])].append(r)
for k in sorted(g):
    if k[0] not in ('GT','SO+GO','S4+G1','SO+G1'): continue
    v=g[k]; rat=sorted(x['pred']/x['gt'] for x in v)
    print(k,len(v),'mra',round(100*sum(x['mra'] for x in v)/len(v),1),'med pred/gt',round(rat[len(rat)//2],3),'p10',round(rat[len(rat)//10],3),'p90',round(rat[9*len(rat)//10],3))
PYEOF
