"""CPU allocation rehearsal with real journals and reviewed-reader stand-ins."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import uuid

import pytest
from orchard_h10.common import ORDER, canonical, opaque, submit_argv, template, write
from orchard_h10.runner import commands, run, summarize

K=Path(__file__).resolve().parents[1]
T=K/'tmp/b8/readk_tmpl/launcher'
B=Path('/scratch/jjyeung/orch_n30/b04_e2ehook')


@pytest.fixture(scope='module')
def rehearsal():
    # Deliberately outside pytest's basetemp and /dev/shm, like a retained production run.
    root=K/'tmp/b8/rehearsal'/('a'+uuid.uuid4().hex[:12]);root.mkdir(parents=True)
    raw=json.loads((K/'items/devs1_routed.json').read_text())
    # Keep ten records per type so each type has both shards and a measured projection.
    selected=sorted([x for t in ORDER for x in [r for r in raw['items'] if r['question_type']==t][:10]],key=lambda r:r['id'])
    from h1eval.items import manifest
    value=manifest('devs1_routed',selected,K/'items/devs1_routed.json')
    write(root/'items.json',value)
    export=root/'e';export.mkdir();write(export/'RESTORE.json',{'step':544})
    write(root/'binding.json',dict(root=str(root),name='manifest.json',sha256='tiny'))
    write(root/'config.json',{})
    settings=dict(export_dir=str(export),artifact_manifest=str(root/'binding.json'),tree=str(K/'tree'),
        config=str(root/'config.json'),frames_root=str(root/'f'),sam3={'tiny':True},selector_head=str(root/'s'))
    write(root/'settings.json',settings)
    cfg=dict(package=str(K),output=str(root/'r'),python=sys.executable,items=str(root/'items.json'),
        export=str(export),binding=str(root/'binding.json'),settings=str(root/'settings.json'),device='cpu',
        plan_sha256=canonical(value),stop_margin=1,return_margin=.1)
    # commands points to the packaged b04 root in production. The tiny worker runs the
    # read-only b04 installation without copying its source tree.
    def launch(argv,**kw):
        argv=list(argv);i=argv.index('--reader-root');argv[i+1]=str(B)
        kw['env']['CUDA_VISIBLE_DEVICES']=''
        return subprocess.Popen([sys.executable,'-B',str(K/'tests/build8_worker.py'),*argv],**kw)
    result=run(cfg,['','cpu1'],time.time()+300,launcher=launch)
    return root,cfg,result,launch


def test_slurm_opacity_and_budget():
    from orchard_h10.build import batch
    token='ab12cd34ef56a'
    argv=submit_argv(token,4,'01:15:00')
    assert '--job-name=a15_cot_ap'+token in argv and '--export=NONE' in argv
    opaque(argv+['/tmp','/dev/null','A_N=4','A_T=4500','/project/community/jjyeung/'+token])
    text=batch(b'contents exempt',token)
    opaque(text.split("<<'A'")[0].splitlines())
    for bad in ('--comment=SpLiT','--chdir=/tmp/QWEN','H10_SETTINGS=x','/logs/faithful','--job-name=a15_cot_ap_head'):
        with pytest.raises(ValueError):opaque([bad])
    with pytest.raises(ValueError):submit_argv(token,4,'02:00:00')
    with pytest.raises(ValueError):submit_argv('ab12_cd34ef56',4,'01:15:00')


def test_order_shards_modes_and_text(rehearsal):
    root,cfg,result,_=rehearsal
    assert result['complete'] and result['completed']==result['expected']==110
    events=[json.loads(s) for s in (root/'r/STEPS.jsonl').read_text().splitlines()]
    assert [r['type'] for r in events if r['event']=='start']==[t for t in ORDER for _ in range(2)]
    for i,t in enumerate(ORDER):
        group=events[4*i:4*i+4]
        assert [r['event'] for r in group]==['start','start','exit','exit']
        assert {r['shard'] for r in group}=={'0/2','1/2'}
    seen=set()
    for p in (root/'r/metadata/journals').glob('*/*/items.jsonl'):
        rows=[json.loads(line) for line in p.read_text().splitlines()]
        for r in rows:
            key=(r['id'],r['arm'],r['mode']);assert key not in seen;seen.add(key)
            assert r['arm']=='own' and r['output']['text']=='</think><answer>1.00 meters</answer>'
    assert len(seen)==110
    assert list((root/'r/metadata/journals').glob('*/*/projection.json'))
    assert json.loads((root/'r/metadata/projection.json').read_text())['sample_reads']==110


def test_resume_preserves_completed_records(rehearsal):
    root,cfg,result,launch=rehearsal
    before={str(p):p.read_bytes() for p in (root/'r/metadata/journals').glob('*/*/items.jsonl')}
    resumed=run(cfg,['','cpu1'],time.time()+300,launcher=launch)
    assert resumed['complete']
    assert before=={str(p):p.read_bytes() for p in map(Path,before)}
    changed=dict(cfg,plan_sha256='0'*64)
    with pytest.raises(ValueError,match='same plan'):run(changed,['','cpu1'],time.time()+300,launcher=launch)


def test_guard_admits_no_new_process(rehearsal):
    root,cfg,_,_=rehearsal
    cfg=dict(cfg,output=str(root/'guard'))
    def forbidden(*args,**kwargs):raise AssertionError('Guard launched a process')
    result=run(cfg,['','cpu1'],time.time(),launcher=forbidden)
    assert result['stopped'] and result['completed']==0


def test_deadline_resume_and_return_layout(rehearsal,monkeypatch):
    root,cfg,_,launch=rehearsal
    cfg=dict(cfg,output=str(root/'partial'),stop_margin=8,return_margin=1)
    monkeypatch.setenv('B8_DELAY','.4')
    partial=run(cfg,['','cpu1'],time.time()+16,launcher=launch)
    assert partial['stopped'] and 0<partial['completed']<partial['expected']
    monkeypatch.delenv('B8_DELAY')
    S,J,R,I,A=template(T)
    # Exercise the unchanged archive builder and pool return; no network channel.
    pool=root/'pool';token='abcdef0123456';(pool/token).mkdir(parents=True)
    monkeypatch.setattr(R,'pool_operation',lambda action,pool,token,local=None,timeout=60:I.operate(action,pool,token,local))
    def offline(*a,**kw):raise RuntimeError('CPU rehearsal has no network')
    monkeypatch.setattr(R,'upload',offline)
    returned=R.publish(Path(cfg['output']),pool,token,cfg['plan_sha256'],0,synthetic=True)
    assert returned['returned'] and not returned['complete']
    archive=pool/token/'result.tar.gz'
    with tarfile.open(archive) as tar:
        names=tar.getnames()
        assert 'metadata/projection.json' in names and 'SUMMARY.json' in names
        assert any(n.endswith('/items.jsonl') for n in names)
        assert not any(n.startswith('cache/') for n in names)
        assert all(t.isfile() for t in tar)
    from orchard_h10.job import restore_resume
    dest=root/'resumed'
    restore_resume(dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size),dest,cfg,S)
    assert not (dest/'metadata/STOP').exists()
    cfg=dict(cfg,output=str(dest))
    resumed=run(cfg,['','cpu1'],time.time()+300,launcher=launch)
    assert resumed['complete'] and resumed['completed']==110
    write(root/'REHEARSAL.json',dict(root=str(root),complete=True,partial_records=partial['completed'],
        final_records=resumed['completed'],return_files=names,synthetic=True))


def test_missing_production_inputs_refuse():
    from orchard_h10.job import check_inputs
    with pytest.raises(ValueError,match='Unresolved'):check_inputs({'schema':1,'archives':[]},{})


def test_inflight_deadline_leaves_no_partial_record(rehearsal,monkeypatch):
    root,cfg,_,launch=rehearsal
    cfg=dict(cfg,output=str(root/'inflight'))
    monkeypatch.setenv('B8_DELAY','20')
    argv=commands(cfg,ORDER[0],0,['','cpu1'],time.time()+6,time.time()+8)
    from orchard_h10.runner import environment
    with (root/'inflight.log').open('wb') as log:
        process=launch(argv,env=environment(cfg,'',0),cwd=K,stdout=log,stderr=subprocess.STDOUT)
        assert process.wait()==75
    from h1eval.h10.launch import read_records
    assert read_records(root/'inflight/metadata/journals/0/0/items.jsonl')==[]


def test_package_pins_and_embedded_bootstrap():
    import base64
    import re
    from orchard_h10.common import sha
    package=K/'orchard_h10/package';cfg=json.loads((package/'CONFIG.json').read_text())
    assert sha(package/'0.tgz')==cfg['payload_sha256']
    with tarfile.open(package/'0.tgz') as tar:
        observed={e.name:dict(bytes=e.size,sha256=hashlib.sha256(tar.extractfile(e).read()).hexdigest()) for e in tar}
    assert observed==cfg['payload_pins']
    assert 'b/e2e_reader/parity.py' in observed and 'b/heads/selector/selector_head.py' in observed
    assert 'b/parity_kit/stage_restore.py' in observed and 'items/devs1_routed.json' in observed
    assert not any(n.endswith(('.pt','.safetensors','.png')) for n in observed)
    assert all(sha(T/n)==h for n,h in cfg['template_pins'].items())
    for n in ('runner','job','common','prepare','operator'):
        path='orchard_h10/'+n+'.py'
        assert observed[path]['sha256']==sha(K/path)
    text=(package/'BATCH.sh').read_text()
    raw=base64.b64decode(re.search(r"b=base64.b64decode\('([^']+)'",text)[1])
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        assert json.load(tar.extractfile('0.json'))==cfg
        assert tar.extractfile('p/orchard_h10/job.py').read()==(K/'orchard_h10/job.py').read_bytes()
    assert len(text)<3*1024**2


def test_resume_rejects_changed_input_archives(tmp_path,monkeypatch):
    import orchard_h10.runner as runner
    monkeypatch.setattr(runner,'summarize',lambda *a:dict(complete=False,completed=0,expected=1))
    cfg=dict(output=str(tmp_path),plan_sha256='0'*64,inputs_sha256='a'*64)
    runner.run(cfg,['0'],time.time())
    with pytest.raises(ValueError,match='same plan'):
        runner.run(dict(cfg,inputs_sha256='b'*64),['0'],time.time())


def test_worker_failure_does_not_launch_next_type(tmp_path,monkeypatch):
    import orchard_h10.runner as runner
    monkeypatch.setattr(runner,'summarize',lambda *a:dict(complete=False,completed=0,expected=1))
    cfg=dict(output=str(tmp_path),package=str(K),python=sys.executable,export='x',binding='x',settings='x',plan_sha256='0'*64)
    seen=[]
    class Failed:
        def wait(self):return 9
    def launch(argv,**kw):seen.append(argv);return Failed()
    value=runner.run(cfg,['0','1'],time.time()+3600,launcher=launch)
    assert value['failure'] and len(seen)==2
    assert all(argv[argv.index('--types')+1]==ORDER[0] for argv in seen)


def test_deadline_crosses_reader_exception_handlers(monkeypatch):
    import h1eval.h10.launch as launch
    def slow(args):
        try:time.sleep(.1)
        except Exception:raise AssertionError('Reader swallowed allocation stop')
        raise AssertionError('Deadline did not fire')
    monkeypatch.setattr(launch,'run',slow)
    argv=[v for key in ('items','export','artifact-manifest','reader-root','out') for v in ('--'+key,'unused')]
    assert launch.main(argv+['--finish-by',str(time.time()+.02)])==75
