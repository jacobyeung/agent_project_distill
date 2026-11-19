W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - >&2 <<'PY'
import json,os,hashlib,tarfile
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/out/UPLOADS_NEW.json'))
t=tarfile.open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k23u.tar','w')
for e in d:
    if e['name'].startswith('u/'):
        p=e['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest()
        print(e['name'],e['bytes'],os.path.getsize(p),h==e['sha256'],e.get('availability'))
        t.add(p,arcname=e['name'])
t.close()
PY
sha256sum $W/work/k23u.tar >&2; stat -c %s $W/work/k23u.tar >&2
base64 -w0 $W/work/k23u.tar
