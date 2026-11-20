J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2; date -u +%TZ; free -g | sed -n 2p
mkdir -p $J/attic/partial_package_codex503 && mv $J/out/tree_rebuild_b24m4y2_9b1f8ba1.tar $J/attic/partial_package_codex503/ && ls $J/attic/partial_package_codex503
cd $J && tmux new-session -d -s tr22_pkg24m4y2 "cd $J && OMP_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24m4y2/package.py > work/build24m4y2/package_rerun_lane.log 2>&1"; sleep 5; tmux ls | grep tr22; cat $J/work/build24m4y2/package_rerun_lane.log
echo ===STAGE
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24m4y2; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24m4y2'
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
for tag in ('24M4Y2',):
    e=entries(W+'/w24y2/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24y2/out/UPLOADS_%s.list'%tag) if l.strip()]
    miss=[n for n in names if n not in e]
    print(tag,'list',len(names),'json',len(e),'missing',miss[:3])
    assert not miss, tag
    for n in names: final[n]=dict(e[n],tag=tag)
tot=0; sums=[]
for n,x in sorted(final.items()):
    assert not n.startswith('/') and '..' not in n.split('/'), n
    p=x['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest(); assert h==x['sha256'],(n,p)
    dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True)
    shutil.copyfile(p,dst); assert hashlib.sha256(open(dst,"rb").read()).hexdigest()==h
    tot+=os.path.getsize(p); sums.append('%s  %s'%(h,n))
open(W+'/work/up24m4y2.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24m4y2.sha; sha256sum $W/work/up24m4y2.sha | cut -c1-16
grep -E "  (n|q|qd)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24m4y2.sha
cd $W/work && tar cf $W/work/s24m4y2.tar -C $S $(cd $S && ls) && ls -l $W/work/s24m4y2.tar && sha256sum $W/work/s24m4y2.tar
