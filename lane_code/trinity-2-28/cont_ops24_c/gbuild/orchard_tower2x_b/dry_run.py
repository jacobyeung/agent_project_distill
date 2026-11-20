"""Run one real capture per admitted arm through the CPU stub after recipe verification."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LOW=Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres')

def main():
    spec=importlib.util.spec_from_file_location('worker',ROOT/'2.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    source=ROOT/'1.json';cfg=json.loads(source.read_text())
    pay=ROOT.parent/'work/payload'
    cfg.update(x8=[str(pay/'tree')],xc=os.environ.get('K3_SERVED_ROOT','/scratch/jjyeung/devs1_frames'),xl=str(LOW))
    if cfg['xk'][0]:cfg['x8'].append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
    for pin in cfg['x9']:pin[0]=str(pay/pin[0].split('/p/',1)[1])
    selection=json.loads((LOW.parent/'SELECTION.json').read_text())
    for row in cfg['x3']:
        v=row['x3'].split('/')[-1]
        for arm in row['x4']:
            if arm is None:continue
            for j,(index,low) in enumerate(zip(arm['x0'],arm['x5'])):
                if low:arm['x3'][j]=str(Path(v)/(v+'_frames')/'lowres_wide'/selection[v]['names'][str(index)])
    result=worker.run(cfg,stub=True,only=1)
    assert result['complete'],dict(error=result['error'],ran=result['ran'])
    recipe=json.loads((LOW/'out/RECIPE_K3.json').read_text())
    records={(r['video'],r['index']):r for r in recipe['records']}
    checked=[]
    for original in cfg['x3']:
        row=copy.deepcopy(original)
        v=row['x3'].split('/')[-1];a=row['x4'][0]
        for j,index in enumerate(a['x0']):
            rec=records[v,index]
            a['x1'][j]=rec['source_sha256']
            a['x3'][j]=str(Path(v)/(v+'_frames')/'lowres_wide'/selection[v]['names'][str(index)])
            a['x5'][j]=True
            a['x6'][j]=rec['decoded_raw_sha256']
        frames,hashes,elapsed=worker.images(cfg,row,0)
        assert hashes==[records[v,i]['decoded_raw_sha256'] for i in a['x0']]
        if recipe['pixel_exact']==320:
            assert hashes==original['x4'][0]['x6']
        checked.append(dict(video=v,anchors=len(hashes),matches_recipe=True,
                            matches_served=hashes==original['x4'][0]['x6'],seconds=elapsed))
    with (ROOT/'DECODE_K3b.json').open('x') as f:
        json.dump(dict(anchors=sum(r['anchors'] for r in checked),records=checked),f,indent=2)
    raw=worker.write(ROOT/'DRY.json',result)
    worker.write(ROOT/'DRY.1.json',dict(schema=2,token=cfg['x0'],input_sha256=worker.digest(source),
        sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),complete=True,stub=True,job='0'))
    print(json.dumps(dict(passed=True,frames=[len(a['ids']) for a in result['rows'][0]['arms'] if a['status']=='ok'])))

if __name__=='__main__':main()
