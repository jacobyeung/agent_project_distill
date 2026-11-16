import json, re
from collections import Counter
P='scratch/jjyeung/orch_n30/native_r2/work/parent'
R=json.load(open('R1_distroom.json'))
tasks={('devrows:'+x['id']):x for x in map(json.loads,open(P+'/r3/TASKS.jsonl'))}
def mra(pred,gt):
    try: p=float(pred); g=float(gt)
    except: return 0.0
    ths=[0.5+0.05*i for i in range(10)]
    if g==0: return 1.0 if p==0 else 0.0
    d=abs(p-g)/abs(g)
    return sum(d<=1-t+1e-12 for t in ths)/10
def extract(text):
    if not re.search(r'</think\s*>',text,re.I): return None
    suf=re.split(r'</think\s*>',text,flags=re.I)[-1]
    m=re.search(r'<answer>(.*?)</answer>',suf,re.S)
    s=m.group(1) if m else (suf.strip().splitlines() or [''])[-1]
    return s.strip().split(' ')[0].rstrip('.').strip()
mism=Counter(); ex=[]; trunc=0; units=Counter()
for a in ('unflagged','scripted'):
    for r in R['arms'][a]:
        t=tasks[r['key']]
        if 'decode' not in r: continue
        txt=r['decode'].get('text','')
        if '<TRUNC' in txt: trunc+=1; continue
        if r.get('geometry_refusal'): continue
        ans=extract(txt); gt=t['released_answer']
        sc=0.0 if ans is None else mra(ans,gt)
        rec=r['scores']['released_answer']
        if abs(sc-rec)>1e-9: mism[a]+=1; ex.append((a,r['key'],ans,gt,sc,rec))
        # full final suffix to detect unit words
        suf=re.split(r'</think\s*>',txt,flags=re.I)[-1] if ans is not None else ''
        w=re.findall(r'(cm|centimet|meter|metre|\bm\b|feet|foot|ft|inch|in\b|square)',suf,re.I)
        units[(a,len(w)>0)]+=1
print('truncated texts',trunc,'mismatch',dict(mism)); print(ex[:10]); print(units)
import math, statistics as st
F={'m':1,'cm':0.01,'in':0.0254,'ft':0.3048,'sq m':1,'sq ft':0.092903}
def unit(q):
    m=re.findall(r'\b(square\s+)?(millimeters?|millimetres?|centimeters?|centimetres?|meters?|metres?|inches|inch|feet|foot)\b',q,re.I)
    s,v=m[-1]; v=v.lower().replace('metre','meter')
    u='cm' if v.startswith('centi') else 'm' if v.startswith('meter') else 'in' if v.startswith('inch') else 'ft'
    return ('sq ' if s else '')+u
for a in ('unflagged','scripted'):
    by={}
    for r in R['arms'][a]:
        if 'decode' not in r: continue
        t=tasks[r['key']]; ans=extract(r['decode']['text'])
        try: p=float(ans)
        except: continue
        g=float(t['released_answer']); u=unit(t['question'])
        if p<=0: continue
        # classify: answer looks like metres-value (p ~ g*F) vs asked-unit (p~g)
        r_asked=abs(math.log(p/g)); r_m=abs(math.log(p/(g*F[u])))
        by.setdefault(u,Counter())['asked' if r_asked<=r_m else 'metre_value']+=1
    print(a,{u:dict(c) for u,c in by.items()})
