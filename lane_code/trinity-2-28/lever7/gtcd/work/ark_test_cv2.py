import json, sys, glob, os, hashlib, io
import numpy as np, cv2
from PIL import Image
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
cid=sys.argv[1]
c=[x for x in G['captures'] if x['capture']=='arkitscenes/'+cid][0]
base=f'/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/{cid}/{cid}_frames'
rows=np.loadtxt(base+'/lowres_wide.traj')
pngs={round(float(os.path.basename(p)[len(cid)+1:-4]),3):p for p in glob.glob(base+'/lowres_wide/*.png')}
ok=0;tot=0
for f in c['frames']:
    i=f['index']; p=pngs.get(round(rows[i,0],3))
    if p is None: continue
    tot+=1
    served=np.asarray(Image.open(f['path']).convert('RGB'))
    bgr=cv2.imread(p,cv2.IMREAD_COLOR)
    res=[]
    for nm,fl in [('linear',cv2.INTER_LINEAR),('cubic',cv2.INTER_CUBIC),('lanczos4',cv2.INTER_LANCZOS4),('area',cv2.INTER_AREA),('linear_exact',cv2.INTER_LINEAR_EXACT),('nearest',cv2.INTER_NEAREST)]:
        r=cv2.cvtColor(cv2.resize(bgr,(640,480),interpolation=fl),cv2.COLOR_BGR2RGB)
        d=np.abs(r.astype(int)-served.astype(int)); res.append((d.mean(),nm,int(d.max())))
        if d.max()==0:
            # re-encode test
            buf=io.BytesIO(); Image.fromarray(r).save(buf,format='PNG'); s1=hashlib.sha256(buf.getvalue()).hexdigest()
            ok_,enc=cv2.imencode('.png',cv2.cvtColor(r,cv2.COLOR_RGB2BGR)); s2=hashlib.sha256(enc.tobytes()).hexdigest()
            res.append(('PIXELS EXACT', nm, 'pil_png_sha_match', s1==f['sha256'], 'cv2_png_sha_match', s2==f['sha256']))
    res.sort(key=lambda x: (0 if x[0]=='PIXELS EXACT' else 1, x[0] if x[0]!='PIXELS EXACT' else 0))
    print(i, res[:3])
