import json,collections,re,numpy as np
def parse(resp):
    m=re.search(r'centre \(([-\d\.]+), ([-\d\.]+), ([-\d\.]+)\) m\nsize ([\d\.]+) x ([\d\.]+) x ([\d\.]+) m',resp or '')
    if not m: return None
    v=list(map(float,m.groups())); return np.array(v[:3]),np.array(v[3:])
R=[json.loads(l) for l in open('f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl')]
H={}
for x in R:
    if x['mode']!='none': continue
    for c in x['output']['calls']['records']:
        if c['family']=='ground' and c.get('served'):
            p=parse(c.get('response')); m=re.search(r'obj="([^"]*)"',c['call'])
            if p: H[(x['id'],m[1])]=p
d=json.load(open('n2r/full_c8r/x/native/R1.json'))
T={}
for a in d['arms']['unflagged']:
    if a['question_type']!='object_abs_distance' or 'decode' not in a: continue
    for c in a['decode']['calls']:
        if c.get('kind')=='ground':
            p=parse(c.get('response')); m=re.search(r'obj="([^"]*)"',c['call'])
            if p: T[(a['key'].split(':',1)[1],m[1])]=p
ks=sorted(set(H)&set(T))
rc=np.array([np.linalg.norm(H[k][0])/max(np.linalg.norm(T[k][0]),1e-6) for k in ks])
rs=np.array([np.max(H[k][1])/max(np.max(T[k][1]),1e-6) for k in ks])
dc=np.array([np.linalg.norm(H[k][0]-T[k][0]) for k in ks])
print('pairs both seen',len(ks))
q=lambda a:np.round(np.percentile(a,[10,25,50,75,90]),2)
print('|centre| own/tower ratio pct10..90',q(rc))
print('max side own/tower ratio',q(rs))
print('centre distance own-tower (m)',q(dc))
