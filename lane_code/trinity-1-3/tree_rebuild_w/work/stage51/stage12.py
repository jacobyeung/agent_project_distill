import json,base64,hashlib,os,glob
K='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/work/build12/kits/r1/k/'
dec=lambda f:json.loads(base64.b64decode(json.load(open(K+f))['payload']))
s=dec('s.json');kc=dec('c.json')
oc=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json'))
unres=set(s['unresolved']);rows={}
def walk(a,b,p):
    if isinstance(a,dict) and isinstance(b,dict):
        if isinstance(a.get('path'),str) and a['path'] in unres and 'sha256' in a:
            rows.setdefault(a['path'],dict(dest=a['path'],sha256=a['sha256'],source=b.get('path'),keys=[]))['keys'].append(p)
        for k in a:
            if k in b: walk(a[k],b[k],p+'.'+k)
    elif isinstance(a,list) and isinstance(b,list):
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,p+'[%d]'%i)
walk(kc,oc,'config')
# catalog entries keyed by sha in s1_routing.catalog
print('unresolved',len(unres),'mapped',len(rows))
missing=unres-set(rows)
# local verified copies
loc={}
for f in glob.glob('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k/*'):
    loc[hashlib.sha256(open(f,'rb').read()).hexdigest()]=f
b0=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4/cert_p4_hz_a71_3/b/b0.json'))
b0s={}
def w2(o):
    if isinstance(o,dict):
        if 'sha256' in o and ('parts' in o or 'file' in o): b0s[o['sha256']]=o.get('parts') or [o.get('file')]
        for v in o.values(): w2(v)
    elif isinstance(o,list):
        for v in o: w2(v)
w2(b0)
P=open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json').read()
out=[]
for d,r in sorted(rows.items()):
    sh=r['sha256'];src=r['source'] or ''
    r.update(in_P_admitted_config=sh in P, P_orchard_parts=b0s.get(sh), local_copy=loc.get(sh) or (src if os.path.isfile(src) and hashlib.sha256(open(src,'rb').read()).hexdigest()==sh else None))
    r['resolution']=('P_staged_orchard_source' if r['P_orchard_parts'] else 'local_verified_copy' if r['local_copy'] else 'P_config_pin_only' if r['in_P_admitted_config'] else 'UNRESOLVED')
    out.append(r)
from collections import Counter
print(Counter(x['resolution'] for x in out)); print('also local',sum(1 for x in out if x['local_copy']))
for x in out:
    if x['resolution'] in('UNRESOLVED','P_config_pin_only'): print(x['resolution'],x['keys'][0][:70],x['source'][-60:] if x['source'] else None)
print('missing',sorted(missing)[:5])
json.dump(dict(kit_sha256='48673778568b5c0d51451a40d717a4d90cf590593190672477f9207726ad2204',entries=out,unmapped=sorted(missing)),open('STAGE_B12.json','w'),indent=1)
