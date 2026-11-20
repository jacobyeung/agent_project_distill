X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173796; ls $O; ls $X/u | grep -c 655b953d
python3 -I -s -B - <<'PY'
import json
O='/project/community/jjyeung/okh7/x_22c714e1/o/173796'
for n in ('materialization.json','receipt.json'):
    v=json.load(open(O+'/'+n)); print('@@',n,list(v)[:40])
    for k in ('source_deferrals','sources','legacy_compatibility','per_source','refused','contract_deferred_qids','selection','dispositions'):
        if k in v: print(' ',k,json.dumps(v[k])[:1500])
PY
