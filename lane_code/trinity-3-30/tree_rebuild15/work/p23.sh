W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24k; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24k'
def entries(j):
    d=json.load(open(j)); out={}
    def walk(x):
        if isinstance(x,dict):
            if 'local_path' in x and ('name' in x or 'opaque_name' in x): out[x.get('name') or x.get('opaque_name')]=x
            else:
                for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(d); return out
final={}
for tag in ('24D','24E','24F','24G','24H','24I','24K'):
    e=entries(W+'/w24/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24/out/UPLOADS_%s.list'%tag) if l.strip()]
    miss=[n for n in names if n not in e]
    print(tag,'list',len(names),'json',len(e),'missing',miss[:3])
    assert not miss, tag
    for n in names: final[n]=dict(e[n],tag=tag)
tot=0; sums=[]
for n,x in sorted(final.items()):
    assert not n.startswith('/') and '..' not in n.split('/'), n
    p=x['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest(); assert h==x['sha256'],(n,p)
    dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True)
    os.symlink(p,dst)
    tot+=os.path.getsize(p); sums.append('%s  %s'%(h,n))
open(W+'/work/up24k.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24k.sha; sha256sum $W/work/up24k.sha | cut -c1-16
grep -E "  (n|q)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24k.sha
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/work/build24k
ls $K | grep -iE "jr|rout|submit|JOB|ORCH" ; grep -rn -l "jr.sh" $K/*.md $W/w24/out/*.md 2>/dev/null | head
grep -n -B2 -A8 "jr.sh" $W/w24/out/N_CARD_KIT_ROWS.md $K/*.md 2>/dev/null | head -40 | cut -c1-300
ls $W/w24/out/../work/build24c/ 2>/dev/null | grep -i "j.sh"; find $W/w24 -maxdepth 4 -name "j.sh" 2>/dev/null | head
