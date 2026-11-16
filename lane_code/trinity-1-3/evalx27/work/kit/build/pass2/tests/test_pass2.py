import base64
from collections import Counter
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS
import pytest
from conftest import ROOT
from test_kit import fresh,spec,cohort
import orchard_launcher as L
import orchard_job as J
import orchard_stage as S
import chain_save
import fixtures as F


def embedded(destination):
    from run import unpack
    script=(destination/'BATCH.sh').read_text()
    boot=unpack(base64.b64decode(re.search(r"^raw=base64.b64decode\('([^']+)'",script,re.M)[1]))
    return boot,unpack(boot['bootstrap/payload.tar.gz'])


def test_modes_ship_identical_code_and_cpu_argv():
    p=fresh('modes');p.mkdir()
    configs={m:L.prepare('p0123456789',p/m,mode=m) for m in ('proof','production')}
    a,b=configs.values();assert {k for k in a if a[k]!=b[k]}=={'mode'}
    boot_a,pay_a=embedded(p/'proof');boot_b,pay_b=embedded(p/'production')
    assert pay_a==pay_b
    assert {k for k in boot_a if boot_a[k]!=boot_b[k]}=={'bootstrap/CONFIG.json'}
    for mode,cfg in configs.items():L.validate_batch((p/mode/'BATCH.sh').read_text(),cfg)
    cpu=L.submit_argv(None,a['token'],proof=True);gpu=L.submit_argv(None,a['token'])
    assert '--gres=gpu:1' in gpu and not any(x.startswith('--gres') for x in cpu)
    assert {'--partition=general','--cpus-per-task=16','--mem=128G','--time=02:00:00'}<=set(cpu)
    assert {'--mem=200G','--time=06:00:00'}<=set(gpu)
    assert '--job-name=a15_cot_app0123456789' in cpu
    assert '--mem=128G' in L.submit_command(a['token'],proof=True)[-1]
    assert all('/proof/fakes.py' not in x for x in cpu)
    with pytest.raises(ValueError):L.prepare('p0123456789',p/'bad',mode='wrong')


def test_subset_is_shared_by_all_callers():
    from selection import select
    from data import tasks_for
    import worker,frame_stage,merge,budget_merge
    rows=select(cohort());ids=sorted(str(r['id']) for r in rows)
    assert len(rows)==16 and set(Counter(r['question_type'] for r in rows).values())=={2}
    assert rows==select(list(reversed(cohort())))
    s=dict(spec(),example_ids=ids)
    for module in (worker,frame_stage,merge,budget_merge):
        assert [t['example_id'] for t in sorted(module.tasks_for(s,dict(video_root='/tmp/v')),key=lambda t:t['example_id'])]==ids
    for bad in ([],['bad'],list(reversed(ids)),ids+[ids[0]],[1]):
        with pytest.raises(ValueError):tasks_for(dict(s,example_ids=bad),dict(video_root='/tmp/v'))


def test_proof_card_records_real_error_surface(monkeypatch):
    import proof_card
    monkeypatch.setattr(proof_card.subprocess,'run',lambda argv,**kw:subprocess.CompletedProcess(argv,9,'','driver unavailable\n'))
    r=proof_card.card(True);assert len(r['observations'])==2 and 'driver unavailable' in r['nvidia_smi']
    def missing(*a,**kw):raise FileNotFoundError('nvidia-smi missing')
    monkeypatch.setattr(proof_card.subprocess,'run',missing)
    assert proof_card.card()['observations'][0]['error']=='nvidia-smi missing'


