import json,collections,sys
F='/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
R=[json.loads(l) for l in open(F)]
out={}
def st(x):
    r=(x.get('response') or '')
    if not x['served']: return 'unserved'
    if 'not seen' in r: return 'not_seen'
    if r.startswith('error'): return 'error'
    return 'ok'
base_ns={}
for mode in ('none','scale_scene:0.5','scale_scene:2','ALL'):
    rs=[r for r in R if mode=='ALL' or r['mode']==mode]
    d=collections.Counter()
    for r in rs:
        recs=r['output']['calls']['records']; S=[(x['family'],st(x)) for x in recs]
        ns=any(s=='not_seen' for f,s in S); cap=r['output']['finish']=='max_calls'
        first2=[s for f,s in S if f=='ground'][:2]
        d['reads']+=1; d['capped']+=cap; d['any_not_seen']+=ns
        d['ns_and_capped']+=ns and cap; d['clean_and_capped']+=(not ns) and cap
        d['first_ground_not_seen']+=('not_seen' in first2)
        d['ground_not_seen_calls']+=sum(1 for f,s in S if f=='ground' and s=='not_seen')
        d['gap_not_seen_calls']+=sum(1 for f,s in S if f=='gap' and s=='not_seen')
        d['ground_calls']+=sum(1 for f,s in S if f=='ground'); d['gap_calls']+=sum(1 for f,s in S if f=='gap')
        d['error_calls']+=sum(1 for f,s in S if s=='error'); d['unserved_calls']+=sum(1 for f,s in S if s=='unserved')
        d['gap_value_served']+=any(f=='gap' and s=='ok' for f,s in S)
        d['ns_answered']+=ns and not cap
        d['ns_answered_score_sum_x100']+=round(100*r['measurements']['M2']['task_accuracy']) if ns and not cap else 0
        d['calls_total']+=len(S)
        if mode=='none': base_ns[r['id']]=ns
        elif mode!='ALL': d['ns_given_base_ns']+=ns and base_ns.get(r['id'],False); d['ns_given_base_clean']+=ns and not base_ns.get(r['id'],True); d['base_ns']+=base_ns.get(r['id'],False)
    m3=[r['measurements'].get('M3',{}) for r in rs if r['measurements'].get('M3',{}).get('eligible')]
    d['m3_eligible']=len(m3)
    out[mode]=dict(d)
print(json.dumps(out,indent=0))
