import json,collections,numpy as np
P=json.load(open('pairs_cache.json'))
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
MC='n2r/mc/sj/mask_recall_run/results/'
man={c['native']:c for c in json.load(open(MC+'dense/MANIFEST.json'))['captures']}
for o in P: o['hw']=tuple(man[o['native']]['hw']); o['portrait']=o['hw'][0]>o['hw'][1]
ns=[o for o in P if o['h1']=='not seen']; se=[o for o in P if o['h1']=='seen']
print('pairs',len(P),'ns',len(ns),'items',len(set(o['id'] for o in ns)))
def rate(key):
    C=collections.Counter((key(o),o['h1']) for o in P); ks=sorted(set(k for k,_ in C))
    return [(k,C[(k,'not seen')],C[(k,'not seen')]+C[(k,'seen')]) for k in ks]
print('dataset',rate(lambda o:o['dataset']))
print('portrait',rate(lambda o:o['portrait']))
print('hw',rate(lambda o:o['hw']))
nm=rate(lambda o:o['name']); nm=sorted(nm,key=lambda t:(-t[1],-t[2]))
print('names (ns,total) top:',[(k,a,b) for k,a,b in nm if a>0])
print('names never ns (count>=3):',[(k,b) for k,a,b in nm if a==0 and b>=3])
q=lambda a:list(np.round(np.percentile(a,[10,25,50,75,90]),3))
for lab,S in (('ns',ns),('seen',se)):
    d=[o['dense'] for o in S if o['dense']['cache']=='ok']
    print(lab,'n_frames_s03',q([x['n_frames_s03'] for x in d]),'max_score',q([x['max_score'] for x in d]),'max_presence',q([x['max_presence'] for x in d]),'med_area_s03',q([x['med_area_s03'] for x in d]))
# aliases: does dense_aliases prompt differ from raw name?
def alias_prompts(o):
    import numpy as np
    return None
