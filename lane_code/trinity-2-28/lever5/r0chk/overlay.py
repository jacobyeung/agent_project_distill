import sys,json,numpy as np
from PIL import Image,ImageDraw
sys.argv=['x']; exec(open('align2.py').read().split("pairs=json.load")[0])
def aligned(dv,tr):
    xa=load(dv); xb=load(tr); a=band(xa); b=band(xb); s,deg=score(a,b)
    q=b@rot(np.radians(deg)).T; ta=cKDTree(a); sh=np.zeros(2)
    for _ in range(8):
        d,i=ta.query(q+sh); m=d<np.percentile(d,70); sh+=np.mean(a[i[m]]-(q[m]+sh),0)
    def mid(x,c): z=x[:,2]; lo,hi=np.percentile(z,[1,99]); y=x[(z>lo+0.2)&(z<hi-0.2)]; y=y[rng.choice(len(y),min(len(y),150000),replace=False)]; return y[:,:2]-c
    ca=xa[:,:2][(xa[:,2]>np.percentile(xa[:,2],99)-0.9)].mean(0); cb=xb[:,:2][(xb[:,2]>np.percentile(xb[:,2],99)-0.9)].mean(0)
    pa=mid(xa,ca); pb=mid(xb,cb)@rot(np.radians(deg)).T+sh
    return pa,pb,s
def img(pa,pb,title,px=300,half=4.5):
    I=np.full((px,px,3),255,np.uint8)
    for p,ch in ((pa,0),(pb,2)):
        ij=((p+half)/(2*half)*px).astype(int); ok=(ij>=0).all(1)&(ij<px).all(1)
        h=np.zeros((px,px)); np.add.at(h,(ij[ok,1],ij[ok,0]),1); m=h>2
        for c in range(3):
            if c!=ch: I[...,c][m]=(I[...,c][m]*0.35).astype(np.uint8)
    im=Image.fromarray(I[::-1]); ImageDraw.Draw(im).text((4,4),title,fill=(0,0,0)); return im
rows=[('49fe768553','5334a4164a'),('69e56cf0f8','4f144c7489'),('781f5de0a8','8d0f714398')]
W=Image.new('RGB',(3*305,305),'white')
for k,(dv,tr) in enumerate(rows):
    pa,pb,s=aligned(dv,tr); W.paste(img(pa,pb,f'{dv}(red-ish) vs {tr} in {s:.2f}'),(k*305,0))
W.save('stage_c/OVERLAY.png'); print('ok')
