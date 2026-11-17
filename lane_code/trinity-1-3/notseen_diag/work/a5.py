import json,collections,re
def gstat(resp):
    r=(resp or '').strip()
    m=re.match(r'^(.*?): (not seen|unresolved|box unavailable)$',r)
    if m: return m[2]
    if ': frames' in r: return 'seen'
    return 'other'
P=[json.loads(l) for l in open('b04v7/b04_e2ehook/out/proofs/PARITY_own_depth_p0_51rows.jsonl')]
PS=collections.defaultdict(set)
for x in P:
    if x['question_type']!='object_abs_distance': continue
    key=x['key'].split(':',1)[1]
    for c in x['calls']['records']:
        if c['family']=='ground' and c.get('served'):
            m=re.search(r'obj="([^"]*)"',c['call']); PS[(key,m[1])].add(gstat(c.get('response')))
rows=json.load(open('calls.json'))
H=collections.defaultdict(set)
for r in rows:
    if r['family']=='ground' and r['mode']=='none' and r['st'] in ('seen','not seen'): H[(r['id'],r['name'])].add(r['st'])
n2r=json.load(open('n2r_calls.json'))['unflagged']
T=collections.defaultdict(set)
for key,r in n2r.items():
    for c in r['calls']:
        if c['kind']=='ground' and c['st'] in ('seen','not seen'): T[(key,c['name'])].add(c['st'])
one=lambda s: (next(iter(s)) if len(s)==1 else 'mixed') if s else 'nc'
keys=sorted(set(PS)|set(k for k in H if k[0] in set(k2[0] for k2 in PS)))
tab=collections.Counter((one(T.get(k)),one(PS.get(k)),one(H.get(k))) for k in keys)
print('items in parity:',len(set(k[0] for k in PS)),'pairs',len(PS))
print('(tower170056, parity_G3Txs_rawname, H1-0 own) counts:')
for k,v in sorted(tab.items(), key=lambda kv:-kv[1]): print(k,v)
