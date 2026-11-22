# Apply wa.py's exact orient()+imencode to the /data3-3dod lowres_wide copies on local scratch; compare with served anchors.
import json, sys, glob, os, hashlib
import numpy as np, cv2
cv2.setNumThreads(1)
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
import gzip
P=json.load(gzip.open('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/in/pk/frame_plan.json.gz'))
F=json.load(open('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'))
al={c['native']:c['plan_alias'] for c in F['captures']}
for cid in sys.argv[1:]:
    c=[x for x in G['captures'] if x['capture']=='arkitscenes/'+cid][0]
    e=P['a'][al[c['native']]]
    base=f'/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/{cid}/{cid}_frames/lowres_wide'
    files=sorted(glob.glob(base+'/*.png')); ts=np.array([float(os.path.basename(p)[:-4].rpartition('_')[2]) for p in files])
    need={k:t for k,t,fl in e['need']}
    n=sha_ok=px_ok=0; diffs=[]
    for f in c['frames']:
        t=need[f['index']]; j=int(np.argmin(np.abs(ts-t)))
        if abs(ts[j]-t)>0.002: continue
        img=cv2.imread(files[j],cv2.IMREAD_COLOR)
        rot=e['rot']
        if rot=='cw': img=cv2.rotate(img,cv2.ROTATE_90_CLOCKWISE)
        elif rot=='ccw': img=cv2.rotate(img,cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rot=='180': img=cv2.rotate(img,cv2.ROTATE_180)
        h,w=img.shape[:2]; img2=cv2.resize(img,(int(round(w*2.5)),int(round(h*2.5))),interpolation=cv2.INTER_CUBIC)
        ok,enc=cv2.imencode('.png',img2,[cv2.IMWRITE_PNG_COMPRESSION,3])
        served=cv2.imread(f['path'],cv2.IMREAD_COLOR)
        n+=1; sha_ok+=hashlib.sha256(enc.tobytes()).hexdigest()==f['sha256']
        d=np.abs(img2.astype(int)-served.astype(int)); px_ok+=d.max()<=1; diffs.append(d.mean())
    print(cid,'rot',e['rot'],'anchors_tested',n,'sha_equal',sha_ok,'pixels_within1',px_ok,'mean_abs_median',round(float(np.median(diffs)),3) if diffs else None)
