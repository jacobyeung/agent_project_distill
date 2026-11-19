import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
T=['relative_count']
S={st:{r['id']:r for r in K.direct(run,st,'dev-S1',types=T)} for run,st in (('S1',544),('R1',200),('R1',400))}
r=list(S[400].values())[0]; print(r['question'][:400], r['options'], r['gt'])
def sk(t): 
    t=(t or '').split('</think>')[0]
    return re.sub(r'\d+','N',re.sub(r'(of|instances of|each distinct) [a-z ]+','\\1 X',t.strip().split('\n')[0]))[:90]
for st in (544,200,400):
    c=Counter(sk(r['text']) for r in S[st].values()); print(st,c.most_common(4))
    print('   pred dist',Counter(r['pred'] for r in S[st].values()).most_common(6),'gt dist',Counter(r['gt'] for r in S[st].values()).most_common(6))
w=[r for r in S[400].values() if (r['score'] or 0)<0.5][:3]
for r in w:
    print('=====',r['id'],r['question'].split('\n')[0][:250],r['options'],'gt',r['gt'],'pred',r['pred'],'| 200 pred',S[200][r['id']]['pred'],S[200][r['id']]['forced_close']); print((r['text'] or '')[:700])
