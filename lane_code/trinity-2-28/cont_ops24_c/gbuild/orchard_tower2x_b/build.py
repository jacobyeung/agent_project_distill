"""Build only after the served-raster comparison has established the recipe.

The 50 MB limit includes the placement and a 4.5 MB return reserve.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OUT=BASE.parent/'cap/score_tower2x_b'
LOW=Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres')
TOKEN='ac794e028b16f'
REMOTE='/project/community/jjyeung/'+TOKEN

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def put(p,obj):
    with Path(p).open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--drop-c',action='store_true')
    ap.add_argument('--project-cap',type=int,default=50_000_000)
    args=ap.parse_args()
    recipe=json.loads((LOW/'out/RECIPE_K3.json').read_text())
    assert recipe['anchors']==320 and len(recipe['records'])==320
    assert all(r['pixel_exact'] is not None and r['max_abs'] is not None for r in recipe['records'])
    cfg=json.loads((BASE/'orchard_tower2x/1.json').read_text())
    ref=json.loads((BASE.parent/'cap/score_tower2x/REFERENCE.json').read_text())
    selection_path=LOW.parent/'SELECTION.json'
    assert sha(selection_path)==recipe['selection_sha256']
    selection=json.loads(selection_path.read_text())
    exact=recipe['pixel_exact']==320
    library,filt,_=recipe['recipe'].split('/')
    if library=='PIL':
        code=int(getattr(Image.Resampling,filt.upper()))
    else:
        sys.path.append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
        import cv2
        cv2.setNumThreads(1)
        code={'nearest':cv2.INTER_NEAREST,'bilinear':cv2.INTER_LINEAR,'bicubic':cv2.INTER_CUBIC,
              'lanczos':cv2.INTER_LANCZOS4,'area':cv2.INTER_AREA}[filt]
    records={(r['video'],r['index']):r for r in recipe['records']}
    sky=dict(zip(['41069054','41291643','42899535','41159782','43828368','45663051','47332598','45261332','43649603','44358634'],
                 ['Down','Up','Up','Up','Up','Left','Left','Left','Left','Left']))
    # Count original PNG bytes before packing. C can be explicitly dropped for an exact recipe;
    # the requested nonexact fallback automatically drops it when necessary.
    total=0
    for v,s in selection.items():
        d=LOW/v/(v+'_frames')/'lowres_wide'
        total+=sum((d/s['names'][str(i)]).stat().st_size for i in s['selected'] if not exact or i not in s['anchors'])
    drop=args.drop_c or (not exact and total+4_500_000>=args.project_cap)
    if exact and not drop and total+4_500_000>=args.project_cap:
        raise ValueError('B+C originals exceed the placement cap. Resolve --drop-c or --project-cap before building.')
    cfg.update(x0=TOKEN,xk=[0 if library=='PIL' else 1,code,'cv2'],xl=REMOTE+'/8',
        xp=[['(32, 64, 96)','(32, 63, 64, 94, 96)',3],['(32, 64, 96)','(32, 63, 64, 94, 96)',1],
            ['or frames % 2','or (frames % 2 and frames != 63)',1]],
        xm=['aggregator','local_camera_head','global_camera_head','depth_head','point_head','student_pilot._tower_native','selected_layers'],
        xr=[0,1,2] if exact else [0,3,1,2],xs=3.,xt=True)
    low_files={}
    for row,reference in zip(cfg['x3'],ref['captures']):
        v=row['x3'].split('/')[-1];s=selection[v];anchors=s['anchors']
        assert anchors==row['x4'][0]['x0']
        row['x6']=recipe['turns_ccw'][sky[v]]
        original=row['x4'][0]
        plans=[anchors,sorted(anchors+[round(a+3*(b-a)/6) for a,b in zip(anchors,anchors[1:])]),
               sorted(anchors+[round(a+j*(b-a)/6) for a,b in zip(anchors,anchors[1:]) for j in (2,4)])]
        if not exact:plans.append(anchors)
        row['x4']=[];reference['arms']=[]
        for arm,ids in enumerate(plans):
            if arm==2 and drop:
                row['x4'].append(None);reference['arms'].append(None);continue
            hashes,raw_hashes,names,flags=[],[],[],[]
            for i in ids:
                low=arm!=0 and (not exact or i not in anchors)
                if low:
                    p=LOW/v/(v+'_frames')/'lowres_wide'/s['names'][str(i)]
                    h=sha(p);low_files[h+'.png']=p
                    with Image.open(p) as im:
                        arr=np.ascontiguousarray(np.rot90(np.asarray(im.convert('RGB')),row['x6']))
                    if library=='PIL':im=Image.fromarray(arr).resize(tuple(reversed(row['x5'])),code)
                    else:im=Image.fromarray(cv2.resize(arr,tuple(reversed(row['x5'])),interpolation=code))
                    raw=hashlib.sha256(im.tobytes()).hexdigest();name=h+'.png'
                    if i in anchors:
                        assert h==records[v,i]['source_sha256'] and raw==records[v,i]['decoded_raw_sha256']
                else:
                    h=original['x1'][anchors.index(i)];raw=records[v,i]['served_raw_sha256'];name=h[:2]+'/'+h+'.png'
                    assert h==records[v,i]['served_sha256']
                hashes.append(h);raw_hashes.append(raw);names.append(name);flags.append(low)
            slots=[ids.index(i) for i in anchors]
            row['x4'].append(dict(x0=ids,x1=hashes,x2=slots,x3=names,x5=flags,x6=raw_hashes))
            reference['arms'].append(dict(ids=ids,sha256=hashes,raw_sha256=raw_hashes,slots=slots))
    cfg['xq']=0
    cost=lambda a:cfg['x7'][2]*cfg['x7'][3+(0 if a==3 else a)]+cfg['xs']
    fixed=cfg['x7'][0]+cfg['x7'][1]+cfg['x7'][6]
    tasks=[(r,a) for a in cfg['xr'] for r,row in enumerate(cfg['x3']) if row['x4'][a] is not None]
    full_estimate=fixed+sum(cost(a) for _,a in tasks)
    if full_estimate>1500:
        raise ValueError(f'All requested arms forecast {full_estimate/60:.2f} min; stop before packaging (25 min cap).')
    cfg['xr']=[a for a in cfg['xr'] if any(row['x4'][a] is not None for row in cfg['x3'])]
    estimate=fixed
    for r,a in tasks:
        if estimate+cost(a)>1500:break
        estimate+=cost(a);cfg['xq']+=1
    assert cfg['xq']>=10
    put(ROOT/'1.json',cfg)
    ref.update(token=TOKEN,input_sha256=sha(ROOT/'1.json'),labels=['A','B','C'] if exact else ['A','B','C',"A'"],
               recipe_sha256=sha(LOW/'out/RECIPE_K3.json'),active_comparisons=['B'] if drop else ['B','C'])
    put(OUT/'REFERENCE.json',ref)
    with tarfile.open(ROOT/'8.tgz','x:gz') as t:
        for name,p in sorted(low_files.items()):
            blob=p.read_bytes();assert hashlib.sha256(blob).hexdigest()+'.png'==name
            info=tarfile.TarInfo(name);info.size=len(blob);info.mode=0o600;info.mtime=0
            t.addfile(info,io.BytesIO(blob))
    (ROOT/'BATCH.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexec /usr/bin/python3 -I -s -B '+REMOTE+'/0.py 1 '+REMOTE+'\n')
    bound=['0.py','1.json','2.py','8.tgz','BATCH.sh']
    put(ROOT/'3.json',{n:sha(ROOT/n) for n in bound});bound.append('3.json')
    placement=sum((ROOT/n).stat().st_size for n in bound)
    assert placement+4_500_000<args.project_cap
    assets={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in bound}
    place=(BASE/'orchard_tower2x/o_place.sh').read_text()
    start=place.index('assets=');end=place.index('\ndata=',start)
    place=place[:start]+'assets='+repr(assets)+place[end:]
    old=json.loads((BASE/'orchard_tower2x/BUILD.json').read_text())
    place=place.replace(old['path'],REMOTE).replace('2_000_000',str(args.project_cap-4_500_000))
    (ROOT/'o_place.sh').write_text(place)
    for name in ('o_cpu.sh','o_check_sub.sh','o_fetch.sh','SUBMIT.cmd'):
        text=(BASE/'orchard_tower2x'/name).read_text().replace(old['token'],TOKEN)
        text=text.replace('--cpus-per-task=16 --mem=200G','--cpus-per-task=8 --mem=20G')
        text=text.replace('--cpus-per-task=1 --mem=2G --time=00:05:00','--cpus-per-task=8 --mem=20G --time=00:30:00')
        (ROOT/name).write_text(text)
    put(ROOT/'BUILD.json',dict(token=TOKEN,path=REMOTE,bound_files=bound,placement_bytes=placement,
        return_reserve_bytes=4_500_000,project_budget_bytes=args.project_cap,
        original_lowres_bytes=sum(p.stat().st_size for p in low_files.values()),C_dropped=drop,pixel_exact=exact))
    put(ROOT/'FORECAST.json',dict(estimate_minutes=estimate/60,full_minutes=(fixed+sum(cost(a) for _,a in tasks))/60,
        admitted_prefix=tasks[:cfg['xq']],execution_order=cfg['xr'],decode_allowance_seconds_per_capture_arm=3,
        prior= json.loads((BASE/'orchard_tower2x/FORECAST.json').read_text()),
        note='All requested tasks fit below 25 min. Tasks run in arm order only if their conservative cost plus the 120 s return reserve fits the allocation deadline. Cold staging and GPU memory remain unmeasured.'))
    print(json.dumps(dict(placement_bytes=placement,forecast_minutes=estimate/60,C_dropped=drop)))

if __name__=='__main__':main()
