W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - >&2 <<'PY'
import json,os,hashlib,tarfile
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/UPLOADS_NEW_23B.json'))
d=d if isinstance(d,list) else d.get('files',d)
t=tarfile.open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k23b.tar','w')
for e in d:
    p=e['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest()
    print(e['name'],e['bytes'],h==e['sha256'])
    t.add(p,arcname=e['name'])
t.close()
PY
sha256sum $W/work/k23b.tar >&2; stat -c %s $W/work/k23b.tar >&2
ps -u jjyeung -o pid,rss,etime,args | grep -v grep | grep "w23\|build23b\|native23" | cut -c1-150 >&2
base64 -w0 $W/work/k23b.tar
