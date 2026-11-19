W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24; test ! -e $S && mkdir -p $S
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24'
d=json.load(open(W+'/w24/out/UPLOADS_MINIMAL.json'))
names=[l.strip() for l in open(W+'/w24/out/UPLOADS_MINIMAL.list') if l.strip()]
ent={}
for k,v in d['kits'].items():
    for e in v['files']:
        n=e.get('name') or e.get('opaque_name'); ent.setdefault(n,e)
tot=0; miss=[]
for n in names:
    e=ent.get(n)
    if e is None: miss.append(n); continue
    p=e['local_path']; dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True)
    if not os.path.lexists(dst): os.symlink(p,dst)
    sz=os.path.getsize(p); tot+=sz
    assert sz==e['bytes'],(n,sz,e['bytes'])
print('files',len(names),'missing',len(miss),miss[:3],'bytes',tot)
PY
cd $S && ls | tr '\n' ' '; echo; tar chf - $(ls) | wc -c
