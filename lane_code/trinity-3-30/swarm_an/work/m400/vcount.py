import sys,re; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
R=[r for r in K.direct('R1',400,'R0-dev',types=['object_counting']) if r['subtype']=='multiple']
def cats(q):
    m=re.search(r'([a-z ]+)\(s\) and ([a-z ]+)\(s\)',q); return (m.group(1).strip().split(' ')[-1], m.group(2).strip()) if m else None
n2=0; tot=0
for r in R:
    c=cats(r['question']); th=(r['text'] or '').split('</think>')[0]
    if not c: continue
    tot+=1; n2+= c[1] in th
print('multiple items parsed',tot,'second category named in trace',n2, 'MRA %.1f'%(100*sum(r['score'] for r in R)/len(R)))
print(R[0]['question'][:200]); print(R[0]['text'][:300])
S={r['id']:r for r in K.direct('R1',400,'dev-S1',types=['object_counting','relative_count'])}
for i in ('vsi590k_050949','vsi590k_179311','vsi590k_087487'):
    r=S[i]; print('==',i,r['question'][:150],r['options'],'gt',r['gt'],'pred',r['pred']); print((r['text'] or '')[:400])
