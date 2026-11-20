"""Check every served anchor against timestamp-bound source PNGs on local scratch."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from PIL import Image, __version__ as pil_version

ROOT = Path(__file__).resolve().parent
LOW = Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres')
STORE = Path(os.environ.get('K3_SERVED_ROOT','/scratch/jjyeung/devs1_frames'))
SKY = dict(zip(['41069054','41291643','42899535','41159782','43828368','45663051','47332598','45261332','43649603','44358634'],
               ['Down','Up','Up','Up','Up','Left','Left','Left','Left','Left']))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(p, obj):
    with p.open('x') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')

def main():
    started = time.monotonic()
    cfg = json.loads((ROOT.parent/'orchard_tower2x/1.json').read_text())
    missing = []
    for row in cfg['x3']:
        for index,h in zip(row['x4'][0]['x0'],row['x4'][0]['x1']):
            p=STORE/h[:2]/(h+'.png')
            if not p.is_file():
                missing.append(dict(capture=row['x3'],index=index,served_sha256=h,path=str(p),
                                    pixel_exact=None,max_abs=None,png_byte_exact=None))
    if missing:
        put(LOW/'out/MISSING_ANCHORS_K3.json',dict(status='blocked',missing=len(missing),records=missing))
        raise ValueError(f'{len(missing)} served PNGs are missing; no recipe can be selected or pixel differences measured.')
    selection_path = LOW.parent/'SELECTION.json'
    selection = json.loads(selection_path.read_text())
    filters = {'nearest':Image.Resampling.NEAREST, 'bilinear':Image.Resampling.BILINEAR,
               'bicubic':Image.Resampling.BICUBIC, 'lanczos':Image.Resampling.LANCZOS,
               'box':Image.Resampling.BOX}
    cv = None
    try:
        sys.path.append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
        import cv2 as cv
        cv.setNumThreads(1)
    except ImportError:
        pass
    methods = ['PIL/'+k for k in filters]
    if cv is not None:
        cfilters = dict(nearest=cv.INTER_NEAREST, bilinear=cv.INTER_LINEAR,
                        bicubic=cv.INTER_CUBIC, lanczos=cv.INTER_LANCZOS4, area=cv.INTER_AREA)
        methods += ['OpenCV/'+k for k in cfilters]
    records, aggregate = [], {}
    manifest = json.loads((ROOT.parent/'work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json').read_text())
    manifest = {x['scene']:x for x in manifest['captures']}
    for row in cfg['x3']:
        video = row['x3'].split('/')[-1]
        sel = selection[video]
        anchors = row['x4'][0]['x0']
        assert anchors == sel['anchors']
        fm = manifest[row['x3']]
        assert sel['n_frames'] == fm['total_num_frames']
        wanted = sorted(set(anchors+[round(a+j*(b-a)/6) for a,b in zip(anchors,anchors[1:]) for j in (2,3,4)]))
        assert wanted == sel['selected'] and len(wanted) == 125
        source_dir = LOW/video/(video+'_frames')/'lowres_wide'
        names = [sel['names'][str(i)] for i in wanted]
        assert names == sorted(names, key=lambda n:float(n.removesuffix('.png').split('_')[-1]))
        assert set(names) <= {p.name for p in source_dir.glob('*.png')}
        turns = [0] if SKY[video]=='Up' else [2] if SKY[video]=='Down' else [1,3]
        for index, served_hash in zip(anchors,row['x4'][0]['x1']):
            p = source_dir/sel['names'][str(index)]
            low_bytes = p.read_bytes()
            with Image.open(io.BytesIO(low_bytes)) as im:
                assert im.size == (256,192)
                src = np.array(im.convert('RGB'))
            served_bytes = (STORE/served_hash[:2]/(served_hash+'.png')).read_bytes()
            assert sha(served_bytes) == served_hash
            with Image.open(io.BytesIO(served_bytes)) as im:
                target = np.array(im.convert('RGB'))
            assert list(target.shape[:2]) == row['x5']
            scores = {}
            for turn in turns:
                rotated = np.ascontiguousarray(np.rot90(src,turn))
                for method in methods:
                    lib, filt = method.split('/')
                    if lib == 'PIL':
                        result = np.array(Image.fromarray(rotated).resize(tuple(reversed(row['x5'])), filters[filt]))
                    else:
                        result = cv.resize(rotated,tuple(reversed(row['x5'])),interpolation=cfilters[filt])
                    delta = np.abs(result.astype(np.int16)-target.astype(np.int16))
                    key = method+('/left_ccw' if turn==1 else '/left_cw' if turn==3 else '')
                    # Non-sideways captures contribute to both candidate direction conventions.
                    keys = [key] if turn in (1,3) else [key+'/left_ccw',key+'/left_cw']
                    stats = dict(pixel_exact=not bool(delta.any()),max_abs=int(delta.max()),mae=float(delta.mean()))
                    buf = io.BytesIO()
                    Image.fromarray(result).save(buf, format='PNG')
                    stats.update(encoded_png_sha256=sha(buf.getvalue()),
                                 png_byte_exact=buf.getvalue()==served_bytes)
                    for key in keys:
                        scores[key] = stats
                        a = aggregate.setdefault(key,dict(anchors=0,exact=0,png_byte_exact=0,max_abs=0,mae_sum=0.))
                        a['anchors'] += 1; a['exact'] += stats['pixel_exact']
                        a['png_byte_exact'] += stats['png_byte_exact']
                        a['max_abs'] = max(a['max_abs'],stats['max_abs']);a['mae_sum'] += stats['mae']
            records.append(dict(video=video,index=index,source=str(p),source_sha256=sha(low_bytes),
                                served_sha256=served_hash,served_raw_sha256=sha(target.tobytes()),candidates=scores))
    best = min(aggregate,key=lambda k:(-aggregate[k]['exact'],aggregate[k]['mae_sum'],aggregate[k]['max_abs']))
    lib,filt,left = best.split('/')
    turns = dict(Up=0,Down=2,Left=1 if left=='left_ccw' else 3,Right=3 if left=='left_ccw' else 1)
    for rec in records:
        with Image.open(rec['source']) as im:
            src = np.ascontiguousarray(np.rot90(np.array(im.convert('RGB')),turns[SKY[rec['video']]]))
        hw = next(r['x5'] for r in cfg['x3'] if r['x3'].endswith(rec['video']))
        if lib=='PIL':
            im = Image.fromarray(src).resize(tuple(reversed(hw)),filters[filt])
        else:
            im = Image.fromarray(cv.resize(src,tuple(reversed(hw)),interpolation=cfilters[filt]))
        buf=io.BytesIO();im.save(buf,format='PNG')
        rec.update(**rec['candidates'][best],decoded_raw_sha256=sha(np.array(im).tobytes()))
    result = dict(recipe=best,turns_ccw=turns,library_versions=dict(PIL=pil_version,OpenCV=None if cv is None else cv.__version__),
                  opencv_note='Unavailable in the authorized Python; no package installation.' if cv is None else 'Tested',
                  anchors=len(records),pixel_exact=sum(r['pixel_exact'] for r in records),
                  png_byte_exact=sum(r['png_byte_exact'] for r in records),max_abs=max(r['max_abs'] for r in records),
                  candidates=aggregate,records=records,selection_sha256=sha(selection_path.read_bytes()),
                  seconds=time.monotonic()-started,
                  png_encoder='Pillow Image.save(format=PNG), default settings; RGB uint8 row-major raw hashes',
                  source_index_binding='SELECTION names map original timestamp ranks; local directory is a 125-frame subset, never reindexed.')
    result.update(served_root=str(STORE),selected_recipe=best if result['pixel_exact']==320 else None)
    put(LOW/'out/RECIPE_K3.json',result)
    print(json.dumps({k:result[k] for k in ('recipe','anchors','pixel_exact','png_byte_exact','max_abs','seconds')}))

if __name__=='__main__':
    main()
