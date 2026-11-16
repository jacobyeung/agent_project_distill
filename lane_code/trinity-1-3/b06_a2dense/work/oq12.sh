set -u; F=/project/community/jjyeung/okh7/db3954b2/selftest; K=/project/community/jjyeung/cp4tk_fr/k6tk; cd $F
ls $K/parts/a0n3 | head -5
nice -n 19 /project/community/jjyeung/cp4tk_fr/venv/bin/python -I - <<'PY'
import json, tarfile, cv2, numpy as np, os, glob
K='/project/community/jjyeung/cp4tk_fr/k6tk'
pairs=json.load(open('pairs.json'))
hits={l.split('\t')[0]:l.split('\t')[1].strip() for l in open('hits.tsv')}
want={}
for k,old,new in pairs: want.setdefault(hits[old],{})[old[:2]+'/'+old+'.png']=(k,old,new)
res=[]
for tname,members in want.items():
    tp=glob.glob(f'{K}/parts/*/{tname}')[0]
    with tarfile.open(tp,'r:') as t:
        for m in t:
            if m.name in members:
                k,old,new=members[m.name]
                a=cv2.imdecode(np.frombuffer(t.extractfile(m).read(),np.uint8),cv2.IMREAD_UNCHANGED)
                b=cv2.imread(f'loca/store/{new[:2]}/{new}.png',cv2.IMREAD_UNCHANGED)
                d=np.abs(a.astype(int)-b.astype(int))
                res.append(dict(k=k,eq=old==new,shape=[a.shape,b.shape],max=int(d.max()),mean=round(float(d.mean()),4),frac=round(float((d>0).mean()),5),psnr=round(float(10*np.log10(255**2/max((d**2).mean(),1e-12))),2)))
print(json.dumps(res))
import platform; print(cv2.getBuildInformation().split('CPU/HW features')[1][:600] if 'CPU/HW features' in cv2.getBuildInformation() else '', platform.processor())
PY
grep -m3 -i "model name\|flags" /proc/cpuinfo | cut -c1-300
