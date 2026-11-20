"""Synthetic raster test through the real frozen preprocessing and CPU stub tower.

This test does not verify the missing served anchors or choose a production recipe.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('worker',ROOT/'2.py')
W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)

def main():
    started=time.monotonic()
    cfg=json.loads((ROOT.parent/'orchard_tower2x/1.json').read_text())
    import tempfile
    data=Path(tempfile.mkdtemp(prefix='cpu_fixture_',dir=ROOT))
    served=data/'s';served.mkdir();low=data/'l';low.mkdir()
    anchor=list(range(0,187,6))
    plans=[anchor,sorted(anchor+list(range(3,186,6))),sorted(anchor+list(range(2,186,6))+list(range(4,186,6))),anchor]
    made={}
    for i in sorted(set(sum(plans,[]))):
        y,x=np.mgrid[:192,:256]
        a=np.stack([(x+i)%256,(y+2*i)%256,(x+y+3*i)%256],axis=-1).astype(np.uint8)
        source=Image.fromarray(a);p=low/(str(i)+'.png');source.save(p)
        im=Image.fromarray(np.rot90(a,2).copy()).resize((640,480),Image.Resampling.BILINEAR)
        raw=hashlib.sha256(im.tobytes()).hexdigest()
        sh=None
        if i in anchor:
            import io
            b=io.BytesIO();im.save(b,format='PNG');blob=b.getvalue();sh=hashlib.sha256(blob).hexdigest()
            dest=served/sh[:2];dest.mkdir(exist_ok=True)
            (dest/(sh+'.png')).write_bytes(blob)
        made[i]=(W.digest(p),raw,sh)
    row=dict(cfg['x3'][0],x4=[],x6=2)
    for arm,ids in enumerate(plans):
        islow=[arm==3 or i not in anchor for i in ids]
        row['x4'].append(dict(x0=ids,x1=[made[i][0 if l else 2] for i,l in zip(ids,islow)],
            x2=[ids.index(i) for i in anchor],x3=[str(i)+'.png' if l else made[i][2][:2]+'/'+made[i][2]+'.png' for i,l in zip(ids,islow)],
            x5=islow,x6=[made[i][1] for i in ids]))
    pay=ROOT.parent/'work/payload'
    cfg.update(x3=[row],x8=[str(pay/'tree')],xc=str(served),xl=str(low),
               xk=[0,int(Image.Resampling.BILINEAR),'cv2'],
               xp=[['(32, 64, 96)','(32, 63, 64, 94, 96)',3],['(32, 64, 96)','(32, 63, 64, 94, 96)',1],
                   ['or frames % 2','or (frames % 2 and frames != 63)',1]],
               xm=['aggregator','local_camera_head','global_camera_head','depth_head','point_head','student_pilot._tower_native','selected_layers'],
               xq=4,xr=[0,1,2,3],xs=3.,xt=True)
    for pin in cfg['x9']:
        pin[0]=str(pay/pin[0].split('/p/',1)[1])
    result=W.run(cfg,stub=True,only=1)
    if not result['complete']:
        W.Engine(cfg,True).run(row,1)
    assert result['complete'],dict(error=result['error'],ran=result['ran'])
    assert [len(a['c2w']) for a in result['rows'][0]['arms']]==[32,63,94,32]
    expected=row['x4'][0]['x6']
    for arm in result['rows'][0]['arms']:
        assert [arm['raw_sha256'][s] for s in arm['slots']]==expected
    bad=dict(cfg,xt=False)
    try:W.run(bad,stub=True)
    except ValueError:pass
    else:raise AssertionError('Unverified recipe admitted')
    bad=dict(cfg,x7=[1501.]+cfg['x7'][1:])
    try:W.run(bad,stub=True)
    except ValueError:pass
    else:raise AssertionError('Excess forecast admitted')
    result['test_scope']='Synthetic fixture only. Real 1024/518 preprocessing, real pose decoding, stub backbone and heads; no recipe evidence.'
    result['test_seconds']=time.monotonic()-started
    W.write(ROOT/'CPU_PIPELINE.json',result)
    print(json.dumps(dict(passed=True,frames=[32,63,94,32],seconds=result['test_seconds'],
                         rss_kib=max(a['rss_kib'] for a in result['rows'][0]['arms']))))

if __name__=='__main__':main()
