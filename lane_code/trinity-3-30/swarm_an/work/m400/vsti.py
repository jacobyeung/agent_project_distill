import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import Counter
S={st:{r['id']:r for r in K.vsti(run,st)} for run,st in (('S1',544),('R1',200),('R1',400))}
def sk(t):
    t=(t or '').split('</think>')[0].strip(); l=t.split('\n')[0]
    return re.sub(r'\d+(\.\d+)?','N',re.sub(r'(the|a|an) [a-z ]+?( in| at|,|\.|;| and| first)','\\1 X\\2',l))[:70]
for st in (544,200,400):
    c=Counter(sk(r['text']) for r in S[st].values()); print(st,'distinct openings',len(c),c.most_common(3))
top544=set(k for k,_ in Counter(sk(r['text']) for r in S[544].values()).most_common(5))
for st in (200,400): print(st,'traces opening with one of 544 top-5 skeletons',sum(sk(r['text']) in top544 for r in S[st].values()))
for ty in ('obj_obj_relative_pos_lr','obj_obj_relative_pos_nf'):
    ids=[i for i,r in S[400].items() if r['type']==ty]
    rw=[i for i in ids if (S[200][i]['score'] or 0)>0.5 and (S[400][i]['score'] or 0)<0.5]; wr=[i for i in ids if (S[200][i]['score'] or 0)<0.5 and (S[400][i]['score'] or 0)>0.5]
    print(ty,'200->400 R->W',len(rw),'W->R',len(wr),'| pred dist 200',Counter(S[200][i]['pred'] for i in ids).most_common(3),'400',Counter(S[400][i]['pred'] for i in ids).most_common(3),'gt',Counter(S[400][i]['gt'] for i in ids).most_common(3))
    for i in rw[:2]:
        r=S[400][i]; print('  ==',i,r['question'].split('\n')[0][:200],r['options'],'gt',r['gt'])
        for st in (200,400): print('    %d %s: %s'%(st,S[st][i]['pred'],(S[st][i]['text'] or '').split('</think>')[0].strip().replace('\n',' / ')[:380]))
