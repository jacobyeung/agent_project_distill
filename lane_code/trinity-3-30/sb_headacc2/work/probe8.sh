R=/scratch/jjyeung/orch_n30
echo "@@@ DEBUG"; head -c 6000 $R/sb_kbox3/out/DEBUG.md 2>&1
echo; echo "@@@ logs"; tail -c 1800 $R/sb_kbox3/out/box_ladder/serving_scale_audit.log 2>&1; echo; tail -c 1800 $R/sb_kbox3/out/box_ladder/serving_guard_audit.log 2>&1
echo; echo "@@@ receipt"
/usr/bin/python3 - <<'PYEOF'
import json
T='/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/'
d=json.load(open(T+'tables/TABLE_RECEIPT.json'))
print({k:(str(v)[:300]) for k,v in d.items() if k not in ('gt_set','files','gt_canvas_map')})
r=json.load(open(T+'REPORT.json')); print('REPORT keys', list(r.keys())[:40]); print({k:str(r[k])[:200] for k in list(r.keys())[:40] if not isinstance(r[k],(dict,list))})
import glob, os
p='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/'
for f in ('data/SCALES_S4.json','data/TABLES_RECEIPT.json','data/RECEIPT.json','work/run_iso/selector_head.json'):
    q=p+f
    if os.path.exists(q): print('##', f, open(q).read()[:900])
print(sorted(os.listdir(p+'data'))[:30])
PYEOF
