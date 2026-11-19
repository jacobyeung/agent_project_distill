import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
for run,st,s in (('S1',544,'dev-S1'),('S1',544,'R0-dev'),('R1',100,'R0-dev')):
    d=[r for r in K.direct(run,st,s) if 'direction' in r['type']]
    lines=Counter()
    for r in d:
        t=(r['text'] or '').split('</think>')[0]
        for l in t.strip().split('\n'):
            lines[re.sub(r'[0-9]+','N',re.sub(r'(at|by|facing|find|the) [a-z ]+','\\1 X',l))[:90]]+=1
    print(run,st,s,len(d)); 
    for k,v in lines.most_common(14): print(' ',v,k)
d=[r for r in K.direct('R1',400,'R0-dev') if 'direction' in r['type']]
qs=Counter()
for r in d: qs[(r['type'][-4:], 'away' in r['question'], len(r['options']), r['options'][0][3:] if r['options'] else '')]+=1
for k,v in sorted(qs.items()): print(v,k)
for t in ('easy','medium'):
    r=[x for x in d if x['type'].endswith(t)][0]; print(r['question'],r['options'],r['gt'])
