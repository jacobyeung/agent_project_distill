"""Synthetic step-200/400 packages and complete-return comparison coverage."""
import copy
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
from build_h_base import make_batch, added, jd
from build_support import write_tar, read_tar
from build_remainder_h import build
from return_tools_h import package_info, binding_for, canonical, read, require
from score_h_merge import score
import hashlib

HERE=Path(__file__).resolve().parent
ROOT=Path(tempfile.mkdtemp(prefix='steps-',dir=str(HERE/'validation')))
previous=read(HERE/'TEST_RESULTS.json');evidence=Path(previous['evidence'])
full=HERE/'in/H544/package';info=package_info(full)
with tarfile.open(str(full/'a/f/0.tgz')) as t:original={m.name:t.extractfile(m).read() for m in t.getmembers()}
rem_spec=read(evidence/'SCORE_SPEC.json')['remainder']
with tarfile.open(rem_spec['archive']) as t:remainder={m.name:t.extractfile(m).read() for m in t.getmembers()}
sha=lambda b:hashlib.sha256(b).hexdigest()

def publish(d,files,p,complete):
    d.mkdir();archive=d/'0.tgz'
    with tarfile.open(str(archive),'w:gz') as t:
        for n,b in sorted(files.items()):t.addfile(added(n,b)[0],io.BytesIO(b))
    pi=package_info(p);token=pi['token']+'000003e7'
    ex=dict(job='999',token=token,plan_sha256=pi['plan'],synthetic=False,complete=complete,status='COMPLETE' if complete else 'FAILED',archive_complete=True,conflicting_terminal_markers=False,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive.read_bytes()))
    (d/'EXIT.json').write_bytes(jd(ex))
    receipt=dict(token=token,job='999',plan_sha256=pi['plan'],returned=True,channels={'pool':dict(verified=True,files={n:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for n,p in [('EXIT.json',d/'EXIT.json'),('result.tar.gz',archive)]})})
    (d/'RETURN_RECEIPT.json').write_bytes(jd(receipt))
    return dict(package=str(p),archive=str(archive),exit=str(d/'EXIT.json'),receipt=str(d/'RETURN_RECEIPT.json'))

checks=[]
for step in (200,400):
    b=binding_for(step);p=ROOT/('parent%d'%step);p.mkdir();pf=dict(info['payload']);plan=copy.deepcopy(info['plan_value'])
    plan['token']='d'+os.urandom(6).hex();plan['export_binding']={k:b[k] for k in plan['export_binding']};pf['9.json']=jd(plan)
    names=['0.json','CONFIG.json','0.tgz','BATCH.sh','3.py','PACKAGE.json','INPUTS.example.json','SUBMIT.cmd','a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json']
    nf={n:(full/n).read_bytes() for n in names};nf['0.tgz']=write_tar([added(n,pf[n]) for n in sorted(pf)])
    pub=read(full/'0.json');pub.update(token=plan['token'],payload_bytes=len(nf['0.tgz']),payload_sha256=sha(nf['0.tgz']),plan_sha256=canonical(plan));nf['0.json']=nf['CONFIG.json']=jd(pub)
    nf['BATCH.sh']=make_batch(nf['BATCH.sh'],info['token'],plan['token'],(full/'0.json').read_bytes(),nf['0.json'],nf['a/6.py'],nf['a/6.py'])
    pin=json.loads(nf['a/export.json'])
    pin.update({k:b[k] for k in ('run','step','object','lineage','member_directory','config_sha256','archive_sha256','archive_bytes')})
    for k,h in b['preparation_sha256'].items():pin['preparation'][k]['sha256']=h
    nf['a/export.json']=jd(pin);inputs=json.loads(nf['a/1.json']);inputs['export_pin'].update(bytes=len(nf['a/export.json']),sha256=sha(nf['a/export.json']));nf['a/1.json']=jd(inputs)
    pk=json.loads(nf['PACKAGE.json']);pk['token']=plan['token'];pk['files']={n:sha(nf[n]) for n in pk['files']};nf['PACKAGE.json']=jd(pk)
    for n,raw in nf.items():target=p/n;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
    pi=package_info(p);files=dict(original)
    files['metadata/INPUTS.json']=nf['a/1.json'];files['metadata/EXPORT_PIN.json']=nf['a/export.json']
    for n in ('metadata/IDENTITY.json','metadata/reads/0/metadata/READ_IDENTITY.json','metadata/reads/0/metadata/IDENTITY.json'):
        v=json.loads(files[n]);v.update(plan=pi['plan'],inputs=canonical({k:v for k,v in inputs.items() if k!='resume'}));files[n]=jd(v)
    files['metadata/RETURN_ID.json']=jd(dict(token=pi['token']+'000003e7',job='999'))
    for n in list(files):
        if n.endswith('/environment.json'):
            v=json.loads(files[n]);v['binding']['step']=step;files[n]=jd(v)
    partial=publish(ROOT/('partial%d'%step),files,p,False)
    os.environ['KROOT']=str(ROOT/'packages')
    r=build(p,partial['archive'],partial['exit'],partial['receipt'],ROOT/('build%d'%step))
    assert r['export_binding']==plan['export_binding'] and r['serving_pins']==info['serving_pins'];checks.append('step_%d_build'%step)
    # Complete the full return for --other without changing frozen membership.
    files['SUMMARY.json']=jd(dict(expected=900,completed=900,complete=True))
    for t in (1,2):
        prefix='metadata/reads/0/metadata/journals/%d/0/'%t
        files[prefix+'items.jsonl']=files.get(prefix+'items.jsonl',b'')+remainder[prefix+'items.jsonl']
        env=json.loads(original['metadata/reads/0/metadata/journals/1/0/environment.json']);env['binding']['step']=step
        env['binding']['ids']=[i['id'] for i in info['manifest']['items'] if i['question_type']==['camera_displacement','camera_rotation','camera_movement_direction'][t]]
        files[prefix+'environment.json']=jd(env)
    complete=publish(ROOT/('complete%d'%step),files,p,True)
    (ROOT/('OTHER%d.json'%step)).write_bytes(jd(complete))
    result=score(read(evidence/'SCORE_SPEC.json'),ROOT/('score%d'%step),complete)
    assert sum(v['answer']['n'] for v in result['current_minus_other'].values())==900
    checks.append('step_%d_complete_comparison'%step)
    (ROOT/('SCORES%d.json'%step)).write_bytes(jd(result))
report=dict(passed=True,synthetic=True,checks=checks,evidence=str(ROOT),real_step200_or_400_tested=False)
(HERE/'STEP_TEST_RESULTS.json').write_bytes(jd(report));print(json.dumps(report))
