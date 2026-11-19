"""Resolve the r1 kit's unresolved staging entries against verified sources (lane tree_rebuild8). usage: resolve.py KIT_DIR ORIGINAL_CONFIG OUT"""
import json,base64,hashlib,os,glob,sys
from collections import Counter
K,OC,OUT=sys.argv[1]+'/k/',sys.argv[2],sys.argv[3]
dec=lambda f:json.loads(base64.b64decode(json.load(open(K+f))['payload']))
s=dec('s.json');kc=dec('c.json');oc=json.load(open(OC));unres=set(s['unresolved']);rows={}
def walk(a,b,p):
    if isinstance(a,dict) and isinstance(b,dict):
        if isinstance(a.get('path'),str) and a['path'] in unres and 'sha256' in a:
            rows.setdefault(a['path'],dict(dest=a['path'],sha256=a['sha256'],source=b.get('path'),keys=[]))['keys'].append(p)
        for k in a:
            if k in b: walk(a[k],b[k],p+'.'+k)
    elif isinstance(a,list) and isinstance(b,list):
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,p+'[%d]'%i)
walk(kc,oc,'config')
for sh,dest in kc.get('s1_routing',{}).get('catalog',{}).items():
    if dest in unres: rows.setdefault(dest,dict(dest=dest,sha256=sh,source=oc['s1_routing']['catalog'][sh],keys=[]))['keys'].append('config.s1_routing.catalog.'+sh)
loc={hashlib.sha256(open(f,'rb').read()).hexdigest():f for f in glob.glob('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k/*')+glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/kit07ca49df_meta/m/k/*.json')}
b0=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4/cert_p4_hz_a71_3/b/b0.json'))  # P's staging plan for job 171377's kit
parts={};pk={}
def w2(o):
    if isinstance(o,dict):
        if 'sha256' in o and ('parts' in o or 'file' in o): parts[o['sha256']]=o.get('parts') or [o.get('file')]
        for v in o.values(): w2(v)
    elif isinstance(o,list):
        for v in o: w2(v)
w2(b0)
for p in b0['staged_inputs']['packages']:
    for it in p['inventory']: pk[it['name']]=dict(package=p['source'],package_sha256=p['sha256'],destination=p['destination'],member=it['name'])
P=open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json').read()  # P's admitted job config fac07052
for r in rows.values():
    sh,src=r['sha256'],r['source'] or '';name=os.path.basename(src)
    lc=loc.get(sh) or (src if os.path.isfile(src) and hashlib.sha256(open(src,'rb').read()).hexdigest()==sh else None)
    r.update(local_copy=lc,P_orchard_parts=parts.get(sh),P_package_member=pk.get(name),in_P_admitted_config=sh in P)
    r['resolution']=('local_verified_copy' if lc else 'P_staged_orchard_source' if r['P_orchard_parts'] else 'P_staged_package_member' if r['P_package_member']
                     else 'P_config_pin_only' if r['in_P_admitted_config'] else 'UNRESOLVED')
out=sorted(rows.values(),key=lambda r:r['dest'])
res=dict(kit=sys.argv[1],unresolved=len(unres),mapped=len(rows),unmapped=sorted(unres-set(rows)),by_resolution=dict(Counter(x['resolution'] for x in out)),entries=out)
json.dump(res,open(OUT,'w'),indent=1);print(json.dumps({k:v for k,v in res.items() if k!='entries'}))
for x in out:
    if x['resolution'] in('UNRESOLVED','P_config_pin_only'): print(x['resolution'],x['keys'],x['sha256'][:12],x['source'])
