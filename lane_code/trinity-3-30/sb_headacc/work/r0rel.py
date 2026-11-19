import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
R=[r for r in K.direct('R1', 200, 'R0-dev') if r['type']=='object_rel_distance']
n=0; lens=collections.Counter(); bad=[]
for r in R:
    t=r['text'].replace('\n',' ')
    m=re.search(r'nearest-to-farthest order from (.+?) is: (.+?)\.\s', t+' ')
    if m:
        n+=1; lens[len(re.split(r',\s*then\s+|,\s*', m.group(2)))]+=1
    else: bad.append(t[:160])
print('parsed', n, 'of', len(R), 'order lengths', dict(lens)); print(bad[:3])
print('options example', R[0]['options'], '|', R[0]['question'][:200])
