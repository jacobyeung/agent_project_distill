D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817; cd $D; date -u +%TZ; ls | tr '\n' ' '; echo
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
t=json.load(open('timings.json'))
for k in ('returncode','post_returncode','aggregate_limit_status','aggregate_publication_bytes','publication_errors','log_tail_errors','routing_types','routing_types_refusal','nsample','task_a','proc_status','rdiff_status','rdiff_returncode'):
    if k in t: print(k, json.dumps(t[k])[:1500])
c=json.load(open('chain.json')); print('CHAIN', {k:c.get(k) for k in ('status','all_streams_status','refused_rows','extent_exempted_rows','extent_still_checked_rows','first_ten_refusals')}, json.dumps(c.get('extent_scope',{}))[:900])
n=json.load(open('nd.json')); print('ND', {k:(v if not isinstance(v,(list,dict)) else type(v).__name__+str(len(v))) for k,v in n.items()}); print('ND meta', json.dumps(n.get('metadata_classes'))[:800]); print('ND state', json.dumps(n.get('state'))[:800])
r=json.load(open('routing_types.json')); print('RT', r.get('status'), r.get('rows_by_type'), [(x['type'],round(x['percent_off'],2),x['status']) for x in r.get('types',[])])
p=json.load(open('proc_check.json')); print('PROC', p.get('status'), p.get('count'), p.get('n_tree'))
PY
grep -n "Error\|REFUS\|FAIL\|Traceback" job.log | grep -v '{"source\|remove_list' | tail -10 | cut -c1-300
