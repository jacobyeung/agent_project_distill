"""Exercise the actual byte stream, packaged PNGs, worker and scoring schema locally."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
LOW=Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres')

def main():
    started=time.monotonic()
    build=json.loads((ROOT/'BUILD.json').read_text())
    header=(ROOT/'o_place_head.sh').read_bytes();archive=(ROOT/'place.tar').read_bytes()
    assert len(header)+len(archive)==build['stream_bytes']
    work=Path(tempfile.mkdtemp(prefix='stream_',dir=ROOT));dest=work/'p'
    local_header=header.replace(build['path'].encode(),str(dest).encode())
    done=subprocess.run(['bash','-s'],input=local_header+archive,capture_output=True,check=True)
    assert int(done.stdout)==build['placement_bytes']
    for name in build['bound_files']:assert (dest/name).read_bytes()==(ROOT/name).read_bytes()
    rejected=[]
    for name,blob in [('short',archive[:-1]),('corrupt',bytes([archive[0]^1])+archive[1:]),('extra',archive+b'x')]:
        bad=work/name
        p=subprocess.run(['bash','-s'],input=header.replace(build['path'].encode(),str(bad).encode())+blob,capture_output=True)
        assert p.returncode and not bad.exists()
        rejected.append(name)
    spec=importlib.util.spec_from_file_location('worker',dest/'2.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    entry_spec=importlib.util.spec_from_file_location('entry',dest/'0.py')
    entry=importlib.util.module_from_spec(entry_spec);entry_spec.loader.exec_module(entry)
    cfg,verified_worker=entry.verify(dest)
    assert len(verified_worker.tasks(cfg))==20 and cfg['xr']==[0,1]
    source=dest/'1.json'
    pins=json.loads((dest/'3.json').read_text())
    assert all(worker.digest(dest/n)==h for n,h in pins.items())
    assert abs(worker.forecast(cfg)-json.loads((ROOT/'FORECAST.json').read_text())['estimate_seconds'])<1e-9
    frames=work/'8';frames.mkdir()
    with tarfile.open(dest/'8.tgz') as t:
        members=t.getmembers();assert len(members)==630
        for member in members:
            assert member.isfile() and '/' not in member.name
            (frames/member.name).write_bytes(t.extractfile(member).read())
    pay=ROOT.parent/'work/payload'
    cfg.update(x8=[str(pay/'tree')],xl=str(frames))
    if cfg['xk'][0]:cfg['x8'].append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
    for pin in cfg['x9']:pin[0]=str(pay/pin[0].split('/p/',1)[1])
    result=worker.run(cfg,stub=True,only=1)
    if not result['complete']:raise AssertionError(result)
    assert result['ran']==[[0,0],[0,1]]
    assert [len(a['c2w']) for a in result['rows'][0]['arms']]==[32,63]
    recipe=json.loads((LOW/'out/RECIPE_K3c.json').read_text())
    records={(r['video'],r['index']):r for r in recipe['records']}
    selection=json.loads((LOW.parent/'SELECTION.json').read_text())
    checked=[]
    # Decode all 320 packaged anchors; run real preprocessing/inference stubs for capture zero.
    for row in cfg['x3']:
        v=row['x3'].split('/')[-1];ids=row['x4'][0]['x0']
        ims,hashes,_=worker.images(cfg,row,0)
        assert hashes==[records[v,i]['decoded_raw_sha256'] for i in ids]
        if row is cfg['x3'][0]:
            errors=[]
            for i,im in zip(ids,ims):
                rec=records[v,i];h=rec['served_sha256']
                p=Path(recipe['served_root'])/h[:2]/(h+'.png');assert worker.digest(p)==h
                with Image.open(p) as target:d=np.abs(np.asarray(im).astype(np.int16)-np.asarray(target.convert('RGB')).astype(np.int16))
                assert float(d.mean())==rec['mae'] and int(d.max())==rec['max_abs']
                errors.append((float(d.mean()),int(d.max())))
            measured=dict(mean_absolute_error=float(np.mean([x[0] for x in errors])),max_abs=max(x[1] for x in errors))
            assert measured==recipe['per_capture'][v]
        expected=sorted(ids+[round(a+3*(b-a)/6) for a,b in zip(ids,ids[1:])])
        assert row['x4'][1]['x0']==expected and len(expected)==63
        assert all(row['x4'][1]['x6'][s]==h for s,h in zip(row['x4'][1]['x2'],hashes))
        checked.append(dict(video=v,anchors=len(hashes),matches_recipe=True,b_indices=expected))
    required={'status','ids','sha256','raw_sha256','slots','c2w','scale','gravity','seconds','decode_seconds','inference_seconds','shape','peak_bytes','reserved_bytes','rss_kib'}
    for a in result['rows'][0]['arms']:
        assert set(a)==required
        assert [a['raw_sha256'][s] for s in a['slots']]==result['rows'][0]['arms'][0]['raw_sha256']
    raw=worker.write(ROOT/'DRY_K3c.json',result)
    worker.write(ROOT/'DRY_K3c.1.json',dict(schema=2,token=cfg['x0'],input_sha256=worker.digest(source),
        sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),complete=True,stub=True,job='0'))
    sys.path.insert(0,str(ROOT.parent.parent/'cap/score_tower2x_b'))
    import score
    scored=score.score(result,json.loads((ROOT.parent.parent/'cap/score_tower2x_b/REFERENCE.json').read_text()))
    assert scored['verdict']=='synthetic'
    report=dict(passed=True,real_capture=cfg['x3'][0]['x3'],frames=[32,63],error=measured,
        stream_bytes=len(header)+len(archive),installed_files_equal=True,rejected_streams=rejected,
        checked=checked,return_schema=True,score_verdict=scored['verdict'],seconds=time.monotonic()-started,
        rss_kib=max(a['rss_kib'] for a in result['rows'][0]['arms']),
        scope='Real packaged rasters, actual 1024/518 preprocessing and pose conversion; stub backbone/heads; no GPU evidence.')
    (ROOT/'CPU_K3c.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checked'}))

if __name__=='__main__':main()
