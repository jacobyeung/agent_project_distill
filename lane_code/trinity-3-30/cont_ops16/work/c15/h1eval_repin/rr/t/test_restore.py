"""Reviewer test: run new stage_restore.stage metadata checks on CPU in a copy."""
import copy, hashlib, json, shutil, sys, tempfile
from pathlib import Path
R=Path('/scratch/jjyeung/orch_n30/review_h1eval/work'); sys.path.insert(0,str(R/'new/b'))
from parity_kit import stage_restore as SR
from parity_kit.common import META, PREP, REQUEST
H=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/in/h1_1_run_inputs')
E544=json.loads(Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin/out/export_544.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
H1=dict(config=H/'node_local/config.json',receipt=H/'node_local/prepared/s1_receipt.json',data_receipt=H/'inputs/data_receipt.json')
D0=dict(config=META/PREP/'config.json',receipt=META/PREP/'prepared/s1_receipt.json',data_receipt=META/'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json')
def pins_for(files, artifact_raw, member='m100', step=100):
    cfg=json.loads(Path(files['config']).read_text()); data=json.loads(Path(files['data_receipt']).read_text())
    src=dict(config=data['config']['path'],receipt=cfg['preparation']['path'],data_receipt='/x/data_receipt.json')
    prep={k:dict(path='p0/'+k+'.json',source_path=src[k],sha256=sha(Path(v).read_bytes()),bytes=Path(v).stat().st_size) for k,v in files.items()}
    return dict(schema='h1-export-pins-v1',member_directory=member,lineage='SFT',step=step,
                artifact=dict(sha256=sha(artifact_raw),bytes=len(artifact_raw)),heads=dict(sha256='0'*64,bytes=1),
                full_weights=dict(sha256='0'*64,bytes=1),preparation=prep)
def run(name, files, artifact, pins_mut=None, file_mut=None, expect=None):
    tmp=Path(tempfile.mkdtemp(dir=R/'t')); d=tmp/'d'; heads=tmp/'heads'; heads.mkdir()
    raw=json.dumps(artifact).encode(); (heads/'artifact.json').write_bytes(raw)
    pins=pins_for(files, raw)
    if pins_mut: pins_mut(pins)
    for k,v in files.items():
        p=d/('p0/'+k+'.json'); p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(v,p)
    if file_mut: file_mut(d)
    try:
        SR.stage(tmp/'src',heads,META,tmp/'out',request=REQUEST,export_pins=pins,data_root=d,
                 model_manifest_tar=tmp/'nonexistent.tar',base_assets=tmp)
        msg='NO ERROR'
    except Exception as e: msg=f'{type(e).__name__}: {e}'
    ok = expect in msg
    print(('PASS' if ok else 'FAIL'), name, '->', msg[:150]); return ok
good=dict(config_sha256='26a60a5cf1c0d403050b0026bedd3e4ab8b08891fff992cc7ccab8931b92f2ef',base_identity='c202236235762e1c871ad0ccb60c8ee5ba337b9a',frame_layout='duplicate',geometry_online=False)
A='nonexistent.tar'  # reaching original_assets == all metadata checks passed
res=[]
res.append(run('H1-1 real prep + matching artifact passes metadata',H1,good,expect=A))
res.append(run('H1-1 prep + 544-config artifact refuses',H1,{**good,'config_sha256':'84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb'},expect='export architecture or identity differs'))
res.append(run('D0 prep + H1-1 artifact refuses',D0,good,expect='export architecture or identity differs'))
res.append(run('D0 prep + 544 artifact passes metadata',D0,{**good,'config_sha256':'84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb'},expect=A))
res.append(run('base identity differs',H1,{**good,'base_identity':'x'},expect='identity differs'))
res.append(run('frame layout differs',H1,{**good,'frame_layout':'concat'},expect='identity differs'))
res.append(run('geometry_online true',H1,{**good,'geometry_online':True},expect='identity differs'))
def m(k,f):
    def g(p): f(p['preparation'][k])
    return g
res.append(run('wrong config sha pin',H1,good,m('config',lambda x:x.update(sha256='1'*64)),expect='sha256 mismatch'))
res.append(run('wrong receipt bytes pin',H1,good,m('receipt',lambda x:x.update(bytes=x['bytes']+1)),expect='Preparation size differs'))
res.append(run('wrong data_receipt sha pin',H1,good,m('data_receipt',lambda x:x.update(sha256='1'*64)),expect='sha256 mismatch'))
res.append(run('receipt source_path differs from cfg.preparation',H1,good,m('receipt',lambda x:x.update(source_path='/y')),expect='Preparation receipt pin differs'))
res.append(run('config source_path differs from data.config',H1,good,m('config',lambda x:x.update(source_path='/y')),expect='data receipt binding differs'))
res.append(run('artifact pin sha wrong',H1,good,lambda p:p['artifact'].update(sha256='1'*64),expect='sha256 mismatch'))
def swap(d):  # H1-1 pins, but receipt file replaced by D0 receipt
    shutil.copyfile(D0['receipt'], d/'p0/receipt.json')
res.append(run('receipt file swapped to D0',H1,good,file_mut=swap,expect='sha256 mismatch'))
def tamper(d):
    p=d/'p0/data_receipt.json'; v=json.loads(p.read_text()); v['rehearsal']=True; p.write_text(json.dumps(v))
res.append(run('data receipt tampered',H1,good,file_mut=tamper,expect='sha256 mismatch'))
print('ALL PASS' if all(res) else 'SOME FAIL', sum(res), '/', len(res))
