import json,collections,numpy as np
P=json.load(open('pairs_cache.json'))
MC='n2r/mc/sj/mask_recall_run/results/'
man={v:{c['native']:c for c in json.load(open(MC+v+'/MANIFEST.json'))['captures']} for v in ('dense','dense_aliases')}
cache={}
def load(v,native):
    k=(v,native)
    if k not in cache:
        c=man[v][native]; cache[k]=json.loads(np.load(MC+v+'/candidates/'+c['scene'].replace('/','__')+'.npz')['payload'].tobytes())
    return cache[k]
def prompts(native,name):
    c=load('dense_aliases',native); ph=name.lower()
    pr=collections.Counter(); pres=[]
    for s in range(32):
        rec=c['frames'][str(s)]['phrases'].get(ph)
        if not rec: continue
        pres.append(rec.get('presence',0))
        for e in rec.get('instances') or []: pr[e.get('prompt',rec.get('prompt'))]+=1
        if rec.get('prompt'): pr['@rec:'+str(rec.get('prompt'))]+=0
    return dict(pr), (max(pres) if pres else None)
C=collections.Counter()
for lab in ('not seen','seen'):
    S=[o for o in P if o['h1']==lab and o['dense']['cache']=='ok']
    mp=np.array([o['dense']['max_presence'] for o in S])
    print(lab,len(S),'max_presence<0.5:',int((mp<.5).sum()),' <0.2:',int((mp<.2).sum()),' >=0.9:',int((mp>=.9).sum()))
ex={}
for o in P:
    if o['h1']!='not seen': continue
    pr,mpa=prompts(o['native'],o['name'])
    ex.setdefault(o['name'],[]).append((o['dataset'],round(o['dense']['max_presence'],3),round(o['dense']['max_score'],3),o['dense']['n_frames_s03'],{k:v for k,v in pr.items() if not k.startswith('@')}))
for k,v in sorted(ex.items(),key=lambda kv:-len(kv[1]))[:16]: print(k,v[:4])
