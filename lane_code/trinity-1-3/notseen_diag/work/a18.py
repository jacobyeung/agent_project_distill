import json,collections,re,numpy as np
RP=[json.loads(l) for l in open('replay_out.jsonl')]
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
print('errors by arm',collections.Counter((r['geo'],r['rule'],r['error'][:40]) for r in RP if 'error' in r))
print('error items',len(set(r['id'] for r in RP if 'error' in r)),'datasets',collections.Counter(I[r['id']]['dataset'] for r in RP if 'error' in r and r['geo']=='tower' and r['rule']=='null_argmax'))
# candidates count for not-seen under null
C=collections.Counter()
for r in RP:
    if 'error' in r or r['rule']!='null_argmax': continue
    q={x['name']:x for x in r['queries']}
    for n,resp in r['ground'].items():
        if resp.strip().endswith('not seen'):
            qq=q.get(n); C[(r['geo'],'cands0' if qq and qq['candidates']==0 else 'null_won')]+=1
print('not-seen under null: empty candidates vs null won',dict(C))
# null margins
M=collections.defaultdict(list)
for r in RP:
    if 'error' in r or r['rule']!='null_argmax': continue
    for s in r['sel']: M[(r['geo'],'null' if s['choice']<0 else 'pick')].append(s['null']-s['best'])
for k,v in sorted(M.items()): print(k,len(v),np.round(np.percentile(v,[10,50,90]),2))