@pytest.mark.parametrize('failure',['storage','stage','output_mount','chain_exit','no_complete','conflict','publish'])
def test_job_failure_is_published(monkeypatch,failure):
    p=fresh('joberror');p.mkdir()
    token='p0123456789';logical=J.SJ/('a'+token)
    cfg=dict(token=token,plan_sha256='0'*64,output=str(logical/'o'),
        spec=dict(run=str(logical/'r'),package=str(logical/'p'),artifact=dict(path=str(logical/'artifact.json')),interpreters=dict(vllm='python')))
    source=J.physical(p,cfg['spec']['run'])
    monkeypatch.setenv('SLURM_JOB_ID','900000');monkeypatch.setenv('USER','fixture')
    for key in ('HOME','TMPDIR','XDG_CACHE_HOME'):monkeypatch.setenv(key,str(p))
    monkeypatch.setattr(J.signal,'signal',lambda *a:None)
    def storage(path,**kw):
        if failure=='storage':raise J.StorageRefusal('not local',dict(filesystem='nfs'))
        return dict(source='/dev/other' if failure=='output_mount' and Path(path)!=p else '/dev/local')
    monkeypatch.setattr(J,'storage_proof',storage)
    monkeypatch.setattr(J,'card',lambda **kw:dict(nvidia_smi='fixture'))
    def stage(*args):
        if failure=='stage':raise ValueError('Staging checksum differs')
        return {}
    monkeypatch.setattr(S,'stage',stage);monkeypatch.setattr(J,'namespace',lambda *a:[])
    class Child:
        pid=42
        def __init__(self,*args,**kw):
            if failure in ('conflict','publish'):
                source.mkdir(parents=True,exist_ok=True)
                F.js(source/'COMPLETE.json',dict(plan_sha256='0'*64,synthetic=False))
            if failure=='conflict':F.js(source/'FAILED.json',dict(error='conflict'))
        def wait(self,**kw):return 7 if failure=='chain_exit' else 0
        def poll(self):return 0
    monkeypatch.setattr(J.subprocess,'Popen',Child)
    seen=[]
    def publish(source,*args):
        seen.append(source)
        if failure=='publish':raise OSError('pool full')
        return dict(status='FAILED')
    monkeypatch.setattr(J.R,'publish',publish)
    assert J.run(p,cfg)!=0 and seen==[source]
    if failure=='publish':assert (p/'RETURN_INCOMPLETE.json').exists()
    else:assert (source/'FAILED.json').exists()
    evidence=json.loads((source/'metadata/ORCHARD_LAUNCHER.json').read_text())
    if failure=='storage':assert evidence['storage_refusal']['filesystem']=='nfs'


def test_chain_failure_receipt(monkeypatch):
    import chain
    p=fresh('chainerror');p.mkdir();package=p/'p';(package/'cohort').mkdir(parents=True)
    F.js(package/'cohort/MEDIA_MANIFEST.json',[]);F.js(package/'TRANSPORT.json',{})
    cfg=dict(spec=dict(run=str(p/'r'),package=str(package),inputs=dict(video_root='/tmp/v')),release={},plan_sha256='0'*64)
    def fail(*a,**kw):raise ValueError('decoder refused video')
    monkeypatch.setattr(chain,'utility',fail)
    with pytest.raises(ValueError,match='decoder refused'):chain.run(cfg)
    steps=[json.loads(l) for l in (p/'r/STEPS.jsonl').read_text().splitlines()]
    assert [v['event'] for v in steps]==['start','failed']
    assert json.loads((p/'r/FAILED.json').read_text())['error']=='decoder refused video'
    assert not (p/'r/COMPLETE.json').exists()


@pytest.mark.parametrize('kind',['duplicate','foreign','oversize','strip','symlink','special','escape'])
def test_archive_defensive_branches(kind):
    p=fresh('archiveerror');p.mkdir();raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w') as tf:
        m=tarfile.TarInfo('m544/a');m.size=1
        if kind=='symlink':m.type=tarfile.SYMTYPE;m.linkname='/outside'
        if kind=='special':m.type=tarfile.FIFOTYPE
        if kind=='escape':m.name='../outside'
        tf.addfile(m,io.BytesIO(b'x') if m.isfile() else None)
        if kind=='duplicate':tf.addfile(m,io.BytesIO(b'x'))
    raw.seek(0)
    with pytest.raises(ValueError):S.extract_stream(raw,p/'out',545 if kind=='foreign' else 544,
        0 if kind=='oversize' else 10240,links=kind=='symlink',strip=2 if kind=='strip' else 0)


