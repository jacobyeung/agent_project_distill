"""Package the authorized two-arm experiment and a stdin archive installer."""
import hashlib
import io
import json
from pathlib import Path
import shlex
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
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def pack(path, files, mode):
    with tarfile.open(path,mode,format=tarfile.USTAR_FORMAT) as t:
        for name,p in sorted(files.items()):
            blob=p.read_bytes()
            info=tarfile.TarInfo(name);info.size=len(blob);info.mode=0o600;info.mtime=0
            t.addfile(info,io.BytesIO(blob))

def main():
    recipe=json.loads((LOW/'out/RECIPE_K3c.json').read_text())
    assert recipe['anchors']==320 and recipe['accepted_nonexact']
    assert recipe['turns_ccw']['Up']==recipe['turns_ccw']['Down']==0 and recipe['turns_ccw']['Left']==3
    cfg=json.loads((BASE/'orchard_tower2x/1.json').read_text())
    ref=json.loads((BASE.parent/'cap/score_tower2x/REFERENCE.json').read_text())
    cached=json.loads((BASE.parent/'cap/score_tower2x/T1_EXTRACT.json').read_text())
    assert sha(BASE.parent/'cap/t1.gz')==cached['receipt']['raw_sha256']==ref['t1_receipt']['raw_sha256']
    for r in ref['captures']:
        old=cached['captures'][r['capture']]
        assert r['t1']==old['c2w'] and r['scale']==old['scale']
        assert r['arms'][0]['ids']==old['source_indices']
    selection_path=LOW.parent/'SELECTION.json'
    assert sha(selection_path)==recipe['selection_sha256']
    selection=json.loads(selection_path.read_text())
    library,filt,_=recipe['recipe'].split('/')
    if library=='PIL':code=int(getattr(Image.Resampling,filt.upper()))
    else:
        sys.path.append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
        import cv2
        cv2.setNumThreads(1)
        code={'nearest':cv2.INTER_NEAREST,'bilinear':cv2.INTER_LINEAR,'bicubic':cv2.INTER_CUBIC,
              'lanczos':cv2.INTER_LANCZOS4,'area':cv2.INTER_AREA}[filt]
    records={(r['video'],r['index']):r for r in recipe['records']}
    cfg.update(x0=TOKEN,xk=[0 if library=='PIL' else 1,code,'cv2'],xl=REMOTE+'/8',
        xp=[['(32, 64, 96)','(32, 63, 64, 94, 96)',3],['(32, 64, 96)','(32, 63, 64, 94, 96)',1],
            ['or frames % 2','or (frames % 2 and frames != 63)',1]],
        xm=['aggregator','local_camera_head','global_camera_head','depth_head','point_head','student_pilot._tower_native','selected_layers'],
        xr=[0,1],xs=3.,xt=True,xq=20)
    low_files={}
    for row,reference in zip(cfg['x3'],ref['captures']):
        assert row['x0']==reference['key']
        v=row['x3'].split('/')[-1];s=selection[v];anchors=s['anchors']
        assert anchors==row['x4'][0]['x0']==reference['arms'][0]['ids']
        row['x6']=3 if row['x5'][0]>row['x5'][1] else 0
        plans=[anchors,sorted(anchors+[round(a+3*(b-a)/6) for a,b in zip(anchors,anchors[1:])])]
        row['x4']=[];reference['arms']=[]
        decoded={}
        for i in plans[1]:
            p=LOW/v/(v+'_frames')/'lowres_wide'/s['names'][str(i)]
            h=sha(p);low_files[h+'.png']=p
            with Image.open(p) as im:arr=np.ascontiguousarray(np.rot90(np.asarray(im.convert('RGB')),row['x6']))
            if library=='PIL':im=Image.fromarray(arr).resize(tuple(reversed(row['x5'])),code)
            else:im=Image.fromarray(cv2.resize(arr,tuple(reversed(row['x5'])),interpolation=code))
            raw=hashlib.sha256(im.tobytes()).hexdigest()
            if i in anchors:
                assert h==records[v,i]['source_sha256'] and raw==records[v,i]['decoded_raw_sha256']
            decoded[i]=(h,raw)
        for ids in plans:
            hashes=[decoded[i][0] for i in ids];raws=[decoded[i][1] for i in ids];slots=[ids.index(i) for i in anchors]
            row['x4'].append(dict(x0=ids,x1=hashes,x2=slots,x3=[h+'.png' for h in hashes],x5=[True]*len(ids),x6=raws))
            reference['arms'].append(dict(ids=ids,sha256=hashes,raw_sha256=raws,slots=slots))
    stage,load,factor,t32,t64,_,reserve=cfg['x7']
    estimate=stage+load+factor*10*(t32+t64)+20*cfg['xs']+reserve
    assert estimate<=1500 and len(low_files)==630
    put(ROOT/'1.json',cfg)
    ref.update(token=TOKEN,input_sha256=sha(ROOT/'1.json'),labels=["A'",'B'],baseline="A'",
               control_limit_deg=1.,control_required=8,recipe_sha256=sha(LOW/'out/RECIPE_K3c.json'),active_comparisons=['B'],
               t1_extract_sha256=sha(BASE.parent/'cap/score_tower2x/T1_EXTRACT.json'))
    put(OUT/'REFERENCE.json',ref)
    pack(ROOT/'8.tgz',low_files,'w:gz')
    (ROOT/'BATCH.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexec /usr/bin/python3 -I -s -B '+REMOTE+'/0.py 1 '+REMOTE+'\n')
    bound=['0.py','1.json','2.py','8.tgz','BATCH.sh']
    put(ROOT/'3.json',{n:sha(ROOT/n) for n in bound});bound.append('3.json')
    placement=sum((ROOT/n).stat().st_size for n in bound)
    assert placement+4_500_000<50_000_000
    pack(ROOT/'place.tar',{n:ROOT/n for n in bound},'w')
    size=(ROOT/'place.tar').stat().st_size
    # The complete shell command ends before the first tar byte. exec hands fd 0 to Python.
    installer=f'''import hashlib,io,json,os,sys,tarfile
from pathlib import Path
os.umask(0o077)
p=Path({REMOTE!r})
b=sys.stdin.buffer.read({size+1})
if len(b)!={size} or hashlib.sha256(b).hexdigest()!={sha(ROOT/'place.tar')!r}:raise ValueError('E40')
with tarfile.open(fileobj=io.BytesIO(b),mode='r:') as t:
    members=t.getmembers()
    if len(members)!=6 or set(m.name for m in members)!={set(bound)!r} or any(not m.isfile() for m in members):raise ValueError('E41')
    data={{m.name:t.extractfile(m).read() for m in members}}
if sum(map(len,data.values()))>=45500000:raise ValueError('E42')
for n,h in json.loads(data['3.json']).items():
    if hashlib.sha256(data[n]).hexdigest()!=h:raise ValueError('E43')
p.mkdir(mode=0o700)
for n,b in data.items():
    with (p/n).open('xb') as f:f.write(b)
print(sum(map(len,data.values())))
'''
    header='exec /usr/bin/python3 -I -s -B -c '+shlex.quote(installer)+'\n'
    (ROOT/'o_place_head.sh').write_text(header)
    old=json.loads((BASE/'orchard_tower2x/BUILD.json').read_text())
    for name in ('o_cpu.sh','o_check_sub.sh','o_fetch.sh','SUBMIT.cmd'):
        text=(BASE/'orchard_tower2x'/name).read_text().replace(old['token'],TOKEN)
        text=text.replace('--cpus-per-task=16 --mem=200G','--cpus-per-task=8 --mem=20G')
        text=text.replace('--cpus-per-task=1 --mem=2G --time=00:05:00','--cpus-per-task=8 --mem=20G --time=00:30:00')
        text=text.replace('--partition=general','--partition=general --exclude=orchard-community-4')
        if name=='o_cpu.sh':text=text.replace('reply=$(',"q=$(squeue -u jjyeung -p general -h)\ntest -z \"$q\"\nreply=$(")
        (ROOT/name).write_text(text)
    put(ROOT/'BUILD.json',dict(token=TOKEN,path=REMOTE,bound_files=bound,placement_bytes=placement,
        archive_bytes=size,archive_sha256=sha(ROOT/'place.tar'),header_bytes=len(header.encode()),stream_bytes=size+len(header.encode()),
        return_reserve_bytes=4_500_000,project_budget_bytes=50_000_000,
        original_lowres_bytes=sum(p.stat().st_size for p in low_files.values()),lowres_files=len(low_files),arms=["A'",'B']))
    put(ROOT/'FORECAST.json',dict(estimate_seconds=estimate,estimate_minutes=estimate/60,stage_seconds=stage,
        load_seconds=load,inference_safety_factor=factor,measured_32_seconds=t32,measured_64_seconds=t64,
        count_per_arm=10,decode_seconds=20*cfg['xs'],return_reserve_seconds=reserve,execution_order=cfg['xr'],
        formula='600 + load + 1.5 * 10 * (measured32 + measured64) + 20 * 3 + 120',
        note='The 63-frame estimate uses the measured 64-frame time; real staging and GPU runtime/memory remain unmeasured.'))
    print(json.dumps(dict(placement_bytes=placement,archive_bytes=size,stream_bytes=size+len(header.encode()),forecast_minutes=estimate/60)))

if __name__=='__main__':main()
