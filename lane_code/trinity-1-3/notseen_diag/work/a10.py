import json,collections,ast,numpy as np
from scipy import ndimage
SHAPE=(80,112)
def small_rle(rle):
    h,w=rle['size']
    y=ndimage.zoom(np.arange(h),SHAPE[0]/h,order=0,prefilter=False); x=ndimage.zoom(np.arange(w),SHAPE[1]/w,order=0,prefilter=False)
    counts=np.asarray(rle['counts'],np.int64)
    return (np.searchsorted(np.cumsum(counts),y[:,None]+x[None,:]*h,side='right')%2).astype(bool)
rows,cols=np.indices(SHAPE); u=(cols+.5)/SHAPE[1]*1000; v=(rows+.5)/SHAPE[0]*1000
crop=(u>=20)&(u<=980)&(v>=20)&(v<=980)
P=json.load(open('pairs_cache.json'))
MC='n2r/mc/sj/mask_recall_run/results/'
man={c['native']:c for c in json.load(open(MC+'dense/MANIFEST.json'))['captures']}
cache={}
def load(native):
    if native not in cache:
        c=man[native]; cache[native]=json.loads(np.load(MC+'dense/candidates/'+c['scene'].replace('/','__')+'.npz')['payload'].tobytes())
    return cache[native]
for o in P:
    d=o['dense']
    if d['cache']!='ok': continue
    c=load(o['native']); ph=d['phrase']
    n03=nel=0; fr=set(); areas=[]
    for s in range(32):
        rec=c['frames'][str(s)]['phrases'].get(ph)
        if not rec: continue
        for e in rec.get('instances') or []:
            if float(e['score'])<.3: continue
            n03+=1
            m=e['mask'] if isinstance(e['mask'],dict) else ast.literal_eval(e['mask'])
            sm=small_rle(m); er=ndimage.binary_erosion(sm,structure=np.ones((3,3)))
            k=int((er&crop).sum())
            if k>0: nel+=1; fr.add(s+1)
            areas.append(sum(m['counts'][1::2])/(m['size'][0]*m['size'][1]))
    d.update(n_props_s03=n03,n_props_elig_geomfree=nel,n_frames_elig_geomfree=len(fr))
json.dump(P,open('pairs_cache.json','w'))
C=collections.Counter()
for o in P:
    d=o['dense']
    if d['cache']!='ok': continue
    if d['n_kept']==0: cls='A_sam3_none'
    elif d['n_props_s03']==0: cls='B_score_floor'
    elif d['n_props_elig_geomfree']==0: cls='C_raster_erosion_crop'
    else: cls='D_has_eligible_raster'
    o['cls']=cls; C[(o['h1'],cls)]+=1
for k,v in sorted(C.items()): print(k,v)
json.dump(P,open('pairs_cache.json','w'))
ns=[o for o in P if o['h1']=='not seen']
q=lambda a:list(np.round(np.percentile(a,[10,25,50,75,90]),1))
for lab in ('not seen','seen'):
    S=[o for o in P if o['h1']==lab and o['cls']=='D_has_eligible_raster']
    print(lab,'n_frames_elig',q([o['dense']['n_frames_elig_geomfree'] for o in S]))