@pytest.mark.parametrize('change',['long','md5','archive'])
def test_copy_part_defenses(change):
    p=fresh('part');p.mkdir();part=dict(bytes=2 if change=='long' else 3,sha256=hashlib.sha256(b'abc').hexdigest())
    if change=='md5':part['md5']='wrong'
    with pytest.raises(ValueError):S.copy_parts([part],p/'out',lambda _:io.BytesIO(b'abc'),check_space=False,
        expected_sha='0'*64 if change=='archive' else None)


def test_process_failure_no_retry():
    p=fresh('process');p.mkdir()
    with pytest.raises(RuntimeError,match='no automatic retry'):
        with S.process_stream([sys.executable,'-c','raise SystemExit(4)'],dict(os.environ),p/'log') as stream:stream.read(100)


def test_stdlib_trace_child_and_thread():
    p=fresh('trace');p.mkdir();package=p/'p';package.mkdir()
    script=package/'exercise.py';script.write_text('from concurrent.futures import ThreadPoolExecutor\ndef f(x):\n    return x+1\nwith ThreadPoolExecutor(max_workers=2) as e:\n    assert list(e.map(f,[1,2]))==[2,3]\n')
    cfg=dict(mode='proof',spec=dict(package=str(package),run=str(p/'r')));F.js(p/'cfg.json',cfg)
    result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'launcher/trace_runtime.py'),'--root',str(p),
        '--config',str(p/'cfg.json'),'--script',str(script)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    import trace_runtime
    report=trace_runtime.collect(p,p/'TRACE.json.gz')
    row=next(r for r in report['files'] if r['file']=='exercise.py')
    assert 3 in row['lines'] and 5 in row['lines']
    assert row['sha256']==F.sha(script)
    assert report['processes'][0]['python']==sys.executable


def test_plan_parallel_real_decode():
    import frame_plan
    p=fresh('plan');p.mkdir();v=F.video(p/'d/v.mp4')
    F.js(p/'manifest.json',[dict(relative_path='d/v.mp4',sha256=F.sha(v))])
    result=frame_plan.compute(p,p/'manifest.json',workers=16)
    assert result['videos']['d/v.mp4']['packet_equals_decode'] is True
    F.js(p/'manifest.json',[dict(relative_path='d/v.mp4',sha256='0'*64)])
    with pytest.raises(ValueError):frame_plan.compute(p,p/'manifest.json',workers=16)


def test_lines_union_requires_source_hash():
    import lines_report as lines
    path=ROOT/'launcher/orchard_job.py';h=lines.digest(path)
    wanted,_=lines.scope(path);line=min(wanted)
    local=dict(files=[dict(file='ignored',sha256=h,lines=[line])])
    remote=dict(files=[dict(file='runtime_2/alias.py',sha256=h,lines=sorted(wanted))])
    row=next(r for r in lines.report(local,remote)['modules'] if r['file']=='launcher/orchard_job.py')
    assert row['missing']==[] and row['union']==len(wanted)
    remote['files'][0]['sha256']='0'*64
    report=lines.report(local,remote)
    row=next(r for r in report['modules'] if r['file']=='launcher/orchard_job.py')
    assert row['union']==1 and report['unmatched_orchard_sources']


