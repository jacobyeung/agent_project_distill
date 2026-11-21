import json,base64,os,collections,sys
U='nodej/u'; KD='/scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/kit/n_go/k'
def load(p):
    v=json.load(open(p))
    if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json'): v=json.loads(base64.b64decode(v['payload']))
    return v
def ispin(v): return isinstance(v,dict) and isinstance(v.get('sha256'),str) and len(v['sha256'])==64 and ('path' in v or 'file' in v)
def trin(p): return isinstance(p,str) and (p.startswith(('/scratch/jjyeung','/home/','/data','/tmp/')) and not p.startswith('/tmp/q_22c714e1'))
def pins(v,kp=''):
    if ispin(v): yield kp,v
    if isinstance(v,dict):
        for k,x in v.items(): yield from pins(x,kp+'.'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): yield from pins(x,kp+'[%d]'%i)
P=json.load(open('o/pins_all.json'))
orig=collections.defaultdict(set)
for cont,kp,p,h,s in P:
    if not trin(p): orig[h].add(p)
c=load(KD+'/c.json')
cp=list(pins(c))
print('config pins',len(cp))
objs={}
for kp,v in cp:
    h=v['sha256']
    if os.path.isfile(U+'/'+h):
        try: objs.setdefault(h,[]).append(kp)
        except: pass
print('config-named JSON objects',len(objs))
rows=[]
def scan(h,where,depth):
    try: o=load(U+'/'+h)
    except Exception: return
    for kp,v in pins(o):
        p=v.get('path',v.get('file'))
        if trin(p): rows.append((where,h,kp,p,v['sha256'],sorted(orig.get(v['sha256'],[]))))
        if depth>0 and os.path.isfile(U+'/'+v['sha256']): scan(v['sha256'],where+' > '+h[:8]+kp,depth-1)
for h,kps in sorted(objs.items(),key=lambda x:x[1][0]):
    d=1 if any(k.startswith(('.streams','.r1_training.store_parameter')) for k in kps) else 0
    scan(h,kps[0],d)
json.dump(rows,open('o/inv2.json','w'),indent=1)
cnt=collections.Counter(r[0].split(' > ')[0] for r in rows)
for k,n in sorted(cnt.items()): print(n,k)
