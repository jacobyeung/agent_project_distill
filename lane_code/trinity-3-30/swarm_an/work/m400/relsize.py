import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
T=['relative_size_object']
S={st:{r['id']:r for r in K.direct(run,st,'dev-S1',types=T)} for run,st in (('S1',544),('R1',100),('R1',200),('R1',400))}
ids=list(S[400])
pat=Counter(''.join('R' if (S[st][i]['score'] or 0)>0.5 else 'W' for st in (544,100,200,400)) for i in ids)
print('patterns 544/100/200/400',dict(pat))
print(S[400][ids[0]]['question'][:300],S[400][ids[0]]['options'])
for i in ids:
    p=''.join('R' if (S[st][i]['score'] or 0)>0.5 else 'W' for st in (544,100,200,400))
    if p in ('RRRR','WWWW'): continue
    r=S[400][i]; print('=====',i,p,'gt',r['gt'],'room',r['room'],'|',r['question'].split('?')[0][-160:],r['options'])
    for st in (544,200,400):
        x=S[st][i]; t=(x['text'] or '').split('</think>')[0].strip().replace('\n',' / ')
        print('  %d pred %s: %s'%(st,x['pred'],t[:420]))
