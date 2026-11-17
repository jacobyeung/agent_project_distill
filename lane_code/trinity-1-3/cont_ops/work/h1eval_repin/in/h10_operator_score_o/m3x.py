import json,collections
F='/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl'
R=[json.loads(l) for l in open(F)]
for mode in ('none','scale_scene:0.5','scale_scene:2'):
    rs=[r for r in R if r['mode']==mode]; d=collections.Counter()
    for r in rs:
        ns=any('not seen' in (x.get('response') or '') for x in r['output']['calls']['records'])
        cap=r['output']['finish']=='max_calls'; m=r['measurements']
        g='ns' if ns else 'clean'
        d[g+'_n']+=1; d[g+'_exact']+=bool(m['M1']['exact']); d[g+'_acc_x1000']+=round(1000*m['M2']['task_accuracy'])
        d[g+'_ncalls']+=len(r['output']['calls']['records'])
        u=m.get('M3',{})
        if u.get('eligible'):
            k='follow' if u['follow'] else 'stick' if u['stick'] else ('other_capped' if cap else 'other_answered')
            d['m3_'+g+'_'+k]+=1
        d['sec_'+g]+=round(r['seconds'])
    print(mode, json.dumps(dict(sorted(d.items()))))
ex=[(r['id'],r['mode'],r['measurements']['M3']) for r in R if r['measurements'].get('M3',{}).get('eligible') and not r['measurements']['M3']['follow'] and r['output']['finish']!='max_calls'][:6]
for e in ex: print(e[0],e[1],{k:e[2].get(k) for k in ('baseline_decision','perturbed_decision','answer_text')})