def test_native_fake_replaces_only_async_engine(monkeypatch):
    import types
    import fakes
    processor=object();sentinel=object();created=[]
    v=types.ModuleType('vllm');v.__version__='real-version';v.SamplingParams=sentinel
    v1=types.ModuleType('vllm.v1');eng=types.ModuleType('vllm.v1.engine');boundary=types.ModuleType('vllm.v1.engine.async_llm')
    boundary.AsyncLLM=sentinel;v.v1=v1;v1.engine=eng;eng.async_llm=boundary
    registry=types.ModuleType('vllm.multimodal');registry.MULTIMODAL_REGISTRY=sentinel
    factory=lambda *a,**k:processor
    tr=types.ModuleType('transformers');tr.AutoProcessor=NS(from_pretrained=factory)
    for name,module in [('vllm',v),('vllm.v1',v1),('vllm.v1.engine',eng),('vllm.v1.engine.async_llm',boundary),('vllm.multimodal',registry),('transformers',tr)]:
        monkeypatch.setitem(sys.modules,name,module)
    cls=fakes.install_engine(['x'])
    args=NS(model='path',create_model_config=lambda:created.append(True) or sentinel)
    actual=cls.from_engine_args(args)
    assert created==[True] and actual.model_config is sentinel and actual.selected==['x']
    assert boundary.AsyncLLM is cls and v.SamplingParams is sentinel and v.__version__=='real-version'
    assert registry.MULTIMODAL_REGISTRY is sentinel and tr.AutoProcessor.from_pretrained is factory


@pytest.mark.parametrize('fault',['payload','base_size','base_pin','base_member','export_size','artifact'])
def test_stage_rejects_untrusted_phase(monkeypatch,fault):
    p=fresh('stageguard');p.mkdir();(p/'bootstrap').mkdir();payload=p/'bootstrap/payload.tar.gz';payload.write_bytes(b'payload')
    base=p/'base.tar';base.write_bytes(b'base')
    manifest=F.js(p/'manifest.json',dict(files=[dict(path='a',bytes=1,sha256='1'*64)]))
    transport=F.js(p/'transport.json',dict(parts=[dict(name='a',generation='123')],archive_sha256='3'*64,
        archive_bytes=2 if fault=='export_size' else 1))
    artifact=p/'artifact/metadata/artifact.json';artifact.parent.mkdir(parents=True);artifact.write_bytes(b'{}')
    config=dict(payload_sha256='bad' if fault=='payload' else F.sha(payload),
        assets=dict(groups=[],camera_archive={},bwrap_pin={},base_archive=str(base),base_archive_bytes=5 if fault=='base_size' else 4,
            base_manifest=dict(path=str(manifest),sha256='bad' if fault=='base_pin' else F.sha(manifest)),gcloud_config=str(p)),
        release=dict(transport=dict(path=str(transport))),spec=dict(artifact=dict(path=str(artifact),sha256='bad' if fault=='artifact' else F.sha(artifact)),step=544))
    monkeypatch.setattr(S,'room',lambda *a:None)
    def copy(parts,target,*a,**kw):Path(target).write_bytes(b'x');return dict(bytes=1)
    monkeypatch.setattr(S,'copy_parts',copy)
    monkeypatch.setattr(S,'unpack',lambda *a,**kw:{'a':dict(bytes=2 if fault=='base_member' else 1,sha256='1'*64)})
    monkeypatch.setattr(S,'extract_stream',lambda *a,**kw:{})
    monkeypatch.setattr(S,'config_metadata',lambda *a:{})
    # The export directory must be created by stage; choose an artifact mapping
    # whose parent tree exists only when the artifact is inspected.
    def physical(root,path):
        if path==str(artifact):
            return p/'out/m544/artifact.json'
        return Path(path)
    def extract(stream,destination,step,*args,**kw):
        if step is not None:
            target=Path(destination)/'m544/artifact.json';target.parent.mkdir(parents=True);target.write_bytes(b'{}')
        return {}
    monkeypatch.setattr(S,'extract_stream',extract)
    with pytest.raises(ValueError):S.stage(p,config,physical)
    receipt=json.loads((p/'STAGING.json').read_text())
    assert receipt['phases']['start'] and not receipt['phases'].get('videos')


def test_record_stdin_submission_and_uncertain_output():
    p=fresh('record');L.prepare('p0123456789',p,mode='proof')
    (p/'SUBMIT.out').write_text('12345;cluster\n')
    assert L.submission_record(p)['job']==12345
    with pytest.raises(FileExistsError):L.submission_record(p)
    (p/'SUBMIT.out').write_text('connection dropped\n')
    with pytest.raises(ValueError,match='uncertain'):L.submission_record(p)
