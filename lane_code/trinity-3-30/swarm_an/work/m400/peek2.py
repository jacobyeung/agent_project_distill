import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
w=K.facing('R1',400,'away')
print(w[5]['question'][:300]); print(w[5]['text'][:1500])
for st,sets in ((400,['dev-S1','R0-dev']),):
  for s in sets:
    d=[r for r in K.direct('R1',st,s) if 'direction' in r['type']]
    print(s,len(d),Counter(r['type'] for r in d))
    lines=Counter()
    for r in d:
        t=(r['text'] or '').split('</think>')[0]
        for l in t.strip().split('\n'):
            lines[re.sub(r'[0-9]+','N',re.sub(r'(at|by|facing|find|the) [a-z ]+','\\1 X',l))[:90]]+=1
    for k,v in lines.most_common(25): print(v,k)
    print(d[0]['question'][:300]); print(d[0]['text'][:900])
