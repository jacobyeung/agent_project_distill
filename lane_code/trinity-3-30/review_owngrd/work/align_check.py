import sys, json, collections, numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_owngrd/work/code2')
from owngrd.common import read_json, rle_decode
from owngrd.labels import to_raster
from owngrd.vocab import prompt_name
from owngrd.teacher import capture_key
W='/scratch/jjyeung/orch_n30/b05_owngrd/work/'
man=read_json(W+'manifests/TEACHER_K1.json')
from pathlib import Path
from PIL import Image
tr={'id':lambda m:m,'rot180':lambda m:m[::-1,::-1],'flipud':lambda m:m[::-1],'fliplr':lambda m:m[:,::-1]}
agg=collections.defaultdict(list); shapes=collections.Counter(); n=0
for c in man['captures']:
    d=Path(W+'pull/teacher_k1/'+capture_key(c['canonical']))
    if not (d/'DONE.json').exists(): continue
    gp=Path(c['gt']['path'])
    if not gp.exists():
        gp=Path(W+'gt/x')/gp.relative_to(gp.parents[2]) if False else None
    t=read_json(d/'teacher.json.gz')
    import glob
    # locate gt
    cand=glob.glob(W+'gt/x/dose_pool/out/*/gt/'+Path(c['gt']['path']).name)
    if not cand: continue
    z=np.load(cand[0])
    id_name={int(i):prompt_name(str(l)) for i,l in zip(z['ids'],z['labels'])}
    f0=c['frames'][0]['path']
    try: im=Image.open(f0); fs=im.size
    except Exception: fs=None
    shapes[(tuple(z['inst'].shape[1:]), tuple(t['frames'][str(t['frame_slots'][0])]['size']), fs)]+=1
    n+=1
    for k,slot in enumerate(t['frame_slots']):
        inst=z['inst'][k]
        if not z['valid'][k]: continue
        for name,p in t['frames'][str(slot)]['phrases'].items():
            gids=[i for i,nm in id_name.items() if nm==name and (inst==i).sum()>=50]
            if not gids: continue
            for pr in p['instances']:
                if pr['joint_score']<=.5: continue
                m=to_raster(rle_decode(pr['mask']),inst.shape)
                for kname,f in tr.items():
                    mm=f(m)
                    agg[kname].append(max(((mm&(inst==i)).sum()/max((mm|(inst==i)).sum(),1)) for i in gids))
print('captures',n,'shapes (raster, teacher size, frame PIL wxh)',dict(shapes))
for k,v in agg.items(): v=np.array(v); print(k,len(v),'meanIoU %.3f'%v.mean(),'frac>=.5 %.3f'%(v>=.5).mean())
