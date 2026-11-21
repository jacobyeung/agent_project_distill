import json, base64, hashlib, os, sys, collections
U='nodej/u'; KD='/scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/kit/n_go/k'
def load(p):
    v=json.load(open(p))
    if isinstance(v,dict) and v.get('encoding') in ('base64','base64-json'):
        v=json.loads(base64.b64decode(v['payload']))
    return v
def ispin(v): return isinstance(v,dict) and 'sha256' in v and ('path' in v or 'file' in v) and isinstance(v.get('sha256'),str) and len(v['sha256'])==64
def trin(p): return isinstance(p,str) and (p.startswith(('/scratch/jjyeung','/home/','/data','/tmp/')) and not p.startswith('/tmp/q_22c714e1'))
pins=[]  # (container, keypath, path, sha)
seen=set(); queue=[]
def walk(v,cont,kp):
    if ispin(v):
        p=v.get('path',v.get('file')); pins.append((cont,kp,p,v['sha256'],set(v)=={'path','sha256'}))
        queue.append(v['sha256'])
    if isinstance(v,dict):
        for k,x in v.items(): walk(x,cont,kp+'.'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk(x,cont,kp+'[%d]'%i)
roots={'k/c.json':load(KD+'/c.json'),'k/n.json':load(KD+'/n.json'),'k/p.json':load(KD+'/p.json'),'k/r.json':load(KD+'/r.json'),'k/h.json':load(KD+'/h.json')}
for n,v in roots.items(): walk(v,n,'')
while queue:
    h=queue.pop()
    if h in seen: continue
    seen.add(h)
    f=U+'/'+h
    if os.path.isfile(f):
        try: walk(load(f),'u/'+h[:12],'')
        except Exception as e: pass
json.dump([list(p[:4])+[p[4]] for p in pins],open('o/pins_all.json','w'))
print('pins',len(pins),'objects walked',len(seen))
T=[p for p in pins if trin(p[2])]
print('Trinity-path pins',len(T))
by=collections.defaultdict(list)
for c,kp,p,h,strict in T: by[(h,p)].append((c,kp))
# originals: same sha with non-Trinity path
orig=collections.defaultdict(set)
for c,kp,p,h,strict in pins:
    if not trin(p): orig[h].add(p)
for (h,p),where in sorted(by.items(),key=lambda x:x[0][1]):
    print('\nSHA',h[:16],'TRINITY PATH',p)
    for c,kp in where[:12]: print('   at',c,kp)
    if len(where)>12: print('   ... +%d more'%(len(where)-12))
    print('   other paths for same sha:',sorted(orig.get(h,[]))[:4])
