import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
T=['relative_count']
for run,st in (('S1',544),('R1',100),('R1',200),('R1',400)):
    R=K.direct(run,st,'dev-S1',types=T)
    nonlet=[r for r in R if str(r['pred']).strip() not in ('A','B','C')]
    steps=Counter(len(re.findall(r'^Step \d', (r['text'] or '').split('</think>')[0], re.M)) for r in R)
    ok=[r for r in R if r not in nonlet]
    print(st,'n',len(R),'MRA %.1f'%(100*sum(r['score'] or 0 for r in R)/len(R)),'non-letter answers',len(nonlet),'| letter answers right %d of %d'%(sum((r['score'] or 0)>0.5 for r in ok),len(ok)),'| steps per trace',dict(sorted(steps.items())),'fc',sum(bool(r['forced_close']) for r in R))
    if st==400:
        print('  non-letter traces with only Step 1:',sum(1 for r in nonlet if len(re.findall(r'^Step \d',(r['text'] or ''),re.M))==1))
        eq=[r for r in ok if 'equal' in (r['text'] or '').split('</think>')[0].split('\n')[-2] ]
        print('  letter answers: stated counts with digits',sum(bool(re.search(r'\d', (r['text'] or '').split('</think>')[0].split('Step 3')[-1])) for r in ok))
