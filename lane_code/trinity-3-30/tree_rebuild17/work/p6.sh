W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; test ! -e $W/work/up24m3c || exit 1; cp -rL $W/work/up24m3 $W/work/up24m3c && cd $W/work/up24m3c && sha256sum -c $W/work/up24m3.sha | grep -vc ': OK$'; find . -type l | wc -l; tar cf - $(ls) | wc -c
python3 - <<'P'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_24M3.json'))
names=set(l.strip() for l in open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_24M3.list') if l.strip())
def walk(x,path=''):
    if isinstance(x,dict):
        if 'local_path' in x:
            n=x.get('name') or x.get('opaque_name')
            if n not in names: print(path, json.dumps(x)[:400])
        else:
            for k,v in x.items(): walk(v,path+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x): walk(v,path+'/%d'%i)
walk(d)
print([k for k in d if not isinstance(d[k],(list,dict))][:20])
P
sha256sum $W/w24/out/jd.sh $W/w24/out/dbb2.py $W/work/dbb2.py /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd/SHA256SUMS.txt | cut -c1-80
