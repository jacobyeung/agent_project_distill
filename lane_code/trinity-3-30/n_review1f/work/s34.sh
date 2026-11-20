R=/scratch/jjyeung/orch_n30/n_review/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; cd $R; sha256sum tests_tcpt_b.json tests_tcpp2_b.json
$PY - <<'PY'
import json
a=json.load(open('/scratch/jjyeung/orch_n30/n_review/r1f/tests_tcpt_b.json')); b=json.load(open('/scratch/jjyeung/orch_n30/n_review/r1f/tests_tcpp2_b.json'))
for k in a:
    fa=sorted(f[0] for f in a[k].get('failures',[])+a[k].get('errors',[])); fb=sorted(f[0] for f in b[k].get('failures',[])+b[k].get('errors',[]))
    print(k,a[k]['ok'],'run',a[k].get('run'),b[k].get('run'),'fail',len(fa),len(fb),'same' if fa==fb else 'DIFF',a[k].get('import_error','')[:150])
    for f in (a[k].get('failures',[])+a[k].get('errors',[]))[:1]: print('   ',f[0][:70],f[1][-220:].replace('\n',' | '))
PY
