import json,numpy as np,os
from PIL import Image, ImageDraw
S=json.load(open('vis_sample.json'))
MC='n2r/mc/sj/mask_recall_run/results/'
man={c['native']:c for c in json.load(open(MC+'dense/MANIFEST.json'))['captures']}
def decode(rle):
    h,w=rle['size']; counts=np.asarray(rle['counts'],np.int64)
    return np.repeat(np.arange(len(counts))%2,counts).astype(bool).reshape((h,w),order='F')
tiles=[]
for s in S:
    f='frames/'+s['png']
    if not os.path.exists(f): print('missing',s['name']); continue
    im=Image.open(f).convert('RGB')
    c=json.loads(np.load(MC+'dense/candidates/'+man[s['native']]['scene'].replace('/','__')+'.npz')['payload'].tobytes())
    rec=c['frames'][str(s['slot'])]['phrases'].get(s['name'])
    ov=np.array(im).astype(float)
    if rec and rec.get('instances'):
        e=max(rec['instances'],key=lambda e:float(e['score']))
        m=decode(e['mask'] if isinstance(e['mask'],dict) else eval(e['mask']))
        if m.shape!=ov.shape[:2]: m=np.array(Image.fromarray(m.astype(np.uint8)*255).resize((ov.shape[1],ov.shape[0])))>0
        ov[m]=0.45*ov[m]+0.55*np.array([255,0,0])
    im2=Image.fromarray(ov.astype(np.uint8)); d=ImageDraw.Draw(im2)
    d.rectangle([0,0,im2.width,22],fill=(0,0,0)); d.text((4,4),'%s | %s | %s s=%.2f p=%s'%(s['name'],s['native'],s['cls'][0],s['score'],None if s['presence'] is None else round(s['presence'],2)),fill=(255,255,0))
    im2.thumbnail((400,400)); tiles.append(im2)
for k in range(0,len(tiles),6):
    T=tiles[k:k+6]; W=2*400; H=3*400
    M=Image.new('RGB',(W,H),(30,30,30))
    for i,t in enumerate(T): M.paste(t,((i%2)*400,(i//2)*400))
    M.save('vis_%d.jpg'%(k//6),quality=80); print('vis_%d.jpg'%(k//6), len(T))
