D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173754/173754; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ
cd $D; ls -la . */ | head -60
$PY - <<'PY'
import json,os
D='/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173754/173754'
for n in ('chain.json','nd.json','routing_types.json','cand_cmp.json','proc_check.json','summary.json'):
    for root in (D,D+'/rd0'):
        p=os.path.join(root,n)
        if os.path.isfile(p):
            v=json.load(open(p)); print('@@',p,os.path.getsize(p))
            if n=='chain.json':
                print({k:v[k] for k in v if k not in ('streams','first_ten_refusals','candidate')})
                for s,r in v['streams'].items(): print(s,{k:r.get(k) for k in ('status','rows_checked','refused_rows','database_rows','complete','unique_rows_checked','counts')})
                print('first',v['first_ten_refusals'][:2])
            elif n=='nd.json':
                print({k:v[k] for k in v if k not in ('samples','paths','content_examples','unclassified_paths','absent_counts','state')}); print('paths',v.get('paths'))
            else: print(json.dumps(v)[:1500])
PY
