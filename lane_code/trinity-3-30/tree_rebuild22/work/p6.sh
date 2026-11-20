W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; P=$W/w24w/out/tree_rebuild_b24m4w_5a01fc47.tar; cat $P.sha256; sha256sum $P | cut -c1-16
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4w | tail -1); head -c 1500 $d/final_message.md; echo; echo ===R; cat $W/w24w/out/BUILD24M4W_REPORT.md; echo ===L; cat $W/w24w/out/UPLOADS_24M4W.list; echo ===D; cat $W/w24w/out/DELIVERY_24M4W.json
timeout 120 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild22/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild22/$(basename $P) | cut -c1-16'"
echo ===STAGE
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24m4w; date -u +%TZ; test ! -e $S && mkdir -p $S || { echo "S EXISTS"; exit 1; }
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib,shutil
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24m4w'
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
for tag in ('24M4W',):
    e=entries(W+'/w24w/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24w/out/UPLOADS_%s.list'%tag) if l.strip()]
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
open(W+'/work/up24m4w.sha','w').write('\n'.join(sums)+'\n')
from collections import Counter
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}),'bytag',Counter(x['tag'] for x in final.values()))
PY
cd $S && tar chf - $(ls) | wc -c; wc -l < $W/work/up24m4w.sha; sha256sum $W/work/up24m4w.sha | cut -c1-16
grep -E "  (n|q|qd)/(SHA256SUMS.txt|k/a.json)$" $W/work/up24m4w.sha
cd $W/work && tar cf $W/work/s24m4w.tar -C $S $(cd $S && ls) && ls -l $W/work/s24m4w.tar && sha256sum $W/work/s24m4w.tar
